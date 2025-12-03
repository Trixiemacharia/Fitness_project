from django.contrib import admin
from .models import Category,Exercise

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=('id','name')
    search_fields = ('name',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)
    fieldsets = (
        (None, {
            'fields' : ('category', 'name', 'description', 'demo_video')
        }),
    )