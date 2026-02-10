from django.shortcuts import render,redirect
from users.models import UserProfile
from .forms import OnboardingForm
from django.contrib.auth.decorators import login_required
from exercises.models import Category, Exercise
from django.http import JsonResponse

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
            {'title': 'Full Body Fat Burn', 'slug': 'full_body', 'level':'beginner'},
            {'title': 'HIIT & Cardio', 'slug': 'hiit', 'level':'intermediate'},
        ]

    elif profile.goal_type == 'bulk':
        workout_cards += [
            {'title': 'Push / Pull / Legs', 'slug': 'ppl','level':'intermediate'},
            {'title': 'Upper / Lower Split', 'slug': 'upper_lower','level':'advanced'},
        ]

    elif profile.goal_type == 'tone':
        workout_cards += [
            {'title': 'Lean Toning', 'slug': 'toning','level':'beginner'},
            {'title': 'Full Body Sculpt', 'slug': 'full_body','level':'intermediate'},
        ]

    # Focus-based cards
    for focus in profile.prefered_focus:
        workout_cards.append({
            'title': f"{focus.capitalize()} Workout",
            'slug': focus,
            'level': profile.fitness_level
        })

    # Fitness-level card
    if profile.fitness_level == 'beginner':
        workout_cards.append({
            'title': 'Beginner Friendly',
            'slug': 'beginner',
            'icon': '🌱',
            'level':'beginner'
        })

         # ---- SORT: put cards matching user's fitness level first ----
    workout_cards.sort(key=lambda x: 0 if x['level'] == profile.fitness_level else 1)

    return render(request, "users/dashboard.html", {
        "profile": profile,
        "workout_cards": workout_cards
    })

@login_required
def search_dashboard_workouts(request):
    query = request.GET.get('q', '').lower()

    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return JsonResponse({"results": []})

    workout_cards = []

    # --- SAME LOGIC AS DASHBOARD ---
    if profile.goal_type == 'lose_weight':
        workout_cards += [
            {'title': 'Full Body Fat Burn', 'slug': 'full_body', 'level': 'beginner'},
            {'title': 'HIIT & Cardio', 'slug': 'hiit', 'level': 'intermediate'},
        ]

    elif profile.goal_type == 'bulk':
        workout_cards += [
            {'title': 'Push / Pull / Legs', 'slug': 'ppl', 'level': 'intermediate'},
            {'title': 'Upper / Lower Split', 'slug': 'upper_lower', 'level': 'advanced'},
        ]

    elif profile.goal_type == 'tone':
        workout_cards += [
            {'title': 'Lean Toning', 'slug': 'toning', 'level': 'beginner'},
            {'title': 'Full Body Sculpt', 'slug': 'full_body', 'level': 'intermediate'},
        ]

    for focus in profile.prefered_focus:
        workout_cards.append({
            'title': f"{focus.capitalize()} Workout",
            'slug': focus,
            'level': profile.fitness_level
        })

    if profile.fitness_level == 'beginner':
        workout_cards.append({
            'title': 'Beginner Friendly',
            'slug': 'beginner',
            'icon': '🌱',
            'level': 'beginner'
        })

    # --- SEARCH FILTER ---
    filtered = [
        card for card in workout_cards
        if query in card['title'].lower()
    ]

    return JsonResponse({"results": filtered})

@login_required
def upload_profile_image(request):
    if request.method == 'POST':
        profile = request.user.profile
        image = request.FILES.get('profile_image')

        if image:
            profile.profile_image = image
            profile.save()
            return JsonResponse({
                'success': True,
                'image_url': profile.profile_image.url
            })

    return JsonResponse({'success': False})

@login_required
def toggle_backup_reminder(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.backup_reminder = not profile.backup_reminder
        profile.save()
        return JsonResponse({'status': profile.backup_reminder})  