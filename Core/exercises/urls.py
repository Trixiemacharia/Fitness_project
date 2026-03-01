from django.urls import path
from . import views

urlpatterns =[
    path('categories/', views.categories_view, name="categories"),
    path('exercise/<int:id>/', views.workout_detail, name="workout_detail"),
    path('dashboard/search/', views.search_workouts, name='search-workouts'),
    # muscle groups API
    path('api/muscle-groups/', views.muscle_group_list, name='muscle-group-list'),
    #Exercise log API
    path('api/logs/',views.get_exercise_logs,   name='exercise-logs'),
    path('api/logs/update/',views.update_exercise_log, name='exercise-log-update'),
    path('api/logs/<int:exercise_id>/reset/',views.reset_exercise_log,  name='exercise-log-reset'),
]
