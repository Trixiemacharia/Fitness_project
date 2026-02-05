from django.shortcuts import render,redirect
from users.models import UserProfile
from .forms import OnboardingForm
from django.contrib.auth.decorators import login_required
from exercises.models import Category, Exercise

@login_required
def create_profile(request):
    if request.method == 'POST':
        form = OnboardingForm(request.POST)
        if form.is_valid():
            profile = form.save()
            profile.user = request.user
            profile.save()
            return redirect('dashboard')
        else:
            form = OnboardingForm()
            return render(request, 'onboarding.html',{'form':form})

@login_required
def view_profile(request):
    profile = request.user.profile
    return render(request,'profile_detail.html',{'profile':profile})

@login_required
def update_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(view_profile)
        else:
            form = OnboardingForm(instance=profile)
            return render(request,'profile_edit.html',{'form': form})
        
@login_required
def delete_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.delete()
        return redirect('home')
    return render(request,'confirm_delete.html')

@login_required
def dashboard(request):
    try:
    # get user profile
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        #user logged in but never completed onboarding
        return redirect("onboarding")
    
    workout_cards = []

    # Goal-based cards
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

    # Focus-based cards
    for focus in profile.prefered_focus:
        workout_cards.append({
            'title': f"{focus.capitalize()} Focus",
            'slug': focus,
            'icon': '🎯'
        })

    # Fitness-level card
    if profile.fitness_level == 'beginner':
        workout_cards.append({
            'title': 'Beginner Friendly',
            'slug': 'beginner',
            'icon': '🌱'
        })

    return render(request, "users/dashboard.html", {
        "profile": profile,
        "workout_cards": workout_cards
    })

