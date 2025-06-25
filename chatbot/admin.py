
# Register your models here.
# chatbot/admin.py
from django.contrib import admin
from .models import PromptConfig, DownloadEmail, StorySession
from django.utils.html import format_html

@admin.register(PromptConfig)
class PromptConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    ordering = ('-created_at',)


@admin.register(DownloadEmail)
class DownloadEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)

@admin.register(StorySession)
class StorySessionAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'email', 'created_at', 'video_link_display')  # ✅ Added 'email'

    def video_link_display(self, obj):
        if obj.video_url:
            return format_html("<a href='{}' target='_blank'>Watch Video 🎥</a>", obj.video_url)
        return "No video yet"

    video_link_display.allow_tags = True
    video_link_display.short_description = "Video Link"