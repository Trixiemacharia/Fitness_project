from .models import Category,Exercise
from rest_framework import serializers

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only =True)

    class Meta:
        model = Category
        fields = ['id','name','image','exercises']