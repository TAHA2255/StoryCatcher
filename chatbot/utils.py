import openai
import requests
from django.conf import settings
import time
import re
import random
from .models import PromptConfig

openai.api_key = settings.OPENAI_API_KEY


import random

QUESTION_VARIANTS = [
    [
        "1. What was the life-changing moment you experienced?\nIt could be anything—a turning point, a challenge, a realization, or even something quiet but deeply meaningful.",
        "1. Can you tell me about a defining experience in your life?\nThink of a moment that shifted something inside you, big or small.",
        "1. Describe a life-altering event you've been through.\nIt might be dramatic or subtle—just something that changed your path."
    ],
    [
        "2. What led up to that moment?\nShare what was happening in your life, your thoughts, or the events that brought you there.",
        "2. Can you walk me through what came before that experience?\nWhat was building inside or around you?",
        "2. Tell me about the lead-up to that moment.\nWhat set the stage for it to unfold?"
    ],
    [
        "3. What did that moment feel like?\nEmotionally, physically, spiritually—whatever you remember most vividly.",
        "3. Try to describe the feeling of that experience.\nWere there sights, sounds, or emotions that stood out?",
        "3. In that moment, how did your body or heart respond?\nFeelings, sensations, or even silence—describe it all."
    ],
    [
        "4. How did this change you afterward?\nTell me how that experience lives in you today.",
        "4. What’s different now, because of that moment?\nIt might be a belief, a habit, a relationship—anything.",
        "4. How did that moment shape who you’ve become?\nWhat part of you grew or transformed?"
    ]
]




# QUESTIONS = [
#     "1. What was the life-changing moment or experience you went through?",
#     "2. What led up to this moment?",
#     "3. What did that moment feel like—emotionally, physically, spiritually?",
#     "4. How did this experience change you afterward?"
# ]

def get_next_question(session):
    fields = ['q1', 'q2', 'q3', 'q4']
    for i, field in enumerate(fields):
        if not getattr(session, field):
            return random.choice(QUESTION_VARIANTS[i])
    return None


def generate_script(session):
    full_story = f"""
    Q1: {session.q1}
    Q2: {session.q2}
    Q3: {session.q3}
    Q4: {session.q4}
    """

    # ✅ Try to get active prompt
    prompt_obj = PromptConfig.objects.filter(use_as_default=True).order_by('-created_at').first()

    if prompt_obj:
        prompt = prompt_obj.prompt_template.replace("{{story}}", full_story)
    else:
        # ✅ Fallback default
        prompt = f"""
You are a compassionate, cinematic AI storyteller.
Be emotionally attuned and encouraging. Make the user feel safe sharing.
turn this story into a compelling short video that builds gradually in emotional intensity by
synthesizing the answers into a 5-7 line commentary for a short narrative video. Use first person. End with an insightful and
inspiring punchline.
Optimize the commentary for use as a prompt for VideoGen by making every line sound like a voiceover so VideoGen
interprets your intention through the tone of your words. Use long, breathy sentences for calm, reflective moods.
Use short, choppy lines to signal intensity or tension. Each line should be emotionally vivid, suggest action or setting, and
flow as a single voiceover.
story:

{full_story}
        """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85
    )

    return response['choices'][0]['message']['content']

import re

def extract_voiceover_script(raw_text):
    """
    Extract only the voiceover script (quoted lines) from an OpenAI-generated response.
    Removes markdown like Mood, overlays, bold, and Scene labels.
    """
    lines = raw_text.splitlines()
    script_lines = []

    for line in lines:
        # Remove mood, overlays, markdown headers
        if line.strip().startswith("**Mood:**") or line.strip().startswith("**Text overlays:**") or "Voiceover Script" in line:
            continue

        # Remove scene numbering (e.g., "1. **Scene 1:**", "**Scene 2:**")
        line = re.sub(r"^(\d+\.\s*)?\*\*Scene \d+\:\*\*", "", line)

        # Extract quoted narration only (text inside quotes)
        matches = re.findall(r"\"([^\"]+)\"", line)
        script_lines.extend(matches)

    # Join all sentences into a single script block
    return " ".join(script_lines)



# utils.py
def fetch_videogen_status(api_file_id):
    headers = {
        "Authorization": f"Bearer {settings.VIDEOGEN_API_KEY}"
    }
    params = { "apiFileId": api_file_id }

    try:
        response = requests.get("https://ext.videogen.io/v1/get-file", headers=headers, params=params)
        result = response.json()
        return result
    except Exception as e:
        print(f"[VideoGen] Error checking video status: {e}")
        return {"loadingState": "REJECTED", "errorDisplayMessage": str(e)}


