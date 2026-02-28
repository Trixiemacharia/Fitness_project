from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=100,default="Workout Program")
    image = models.ImageField(upload_to='category_images/',blank=True,null=True)

    @property
    def total_programs(self):
        return self.exercises.count()

    def __str__(self):
        return self.name
    
class Exercise(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced','Advanced'),
    ]

    category = models.ForeignKey(Category,related_name='exercises',on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField()
    demo_video = models.FileField(upload_to='exercise_videos/',blank=True,null=True)
    image = models.ImageField(upload_to="exercises/",blank=True,null=True)
    duration = models.IntegerField(help_text="Duration in minutes",null=True)

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    sets = models.PositiveIntegerField(default=3)
    reps = models.CharField(max_length=50, default='10', help_text="e.g. '10', '10-12', 'to failure'")
    weight = models.CharField(max_length=50, blank=True, default='Bodyweight', help_text="e.g. '5-8kg', 'Bodyweight', '18kg+'")
    rest_time = models.PositiveIntegerField(default=60, help_text="Rest in seconds")

    def __str__(self):
        return f"{self.name} ({self.level})"
    
#track progress...complete n incomplete workouts per user
class UserExercises(models.Model):
    user= models.ForeignKey(User,on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise,on_delete=models.CASCADE)
    completed = models.BooleanField(default=True)

    def __str__(self):
        return self.exercise