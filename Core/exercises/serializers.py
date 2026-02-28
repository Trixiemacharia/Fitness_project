from .models import Category,Exercise
from rest_framework import serializers

class ExerciseSerializer(serializers.ModelSerializer):
    demo_video = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    rest_time_display = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ['id','name','description','duration',
                  'demo_video','image','level','sets','reps','weight','rest_time','rest_time_display']

    def get_demo_video(self, obj):
        request = self.context.get('request')
        if obj.demo_video:
            return request.build_absolute_uri(obj.demo_video.url)
        return None
    
    def get_image(self,obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_rest_time_display(self, obj):
        if obj.rest_time >= 60 and obj.rest_time % 60 == 0:
            return f"{obj.rest_time // 60} min{'s' if obj.rest_time // 60 > 1 else ''}"
        return f"{obj.rest_time} secs"

class CategorySerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only =True)
    image = serializers.SerializerMethodField()
    total_programs = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id','name','image','exercises','total_programs']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_total_programs(self, obj):
        return obj.exercises.count()