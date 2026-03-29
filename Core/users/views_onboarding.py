from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from datetime import date

ONBOARDING_STEPS = [
    {"field": "gender", "question": "What is your gender?", "type": "choice", "choices": [('M','Male'),('F','Female')]},
    {"field": "date_of_birth", "question": "What is your date of birth?", "type": "dob"},
    {"field": "weight", "question": "What is your current weight?", "type": "number"},
    {"field": "height", "question": "What is your height (cm)?", "type": "height"},
    {"field": "goal_type", "question": "What is your fitness goal?", "type": "choice", "choices": [('tone','Tone'),('bulk','Bulk'),('lose_weight','Lose Weight')]},
    {"field": "activity_level", "question": "How active are you?", "type": "choice", "choices": [
        ('sedentary','Sedentary'),('light','Lightly Active'),('moderate','Moderately Active'),
        ('active','Active'),('very_active','Very Active'),
    ]},
    {"field": "fitness_level", "question": "What's your current fitness level?", "type": "choice", "choices": [
        ('beginner','Beginner'),('intermediate','Intermediate'),('advanced','Advanced'),
    ]},
    {"field": "preferred_focus", "question": "Which areas do you want to focus on?", "type": "multi", "choices": [
        ('legs','Legs'),('abs','Abs'),('glutes','Glutes'),('arms','Arms'),('back','Back'),('shoulder','Shoulders'),
    ]},
    {"field": "wants_meal_plan", "question": "Would you like a meal plan?", "type": "choice", "choices": [
        ('Yes','Yes'),('No','No'),
    ]},
]


@login_required
def onboarding(request):
    step = int(request.GET.get("step", 0))
    data = request.session.get("onboarding_data", {})

    if step >= len(ONBOARDING_STEPS):
        # Save profile
        profile = UserProfile.objects.create(
            user=request.user,
            name=request.user.username,
            email=request.user.email,
            password_hash=request.user.password,
            gender=data.get("gender"),
            date_of_birth=data.get("date_of_birth") or None,
            height=data.get("height"),
            goal_type=data.get("goal_type"),
            activity_level=data.get("activity_level"),
            fitness_level=data.get("fitness_level"),
            prefered_focus=data.get("preferred_focus", []),
            wants_meal_plan=data.get("wants_meal_plan") == "Yes",
        )

        # Save initial weight log — indented inside this block
        raw_weight = data.get("weight")
        if raw_weight:
            try:
                from .models import WeightLog
                WeightLog.objects.create(
                    user=request.user,
                    weight=float(raw_weight),
                    unit='kg',
                    note='Initial weight from onboarding',
                    date=date.today(),
                )
            except Exception as e:
                print(f"WeightLog creation failed: {e}")

        # Auto-generate meal plan — also indented inside this block
        if profile.wants_meal_plan:
            try:
                from services.meal_plan_service import generate_meal_plan
                generate_meal_plan(request.user)
            except Exception as e:
                print(f"Meal plan generation failed: {e}")

        request.session.pop("onboarding_data", None)
        return redirect("dashboard")  # ← this was also missing from your original!

    question = ONBOARDING_STEPS[step]

    if request.method == "POST":
        data = request.session.get("onboarding_data", {})

        if question["type"] == "multi":
            answer = request.POST.getlist("answer")
        elif question["type"] == "dob":
            day   = request.POST.get("dob_day", "").zfill(2)
            month = request.POST.get("dob_month", "").zfill(2)
            year  = request.POST.get("dob_year", "")
            answer = f"{year}-{month}-{day}" if day and month and year else None
        else:
            answer = request.POST.get("answer")

        data[question["field"]] = answer
        request.session["onboarding_data"] = data
        return redirect(f"/onboarding/?step={step + 1}")

    return render(request, "users/onboarding.html", {"question": question, "step": step})