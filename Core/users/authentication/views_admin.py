from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
import json
from datetime import timedelta, date

from users.models import UserProfile
from exercises.models import Exercise, ExerciseLog, Category
from nutrition.models import FoodItem, MealLog


# ── Guard: only staff / superusers may enter ────────────────────────────────
def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin, login_url='dashboard')   # non-admins bounce to their own dashboard
def admin_dashboard(request):
    today = timezone.now().date()
    thirty_days_ago  = today - timedelta(days=30)
    seven_days_ago   = today - timedelta(days=7)
    ninety_days_ago  = today - timedelta(days=90)

    # ════════════════════════════════════════════════
    # 1. USER REPORTS
    # ════════════════════════════════════════════════
    total_users = User.objects.filter(is_staff=False).count()

    # Daily new registrations for the last 30 days
    daily_registrations = (
        User.objects.filter(is_staff=False, date_joined__date__gte=thirty_days_ago)
        .annotate(day=TruncDay('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    reg_labels = [r['day'].strftime('%b %d') for r in daily_registrations]
    reg_data   = [r['count'] for r in daily_registrations]

    # Weekly registrations (last 12 weeks)
    twelve_weeks_ago = today - timedelta(weeks=12)
    weekly_registrations = (
        User.objects.filter(is_staff=False, date_joined__date__gte=twelve_weeks_ago)
        .annotate(week=TruncWeek('date_joined'))
        .values('week')
        .annotate(count=Count('id'))
        .order_by('week')
    )
    weekly_reg_labels = [r['week'].strftime('%b %d') for r in weekly_registrations]
    weekly_reg_data   = [r['count'] for r in weekly_registrations]

    # Monthly registrations (last 12 months)
    twelve_months_ago = today - timedelta(days=365)
    monthly_registrations = (
        User.objects.filter(is_staff=False, date_joined__date__gte=twelve_months_ago)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_reg_labels = [r['month'].strftime('%b %Y') for r in monthly_registrations]
    monthly_reg_data   = [r['count'] for r in monthly_registrations]

    # DAU / MAU
    dau_ids = ExerciseLog.objects.filter(
        updated_at__date=today
    ).values_list('user_id', flat=True).distinct()
    dau = len(set(dau_ids))

    mau_ids = ExerciseLog.objects.filter(
        updated_at__date__gte=thirty_days_ago
    ).values_list('user_id', flat=True).distinct()
    mau = len(set(mau_ids))

    # Active vs inactive (active = logged workout in last 30 days)
    active_user_ids   = set(mau_ids)
    inactive_users    = total_users - len(active_user_ids)
    active_users      = len(active_user_ids)

    # Retention: users who joined > 30 days ago AND have activity in last 30 days
    old_users = set(
        User.objects.filter(is_staff=False, date_joined__date__lte=thirty_days_ago)
        .values_list('id', flat=True)
    )
    retained_users = len(old_users & active_user_ids)
    churned_users  = len(old_users) - retained_users

    # New registrations this month vs inactive
    new_this_month = User.objects.filter(
        is_staff=False, date_joined__date__gte=thirty_days_ago
    ).count()

    # ════════════════════════════════════════════════
    # 2. WORKOUT & ACTIVITY REPORTS
    # ════════════════════════════════════════════════

    # Most popular exercises (by log count)
    popular_exercises = (
        ExerciseLog.objects.values('exercise__name')
        .annotate(log_count=Count('id'))
        .order_by('-log_count')[:10]
    )
    popular_ex_labels = [e['exercise__name'] for e in popular_exercises]
    popular_ex_data   = [e['log_count'] for e in popular_exercises]

    # Average workouts per user (exercise log entries per active user)
    avg_workouts_per_user = round(
        ExerciseLog.objects.count() / max(total_users, 1), 1
    )

    # Workout completion rate
    total_logs     = ExerciseLog.objects.count()
    completed_logs = sum(1 for log in ExerciseLog.objects.select_related('exercise') if log.is_completed)
    completion_rate = round((completed_logs / max(total_logs, 1)) * 100, 1)
    not_completed   = 100 - completion_rate

    # Category breakdown (for pie chart)
    category_breakdown = (
        ExerciseLog.objects.values('exercise__category__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    category_labels = [c['exercise__category__name'] or 'Uncategorized' for c in category_breakdown]
    category_data   = [c['count'] for c in category_breakdown]

    # ════════════════════════════════════════════════
    # 3. NUTRITION REPORTS
    # ════════════════════════════════════════════════

    # Most logged foods
    most_logged_foods = (
        MealLog.objects.values('food_item__name')
        .annotate(log_count=Count('id'))
        .order_by('-log_count')[:10]
    )
    food_labels = [f['food_item__name'] for f in most_logged_foods]
    food_data   = [f['log_count'] for f in most_logged_foods]

    # Average calorie intake per user per day (last 30 days)
    calorie_logs = MealLog.objects.filter(date__gte=thirty_days_ago).select_related('food_item')
    total_calories_logged = sum(log.calories for log in calorie_logs)
    avg_calories_per_user = round(total_calories_logged / max(active_users, 1) / 30, 0)

    # Custom vs database foods
    custom_food_count = FoodItem.objects.filter(is_custom=True).count()
    db_food_count     = FoodItem.objects.filter(is_custom=False).count()

    # Daily calorie trend (last 30 days)
    calorie_by_day = (
        MealLog.objects.filter(date__gte=thirty_days_ago)
        .values('date')
        .annotate(
            total_cals=Sum(
                # approximation: portion_size / 100 * calories_per_100g
                # We use a raw expression but keep it simple via property sum
                Count('id')   # placeholder – see template note
            )
        )
        .order_by('date')
    )
    # Simpler: pull per-user daily averages
    daily_calorie_labels = []
    daily_calorie_data   = []
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        logs = MealLog.objects.filter(date=day).select_related('food_item')
        day_cal = sum(l.calories for l in logs)
        daily_calorie_labels.append(day.strftime('%b %d'))
        daily_calorie_data.append(round(day_cal, 1))

    # ════════════════════════════════════════════════
    # 4. GOAL TRACKING
    # ════════════════════════════════════════════════
    goal_distribution = (
        UserProfile.objects.values('goal_type')
        .annotate(count=Count('user'))
        .order_by('-count')
    )
    goal_labels = [g['goal_type'].replace('_', ' ').title() for g in goal_distribution]
    goal_data   = [g['count'] for g in goal_distribution]

    fitness_level_dist = (
        UserProfile.objects.values('fitness_level')
        .annotate(count=Count('user'))
        .order_by('-count')
    )
    fitness_labels = [f['fitness_level'].title() for f in fitness_level_dist]
    fitness_data   = [f['count'] for f in fitness_level_dist]

    # ════════════════════════════════════════════════
    # 5. QUICK STATS CARDS
    # ════════════════════════════════════════════════
    new_today = User.objects.filter(
        is_staff=False, date_joined__date=today
    ).count()

    new_this_week = User.objects.filter(
        is_staff=False, date_joined__date__gte=seven_days_ago
    ).count()

    context = {
        # Meta
        'today': today,

        # User stats
        'total_users':        total_users,
        'dau':                dau,
        'mau':                mau,
        'active_users':       active_users,
        'inactive_users':     inactive_users,
        'retained_users':     retained_users,
        'churned_users':      churned_users,
        'new_today':          new_today,
        'new_this_week':      new_this_week,
        'new_this_month':     new_this_month,

        # Charts — serialised as JSON for Chart.js
        'reg_labels':         json.dumps(reg_labels),
        'reg_data':           json.dumps(reg_data),
        'weekly_reg_labels':  json.dumps(weekly_reg_labels),
        'weekly_reg_data':    json.dumps(weekly_reg_data),
        'monthly_reg_labels': json.dumps(monthly_reg_labels),
        'monthly_reg_data':   json.dumps(monthly_reg_data),

        # Workout stats
        'avg_workouts_per_user': avg_workouts_per_user,
        'completion_rate':       completion_rate,
        'not_completed':         not_completed,
        'popular_ex_labels':     json.dumps(popular_ex_labels),
        'popular_ex_data':       json.dumps(popular_ex_data),
        'category_labels':       json.dumps(category_labels),
        'category_data':         json.dumps(category_data),

        # Nutrition stats
        'avg_calories_per_user':  avg_calories_per_user,
        'custom_food_count':      custom_food_count,
        'db_food_count':          db_food_count,
        'food_labels':            json.dumps(food_labels),
        'food_data':              json.dumps(food_data),
        'daily_calorie_labels':   json.dumps(daily_calorie_labels),
        'daily_calorie_data':     json.dumps(daily_calorie_data),

        # Goal stats
        'goal_labels':      json.dumps(goal_labels),
        'goal_data':        json.dumps(goal_data),
        'fitness_labels':   json.dumps(fitness_labels),
        'fitness_data':     json.dumps(fitness_data),
    }

    return render(request, 'users/admin_dashboard.html', context)