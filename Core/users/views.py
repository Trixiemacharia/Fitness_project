from django.shortcuts import render,redirect
from .models import UserProfile
from .forms import OnboardingForm
from django.contrib.auth.decorators import login_required

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
    return render(request,'dashboard.html')

