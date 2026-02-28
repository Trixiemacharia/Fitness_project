from django.urls import path
from . import views

urlpatterns =[
    path('categories/', views.categories_view, name="categories"),
    path('exercise/<int:id>/', views.workout_detail, name="workout_detail"),

]