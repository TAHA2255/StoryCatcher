from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StorySession
from .utils import get_next_question, generate_script, create_videogen_video, fetch_videogen_status, create_videogen_video_lazy, get_videogen_file_status_once
import json
from django.shortcuts import render
from .models import StorySession
import requests
from django.conf import settings
from .models import DownloadEmail
import re
import openai



# @csrf_exempt
# def chat_api(request):
#     if not request.session.session_key:
#         request.session.create()
#     user_id = request.session.session_key

#     session, _ = StorySession.objects.get_or_create(user_id=user_id)

#     data = json.loads(request.body)
#     user_message = data.get("message")
#     is_start = data.get("start", False)

#     response_data = []

#     # Initial greet flow
#     if is_start:
#         response_data.append({
#             "role": "assistant",
#             "type": "question",
#             "content": get_next_question(session)
#         })
#         return JsonResponse({"messages": response_data})

#     # Save user's answer to the next unanswered field
#     for field in ['q1', 'q2', 'q3', 'q4']:
#         if not getattr(session, field):
#             setattr(session, field, user_message)
#             session.save()
#             break

#     # Ask next or generate result
#     question = get_next_question(session)
#     if question:
#         response_data.append({
#             "role": "assistant",
#             "type": "question",
#             "content": question
#         })
#     else:
#         if not session.generated_script:
#             script = generate_script(session)
#             session.generated_script = script
#             session.save()
#         else:
#             script = session.generated_script

#         # ✅ Only return script — don't generate video yet
#         response_data.append({
#             "role": "assistant",
#             "type": "result",
#             "content": script
#         })
#         response_data.append({
#             "role": "assistant",
#             "type": "edit_prompt",
#             "content": "Would you like to revise the script? Paste your edits below and click 'Regenerate'."
#         })

#     return JsonResponse({"messages": response_data})

@csrf_exempt
def chat_api(request):
    if not request.session.session_key:
        request.session.create()

    user_id = request.session.session_key
    session, _ = StorySession.objects.get_or_create(user_id=user_id)

    data = json.loads(request.body)
    user_message = data.get("message", "").strip()
    is_start = data.get("start", False)

    # Reset session if restarting
    if is_start:
        session.chat_history = []
        session.generated_script = None
        session.video_url = None
        session.videogen_file_id = None
        session.save()

        # Start conversation
        system_prompt = {
            "role": "system",
            "content": (
                "You are a kind and insightful interviewer. Your job is to ask the user 5 thoughtful questions "
                "to help them reflect on a life-changing experience. Ask one question at a time and wait for the user's response. "
                "When you've collected 5 answers, stop asking and say 'Thanks! I'm ready to turn your story into a visual experience.'"
            )
        }

        session.chat_history.append(system_prompt)
        session.save()

    # Append user's message
    if user_message:
        session.chat_history.append({"role": "user", "content": user_message})

    # Count how many user messages exist
    user_messages = [msg for msg in session.chat_history if msg["role"] == "user"]

    response_data = []

    if len(user_messages) < 5:
        # Ask next question
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=session.chat_history,
            temperature=0.7
        )
        assistant_msg = completion['choices'][0]['message']
        if not isinstance(session.chat_history, list):
             session.chat_history = []
        session.chat_history.append(assistant_msg)
        session.save()

        response_data.append({
            "role": "assistant",
            "type": "question",
            "content": assistant_msg["content"]
        })
    else:
        # Generate script if not already done
        if not session.generated_script:
            # Reconstruct full story from user answers
            answers = [msg["content"] for msg in session.chat_history if msg["role"] == "user"]
            story_text = "\n".join([f"A{i+1}: {ans}" for i, ans in enumerate(answers)])
            session.q1, session.q2, session.q3, session.q4 = answers[:4]
            session.generated_script = generate_script(session)
            session.save()

        response_data.append({
            "role": "assistant",
            "type": "result",
            "content": session.generated_script
        })
        response_data.append({
            "role": "assistant",
            "type": "edit_prompt",
            "content": "Would you like to revise the script? Do your edits below and click 'generate video'."
        })

    return JsonResponse({"messages": response_data})

@csrf_exempt
def generate_video_api(request):

    try:
        if not request.session.session_key:
            return JsonResponse({"error": "Session not found"}, status=403)

        user_id = request.session.session_key
        session = StorySession.objects.get(user_id=user_id)

        data = json.loads(request.body)
        updated_script = data.get("script")

        if updated_script:
            session.generated_script = updated_script
            session.video_url = ""
            session.save()

        # ✅ Start the job but DO NOT wait
        api_file_id = create_videogen_video_lazy(session.generated_script)
        print(api_file_id)

        session.videogen_file_id = api_file_id  # Save file ID to track status later
        session.save()

        return JsonResponse({
            "status": "started",
            "api_file_id": api_file_id
        })
    except Exception as e:
            # Log the error
            import traceback
            traceback.print_exc()

            return JsonResponse({"error": f"Video generation failed: {str(e)}"}, status=500)

    
def chat_home(request):
    request.session.flush()
    return render(request, "chatbot/chat.html")



@csrf_exempt
def video_status_api(request):
    if not request.session.session_key:
        return JsonResponse({"error": "Session not found"}, status=403)

    user_id = request.session.session_key
    session = StorySession.objects.get(user_id=user_id)

    if not session.videogen_file_id:
        return JsonResponse({"status": "not_started"})

    result = get_videogen_file_status_once(session.videogen_file_id)

    if result["loadingState"] == "FULFILLED" and result["apiFileSignedUrl"]:
        session.video_url = result["apiFileSignedUrl"]
        session.save()
        return JsonResponse({
            "status": "done",
            "video_url": result["apiFileSignedUrl"]
        })
    elif result["loadingState"] == "REJECTED":
        return JsonResponse({
            "status": "error",
            "error": result.get("errorDisplayMessage", "Video generation failed.")
        })

    return JsonResponse({
        "status": "processing",
        "progress": result.get("progressPercentage", 0)
    })


from django.contrib.auth.models import User
from django.http import JsonResponse

def create_admin_user(request):
    if User.objects.filter(username="admin").exists():
        return JsonResponse({"status": "Admin already exists"})

    User.objects.create_superuser("admin", "admin@example.com", "admin")
    return JsonResponse({"status": "Superuser created!"})




@csrf_exempt
def collect_email(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")

        # Simple regex-based email validation (backend)
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return JsonResponse({"error": "Invalid email."}, status=400)

        DownloadEmail.objects.get_or_create(email=email)

        # ✅ Also save to the user's StorySession
        if request.session.session_key:
            user_id = request.session.session_key
            session = StorySession.objects.filter(user_id=user_id).first()
            if session:
                session.email = email
                session.save()
        return JsonResponse({"success": True})
    
    return JsonResponse({"error": "Invalid request"}, status=405)
