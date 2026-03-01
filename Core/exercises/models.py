from django.db import models
from django.contrib.auth.models import User

# ===== TRAINING TYPE (was Category) =====
class Category(models.Model):
    TRAINING_TYPES = [
        ('strength', 'Strength'),
        ('hiit',     'HIIT'),
        ('cardio',   'Cardio'),
        ('mobility', 'Mobility'),
    ]

    name          = models.CharField(max_length=100)
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPES, default='strength')
    description   = models.TextField(blank=True)
    image         = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# ===== MUSCLE GROUP =====
class MuscleGroup(models.Model):
    MUSCLE_CHOICES = [
        ('upper_body', 'Upper Body'),
        ('lower_body', 'Lower Body'),
        ('glutes',     'Glutes'),
        ('core',       'Core'),
        ('full_body',  'Full Body'),
        ('cardio',     'Cardio'),
    ]

    name       = models.CharField(max_length=50, choices=MUSCLE_CHOICES, unique=True)
    categories = models.ManyToManyField(Category, related_name='muscle_groups', blank=True)

    def __str__(self):
        return self.get_name_display()


# ===== EXERCISE =====
class Exercise(models.Model):

    LEVEL_CHOICES = [
        ('beginner',     'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced',     'Advanced'),
    ]

    EXERCISE_TYPE_CHOICES = [
        ('strength', 'Strength'),
        ('hiit',     'HIIT'),
        ('cardio',   'Cardio'),
        ('mobility', 'Mobility'),
    ]

    INTENSITY_CHOICES = [
        ('low',      'Low'),
        ('moderate', 'Moderate'),
        ('high',     'High'),
    ]

    # Core fields
    category      = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='exercises')
    muscle_group  = models.ForeignKey(MuscleGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='exercises')
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES, default='strength')
    name          = models.CharField(max_length=200)
    description   = models.TextField(blank=True)
    level         = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    image         = models.ImageField(upload_to='exercises/', blank=True, null=True)
    demo_video    = models.FileField(upload_to='exercise_videos/', blank=True, null=True)

    # Equipment needed
    equipment     = models.CharField(max_length=200, blank=True, default='Bodyweight')

    # Step-by-step instructions
    instructions  = models.TextField(blank=True, help_text='One instruction per line. e.g: 1. Stand with feet shoulder-width apart')

    # ── Strength fields ──────────────────────────────────────────────
    # derived dynamically from level
    sets      = models.PositiveIntegerField(blank=True, null=True)
    reps      = models.CharField(max_length=20, blank=True)   # e.g. "8-12", "to failure"
    weight    = models.CharField(max_length=50, blank=True)   # e.g. "5-8kg", "Bodyweight"
    rest_time = models.PositiveIntegerField(blank=True, null=True, help_text='Rest in seconds')

    # ── HIIT fields ──────────────────────────────────────────────────
    work_time      = models.PositiveIntegerField(blank=True, null=True, help_text='Work duration in seconds')
    hiit_rest_time = models.PositiveIntegerField(blank=True, null=True, help_text='Rest duration in seconds')
    rounds         = models.PositiveIntegerField(blank=True, null=True)

    # ── Cardio fields ────────────────────────────────────────────────
    duration  = models.CharField(max_length=50, blank=True)   # e.g. "30 min"
    distance  = models.CharField(max_length=50, blank=True)   # e.g. "5km"
    intensity = models.CharField(max_length=20, choices=INTENSITY_CHOICES, blank=True)

    class Meta:
        ordering = ['category', 'muscle_group', 'level', 'name']

    def __str__(self):
        return f"{self.name} ({self.level}) — {self.category}"

    # ── Dynamic stat helpers (called by serializer) ──────────────────

    def get_sets(self):
        if self.sets:
            return self.sets
        return {'beginner': 2, 'intermediate': 3, 'advanced': 4}.get(self.level, 3)

    def get_reps(self):
        if self.reps:
            return self.reps
        return {'beginner': '10–15', 'intermediate': '8–12', 'advanced': '6–10'}.get(self.level, '8–12')

    def get_rest_time(self):
        if self.rest_time:
            return self.rest_time
        return {'beginner': 90, 'intermediate': 60, 'advanced': 45}.get(self.level, 60)

    def get_work_time(self):
        if self.work_time:
            return self.work_time
        return {'beginner': 20, 'intermediate': 30, 'advanced': 40}.get(self.level, 30)

    def get_hiit_rest(self):
        if self.hiit_rest_time:
            return self.hiit_rest_time
        return {'beginner': 40, 'intermediate': 30, 'advanced': 20}.get(self.level, 30)

    def get_rounds(self):
        if self.rounds:
            return self.rounds
        return {'beginner': 3, 'intermediate': 4, 'advanced': 5}.get(self.level, 3)
    
    def get_equipment(self):
        return self.equipment if self.equipment else 'Bodyweight'
    
    def get_instructions_list(self):
        if not self.instructions:
            return []
        return [line.strip() for line in self.instructions.strip().splitLines() if line.strip()]
    
class ExerciseLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_logs')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='logs')
    sets_completed = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'exercise')  # one log per user per exercise
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} — {self.exercise.name} ({self.sets_completed} sets)"

    @property
    def is_completed(self):
        return self.sets_completed >= self.exercise.get_sets()

    @property
    def status(self):
        if self.sets_completed == 0:
            return 'not_started'
        elif self.is_completed:
            return 'completed'
        else:
            return 'in_progress'
