from rest_framework import serializers
from .models import Category, MuscleGroup, Exercise, ExerciseLog


class MuscleGroupSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = MuscleGroup
        fields = ['id', 'name', 'display_name']


class ExerciseSerializer(serializers.ModelSerializer):
    muscle_group_name = serializers.CharField(source='muscle_group.get_name_display', read_only=True)
    display_image = serializers.SerializerMethodField()
    display_video = serializers.SerializerMethodField()
    show_media = serializers.SerializerMethodField()
    estimated_calories_burned = serializers.SerializerMethodField()
    computed_sets = serializers.SerializerMethodField()
    computed_reps = serializers.SerializerMethodField()
    computed_rest = serializers.SerializerMethodField()
    computed_work_time = serializers.SerializerMethodField()
    computed_hiit_rest = serializers.SerializerMethodField()
    computed_rounds = serializers.SerializerMethodField()
    rest_time_display = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    instructions_list = serializers.SerializerMethodField()
    cardio_tips_list = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'description', 'level', 'exercise_type',
            'category', 'muscle_group', 'muscle_group_name',
            'image', 'demo_video', 'display_image', 'display_video', 'show_media',
            'instructions', 'instructions_list',
            'cardio_tips', 'cardio_tips_list',
            'sets', 'reps', 'weight', 'rest_time',
            'work_time', 'hiit_rest_time', 'rounds',
            'duration', 'distance', 'intensity',
            'estimated_calories_burned',
            'computed_sets', 'computed_reps', 'computed_rest',
            'computed_work_time', 'computed_hiit_rest', 'computed_rounds',
            'rest_time_display',
            'stats',
        ]

    def get_computed_sets(self, obj):
        return obj.get_sets()

    def get_computed_reps(self, obj):
        return obj.get_reps()

    def get_computed_rest(self, obj):
        return obj.get_rest_time()

    def get_computed_work_time(self, obj):
        return obj.get_work_time()

    def get_computed_hiit_rest(self, obj):
        return obj.get_hiit_rest()

    def get_computed_rounds(self, obj):
        return obj.get_rounds()

    def get_instructions_list(self, obj):
        return obj.get_instructions_list()

    def get_cardio_tips_list(self, obj):
        return obj.get_cardio_tips_list()

    def get_display_image(self, obj):
        return obj.get_image_url()

    def get_display_video(self, obj):
        return obj.get_demo_video_url()

    def get_show_media(self, obj):
        return obj.media_required and bool(obj.get_demo_video_url() or obj.get_image_url())

    def get_estimated_calories_burned(self, obj):
        return obj.get_estimated_calories_burned()

    def get_rest_time_display(self, obj):
        seconds = obj.get_rest_time()
        if seconds >= 60 and seconds % 60 == 0:
            return f"{seconds // 60} min"
        return f"{seconds}s"

    def get_stats(self, obj):
        exercise_type = obj.exercise_type

        if exercise_type == 'strength':
            stats = [
                {'label': 'Sets', 'value': str(obj.get_sets())},
                {'label': 'Reps', 'value': obj.get_reps()},
                {'label': 'Rest', 'value': self.get_rest_time_display(obj)},
            ]
            if obj.weight:
                stats.insert(2, {'label': 'Weight', 'value': obj.weight})
            return stats

        if exercise_type == 'hiit':
            return [
                {'label': 'Work', 'value': f"{obj.get_work_time()}s"},
                {'label': 'Rest', 'value': f"{obj.get_hiit_rest()}s"},
                {'label': 'Rounds', 'value': str(obj.get_rounds())},
            ]

        if exercise_type == 'cardio':
            calories = obj.get_estimated_calories_burned()
            return [
                {'label': 'Duration', 'value': obj.duration or '-'},
                {'label': 'Calories Burned', 'value': f"{calories or 0} kcal"},
            ]

        if exercise_type == 'mobility':
            stats = []
            if obj.duration:
                stats.append({'label': 'Duration', 'value': obj.duration})
            if obj.get_sets():
                stats.append({'label': 'Sets', 'value': str(obj.get_sets())})
            if obj.get_reps():
                stats.append({'label': 'Reps', 'value': obj.get_reps()})
            return stats or [{'label': 'Type', 'value': 'Mobility'}]

        return []


class ExerciseLogSerializer(serializers.ModelSerializer):
    exercise_id = serializers.IntegerField(source='exercise.id', read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    total_sets = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExerciseLog
        fields = [
            'id', 'exercise_id', 'exercise_name',
            'sets_completed', 'total_sets',
            'status', 'is_completed', 'updated_at',
        ]

    def get_total_sets(self, obj):
        return obj.exercise.get_sets()


class CategorySerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)
    muscle_groups = MuscleGroupSerializer(many=True, read_only=True)
    total_exercises = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'training_type', 'description', 'image',
            'muscle_groups', 'exercises', 'total_exercises',
        ]

    def get_total_exercises(self, obj):
        return obj.exercises.count()
