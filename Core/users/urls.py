from django.urls import path
from . import views,views_onboarding, progress_views
from users.authentication import views_auth

urlpatterns=[
    #auth urls
    path('register/',views_auth.register_user, name='register_user'),
    path('login/',views_auth.login_user, name='login_user'),
    path('logout/',views_auth.logout_user,name='logout_user'),

    #views urls 
    path('onboarding/',views_onboarding.onboarding, name='onboarding'),
    path('profile/',views.view_profile,name='view_profile'),
    path('profile/edit/',views.update_profile,name='update_profile'),
    path('profile/delete/',views.delete_profile,name='delete_profile'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('dashboard/search/', views.search_dashboard_workouts, name='search_dashboard_workouts'),
    path('upload-profile-image/', views.upload_profile_image, name='upload_profile_image'),
    path('toggle-backup/', views.toggle_backup_reminder, name='toggle_backup'),

     # Dashboard
    path('dashboard/',views.dashboard,name='dashboard'),
    path('dashboard/search/',views.search_dashboard_workouts, name='search_dashboard_workouts'),

    # Progress API
    path('api/progress/weight/',progress_views.weight_logs,name='weight-logs'),
    path('api/progress/weight/<int:pk>/',progress_views.delete_weight_log,name='weight-log-delete'),
    path('api/progress/measurements/',progress_views.body_measurements,name='body-measurements'),
    path('api/progress/consistency/',progress_views.workout_consistency,name='workout-consistency'),
    path('api/progress/strength/',progress_views.strength_logs,name='strength-logs'),
    path('api/progress/strength/summary/',progress_views.strength_summary,name='strength-summary'),
    path('api/progress/photos/',progress_views.progress_photos,name='progress-photos'),
    path('api/progress/photos/<int:pk>/',progress_views.delete_progress_photo,name='progress-photo-delete'),

    #Preferences API
    path('api/preferences/', progress_views.preferences,name='preferences'),
]