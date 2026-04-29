import random
from datetime import timedelta

from django.shortcuts import render,redirect
from django.utils import timezone
from .forms import OnboardingForm
from django.contrib.auth.decorators import login_required
from exercises.models import Category, Exercise, ExerciseLog
from django.http import JsonResponse
from django.db.models import Q, Sum
from exercises.serializers import CategorySerializer
from nutrition.models import MealLog
from users.models import Feedback, MealPlan, ProgressLog, UserProfile

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
            return render(request, 'onboarding.html',{'form':form})

@login_required
def view_profile(request):
    profile = request.user.profile
    return render(request,'profile_detail.html',{'profile':profile})

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
            return render(request,'profile_edit.html',{'form': form})
        
@login_required
def delete_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.delete()
        return redirect('home')
    return render(request,'confirm_delete.html')

@login_required
def dashboard(request):
    try:
            profile = request.user.profile
    except:
        return redirect("onboarding")

    categories = Category.objects.all()

    return render(request, "users/dashboard.html", {
        "profile": profile,
        "categories": categories
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
                'image_url': profile.profile_image.url
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
    week_logs = ProgressLog.objects.filter(user=request.user, date__range=(week_start, week_end)).order_by('date')
    meal_logs_today = MealLog.objects.filter(user=request.user, date=today).select_related('food_item')

    completed_workouts = week_logs.filter(workout_done=True).count()
    weekly_calories = week_logs.aggregate(total=Sum('calories_burned'))['total'] or 0
    weekly_calorie_target = calorie_target * 7
    weekly_progress = min(
        round((completed_workouts / max(weekly_goal, 1)) * 100),
        100,
    )

    suggestions = _get_suggested_workouts(profile)
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

    reminders = _build_dashboard_reminders(meal_logs_today, today_log, completed_workouts, weekly_goal)
    insights = _build_dashboard_insights(week_logs, weekly_goal, weekly_calories, weekly_calorie_target)

    today_progress = None
    if today_log:
        calories_remaining = max(calorie_target - today_log.calories_burned, 0)
        today_progress = {
            'date': today.isoformat(),
            'progress_percent': min(round((today_log.calories_burned / max(calorie_target, 1)) * 100), 100),
            'calories_burned': today_log.calories_burned,
            'calorie_target': calorie_target,
            'calories_remaining': calories_remaining,
            'workout_done': today_log.workout_done,
            'steps': today_log.steps,
            'water_intake': today_log.water_intake,
            'water_goal': 8,
        }

    return JsonResponse({
        'today_activity': {
            'has_record': today_log is not None,
            'message': '' if today_log else 'No activity recorded today',
            'date': today.isoformat(),
            'calories_burned': today_log.calories_burned if today_log else 0,
            'steps': today_log.steps if today_log else 0,
            'water_intake': today_log.water_intake if today_log else 0,
            'workout_done': today_log.workout_done if today_log else False,
        },
        'goal_progress': today_progress,
        'weekly_stats': {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'weekly_goal': weekly_goal,
            'completed_workouts': completed_workouts,
            'progress_percent': weekly_progress,
            'weekly_calories': weekly_calories,
            'weekly_calorie_target': weekly_calorie_target,
            'activity_series': activity_series,
            'calorie_balance': calorie_balance,
        },
        'meal_plan_enabled': profile.wants_meal_plan,
        'meal_plan_preview': meal_plan_preview,
        'suggested_workouts': suggestions,
        'workout_videos': workout_videos,
        'reminders': reminders,
        'insights': insights,
    })


def _get_weekly_goal(user):
    preferred_days = []
    if hasattr(user, 'preferences') and user.preferences.preferred_days:
        preferred_days = user.preferences.preferred_days
    return max(len(preferred_days), 4)


def _get_daily_calorie_target(profile):
    targets = {
        'lose_weight': 450,
        'tone': 400,
        'bulk': 350,
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
            ]
        })

    return {
        'name': current_meal_plan.name,
        'goal': current_meal_plan.goal.replace('_', ' ').title(),
        'target_calories': current_meal_plan.target_calories,
        'meals': meals,
    }


def _get_suggested_workouts(profile, limit=4):
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

    base_qs = Exercise.objects.select_related('muscle_group', 'category').filter(level=profile.fitness_level)
    relevant_filter = Q()
    if target_groups:
        relevant_filter |= Q(muscle_group__name__in=target_groups)
    if focus_areas:
        for focus in focus_areas:
            relevant_filter |= Q(name__icontains=focus.replace('_', ' '))
            relevant_filter |= Q(description__icontains=focus.replace('_', ' '))

    relevant = list(base_qs.filter(relevant_filter).distinct()) if relevant_filter else []
    fallback = list(base_qs.exclude(id__in=[exercise.id for exercise in relevant]))
    if len(relevant) < limit:
        fallback.extend(
            list(
                Exercise.objects.select_related('muscle_group', 'category')
                .exclude(id__in=[exercise.id for exercise in relevant + fallback])
            )
        )

    random.shuffle(relevant)
    random.shuffle(fallback)
    picked = (relevant + fallback)[:max(limit, 3)]

    return [
        {
            'id': exercise.id,
            'name': exercise.name,
            'duration': _exercise_duration_label(exercise),
            'difficulty': exercise.get_level_display(),
            'target_muscle': exercise.muscle_group.get_name_display() if exercise.muscle_group else exercise.category.name,
            'description': exercise.description,
            'video_url': exercise.demo_video or '',
            'thumbnail': exercise.image.url if exercise.image else '',
            'computed_sets': exercise.get_sets(),
        }
        for exercise in picked
    ]


