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