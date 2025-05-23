
# Register your models here.
# chatbot/admin.py
from django.contrib import admin
from .models import PromptConfig, DownloadEmail

@admin.register(PromptConfig)
class PromptConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    ordering = ('-created_at',)


@admin.register(DownloadEmail)
class DownloadEmailAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)
