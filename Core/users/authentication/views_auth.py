from users.models import UserProfile
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib import messages


def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        user = User.objects.create_user(username=username, email=email,password=password)
        login(request,user)
        return redirect('onboarding')
    return render(request,'register.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request,username=username, password=password)

        if user is not None:
            login(request,user)
            print("✅ Login successful!")
            return redirect('dashboard')
        else:
                print("Invalid username or password")
                messages.error(request,'Invalid username or password')
    return render(request,'welcome.html')
    
def logout_user(request):
    logout(request)
    return redirect('login_user')