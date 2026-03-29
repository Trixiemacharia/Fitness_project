from django.contrib import admin
from django.utils.html import format_html
from .models import Category, MuscleGroup, Exercise


#MUSCLE GROUP
@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display      = ['get_name_display', 'linked_categories']
    filter_horizontal = ['categories']

    def linked_categories(self, obj):
        return ', '.join([c.name for c in obj.categories.all()]) or '—'
    linked_categories.short_description = 'Linked Categories'


#CATEGORY
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
    list_display  = ['id', 'name', 'exercise_type', 'muscle_group', 'level']
    list_filter   = ['exercise_type', 'muscle_group', 'level', 'category']
    search_fields = ['name']
    ordering      = ['exercise_type', 'muscle_group', 'level', 'name']

    fieldsets = (
        ('Core Info', {
            'fields': ('category', 'muscle_group', 'exercise_type', 'name', 'description', 'level'),
        }),
        ('Media - R2 URLs',{
            'description': ('https://pub-a3e3770ca86b453197bf4160321b1b0a.r2.dev'),
            'fields':('demo_video','video_preview_display'),
        }),
        ('Exercise Details', {
            'description': ' Step-by-step instructions shown in the exercise detail screen.',
            'fields': ( 'instructions',),
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
    
    readonly_fields = ['video_preview_display']

    #  Video preview
    def video_preview_display(self, obj):
        if obj.demo_video:
            return format_html(
                '<video width="320" height="200" controls style="border-radius:8px; margin-top:8px;">'
                '<source src="{}" type="video/mp4">'
                'Your browser does not support video.'
                '</video>',
                obj.demo_video
            )
        return format_html('<span style="color:#999;">No video yet — paste R2 URL above</span>')
    video_preview_display.short_description = 'Video Preview'


    # Checkmark in list view showing which exercises have videos
    def has_video(self, obj):
        if obj.demo_video:
            return format_html('<span style="color:green; font-size:16px;">✓</span>')
        return format_html('<span style="color:#ccc;">—</span>')
    has_video.short_description = 'Video'

    # Auto-suggest the expected R2 URL when saving
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.demo_video:
            # Show a hint in the admin message
            category_name = obj.category.training_type if obj.category else 'category'
            filename = obj.name.lower().replace(' ', '_') + '.mp4'
            expected_url = f"exercises/{category_name}/{filename}"
            self.message_user(
                request,
                f' Expected R2 path for this exercise: {expected_url}',
                level='warning'
            )