from django.urls import path
from . import views,views_onboarding
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
]