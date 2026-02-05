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