from django.shortcuts import render,redirect
from users.models import UserProfile
from .forms import OnboardingForm
from django.contrib.auth.decorators import login_required
from exercises.models import Category, Exercise
from django.http import JsonResponse
from django.db.models import Q
from exercises.serializers import CategorySerializer

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
            profile = request.user.profile
    except:
        return redirect("onboarding")

    categories = Category.objects.all()

    return render(request, "users/dashboard.html", {
        "profile": profile,
        "categories": categories
    })
    

@login_required
def search_dashboard_workouts(request):
    query = request.GET.get('q', '').strip()

    if not query:
        categories = Category.objects.prefetch_related('exercises', 'muscle_groups').all()
    else:
        categories = Category.objects.prefetch_related('exercises', 'muscle_groups').filter(
            Q(name__icontains=query) |
            Q(exercises__name__icontains=query)
        ).distinct()

    serializer = CategorySerializer(categories, many=True, context={'request': request})
    return JsonResponse({'results': serializer.data})

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