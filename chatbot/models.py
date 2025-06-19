

# Create your models here.
from django.db import models

class StorySession(models.Model):
    user_id = models.CharField(max_length=255)
    q1 = models.TextField(blank=True)
    q2 = models.TextField(blank=True)
    q3 = models.TextField(blank=True)
    q4 = models.TextField(blank=True)
    generated_script = models.TextField(blank=True, null=True)
    video_url = models.URLField(max_length=1000,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user_script_modification = models.TextField(blank=True)
    videogen_file_id = models.CharField(max_length=255, blank=True, null=True)
    chat_history = models.JSONField(default=list, blank=True, null=True)





class PromptConfig(models.Model):
    name = models.CharField(max_length=100, default="Default")
    prompt_template = models.TextField(help_text="Use {{story}} as a placeholder for the user story.")
    use_as_default = models.BooleanField(default=False)  # ✅ Add this field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class DownloadEmail(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
