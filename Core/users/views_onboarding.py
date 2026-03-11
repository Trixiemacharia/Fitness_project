from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile

ONBOARDING_STEPS =[
    {"field":"gender", "question":"What is your gender?", "type":"choice","choices":[
        ('M','Male'),
        ('F','Female')
        ]},
    {"field":"age","question":"How old are you?","type":"number"},
    {"field":"weight","question":"What is your current weight(kg)?","type":"number"},
    {"field":"height","question":"What is your height(cm?","type":"number"},
    {"field":"goal_type","question":"What is your fitness goal?","type":"choice","choices":[('tone','Tone'), ('bulk','Bulk'), ('lose_weight','Lose Weight')]},
    {"field":"activity_level","question":"How active are you?","type":"choice","choices": [
            ('sedentary', 'Sedentary'),
            ('light', 'Lightly Active'),
            ('moderate', 'Moderately Active'),
            ('active', 'Active'),
            ('very_active', 'Very Active'),
        ],
    },

    {"field":"fitness_level","question":"What's your current fitness level?","type":"choice","choices": [
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
    },
    {"field":"prefered_focus","question":"Which areas do you want to focus on?","type":"multi","choices": [
            ('legs', 'Legs'),
            ('abs', 'Abs'),
            ('glutes', 'Glutes'),
            ('arms', 'Arms'),
            ('back', 'Back'),
            ('shoulder', 'Shoulders'),
        ],
    },
    {"field":"equipment","question":"What equipment do you have access to?","type":"multi","choices":  [
            ('none', 'None'),
            ('dumbells', 'Dumbells'),
            ('resistance_bands', 'Resistance Bands'),
            ('barbell', 'Barbell'),
            ('machines', 'Machines'),
        ],
    },

    {"field":"meal_plan_recommendations","question":"Would you like a meal plan?","type":"choice","choices":[
            ('Yes', 'Yes'),
            ('No', 'No'),
        ],
    },
]


@login_required
def onboarding(request):
    step = int(request.GET.get("step",0)) #track questions

    data = request.session.get("onboarding_data",{})

    if step >= len(ONBOARDING_STEPS):
        userprofile = UserProfile.objects.create(
            user=request.user,
            name = request.user.username,
            email=request.user.email,
            password_hash=request.user.password,  
            gender = data.get("gender"),
            age = data.get("age"),
            height = data.get("height"),
            weight = data.get("weight"),
            goal_type=data.get("goal_type"),
            activity_level = data.get("activity_level"),
            fitness_level = data.get("fitness_level"),
            prefered_focus = data.get("prefered_focus",[]),
            equipment = data.get("equipment",[]),
            meal_plan_recommendations = data.get("meal_plan_recommendations")
        )

        request.session.pop("onboarding_data",None) #clears session data
        return redirect("dashboard")
    question = ONBOARDING_STEPS[step]
    if request.method == "POST":
        data = request.session.get("onboarding_data",{})
        answer= request.POST.getlist("answer")
        if question["type"] == "multi":
            answer = request.POST.getlist("answer")
        elif question["type"] == "choice":
            answer=request.POST.get("answer")
        else:
            answer =request.POST.get("answer")
        data[question["field"]]= answer
        request.session["onboarding_data"] = data

        return redirect(f"/onboarding/?step={step + 1}")
    return render(request,"users/onboarding.html",{"question":question,"step":step})

@login_required
def complete_onboarding(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        profile = request.user.profile
        profile.goal = data.get('goal')
        profile.activity_level = data.get('activity_level')
        profile.weight_kg = data.get('weight')
        profile.height_cm = data.get('height')
        profile.age = data.get('age')
        profile.gender = data.get('gender')
        profile.wants_meal_plan = data.get('wants_meal_plan', False)
        profile.save()

        # Auto generate meal plan if user opted in
        if profile.wants_meal_plan:
            meal_plan = generate_meal_plan(request.user)
            return JsonResponse({
                'success': True,
                'redirect': '/meal-plan/',
                'message': f'Your {profile.get_goal_display()} meal plan is ready!'
            })

        return JsonResponse({'success': True, 'redirect': '/dashboard/'})