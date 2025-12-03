from django.urls import path
from . import views

urlpatterns =[
    path('workouts/', views.workout_library, name="workout_library"),
    path('workouts/<int:id>/', views.workout_detail, name="workout_detail"),
]