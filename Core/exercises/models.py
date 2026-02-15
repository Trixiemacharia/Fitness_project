from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=100,default="Workout Program")
    image = models.ImageField(upload_to='category_images/',blank=True,null=True)
    total_programs = models.IntegerField(default=24)

    def __str__(self):
        return self.name
    
class Exercise(models.Model):
    category = models.ForeignKey(Category,related_name='exercises',on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField()
    demo_video = models.FileField(upload_to='exer',null=True,blank=True)

    def __str__(self):
        return self.name
    
#track progress...complete n incomplete workouts per user
class UserExercises(models.Model):
    user= models.ForeignKey(User,on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise,on_delete=models.CASCADE)
    completed = models.BooleanField(default=True)

    def __str__(self):
        return self.exercise