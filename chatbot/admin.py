from django.contrib import admin

# Register your models here.
# chatbot/admin.py
from django.contrib import admin
from .models import PromptConfig

@admin.register(PromptConfig)
class PromptConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    ordering = ('-created_at',)
