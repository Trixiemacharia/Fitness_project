from datetime import date, timedelta
from collections import defaultdict

from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import UserPreferences, WeightLog, BodyMeasurement, StrengthLog, ProgressPhoto
from .progress_serializers import (
    UserPreferencesSerializer, WeightLogSerializer,
    BodyMeasurementSerializer, StrengthLogSerializer, ProgressPhotoSerializer
)
from exercises.models import ExerciseLog

# PREFERENCES
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def preferences(request):
    prefs, _ = UserPreferences.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        return Response(UserPreferencesSerializer(prefs).data)

    serializer = UserPreferencesSerializer(prefs, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

# WEIGHT LOG
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def weight_logs(request):
    if request.method == 'GET':
        logs = WeightLog.objects.filter(user=request.user)
        return Response(WeightLogSerializer(logs, many=True).data)

    data = request.data.copy()
    if 'date' not in data:
        data['date'] = date.today().isoformat()

    # Upsert — update if entry exists for that date
    existing = WeightLog.objects.filter(user=request.user, date=data['date']).first()
    if existing:
        serializer = WeightLogSerializer(existing, data=data, partial=True)
    else:
        serializer = WeightLogSerializer(data=data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_weight_log(request, pk):
    try:
        log = WeightLog.objects.get(pk=pk, user=request.user)
        log.delete()
        return Response(status=204)
    except WeightLog.DoesNotExist:
        return Response(status=404)

# BODY MEASUREMENTS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def body_measurements(request):
    if request.method == 'GET':
        entries = BodyMeasurement.objects.filter(user=request.user)
        return Response(BodyMeasurementSerializer(entries, many=True).data)

    data = request.data.copy()
    if 'date' not in data:
        data['date'] = date.today().isoformat()

    serializer = BodyMeasurementSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

# WORKOUT CONSISTENCY
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_consistency(request):
    """
    Returns workout activity for the last 12 weeks.
    Auto-calculated from ExerciseLog completions.
    Shape: { weeks: [...], current_streak: N, longest_streak: N, total_workouts: N }
    """
    logs = ExerciseLog.objects.filter(
        user=request.user,
        sets_completed__gt=0
    ).values('updated_at__date').annotate(count=Count('id')).order_by('updated_at__date')

    # Build a set of active dates
    active_dates = {entry['updated_at__date'] for entry in logs}

    # Generate last 12 weeks (84 days)
    today = date.today()
    weeks = []
    for w in range(11, -1, -1):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=w)
        week_data  = []
        for d in range(7):
            day = week_start + timedelta(days=d)
            week_data.append({
                'date':   day.isoformat(),
                'active': day in active_dates,
                'count':  next((e['count'] for e in logs if e['updated_at__date'] == day), 0),
            })
        weeks.append(week_data)

    # Streaks
    all_dates  = sorted(active_dates)
    streak     = 0
    longest    = 0
    current    = 0
    prev       = None

    for d in all_dates:
        if prev and (d - prev).days == 1:
            streak += 1
        else:
            streak = 1
        longest = max(longest, streak)
        prev = d

    # Current streak (from today backwards)
    check = today
    while check in active_dates:
        current += 1
        check -= timedelta(days=1)

    return Response({
        'weeks':           weeks,
        'current_streak':  current,
        'longest_streak':  longest,
        'total_workouts':  len(active_dates),
        'active_this_week': sum(1 for d in active_dates if (today - d).days < 7),
    })

# STRENGTH LOGS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def strength_logs(request):
    if request.method == 'GET':
        exercise_id = request.GET.get('exercise_id')
        qs = StrengthLog.objects.filter(user=request.user)
        if exercise_id:
            qs = qs.filter(exercise_id=exercise_id)
        return Response(StrengthLogSerializer(qs, many=True).data)

    data = request.data.copy()
    if 'date' not in data:
        data['date'] = date.today().isoformat()

    serializer = StrengthLogSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def strength_summary(request):
    """
    Returns top 5 most-logged exercises with their progress over time.
    Used for the strength chart on the progress screen.
    """
    logs = StrengthLog.objects.filter(
        user=request.user,
        weight_lifted__isnull=False
    ).select_related('exercise').order_by('date')

    # Group by exercise
    by_exercise = defaultdict(list)
    for log in logs:
        by_exercise[log.exercise.name].append({
            'date':   log.date.isoformat(),
            'weight': float(log.weight_lifted),
            'unit':   log.weight_unit,
            'reps':   log.reps,
        })

    # Return top 5 by number of entries
    sorted_exercises = sorted(by_exercise.items(), key=lambda x: len(x[1]), reverse=True)[:5]

    return Response([
        {'exercise': name, 'data': data}
        for name, data in sorted_exercises
    ])

# PROGRESS PHOTOS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def progress_photos(request):
    if request.method == 'GET':
        photos = ProgressPhoto.objects.filter(user=request.user)
        return Response(ProgressPhotoSerializer(photos, many=True, context={'request': request}).data)

    data = request.data.copy()
    if 'date' not in data:
        data['date'] = date.today().isoformat()

    serializer = ProgressPhotoSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user=request.user, image=request.FILES.get('image'))
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_progress_photo(request, pk):
    try:
        photo = ProgressPhoto.objects.get(pk=pk, user=request.user)
        photo.image.delete()
        photo.delete()
        return Response(status=204)
    except ProgressPhoto.DoesNotExist:
        return Response(status=404)