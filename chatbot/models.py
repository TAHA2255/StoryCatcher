

# Create your models here.
from django.db import models

class StorySession(models.Model):
    user_id = models.CharField(max_length=255)
    q1 = models.TextField(blank=True)
    q2 = models.TextField(blank=True)
    q3 = models.TextField(blank=True)
    q4 = models.TextField(blank=True)
    generated_script = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user_script_modification = models.TextField(blank=True)