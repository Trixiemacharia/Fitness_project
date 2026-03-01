from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Category, MuscleGroup, Exercise, ExerciseLog
from .serializers import CategorySerializer, ExerciseSerializer, MuscleGroupSerializer, ExerciseLogSerializer
from users.models import UserProfile


# ===== EXISTING VIEWSETS =====

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.prefetch_related('exercises', 'muscle_groups').all()
    serializer_class = CategorySerializer

    def get_serializer_context(self):
        return {'request': self.request}


class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.select_related('category', 'muscle_group').all()
    serializer_class = ExerciseSerializer

    def get_serializer_context(self):
        return {'request': self.request}


# ===== MUSCLE GROUP LIST =====

@api_view(['GET'])
def muscle_group_list(request):
    qs = MuscleGroup.objects.prefetch_related('categories').all()
    training_type = request.GET.get('type')
    if training_type and training_type != 'all':
        qs = qs.filter(categories__training_type=training_type).distinct()
    serializer = MuscleGroupSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


# ===== EXERCISE LOG =====

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exercise_logs(request):
    """
    GET /api/logs/
    Returns all exercise logs for the current user.
    Frontend uses this to restore completion state on load.
    """
    logs = ExerciseLog.objects.filter(user=request.user).select_related('exercise')
    serializer = ExerciseLogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_exercise_log(request):
    """
    POST /api/logs/update/
    Body: { exercise_id: int, sets_completed: int }
    Creates or updates the log for this user + exercise.
    """
    exercise_id    = request.data.get('exercise_id')
    sets_completed = request.data.get('sets_completed', 0)

    if not exercise_id:
        return Response({'error': 'exercise_id required'}, status=400)

    exercise = get_object_or_404(Exercise, id=exercise_id)

    log, _ = ExerciseLog.objects.update_or_create(
        user=request.user,
        exercise=exercise,
        defaults={'sets_completed': sets_completed}
    )

    serializer = ExerciseLogSerializer(log)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def reset_exercise_log(request, exercise_id):
    """
    DELETE /api/logs/<exercise_id>/reset/
    Resets the log for this user + exercise back to 0.
    """
    try:
        log = ExerciseLog.objects.get(user=request.user, exercise_id=exercise_id)
        log.sets_completed = 0
        log.save()
        serializer = ExerciseLogSerializer(log)
        return Response(serializer.data)
    except ExerciseLog.DoesNotExist:
        return Response({'sets_completed': 0, 'status': 'not_started'})


# ===== SEARCH =====

@require_GET
@login_required
def search_workouts(request):
    q = request.GET.get('q', '').strip()
    if not q:
        qs = Category.objects.prefetch_related('exercises', 'muscle_groups').all()
    else:
        qs = Category.objects.prefetch_related('exercises', 'muscle_groups').filter(
            Q(name__icontains=q) | Q(exercises__name__icontains=q)
        ).distinct()
    serializer = CategorySerializer(qs, many=True, context={'request': request})
    return JsonResponse({'results': serializer.data})


# ===== EXISTING TEMPLATE VIEWS =====

def workout_library(request, pk):
    category  = get_object_or_404(Category, pk=pk)
    exercises = Exercise.objects.filter(category=category)
    return render(request, "exercises/workout_library.html", {
        "exercises": exercises,
        "category":  category,
    })

def workout_detail(request, id):
    exercise = get_object_or_404(Exercise, id=id)
    return render(request, "exercises/workout_detail.html", {"exercise": exercise})

def categories_view(request):
    categories = Category.objects.all()
    return render(request, "exercises/category_cards.html")