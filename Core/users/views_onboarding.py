from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile

ONBOARDING_STEPS =[
    {"field":"gender", "question":"What is your gender?", "type":"choice","choices":[('M','Male'),('F','Female')]},
    {"field":"age","question":"How old are you?","type":"number"},
    {"field":"weight","question":"What is your current weight(kg)?","type":"number"},
    {"field":"height","question":"What is your height(cm?","type":"number"},
    {"field":"goal_type","question":"What is your fitness goal?","type":"choice","choices":["Tone","Bulk","Lose Weight"]},
    {"field":"activity_level","question":"How active are you?","type":"choice","choices":["Low","Moderate","High"]},
    {"field":"fitness_level","question":"What's your current fitness level?","type":"choice","choices":["Beginner","Intermediate","Advanced"]},
    {"field":"prefered_focus","question":"Which areas do you want to focus on?","type":"multi","choices":["Legs","Abs","Glutes","Arms","Back","Shoulders"]},
    {"field":"equipment","question":"What equipment do you have access to?","type":"multi","choices":["Dumbells","Resistance bands","Barbell","Hack squat machine","Leg press machine","None"]},
    {"field":"meal_plan_recommendations","question":"Would you like a meal plan?","type":"choices","choices":["Yes","No"]},
]


@login_required
def onboarding(request):
    step = int(request.GET.get("step",0)) #track questions

    data = request.session.get("onboarding_data",{})

    if step >= len(ONBOARDING_STEPS):
        userprofile = UserProfile.objects.create(
            user=request.user,
            gender = data.get("gender"),
            age = data.get("age"),
            height = data.get("height"),
            weight = data.get("weight"),
            goal_type=data.get("goal_type"),
            activity_level = data.get("activity_level"),
            fitness_level = data.get("fitness_level"),
            prefered_focus = ",".join(data.get("prefered_focus",[])),
            equipment = ",".join(data.get("equipment",[])),
            meal_plan_recommendations = data.get("meal_plan_recommendations")
        )

        request.session.pop("onboarding_data",None) #clears session data
        return redirect("dashboard")
    question = ONBOARDING_STEPS[step]
    if request.method == "POST":
        data = request.session.get("onboarding_dats",{})
        answer= request.POST.getlist("answer")
        if question["type"] in ["multi"]:
            request.POST.get("answer")
        data[question["field"]]= answer
        request.session["onboarding_data"] = data

        return redirect(f"/onboarding/?step={step + 1}")
    return render(request,"onboarding.html",{"question":question,"step":step})