def _get_workout_videos(suggestions, limit=3):
    suggestion_ids = [item['id'] for item in suggestions]
    videos = list(
        Exercise.objects.select_related('muscle_group')
        .filter(id__in=suggestion_ids)
        .exclude(demo_video__isnull=True)
        .exclude(demo_video='')
    )
    if len(videos) < limit:
        existing_ids = [item.id for item in videos]
        filler = list(
            Exercise.objects.select_related('muscle_group')
            .exclude(id__in=existing_ids)
            .exclude(demo_video__isnull=True)
            .exclude(demo_video='')
        )
        random.shuffle(filler)
        videos.extend(filler[:limit - len(videos)])

    random.shuffle(videos)
    return [
        {
            'id': exercise.id,
            'title': exercise.name,
            'duration': _exercise_duration_label(exercise),
            'difficulty': exercise.get_level_display(),
            'target_muscle': exercise.muscle_group.get_name_display() if exercise.muscle_group else exercise.category.name,
            'description': exercise.description,
            'thumbnail': exercise.image.url if exercise.image else '',
            'video_url': exercise.demo_video,
            'computed_sets': exercise.get_sets(),
        }
        for exercise in videos[:limit]
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


def _build_dashboard_reminders(meal_logs_today, today_log, completed_workouts, weekly_goal):
    reminders = []
    if not meal_logs_today.filter(meal_type='breakfast').exists():
        reminders.append({'id': 'breakfast', 'text': "You haven't logged breakfast yet"})
    if not today_log or today_log.water_intake < 8:
        behind = max(8 - (today_log.water_intake if today_log else 0), 0)
        reminders.append({'id': 'water', 'text': f"You're {behind} cups behind on water"})
    if not today_log or not today_log.workout_done:
        reminders.append({'id': 'workout', 'text': f'{max(weekly_goal - completed_workouts, 0)} workouts left to hit your weekly goal'})
    return reminders[:3]


def _build_dashboard_insights(week_logs, weekly_goal, weekly_calories, weekly_calorie_target):
    weekday_logs = week_logs.filter(date__week_day__in=[2, 3, 4, 5, 6], workout_done=True).count()
    workout_days = week_logs.filter(workout_done=True).count()
    weekday_consistency = round((weekday_logs / max(5, 1)) * 100)
    calorie_gap = max(weekly_calorie_target - weekly_calories, 0)
    completion_rate = round((workout_days / max(weekly_goal, 1)) * 100)
    return [
        f'Weekday consistency is at {weekday_consistency}% this week.',
        f'You are {calorie_gap} kcal away from your weekly burn target.',
        f'Workout completion is {completion_rate}% of your weekly goal so far.',
    ]


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
                    'responded_at': timezone.localtime(entry.responded_at).strftime('%Y-%m-%d %H:%M') if entry.responded_at else '',
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


@login_required
def progress_log_entry(request):
    today = timezone.localdate()
    if request.method == 'GET':
        log = ProgressLog.objects.filter(user=request.user, date=today).first()
        if not log:
            return JsonResponse({'has_record': False, 'date': today.isoformat()})
        return JsonResponse({
            'has_record': True,
            'date': log.date.isoformat(),
            'calories_burned': log.calories_burned,
            'workout_done': log.workout_done,
            'steps': log.steps,
            'water_intake': log.water_intake,
        })

    calories_burned = int(request.POST.get('calories_burned') or 0)
    steps = int(request.POST.get('steps') or 0)
    water_intake = int(request.POST.get('water_intake') or 0)
    workout_done = request.POST.get('workout_done') in ('true', 'True', '1', 'on')

    if calories_burned == 0 and steps == 0 and water_intake == 0 and not workout_done:
        ProgressLog.objects.filter(user=request.user, date=today).delete()
        return JsonResponse({'success': True, 'deleted': True, 'date': today.isoformat()})

    progress_log, _ = ProgressLog.objects.get_or_create(user=request.user, date=today)
    progress_log.calories_burned = calories_burned
    progress_log.steps = steps
    progress_log.water_intake = water_intake
    progress_log.workout_done = workout_done
    progress_log.save()
    return JsonResponse({
        'success': True,
        'date': progress_log.date.isoformat(),
        'calories_burned': progress_log.calories_burned,
        'workout_done': progress_log.workout_done,
        'steps': progress_log.steps,
        'water_intake': progress_log.water_intake,
    })
