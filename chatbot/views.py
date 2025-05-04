from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StorySession
from .utils import get_next_question, generate_script, create_videogen_video, fetch_videogen_status
import json
from django.shortcuts import render
from .models import StorySession
import requests
from django.conf import settings

@csrf_exempt
def chat_api(request):
    if not request.session.session_key:
        request.session.create()
    user_id = request.session.session_key

    session, _ = StorySession.objects.get_or_create(user_id=user_id)

    data = json.loads(request.body)
    user_message = data.get("message")
    is_start = data.get("start", False)

    response_data = []

    # Initial greet flow
    if is_start:
        response_data.append({
            "role": "assistant",
            "type": "question",
            "content": get_next_question(session)
        })
        return JsonResponse({"messages": response_data})

    # Save user's answer to the next unanswered field
    for field in ['q1', 'q2', 'q3', 'q4']:
        if not getattr(session, field):
            setattr(session, field, user_message)
            session.save()
            break

    # Ask next or generate result
    question = get_next_question(session)
    if question:
        response_data.append({
            "role": "assistant",
            "type": "question",
            "content": question
        })
    else:
        if not session.generated_script:
            script = generate_script(session)
            session.generated_script = script
            session.save()
        else:
            script = session.generated_script

        # ✅ Only return script — don't generate video yet
        response_data.append({
            "role": "assistant",
            "type": "result",
            "content": script
        })
        response_data.append({
            "role": "assistant",
            "type": "edit_prompt",
            "content": "Would you like to revise the script? Paste your edits below and click 'Regenerate'."
        })

    return JsonResponse({"messages": response_data})


@csrf_exempt
def generate_video_api(request):
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

    video_url = create_videogen_video(session.generated_script)


    session.video_url = video_url
    session.save()

    return JsonResponse({
        "message": "Video generated successfully.",
        "video_url": video_url
    })

    
def chat_home(request):
    request.session.flush()
    return render(request, "chatbot/chat.html")



