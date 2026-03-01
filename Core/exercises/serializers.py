from rest_framework import serializers
from .models import Category, MuscleGroup, Exercise, ExerciseLog


# ===== MUSCLE GROUP =====
class MuscleGroupSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model  = MuscleGroup
        fields = ['id', 'name', 'display_name']


# ===== EXERCISE =====
class ExerciseSerializer(serializers.ModelSerializer):
    muscle_group_name = serializers.CharField(source='muscle_group.get_name_display', read_only=True)

    # Dynamic computed stats
    computed_sets      = serializers.SerializerMethodField()
    computed_reps      = serializers.SerializerMethodField()
    computed_rest      = serializers.SerializerMethodField()
    computed_work_time = serializers.SerializerMethodField()
    computed_hiit_rest = serializers.SerializerMethodField()
    computed_rounds    = serializers.SerializerMethodField()
    rest_time_display  = serializers.SerializerMethodField()
    stats              = serializers.SerializerMethodField()
    instructions_list  = serializers.SerializerMethodField()
    equipment_display  = serializers.SerializerMethodField()

    class Meta:
        model  = Exercise
        fields = [
            'id', 'name', 'description', 'level', 'exercise_type',
            'category', 'muscle_group', 'muscle_group_name',
            'image', 'demo_video', 'equipment', 'equipment_display',
            'instructions', 'instructions_list',

            # Raw overrideable fields
            'sets', 'reps', 'weight', 'rest_time',
            'work_time', 'hiit_rest_time', 'rounds',
            'duration', 'distance', 'intensity',

            # Computed
            'computed_sets', 'computed_reps', 'computed_rest',
            'computed_work_time', 'computed_hiit_rest', 'computed_rounds',
            'rest_time_display',

            # Unified stat block for card rendering
            'stats',
        ]

    def get_computed_sets(self, obj):      return obj.get_sets()
    def get_computed_reps(self, obj):      return obj.get_reps()
    def get_computed_rest(self, obj):      return obj.get_rest_time()
    def get_computed_work_time(self, obj): return obj.get_work_time()
    def get_computed_hiit_rest(self, obj): return obj.get_hiit_rest()
    def get_computed_rounds(self, obj):    return obj.get_rounds()
    def get_equipment_display(self, obj):
        return obj.equipment if obj.equipment else 'Bodyweight'
    def get_instructions_list(self, obj):  return obj.get_instructions_list()

    def get_rest_time_display(self, obj):
        s = obj.get_rest_time()
        if s >= 60 and s % 60 == 0:
            return f"{s // 60} min"
        return f"{s}s"

    def get_stats(self, obj):
        """Unified stat block for exercise cards — type-aware."""
        t = obj.exercise_type

        if t == 'strength':
            return [
                {'label': 'Sets',   'value': str(obj.get_sets())},
                {'label': 'Reps',   'value': obj.get_reps()},
                {'label': 'Weight', 'value': obj.weight or 'Bodyweight'},
                {'label': 'Rest',   'value': self.get_rest_time_display(obj)},
            ]
        elif t == 'hiit':
            return [
                {'label': 'Work',   'value': f"{obj.get_work_time()}s"},
                {'label': 'Rest',   'value': f"{obj.get_hiit_rest()}s"},
                {'label': 'Rounds', 'value': str(obj.get_rounds())},
            ]
        elif t == 'cardio':
            stats = [{'label': 'Duration', 'value': obj.duration or '—'}]
            if obj.distance:
                stats.append({'label': 'Distance', 'value': obj.distance})
            if obj.intensity:
                stats.append({'label': 'Intensity', 'value': obj.intensity.capitalize()})
            return stats
        elif t == 'mobility':
            stats = []
            if obj.duration:
                stats.append({'label': 'Duration', 'value': obj.duration})
            if obj.get_sets():
                stats.append({'label': 'Sets', 'value': str(obj.get_sets())})
            if obj.get_reps():
                stats.append({'label': 'Reps', 'value': obj.get_reps()})
            return stats or [{'label': 'Type', 'value': 'Mobility'}]

        return []


# ===== EXERCISE LOG =====
class ExerciseLogSerializer(serializers.ModelSerializer):
    exercise_id    = serializers.IntegerField(source='exercise.id', read_only=True)
    exercise_name  = serializers.CharField(source='exercise.name', read_only=True)
    total_sets     = serializers.SerializerMethodField()
    status         = serializers.CharField(read_only=True)
    is_completed   = serializers.BooleanField(read_only=True)

    class Meta:
        model  = ExerciseLog
        fields = [
            'id', 'exercise_id', 'exercise_name',
            'sets_completed', 'total_sets',
            'status', 'is_completed', 'updated_at',
        ]

    def get_total_sets(self, obj):
        return obj.exercise.get_sets()


# ===== CATEGORY =====
class CategorySerializer(serializers.ModelSerializer):
    exercises       = ExerciseSerializer(many=True, read_only=True)
    muscle_groups   = MuscleGroupSerializer(many=True, read_only=True)
    total_exercises = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = [
            'id', 'name', 'training_type', 'description', 'image',
            'muscle_groups', 'exercises', 'total_exercises',
        ]

    def get_total_exercises(self, obj):
        return obj.exercises.count()