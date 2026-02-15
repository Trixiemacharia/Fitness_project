from django.contrib import admin
from django.utils.html import format_html
from .models import Category,Exercise

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=('id','name','image_tag')
    search_fields = ('name',)

    readonly_fields = ('image_tag',)
    fieldsets = (
        (None, {
            'fields':('name','description','total_programs','image','image_tag')
        }),
    )

    def image_tag(self,obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="auto"/>',obj.image.url)
        return"-"
    image_tag.short_description = 'Image Preview'

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