from django.urls import path
from .views import chat_api,generate_video_api, chat_home, video_status_api, create_admin_user



urlpatterns = [
    #path("", lambda r: render(r, "chatbot/chat.html"), name="chat"),
    path("", chat_home, name="chat"),
     path("create-admin/", create_admin_user),
    path("api/chat/", chat_api, name="chat_api"),
    path("api/generate-video/", generate_video_api, name="generate_video_api"),
    path('api/video-status/', video_status_api, name='video_status_api'),
]
