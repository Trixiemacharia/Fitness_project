from django.contrib import admin
from django.utils.html import format_html
from .models import Category, MuscleGroup, Exercise


# ===== MUSCLE GROUP =====
@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display      = ['get_name_display', 'linked_categories']
    filter_horizontal = ['categories']

    def linked_categories(self, obj):
        return ', '.join([c.name for c in obj.categories.all()]) or '—'
    linked_categories.short_description = 'Linked Categories'


# ===== CATEGORY =====
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'training_type', 'image_tag', 'total_exercises']
    list_filter  = ['training_type']

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px; border-radius:6px;" />', obj.image.url)
        return '—'
    image_tag.short_description = 'Image'

    def total_exercises(self, obj):
        return obj.exercises.count()
    total_exercises.short_description = 'Exercises'


# ===== EXERCISE =====
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display  = ['id', 'name', 'exercise_type', 'muscle_group', 'level', 'category', 'equipment']
    list_filter   = ['exercise_type', 'muscle_group', 'level', 'category']
    search_fields = ['name']
    ordering      = ['exercise_type', 'muscle_group', 'level', 'name']

    fieldsets = (
        ('Core Info', {
            'fields': ('category', 'muscle_group', 'exercise_type', 'name', 'description', 'level', 'image', 'demo_video'),
        }),
        ('Exercise Details', {
            'description': 'Equipment needed and step-by-step instructions shown in the exercise detail screen.',
            'fields': ('equipment', 'instructions'),
        }),
        ('Strength Fields', {
            'classes': ('collapse',),
            'description': 'Leave blank to use level defaults (Beginner: 2×10–15, Intermediate: 3×8–12, Advanced: 4×6–10)',
            'fields': ('sets', 'reps', 'weight', 'rest_time'),
        }),
        ('HIIT Fields', {
            'classes': ('collapse',),
            'description': 'Leave blank to use level defaults (Beginner: 20s/40s×3, Intermediate: 30s/30s×4, Advanced: 40s/20s×5)',
            'fields': ('work_time', 'hiit_rest_time', 'rounds'),
        }),
        ('Cardio Fields', {
            'classes': ('collapse',),
            'fields': ('duration', 'distance', 'intensity'),
        }),
    )