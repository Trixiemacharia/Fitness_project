# services/meal_plan_service.py
import random
from django.db.models import Q
from .nutrition_service import calculate_targets
from myapp.models import Food, MealPlan, MealPlanDay, MealPlanItem

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

MEAL_CALORIE_SPLIT = {
    'breakfast': 0.25,   # 25% of daily calories
    'lunch': 0.35,       # 35%
    'dinner': 0.30,      # 30%
    'snack': 0.10,       # 10%
}


def get_foods_for_meal(meal_type, target_calories):
    """
    Fetch suitable foods from DB for a meal type
    Prioritize local Kenyan foods, supplement with USDA
    """
    # Get local foods first
    local_foods = list(
        Food.objects.filter(
            source='local',
            calories__isnull=False,
            calories__gt=0
        )
    )

    usda_foods = list(
        Food.objects.filter(
            source='usda',
            calories__isnull=False,
            calories__gt=0
        )
    )

    # Prioritize local Kenyan foods
    available_foods = local_foods + usda_foods

    if not available_foods:
        return []

    # Pick foods that reasonably fit the calorie target
    suitable = [
        f for f in available_foods
        if f.calories and (target_calories * 0.5) <= f.calories <= (target_calories * 1.5)
    ]

    # Fallback to any food if nothing fits
    if not suitable:
        suitable = available_foods

    return random.sample(suitable, min(2, len(suitable)))


def generate_meal_plan(user):
    """
    Generates a 7-day meal plan based on user's fitness goal
    """
    profile = user.profile
    targets = calculate_targets(profile)

    # Deactivate old meal plans
    MealPlan.objects.filter(user=user, is_active=True).update(is_active=False)

    # Create new meal plan
    meal_plan = MealPlan.objects.create(
        user=user,
        name=f"7-Day {profile.get_goal_display()} Plan",
        goal=profile.goal,
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
            meal_calories = targets['calories'] * split
            foods = get_foods_for_meal(meal_type, meal_calories)

            for food in foods:
                # Calculate quantity needed to hit calorie target
                quantity = round(meal_calories / food.calories, 1) if food.calories else 1.0

                MealPlanItem.objects.create(
                    meal_plan_day=plan_day,
                    food=food,
                    meal_type=meal_type,
                    quantity=quantity,
                )

    return meal_plan