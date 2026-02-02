from rest_framework import viewsets
from .models import Category,Exercise
from .serializers import CategorySerializer,ExerciseSerializer
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import UserProfile

# Create your views here.
#API endpoints
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class=CategorySerializer

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

# Render HTML templates
def workout_library(request, category):
    exercises = Exercise.objects.filter(category_slug=category)
    return render(request, "exercises/workout_library.html", {
        "exercises": exercises,
        "category":category
        })

def workout_detail(request, id):
    exercise = get_object_or_404(Exercise, id=id)
    return render(request, "exercises/workout_detail.html", {"exercise": exercise})

@login_required
def dashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    workout_cards = []

    #goal-based cards
    if profile.goal_type == 'lose_weight':
        workout_cards += [
            {'title': 'Full Body Fat Burn', 'slug': 'full_body', 'icon': '🔥'},
            {'title': 'HIIT & Cardio', 'slug': 'hiit', 'icon': '⚡'},
        ]


    elif profile.goal_type == 'bulk':
        workout_cards += [
            {'title': 'Push / Pull / Legs', 'slug': 'ppl', 'icon': '🏋🏽‍♀️'},
            {'title': 'Upper / Lower Split', 'slug': 'upper_lower', 'icon': '💪🏽'},
        ]

    elif profile.goal_type == 'tone':
        workout_cards += [
            {'title': 'Lean Toning', 'slug': 'toning', 'icon': '✨'},
            {'title': 'Full Body Sculpt', 'slug': 'full_body', 'icon': '🔥'},
        ]

    #Focus-based cards
    for focus in profile.prefered_focus:
        workout_cards.append({
            'title': focus.capitalize() + ' Focus',
            'slug': focus,
            'icon': '🎯'
        })

        if fitness_level == 'beginner':
           workout_cards.append({
                'title': 'Beginner Friendly',
                'slug': 'beginner',
                'icon': '🌱'
            })

    context = {
        'profile': profile,
        'workout_cards': workout_cards
    }

    return render(request, 'exercises/dashboard.html', context)
