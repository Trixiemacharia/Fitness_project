import hashlib
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.utils import timezone
from .forms import OnboardingForm
from django.contrib.auth.decorators import login_required
from exercises.models import Category, Exercise, ExerciseLog
from django.http import JsonResponse
from django.db.models import Q, Sum
from exercises.serializers import CategorySerializer
from nutrition.models import MealLog
from users.models import Feedback, MealPlan, ProgressLog, UserProfile


def _get_dashboard_goal_copy(profile):
    goal_label = profile.get_goal_type_display() if getattr(profile, "goal_type", None) else "Fitness Goal"
    goal_messages = {
        "tone": "Welcome!! Ready to kick-start your fitness journey and stay consistent today?",
        "bulk": "Welcome!! Ready to build strength and power through your next workout?",
        "lose_weight": "Welcome!! Ready to kick-start your fitness journey and keep moving toward your target?",
    }
    return goal_label, goal_messages.get(profile.goal_type, "Ready to kick-start your fitness journey today?")


@login_required
def create_profile(request):
    if request.method == 'POST':
        form = OnboardingForm(request.POST)
        if form.is_valid():
            profile = form.save()
            profile.user = request.user
            profile.save()
            return redirect('dashboard')
        else:
            form = OnboardingForm()
            return render(request, 'onboarding.html', {'form': form})


@login_required
def view_profile(request):
    profile = request.user.profile
    return render(request, 'profile_detail.html', {'profile': profile})


@login_required
def update_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(view_profile)
        else:
            form = OnboardingForm(instance=profile)
            return render(request, 'profile_edit.html', {'form': form})


@login_required
def delete_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.delete()
        return redirect('home')
    return render(request, 'confirm_delete.html')


@login_required
def dashboard(request):
    try:
        profile = request.user.profile
    except Exception:
        return redirect("onboarding")

    categories = Category.objects.all()
    dashboard_goal_label, dashboard_goal_message = _get_dashboard_goal_copy(profile)

    return render(request, "users/dashboard.html", {
        "profile": profile,
        "categories": categories,
        "dashboard_goal_label": dashboard_goal_label,
        "dashboard_goal_message": dashboard_goal_message,
    })


@login_required
def search_dashboard_workouts(request):
    query = request.GET.get('q', '').strip()

    if not query:
        categories = Category.objects.prefetch_related('exercises', 'muscle_groups').all()
    else:
        categories = Category.objects.prefetch_related('exercises', 'muscle_groups').filter(
            Q(name__icontains=query) |
            Q(exercises__name__icontains=query)
        ).distinct()

    serializer = CategorySerializer(categories, many=True, context={'request': request})
    return JsonResponse({'results': serializer.data})


@login_required
def upload_profile_image(request):
    if request.method == 'POST':
        profile = request.user.profile
        image = request.FILES.get('profile_image')

        if image:
            profile.profile_image = image
            profile.save()
            return JsonResponse({
                'success': True,
                'image_url': profile.profile_image.url,
            })

    return JsonResponse({'success': False})


