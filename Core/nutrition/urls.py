from django.urls import path
from . import views

app_name = 'nutrition'

urlpatterns = [
    path('api/nutrition/foods/', views.FoodSearchView.as_view(), name='food-search'),
    path('api/nutrition/logs/', views.MealLogListCreateView.as_view(), name='meal-logs'),
    path('api/nutrition/logs/<int:pk>/', views.MealLogDeleteView.as_view(), name='meal-log-delete'),
    path('api/nutrition/summary/', views.daily_summary, name='daily-summary'),
    path('api/nutrition/weekly/', views.weekly_summary, name='weekly-summary'),
]