from rest_framework import serializers
from .models import UserPreferences, WeightLog, BodyMeasurement, StrengthLog, ProgressPhoto


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserPreferences
        fields = ['fitness_goal', 'preferred_days', 'units', 'dark_mode', 'notifications']


class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WeightLog
        fields = ['id', 'weight', 'unit', 'note', 'date']


class BodyMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BodyMeasurement
        fields = ['id', 'unit', 'waist', 'hips', 'chest', 'arms', 'thighs', 'note', 'date']


class StrengthLogSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model  = StrengthLog
        fields = ['id', 'exercise', 'exercise_name', 'weight_lifted', 'weight_unit', 'reps', 'sets_done', 'note', 'date', 'auto_logged']


class ProgressPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = ProgressPhoto
        fields = ['id', 'image_url', 'label', 'note', 'date']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None