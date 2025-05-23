import openai
import requests
from django.conf import settings
import time
import re
from .models import PromptConfig

openai.api_key = settings.OPENAI_API_KEY


QUESTIONS = [
    "1. What was the life-changing moment or experience you went through?",
    "2. What led up to this moment?",
    "3. What did that moment feel like—emotionally, physically, spiritually?",
    "4. How did this experience change you afterward?"
]

def get_next_question(session):
    for i, field in enumerate(['q1', 'q2', 'q3', 'q4']):
        if not getattr(session, field):
            return QUESTIONS[i]
    return None


# def generate_script(session):
#     full_story = f"""
#     Q1: {session.q1}
#     Q2: {session.q2}
#     Q3: {session.q3}
#     Q4: {session.q4}
#     """

#     prompt = f"""
# You are a compassionate, cinematic AI storyteller.
# From this story, generate:

# 1. A **4-part storyboard** describing each visual scene in detail with headings, visuals, mood, and text overlays.
# 2. A **short voiceover script**, no more than **80–90 words**, written like a gentle inner monologue, scene by scene, matching the storyboard.

# The script should be paced for a video of about **45–50 seconds**, with poetic and intimate language, vivid imagery, and soft rhythm.

# User Story:
# {full_story}
#     """

#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.85
#     )

#     return response['choices'][0]['message']['content']
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
From this story, generate:

1. A **4-part storyboard** describing each visual scene in detail with headings, visuals, mood, and text overlays.
2. A **short voiceover script**, no more than **80–90 words**, written like a gentle inner monologue, scene by scene, matching the storyboard.

The script should be paced for a video of about **45–50 seconds**, with poetic and intimate language, vivid imagery, and soft rhythm.

User Story:
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
