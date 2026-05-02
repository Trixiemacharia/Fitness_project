# services/dashboard_service.py
from django.utils import timezone
from django.db.models import Sum, Avg
from datetime import timedelta
from myapp.models import MealLog, MealPlan, WeightLog
from .nutrition_service import calculate_targets


def get_daily_progress(user, date=None):
    """
    Compare what user ate today vs their targets
    """
    if not date:
        date = timezone.now().date()

    # Get user targets
    targets = calculate_targets(user.profile)

    # Get today's meal logs
    logs = MealLog.objects.filter(
        user=user,
        date_logged=date
    ).select_related('food')

    # Aggregate totals
    totals = logs.aggregate(
        calories=Sum('total_calories'),
        protein=Sum('total_protein'),
        carbs=Sum('total_carbs'),
        fat=Sum('total_fat'),
    )

    # Replace None with 0
    consumed = {k: round(v or 0, 1) for k, v in totals.items()}

    # Calculate remaining
    remaining = {
        'calories': round(targets['calories'] - consumed['calories'], 1),
        'protein': round(targets['protein'] - consumed['protein'], 1),
        'carbs': round(targets['carbs'] - consumed['carbs'], 1),
        'fat': round(targets['fat'] - consumed['fat'], 1),
    }

    # Calculate % progress toward each target
    progress_pct = {
        key: round(min((consumed[key] / targets[key]) * 100, 100), 1)
        if targets[key] > 0 else 0
        for key in ['calories', 'protein', 'carbs', 'fat']
    }

    # Group meals by type
    meals_by_type = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []}
    for log in logs:
        meals_by_type[log.meal_type].append({
            'id': log.id,
            'food': log.food.name,
            'quantity': log.quantity,
            'unit': log.quantity_unit,
            'calories': log.total_calories,
            'protein': log.total_protein,
            'carbs': log.total_carbs,
            'fat': log.total_fat,
        })

    return {
        'date': str(date),
        'targets': targets,
        'consumed': consumed,
        'remaining': remaining,
        'progress_pct': progress_pct,
        'meals': meals_by_type,
    }


def get_weekly_progress(user):
    """
    Last 7 days of calorie/macro averages vs targets
    """
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)
    targets = calculate_targets(user.profile)

    # Get all logs for the last 7 days
    logs = MealLog.objects.filter(
        user=user,
        date_logged__range=[seven_days_ago, today]
    )

    # Build daily breakdown
    daily_data = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_logs = logs.filter(date_logged=day)
        day_totals = day_logs.aggregate(
            calories=Sum('total_calories'),
            protein=Sum('total_protein'),
            carbs=Sum('total_carbs'),
            fat=Sum('total_fat'),
        )
        daily_data.append({
            'date': str(day),
            'day': day.strftime('%A'),           # Monday, Tuesday etc
            'calories': round(day_totals['calories'] or 0, 1),
            'protein': round(day_totals['protein'] or 0, 1),
            'carbs': round(day_totals['carbs'] or 0, 1),
            'fat': round(day_totals['fat'] or 0, 1),
            'hit_target': (day_totals['calories'] or 0) >= (targets['calories'] * 0.9)
        })

    # Weekly averages
    avg_calories = round(
        sum(d['calories'] for d in daily_data) / 7, 1
    )

    # Streak — consecutive days hitting calorie target
    streak = 0
    for day in reversed(daily_data):
        if day['hit_target']:
            streak += 1
        else:
            break

    return {
        'daily_data': daily_data,
        'targets': targets,
        'weekly_avg_calories': avg_calories,
        'streak': streak,
        'streak_message': f"{streak} day streak! 🔥" if streak > 0 else "Log meals to start your streak"
    }


def get_weight_progress(user):
    """
    Weight trend over time
    """
    logs = WeightLog.objects.filter(user=user).order_by('date_logged')[:30]

    if not logs.exists():
        return {'logs': [], 'change': 0, 'message': 'No weight logs yet'}

    weight_data = [
        {'date': str(log.date_logged), 'weight': log.weight_kg}
        for log in logs
    ]

    first_weight = weight_data[0]['weight']
    latest_weight = weight_data[-1]['weight']
    change = round(latest_weight - first_weight, 1)

    goal = user.profile.goal
    if goal == 'lose_weight':
        on_track = change < 0
        message = "Great progress! Keep going 💪" if on_track else "Stay consistent with your deficit"
    elif goal == 'build_muscle':
        on_track = change > 0
        message = "Gaining well! 💪" if on_track else "Make sure you're in a slight surplus"
    else:
        message = "Maintaining well!" if abs(change) < 1 else "Small adjustments needed"

    return {
        'logs': weight_data,
        'starting_weight': first_weight,
        'current_weight': latest_weight,
        'change': change,
        'message': message,
    }


def get_meal_plan_vs_actual(user):
    """
    Compare today's meal plan suggestions vs what was actually eaten
    """
    today = timezone.now().date()
    day_name = today.strftime('%A').lower()   # e.g 'monday'

    try:
        meal_plan = MealPlan.objects.get(user=user, is_active=True)
        plan_day = meal_plan.days.get(day=day_name)
        plan_items = plan_day.items.select_related('food')
    except (MealPlan.DoesNotExist, Exception):
        return {'has_plan': False}

    # What was planned
    planned = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []}
    for item in plan_items:
        planned[item.meal_type].append({
            'food': item.food.name,
            'quantity': item.quantity,
            'calories': item.calories,
        })

    # What was actually eaten
    daily = get_daily_progress(user, today)

    return {
        'has_plan': True,
        'planned': planned,
        'actual': daily['meals'],
        'planned_calories': meal_plan.target_calories,
        'actual_calories': daily['consumed']['calories'],
        'adherence_pct': round(
            (daily['consumed']['calories'] / meal_plan.target_calories) * 100, 1
        ) if meal_plan.target_calories > 0 else 0
    }