def create_videogen_video(script_text):
    """
    Send script to VideoGen's /v1/script-to-video endpoint and return signed URL.
    """
    clean_script = extract_voiceover_script(script_text)

    headers = {
        "Authorization": f"Bearer {settings.VIDEOGEN_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "script": clean_script,
        "voice": "Matilda",
        "voiceVolume": 1,
        "musicUrl": "",
        "musicVolume": 0.15,
        "captionFontName": "Luckiest Guy",
        "captionFontSize": 75,
        "captionFontWeight": 700,
        "captionTextColor": {
            "red": 255,
            "green": 0,
            "blue": 0
        },
        "captionTextJustification": "CENTER",
        "captionVerticalAlignment": "BOTTOM",
        "captionStrokeWeight": 3,
        "captionBackgroundStyleType": "WRAPPED",
        "captionBackgroundBorderRadius": 0.3,
        "captionBackgroundOpacity": 0.6,
        "aspectRatio": {
            "width": 9,
            "height": 16
        },
        "minDimensionPixels": 1080

    }

    response = requests.post(
        "https://ext.videogen.io/v1/script-to-video",  # new endpoint
        headers=headers,
        json=payload
    )
    response.raise_for_status()

    api_file_id = response.json().get("apiFileId")

    print(f"[VideoGen] apiFileId: {api_file_id}")

    file_data = get_videogen_file_status(api_file_id)
    
    if file_data and file_data.get("apiFileSignedUrl"):
        return file_data["apiFileSignedUrl"]

    return None



def get_videogen_file_status(api_file_id):
    headers = {
        "Authorization": f"Bearer {settings.VIDEOGEN_API_KEY}"
    }


    params = { "apiFileId": api_file_id }

    try:
        for i in range(20):
            response = requests.get("https://ext.videogen.io/v1/get-file", headers=headers, params=params)
            result = response.json()

            print("attempt",result)

            if result["loadingState"] == "FULFILLED" and result["apiFileSignedUrl"]:
                return result

            if result["loadingState"] == "REJECTED":
                print("Video generation failed:", result.get("errorDisplayMessage"))
                return result
            time.sleep(10)

        return None  #
    except Exception as e:
        print(f"[VideoGen] Error polling video: {e}")
        return {}


def create_videogen_video_lazy(script):
    headers = {
        "Authorization": f"Bearer {settings.VIDEOGEN_API_KEY}",
        "Content-Type": "application/json"
    }

    clean_script = extract_voiceover_script(script)

    payload = {
        "script": clean_script,
        "voice": "Matilda",
        "voiceVolume": 1,
        "musicUrl": "",
        "musicVolume": 0.15,
        "captionFontName": "Luckiest Guy",
        "captionFontSize": 75,
        "captionFontWeight": 700,
        "captionTextColor": {"red": 255, "green": 0, "blue": 0},
        "captionTextJustification": "CENTER",
        "captionVerticalAlignment": "BOTTOM",
        "captionStrokeWeight": 3,
        "captionBackgroundStyleType": "WRAPPED",
        "captionBackgroundBorderRadius": 0.3,
        "captionBackgroundOpacity": 0.6,
        "captionIsHidden": False,
        "aspectRatio": {"width": 9, "height": 16},
        "minDimensionPixels": 1080
    }


    for attempt in range(3):
        try:
            response = requests.post(
                "https://ext.videogen.io/v1/script-to-video",
                json=payload,
                headers=headers
            )
            response.raise_for_status()  # 💥 This is where 403 gets raised

            data = response.json()
            if "apiFileId" in data:
                print(f"[VideoGen] apiFileId received on attempt {attempt + 1}")
                return data["apiFileId"]

            print(f"[VideoGen] Unexpected response: {data}")
        except requests.exceptions.HTTPError as e:
            print(f"[VideoGen] HTTP error on attempt {attempt+1}: {e}")
            try:
                print("Response:", response.json())
            except Exception:
                pass
        except Exception as e:
            print(f"[VideoGen] Exception on attempt {attempt+1}: {e}")

        time.sleep(10)

    print("[VideoGen] Failed to obtain apiFileId after retries.")
    return None


def get_videogen_file_status_once(api_file_id):
    headers = {
        "Authorization": f"Bearer {settings.VIDEOGEN_API_KEY}"
    }

    params = {"apiFileId": api_file_id}

    try:
        response = requests.get("https://ext.videogen.io/v1/get-file", headers=headers, params=params)
        return response.json()
    except Exception as e:
        print(f"[VideoGen] Error checking video: {e}")
        return {"loadingState": "ERROR", "errorDisplayMessage": str(e)}
