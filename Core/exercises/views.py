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

    def get_serializer_context(self):
        return {'request': self.request}

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

    def get_serializer_context(self):
        return {'request': self.request}

# Render HTML templates
def workout_library(request, pk):
    category = get_object_or_404(Category, pk=pk)
    exercises = Exercise.objects.filter(category=category)
    return render(request, "exercises/workout_library.html", {
        "exercises": exercises,
        "category":category
        })

def workout_detail(request, id):
    exercise = get_object_or_404(Exercise, id=id)
    return render(request, "exercises/workout_detail.html", {"exercise": exercise})

def categories_view(request):
    categories = Category.objects.all()
    return render(request,"exercises/category_cards.html")