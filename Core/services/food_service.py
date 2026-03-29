# services/food_service.py
import requests
from django.conf import settings
from django.core.cache import cache
from nutrition.models import FoodItem


def search_food(query):
    cache_key = f"food_search_{query.lower().strip()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Step 1: get local results
    local_results = list(FoodItem.objects.filter(
        name__icontains=query
    ).values(
        'id', 'name', 'category', 'calories_per_100g',
        'protein_per_100g', 'carbs_per_100g', 'fats_per_100g',
        'fiber_per_100g', 'serving_unit', 'default_serving_size'
    ))

    # Step 2: ALWAYS call USDA too — don't skip it
    local_names = {r['name'].lower() for r in local_results}
    usda_results = fetch_from_usda(query)

    for item in usda_results:
        if item['name'].lower() in local_names:
            continue  # already have it, skip

        # Save to DB so next search is instant
        food, _ = FoodItem.objects.get_or_create(
            name=item['name'],
            source='usda',
            defaults={
                'category':           'staples',
                'calories_per_100g':  item.get('calories', 0),
                'protein_per_100g':   item.get('protein', 0),
                'carbs_per_100g':     item.get('carbs', 0),
                'fats_per_100g':      item.get('fat', 0),
                'fiber_per_100g':     item.get('fiber', 0),
                'usda_fdc_id':        item.get('fdc_id'),
            }
        )
        local_results.append({
            'id':                   food.id,
            'name':                 food.name,
            'category':             food.category,
            'calories_per_100g':    food.calories_per_100g,
            'protein_per_100g':     food.protein_per_100g,
            'carbs_per_100g':       food.carbs_per_100g,
            'fats_per_100g':        food.fats_per_100g,
            'fiber_per_100g':       food.fiber_per_100g,
            'serving_unit':         food.serving_unit,
            'default_serving_size': food.default_serving_size,
        })

    cache.set(cache_key, local_results, timeout=3600)
    return local_results


def fetch_from_usda(query):
    try:
        url = f"{settings.USDA_BASE_URL}/foods/search"
        params = {
            'query':    query,
            'api_key':  settings.USDA_API_KEY,
            'pageSize': 5,
            'dataType': 'Foundation,SR Legacy',
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        parsed = []
        for food in data.get('foods', []):
            nutrients = {
                n['nutrientName']: n['value']
                for n in food.get('foodNutrients', [])
            }
            name = food.get('description', '').title()
            if not name:
                continue
            parsed.append({
                'fdc_id':   food.get('fdcId'),
                'name':     name,
                'calories': nutrients.get('Energy', 0),
                'protein':  nutrients.get('Protein', 0),
                'carbs':    nutrients.get('Carbohydrate, by difference', 0),
                'fat':      nutrients.get('Total lipid (fat)', 0),
                'fiber':    nutrients.get('Fiber, total dietary', 0),
            })
        return parsed

    except requests.exceptions.RequestException as e:
        print(f"USDA API error: {e}")
        return []