@login_required
def toggle_backup_reminder(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.backup_reminder = not profile.backup_reminder
        profile.save()
        return JsonResponse({'status': profile.backup_reminder})


@login_required
def dashboard_summary(request):
    profile = request.user.profile
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_goal = _get_weekly_goal(request.user)
    calorie_target = _get_daily_calorie_target(profile)

    today_log = ProgressLog.objects.filter(user=request.user, date=today).first()
    week_logs = ProgressLog.objects.filter(
        user=request.user, date__range=(week_start, week_end)
    ).order_by('date')
    meal_logs_today = MealLog.objects.filter(
        user=request.user, date=today
    ).select_related('food_item')

    # ── Weekly stats (used for charts only) ──────────────────────────
    completed_workouts_week = week_logs.filter(workout_done=True).count()
    completed_today_count = _get_completed_workouts_today_count(request.user, today)
    daily_workout_target = 4
    weekly_calories = week_logs.aggregate(total=Sum('calories_burned'))['total'] or 0
    weekly_calorie_target = calorie_target * 7
    weekly_progress = min(
        round((completed_workouts_week / max(weekly_goal, 1)) * 100),
        100,
    )

    # ── Today's stats ────────────────────────────────────────────────
    calories_burned_today = today_log.calories_burned if today_log else 0
    completed_today = today_log.workout_done if today_log else False

    # ── Daily calorie progress ───────────────────────────────────────
    calories_remaining = calorie_target - calories_burned_today  # can be negative
    progress_percent = min(
        round((calories_burned_today / max(calorie_target, 1)) * 100), 100
    )

    # Contextual calorie-remaining message
    if calories_remaining > 0:
        calorie_message = f"You're {calories_remaining} kcal away from today's goal"
    else:
        calorie_message = "You've hit your goal 🎉"

    suggestions = _get_suggested_workouts(profile, request.user, today)
    workout_videos = _get_workout_videos(suggestions, limit=3)
    meal_plan_preview = _build_meal_plan_preview(request.user, today, profile.wants_meal_plan)

    workout_counts_by_day = {
        log.date: 1 if log.workout_done else 0
        for log in week_logs
    }
    calorie_balance = []
    activity_series = []
    for day_index in range(7):
        day = week_start + timedelta(days=day_index)
        log = next((item for item in week_logs if item.date == day), None)
        calories = log.calories_burned if log else 0
        calorie_balance.append(calories - calorie_target)
        activity_series.append({
            'label': day.strftime('%a'),
            'workouts': workout_counts_by_day.get(day, 0),
            'steps': log.steps if log else 0,
            'calories_burned': calories,
        })

    # ── Daily reminders & insights ───────────────────────────────────
    reminders = _build_dashboard_reminders(meal_logs_today, today_log, completed_today)
    insights = _build_dashboard_insights(today_log, calorie_target, completed_today)

    today_progress = None
    if today_log:
        today_progress = {
            'date': today.isoformat(),
            'progress_percent': progress_percent,
            'calories_burned': calories_burned_today,
            'calorie_target': calorie_target,
            # Raw number for JS to build its own message if needed
            'calories_remaining': calories_remaining,
            # Human-readable contextual message
            'calorie_message': calorie_message,
            'workout_done': today_log.workout_done,
            'steps': today_log.steps,
            'water_intake': today_log.water_intake,
            'water_goal': 8,
        }
    else:
        # No log yet — still expose target so UI can show it
        today_progress = {
            'date': today.isoformat(),
            'progress_percent': 0,
            'calories_burned': 0,
            'calorie_target': calorie_target,
            'calories_remaining': calorie_target,
            'calorie_message': f"You're {calorie_target} kcal away from today's goal",
            'workout_done': False,
            'steps': 0,
            'water_intake': 0,
            'water_goal': 8,
        }

    return JsonResponse({
        'today_activity': {
            'has_record': today_log is not None,
            'message': '' if today_log else 'No activity recorded today',
            'date': today.isoformat(),
            'calories_burned': calories_burned_today,
            'steps': today_log.steps if today_log else 0,
            'water_intake': today_log.water_intake if today_log else 0,
            'workout_done': completed_today,
            'completed_workouts_count': completed_today_count,
            'daily_workout_target': daily_workout_target,
        },
        'goal_progress': today_progress,
        'weekly_stats': {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'weekly_goal': weekly_goal,
            'completed_workouts': completed_workouts_week,
            'completed_today': completed_today_count,
            'daily_workout_target': daily_workout_target,
            'progress_percent': weekly_progress,
            'weekly_calories': weekly_calories,
            'weekly_calorie_target': weekly_calorie_target,
            'activity_series': activity_series,
            'calorie_balance': calorie_balance,
            'current_streak': _get_current_workout_streak(request.user, today),
        },
        'meal_plan_enabled': profile.wants_meal_plan,
        'meal_plan_preview': meal_plan_preview,
        'suggested_workouts': suggestions,
        'workout_videos': workout_videos,
        'reminders': reminders,
        'insights': insights,
    })


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_weekly_goal(user):
    preferred_days = []
    if hasattr(user, 'preferences') and user.preferences.preferred_days:
        preferred_days = user.preferences.preferred_days
    return max(len(preferred_days), 4)


def _get_daily_calorie_target(profile):
    """
    Returns how many kcal the user should aim to burn TODAY based on their goal.
    Values are intentional and goal-driven — not random.
    """
    targets = {
        'lose_weight': 450,
        'tone': 400,
        'bulk': 300,
    }
    return targets.get(profile.goal_type, 400)


def _build_meal_plan_preview(user, today, wants_meal_plan):
    if not wants_meal_plan:
        return None

    current_meal_plan = (
        MealPlan.objects.filter(user=user, is_active=True)
        .prefetch_related('days__items__food')
        .first()
    )
    if not current_meal_plan:
        return None

    day_key = today.strftime('%A').lower()
    day_plan = current_meal_plan.days.filter(day=day_key).first()
    if not day_plan:
        return {
            'name': current_meal_plan.name,
            'goal': current_meal_plan.goal.replace('_', ' ').title(),
            'target_calories': current_meal_plan.target_calories,
            'meals': [],
        }

    meals = []
    for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
        items = day_plan.items.filter(meal_type=meal_type)
        if not items.exists():
            continue
        meals.append({
            'meal_type': meal_type.title(),
            'items': [
                {
                    'food': item.food.name,
                    'quantity': item.quantity,
                    'unit': item.quantity_unit,
                    'calories': item.calories,
                }
                for item in items
            ],
        })

    return {
        'name': current_meal_plan.name,
        'goal': current_meal_plan.goal.replace('_', ' ').title(),
        'target_calories': current_meal_plan.target_calories,
        'meals': meals,
    }


def _stable_daily_order(exercises, user, day):
    def score(exercise):
        key = f"{user.id}:{day.isoformat()}:{exercise.id}".encode('utf-8')
        return hashlib.md5(key).hexdigest()

    return sorted(exercises, key=score)


def _get_suggested_workouts(profile, user, day, limit=4):
    focus_map = {
        'glutes': ['glutes', 'lower_body'],
        'legs': ['lower_body', 'glutes'],
        'abs': ['core'],
        'arms': ['upper_body'],
        'back': ['upper_body'],
        'shoulder': ['upper_body'],
    }
    focus_areas = profile.prefered_focus or []
    target_groups = []
    for focus in focus_areas:
        target_groups.extend(focus_map.get(focus, []))

    base_qs = Exercise.objects.select_related('muscle_group', 'category').filter(
        level=profile.fitness_level
    )
    relevant_filter = Q()
    if target_groups:
        relevant_filter |= Q(muscle_group__name__in=target_groups)
    if focus_areas:
        for focus in focus_areas:
            relevant_filter |= Q(name__icontains=focus.replace('_', ' '))
            relevant_filter |= Q(description__icontains=focus.replace('_', ' '))

    relevant = list(base_qs.filter(relevant_filter).distinct()) if relevant_filter else []
    fallback = list(base_qs.exclude(id__in=[e.id for e in relevant]))
    if len(relevant) < limit:
        fallback.extend(
            list(
                Exercise.objects.select_related('muscle_group', 'category')
                .exclude(id__in=[e.id for e in relevant + fallback])
            )
        )

    ordered = _stable_daily_order(relevant, user, day) + _stable_daily_order(fallback, user, day)
    picked = ordered[:max(limit, 4)]

    return [
        {
            'id': e.id,
            'name': e.name,
            'duration': _exercise_duration_label(e),
            'difficulty': e.get_level_display(),
            'target_muscle': (
                e.muscle_group.get_name_display() if e.muscle_group else e.category.name
            ),
            'description': e.description,
            'video_url': e.get_demo_video_url(),
            'thumbnail': e.get_image_url(),
            'computed_sets': e.get_sets(),
            'exercise_type': e.exercise_type,
            'estimated_calories_burned': e.get_estimated_calories_burned(),
        }
        for e in picked
    ]


def _get_workout_videos(suggestions, limit=3):
    suggestion_ids = [item['id'] for item in suggestions]
    videos = list(
        Exercise.objects.select_related('muscle_group')
        .filter(id__in=suggestion_ids)
    )
    videos = [video for video in videos if video.get_demo_video_url()]
    return [
        {
            'id': e.id,
            'title': e.name,
            'duration': _exercise_duration_label(e),
            'difficulty': e.get_level_display(),
            'target_muscle': (
                e.muscle_group.get_name_display() if e.muscle_group else e.category.name
            ),
            'description': e.description,
            'thumbnail': e.get_image_url(),
            'video_url': e.get_demo_video_url(),
            'computed_sets': e.get_sets(),
        }
        for e in videos[:limit]
    ]


def _exercise_duration_label(exercise):
    if exercise.duration:
        return exercise.duration
    if exercise.exercise_type == 'hiit':
        return f"{exercise.get_work_time() * exercise.get_rounds() // 60 or 1} min"
    if exercise.exercise_type == 'strength':
        return f"{exercise.get_sets() * 4} min"
    if exercise.exercise_type == 'mobility':
        return "10 min"
    return "12 min"


def _get_completed_workouts_today_count(user, today):
    logs = ExerciseLog.objects.filter(user=user, updated_at__date=today).select_related('exercise')
    return sum(1 for log in logs if log.is_completed)


def _get_current_workout_streak(user, today):
    streak = 0
    cursor = today
    while True:
        if not ProgressLog.objects.filter(user=user, date=cursor, workout_done=True).exists():
            break
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _build_dashboard_reminders(meal_logs_today, today_log, completed_today):
    """Daily reminders — scoped entirely to today."""
    reminders = []

    if not meal_logs_today.filter(meal_type='breakfast').exists():
        reminders.append({'id': 'breakfast', 'text': "You haven't logged breakfast yet today"})

    water_intake = today_log.water_intake if today_log else 0
    if water_intake < 8:
        behind = 8 - water_intake
        reminders.append({'id': 'water', 'text': f"You're {behind} cups behind on today's water goal"})

    if not completed_today:
        reminders.append({'id': 'workout', 'text': "You haven't completed today's workout yet"})

    return reminders[:3]


def _build_dashboard_insights(today_log, calorie_target, completed_today):
    """Daily insights — all scoped to today."""
    insights = []

    # 1. Calorie burn progress (daily, dynamic)
    calories_burned = today_log.calories_burned if today_log else 0
    calorie_gap = calorie_target - calories_burned
    if calorie_gap > 0:
        insights.append(f"You're {calorie_gap} kcal away from today's burn target.")
    else:
        insights.append("You've hit your calorie burn goal today 🎉")

    # 2. Workout status (daily)
    if completed_today:
        insights.append("Today's workout is done — great work!")
    else:
        insights.append("No workout logged yet today — you've still got time!")

    # 3. Hydration (daily)
    water = today_log.water_intake if today_log else 0
    if water >= 8:
        insights.append("You're well hydrated today 💧")
    elif water >= 4:
        insights.append(f"You've had {water} of 8 cups today — keep sipping!")
    else:
        insights.append("Drink more water today — aim for 8 cups 💧")

    return insights


# ── Feedback ───────────────────────────────────────────────────────────────────

@login_required
def feedback_entries(request):
    if request.method == 'GET':
        entries = Feedback.objects.filter(user=request.user)
        return JsonResponse({
            'results': [
                {
                    'id': entry.id,
                    'category': entry.get_category_display(),
                    'status': entry.get_status_display(),
                    'message': entry.message,
                    'admin_response': entry.admin_response,
                    'created_at': timezone.localtime(entry.created_at).strftime('%Y-%m-%d %H:%M'),
                    'responded_at': (
                        timezone.localtime(entry.responded_at).strftime('%Y-%m-%d %H:%M')
                        if entry.responded_at else ''
                    ),
                }
                for entry in entries
            ]
        })

    category = request.POST.get('category', 'feature')
    message = (request.POST.get('message') or '').strip()
    if not message:
        return JsonResponse({'error': 'Message is required.'}, status=400)

    entry = Feedback.objects.create(
        user=request.user,
        category=category,
        message=message,
    )
    return JsonResponse({
        'success': True,
        'entry': {
            'id': entry.id,
            'category': entry.get_category_display(),
            'status': entry.get_status_display(),
            'message': entry.message,
            'admin_response': entry.admin_response,
            'created_at': timezone.localtime(entry.created_at).strftime('%Y-%m-%d %H:%M'),
            'responded_at': '',
        }
    }, status=201)


# ── Progress log ───────────────────────────────────────────────────────────────

@login_required
def progress_log_entry(request):
    today = timezone.localdate()
    date_param = request.GET.get('date') if request.method == 'GET' else request.POST.get('date')
    target_date = today
    if date_param:
        try:
            target_date = datetime.fromisoformat(date_param).date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    if request.method == 'GET':
        log = ProgressLog.objects.filter(user=request.user, date=target_date).first()
        if not log:
            return JsonResponse({'has_record': False, 'date': target_date.isoformat()})
        return JsonResponse({
            'has_record': True,
            'date': log.date.isoformat(),
            'calories_burned': log.calories_burned,
            'workout_done': log.workout_done,
            'steps': log.steps,
            'water_intake': log.water_intake,
        })

    progress_log, _ = ProgressLog.objects.get_or_create(user=request.user, date=target_date)
    if 'calories_burned' in request.POST:
        progress_log.calories_burned = int(request.POST.get('calories_burned') or 0)
    if 'steps' in request.POST:
        progress_log.steps = int(request.POST.get('steps') or 0)
    if 'water_intake' in request.POST:
        progress_log.water_intake = int(request.POST.get('water_intake') or 0)
    if 'workout_done' in request.POST:
        progress_log.workout_done = request.POST.get('workout_done') in ('true', 'True', '1', 'on')

    if progress_log.is_empty():
        progress_log.delete()
        return JsonResponse({'success': True, 'deleted': True, 'date': target_date.isoformat()})

    progress_log.save()
    return JsonResponse({
        'success': True,
        'date': progress_log.date.isoformat(),
        'calories_burned': progress_log.calories_burned,
        'workout_done': progress_log.workout_done,
        'steps': progress_log.steps,
        'water_intake': progress_log.water_intake,
    })
