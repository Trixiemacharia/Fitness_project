from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from datetime import date

ONBOARDING_STEPS = [
    {"field": "gender", "question": "What is your gender?", "type": "choice", "choices": [('M','Male'),('F','Female')]},
    {"field": "date_of_birth", "question": "What is your date of birth?", "type": "dob"},
    {"field": "weight", "question": "What is your current weight(kg)?", "type": "number"},
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
]

MIN_BIRTH_YEAR = 1900
MIN_AGE = 13
MAX_AGE = 100


def _validate_dob(post_data):
    day = (post_data.get("dob_day") or "").strip()
    month = (post_data.get("dob_month") or "").strip()
    year = (post_data.get("dob_year") or "").strip()

    if not all([day, month, year]):
        return None, "Please enter your full date of birth."

    try:
        dob = date(int(year), int(month), int(day))
    except ValueError:
        return None, "Please enter a valid date of birth."

    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    if dob > today:
        return None, "Date of birth cannot be in the future."
    if dob.year < MIN_BIRTH_YEAR:
        return None, f"Please enter a birth year from {MIN_BIRTH_YEAR} onwards."
    if age < MIN_AGE:
        return None, f"You must be at least {MIN_AGE} years old to use this app."
    if age > MAX_AGE:
        return None, "Please enter a realistic date of birth."

    return dob.isoformat(), None


def _validate_answer(question, post_data):
    question_type = question["type"]

    if question_type == "multi":
        answer = post_data.getlist("answer")
        valid_choices = {choice[0] for choice in question.get("choices", [])}
        if not answer:
            return None, "Please select at least one option."
        if any(choice not in valid_choices for choice in answer):
            return None, "Please select valid focus areas."
        return answer, None

    if question_type == "dob":
        return _validate_dob(post_data)

    answer = (post_data.get("answer") or "").strip()
    if not answer:
        return None, "This field is required."

    if question_type == "choice":
        valid_choices = {choice[0] for choice in question.get("choices", [])}
        if answer not in valid_choices:
            return None, "Please choose one of the listed options."
        return answer, None

    if question_type == "number":
        try:
            value = float(answer)
        except ValueError:
            return None, "Please enter a valid number."
        if value <= 0 or value > 500:
            return None, "Please enter a realistic weight."
        return answer, None

    if question_type == "height":
        try:
            value = float(answer)
        except ValueError:
            return None, "Please enter a valid height."
        if value < 50 or value > 300:
            return None, "Please enter a height between 50 cm and 300 cm."
        return answer, None

    return answer, None


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


        request.session.pop("onboarding_data", None)
        return redirect("dashboard")  # ← this was also missing from your original!

    question = ONBOARDING_STEPS[step]

    if request.method == "POST":
        data = request.session.get("onboarding_data", {})
        answer, error = _validate_answer(question, request.POST)

        if error:
            return render(request, "users/onboarding.html", {
                "question": question,
                "step": step,
                "error": error,
                "form_data": request.POST,
                "selected_answers": request.POST.getlist("answer"),
            })

        data[question["field"]] = answer
        request.session["onboarding_data"] = data
        return redirect(f"/onboarding/?step={step + 1}")

    return render(request, "users/onboarding.html", {
        "question": question,
        "step": step,
        "form_data": {},
        "selected_answers": [],
    })
