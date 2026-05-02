# services/meal_plan_service.py
import random
from django.db.models import Q
from .nutrition_service import calculate_targets
from users.models import MealPlan, MealPlanDay, MealPlanItem
from nutrition.models import FoodItem

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

MEAL_CALORIE_SPLIT = {
    'breakfast': 0.25,
    'lunch': 0.35,       
    'dinner': 0.30,      
    'snack': 0.10,       
}


def get_foods_for_meal(meal_type, target_calories):
    # Get local foods first
    local_foods = list(
        FoodItem.objects.filter(
            source='local',
            calories_per_100g__gt = 0
        )
    )

    usda_foods = list(
        FoodItem.objects.filter(
            source='usda',
            calories_per_100g__gt=0
        )
    )

    # Prioritize local Kenyan foods
    all_foods = local_foods + usda_foods

    if not all_foods:
        return []

    # Pick foods that reasonably fit the calorie target
    suitable = [
        f for f in all_foods
        if (target_calories * 0.3) <= f.calories_per_100g <= (target_calories * 1.5)
    ]
    if not suitable:
        suitable = all_foods

    return random.sample(suitable, min(2, len(suitable)))


def generate_meal_plan(user):
    profile = user.profile
    targets = calculate_targets(profile)

    # Deactivate old meal plans
    MealPlan.objects.filter(user=user, is_active=True).update(is_active=False)

    # Create new meal plan
    meal_plan = MealPlan.objects.create(
        user=user,
        name=f"7-Day {profile.get_goal_type_display()} Plan",
        goal=profile.goal_type,
        target_calories=targets['calories'],
        target_protein=targets['protein'],
        target_carbs=targets['carbs'],
        target_fat=targets['fat'],
    )

    # Generate each day
    for day in DAYS:
        plan_day = MealPlanDay.objects.create(
            meal_plan=meal_plan,
            day=day
        )

        # Generate each meal for the day
        for meal_type, split in MEAL_CALORIE_SPLIT.items():
            meal_target_calories = targets['calories'] * split
            foods = get_foods_for_meal(meal_type, meal_target_calories)

            for food in foods:
                # Calculate quantity needed to hit calorie target
                quantity = round((meal_target_calories / food.calories_per_100g) * 100, 1) if food.calories_per_100g else 100.0

                MealPlanItem.objects.create(
                    meal_plan_day=plan_day,
                    food=food,
                    meal_type=meal_type,
                    quantity=quantity,
                    quantity_unit = 'g',
                )

    return meal_plan