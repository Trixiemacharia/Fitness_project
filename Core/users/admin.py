from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'status', 'created_at', 'responded_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('user__username', 'message', 'admin_response')
