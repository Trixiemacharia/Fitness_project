from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.text import slugify

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

    # image and demo_video are always optional (blank/null=True).
    # For cardio exercises, these fields are intentionally left empty —
    # use `cardio_tips` to enrich the experience instead.
    # Use the `media_required` property to check whether to show/hide
    # media upload fields in forms or admin.
    image         = models.ImageField(upload_to='exercises/', blank=True, null=True)
    demo_video    = models.URLField(blank=True, null=True, help_text="https://pub-a3e3770ca86b453197bf4160321b1b0a.r2.dev")

    # Step-by-step instructions
    instructions  = models.TextField(blank=True, help_text='One instruction per line. e.g: 1. Stand with feet shoulder-width apart')

    # ── Cardio-only guidance (replaces media for cardio exercises) ────────────
    # For exercises like brisk walking, cycling, skipping — where a demo video
    # adds little value — populate this field with movement cues instead.
    # Leave blank for strength / HIIT / mobility exercises.
    cardio_tips = models.TextField(
        blank=True,
        help_text=(
            'Cardio exercises only. One tip per line, e.g:\n'
            '* Walk at a steady pace\n'
            '* Keep posture upright\n'
            '* Swing arms naturally\n'
            '* Maintain rhythmic breathing'
        )
    )

    # ── Strength fields ──────────────────────────────────────────────
    # derived dynamically from level
    sets      = models.PositiveIntegerField(blank=True, null=True)
    reps      = models.CharField(max_length=20, blank=True)
    weight    = models.CharField(max_length=50, blank=True)
    rest_time = models.PositiveIntegerField(blank=True, null=True, help_text='Rest in seconds')

    # ── HIIT fields ──────────────────────────────────────────────────
    work_time      = models.PositiveIntegerField(blank=True, null=True, help_text='Work duration in seconds')
    hiit_rest_time = models.PositiveIntegerField(blank=True, null=True, help_text='Rest duration in seconds')
    rounds         = models.PositiveIntegerField(blank=True, null=True)

    # ── Cardio fields ────────────────────────────────────────────────
    duration  = models.CharField(max_length=50, blank=True)
    distance  = models.CharField(max_length=50, blank=True)
    intensity = models.CharField(max_length=20, choices=INTENSITY_CHOICES, blank=True)

    class Meta:
        ordering = ['category', 'muscle_group', 'level', 'name']

    def __str__(self):
        return f"{self.name} ({self.level}) — {self.category}"

    # ── Media helpers ─────────────────────────────────────────────────────────

    @property
    def is_cardio(self):
        """True when this exercise is classified as a cardio exercise."""
        return self.exercise_type == 'cardio'

    @property
    def media_required(self):
        """
        False for cardio exercises — image and demo_video are intentionally
        optional and can safely be left blank. True for all other types where
        media meaningfully aids understanding of the movement.
        Use this in admin fieldsets, serializers, or template logic to
        conditionally show/hide media upload fields.
        """
        return not self.is_cardio

    @property
    def has_media(self):
        """True if either image or demo_video has been supplied."""
        return bool(self.image or self.demo_video)

    # ── Dynamic stat helpers  ──────────────────

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

    def get_instructions_list(self):
        if not self.instructions:
            return []
        return [line.strip() for line in self.instructions.strip().splitlines() if line.strip()]

    def get_cardio_tips_list(self):
        """
        Returns cardio_tips as a clean list of strings, stripping leading
        bullet markers (* or -) for consistent rendering in templates.
        Returns an empty list for non-cardio exercises.
        """
        if not self.is_cardio or not self.cardio_tips:
            return []
        tips = []
        for line in self.cardio_tips.strip().splitlines():
            line = line.strip().lstrip('*-').strip()
            if line:
                tips.append(line)
        return tips

    def _normalized_media_stem(self):
        return slugify(self.name).replace('-', '_')

    def _r2_relative_video_path(self):
        training_type = (self.category.training_type if self.category else self.exercise_type or '').strip().lower()
        filename = f"{self._normalized_media_stem()}.mp4"

        if training_type == 'strength':
            muscle_folder = (self.muscle_group.name if self.muscle_group else 'upper_body').strip().lower()
            return f"strength/{muscle_folder}/{filename}"

        if training_type in {'hiit', 'mobility', 'cardio'}:
            return f"{training_type}/{filename}"

        return f"{(self.exercise_type or 'strength').strip().lower()}/{filename}"

    def get_demo_video_url(self):
        if self.is_cardio:
            return ''

        raw = (self.demo_video or '').strip()
        if raw.startswith('http://') or raw.startswith('https://'):
            return raw

        relative_path = raw.lstrip('/') if raw else self._r2_relative_video_path()
        base = getattr(settings, 'R2_PUBLIC_BASE_URL', '').rstrip('/')
        if not base:
            return relative_path
        return f"{base}/{relative_path}"

    def get_image_url(self):
        if self.is_cardio or not self.image:
            return ''
        try:
            return self.image.url
        except Exception:
            return ''

    def get_estimated_calories_burned(self):
        if not self.is_cardio:
            return None

        duration_text = (self.duration or '').strip().lower()
        duration_minutes = 20
        digits = ''.join(ch if ch.isdigit() else ' ' for ch in duration_text).split()
        if digits:
            duration_minutes = max(int(digits[0]), 1)

        intensity_map = {
            'low': 6,
            'moderate': 8,
            'high': 10,
        }
        calories_per_minute = intensity_map.get((self.intensity or '').lower(), 8)
        return duration_minutes * calories_per_minute


class ExerciseLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_logs')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='logs')
    sets_completed = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'exercise')
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
