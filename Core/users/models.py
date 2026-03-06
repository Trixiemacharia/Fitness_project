from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    GOAL_CHOICES = [
        ('tone','Tone'),
        ('bulk','Bulk'),
        ('lose_weight','Lose Weight'),
    ]
    ACTIVITY_LEVEL_CHOICES =[
        ('sedentary','Sedentary'),
        ('light','Lightly Active'),
        ('moderate','Moderately Active'),
        ('active','Active'),
        ('very_active','Very Active'),
    ]
    FITNESS_LEVEL_CHOICES=[
        ('beginner','Beginner'),
        ('intermediate','Intermediate'),
        ('advanced','Advanced'),
    ]
    FOCUS_CHOICES =[
        ('legs','Legs'),
        ('abs','Abs'),
        ('glutes','Glutes'),
        ('arms','Arms'),
        ('back','Back'),
        ('shoulder','Shoulder'),
    ]
    EQUIPMENTS_AVAILABLE_TO_THEM=[
        ('none','None'),
        ('dumbells','Dumbells'),
        ('resistance_bands','Resistance Bands'),
        ('barbell','Barbell'),
        ('machines','Machines'),
    ]

    user = models.OneToOneField(User,on_delete=models.CASCADE,primary_key=True,related_name='profile')
    name = models.CharField(max_length=20)
    profile_image = models.ImageField(upload_to='avatars/',blank=True, null=True)
    backup_reminder = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=1,choices=[('M','Male'),('F','Female')])
    age = models.PositiveIntegerField()
    height = models.FloatField()
    weight = models.FloatField()
    goal_type= models.CharField(max_length=20,choices=GOAL_CHOICES)
    activity_level = models.CharField(max_length=20,choices=ACTIVITY_LEVEL_CHOICES)
    fitness_level = models.CharField(max_length=20,choices=FITNESS_LEVEL_CHOICES)
    prefered_focus = models.JSONField(default=list) #multi-select
    equipment = models.JSONField(default=list) #multi-select
    meal_plan_recommendations = models.CharField(max_length=3,choices=[('Yes','Yes'),('No','No')])
    bio = models.TextField(blank=True,null=True)
    joined_on = models.DateTimeField(auto_now_add=True)

def __str__(self):
    return self.user.username

# ===== USER PREFERENCES =====
class UserPreferences(models.Model):
    GOAL_CHOICES = [
        ('lose_weight',   'Lose Weight'),
        ('build_muscle',  'Build Muscle'),
        ('stay_active',   'Stay Active'),
        ('improve_endurance', 'Improve Endurance'),
        ('flexibility',   'Flexibility & Mobility'),
    ]
    UNIT_CHOICES = [
        ('metric',   'Metric (kg, cm)'),
        ('imperial', 'Imperial (lbs, inches)'),
    ]
    DAY_CHOICES = [
        ('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'),
        ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday'),
    ]

    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    fitness_goal     = models.CharField(max_length=30, choices=GOAL_CHOICES, default='stay_active')
    preferred_days   = models.JSONField(default=list, blank=True)   # e.g. ["mon","wed","fri"]
    units            = models.CharField(max_length=10, choices=UNIT_CHOICES, default='metric')
    dark_mode        = models.BooleanField(default=True)
    notifications    = models.BooleanField(default=True)
    updated_at       = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} preferences"


# ===== WEIGHT LOG =====
class WeightLog(models.Model):
    UNIT_CHOICES = [('kg', 'kg'), ('lbs', 'lbs')]

    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    weight = models.DecimalField(max_digits=5, decimal_places=1)
    unit   = models.CharField(max_length=3, choices=UNIT_CHOICES, default='kg')
    note   = models.CharField(max_length=200, blank=True)
    date   = models.DateField()

    class Meta:
        ordering = ['date']
        unique_together = ('user', 'date')   # one entry per day

    def __str__(self):
        return f"{self.user.username} — {self.weight}{self.unit} on {self.date}"


# ===== BODY MEASUREMENT =====
class BodyMeasurement(models.Model):
    UNIT_CHOICES = [('cm', 'cm'), ('inches', 'inches')]

    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='measurements')
    unit   = models.CharField(max_length=10, choices=UNIT_CHOICES, default='cm')
    waist  = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hips   = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    chest  = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    arms   = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    thighs = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    note   = models.CharField(max_length=200, blank=True)
    date   = models.DateField()

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.user.username} measurements on {self.date}"


# ===== STRENGTH LOG =====
class StrengthLog(models.Model):
    from exercises.models import Exercise   # local import to avoid circular

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strength_logs')
    exercise      = models.ForeignKey('exercises.Exercise', on_delete=models.CASCADE, related_name='strength_logs')
    weight_lifted = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    weight_unit   = models.CharField(max_length=3, choices=[('kg','kg'),('lbs','lbs')], default='kg')
    reps          = models.PositiveIntegerField(null=True, blank=True)
    sets_done     = models.PositiveIntegerField(default=1)
    note          = models.CharField(max_length=200, blank=True)
    date          = models.DateField()
    auto_logged   = models.BooleanField(default=False)  # True = created from ExerciseLog completion

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.user.username} — {self.exercise.name} {self.weight_lifted}{self.weight_unit} on {self.date}"


# ===== BEFORE / AFTER PHOTO =====
class ProgressPhoto(models.Model):
    LABEL_CHOICES = [
        ('before', 'Before'),
        ('after',  'After'),
        ('progress', 'Progress'),
    ]

    user  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_photos')
    image = models.ImageField(upload_to='progress_photos/')
    label = models.CharField(max_length=10, choices=LABEL_CHOICES, default='progress')
    note  = models.CharField(max_length=200, blank=True)
    date  = models.DateField()

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.user.username} — {self.label} photo on {self.date}"