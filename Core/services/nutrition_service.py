ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9,
}

def calculate_tdee(profile):
    """
    Calculate Total Daily Energy Expenditure using Mifflin-St Jeor formula
    """
    weight = profile.weight
    height = profile.height
    age = profile.age
    gender = profile.gender

    if not all([weight, height, age]):
        return 2000  # safe default if profile incomplete

    # Mifflin-St Jeor BMR
    if gender == 'M':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    multiplier = ACTIVITY_MULTIPLIERS.get(profile.activity_level, 1.55)
    return round(bmr * multiplier)


def calculate_targets(profile):
    tdee = calculate_tdee(profile)
    goal = profile.goal_type

    if goal == 'lose_weight':
        calories = tdee - 500         # caloric deficit
        protein_ratio = 0.35          # higher protein to preserve muscle
        carbs_ratio = 0.35
        fat_ratio = 0.30

    elif goal == 'bulk':
        calories = tdee + 300         # caloric surplus
        protein_ratio = 0.30
        carbs_ratio = 0.45            # more carbs for energy/training
        fat_ratio = 0.25

    else:  # tone
        calories = tdee
        protein_ratio = 0.25
        carbs_ratio = 0.45
        fat_ratio = 0.30

    return {
        'calories': round(calories),
        'protein': round((calories * protein_ratio) / 4),   # 4 cal per gram
        'carbs': round((calories * carbs_ratio) / 4),
        'fats': round((calories * fat_ratio) / 9),           # 9 cal per gram
    }