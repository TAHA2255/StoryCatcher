# 🎥 StoryCatcher – Your Life, Told Visually

**StoryCatcher** is a Django + OpenAI-powered web app that turns your life-changing moment into a cinematic, voiceover-driven video. Users go through a conversational interview, generate a voiceover script with AI, and get a downloadable video created with the VideoGen API.

---

## 🚀 Features

- 🤖 Conversational AI chatbot to guide user storytelling
- ✍️ Dynamic script generation via OpenAI (GPT-4 / GPT-4o)
- 🎬 Video creation powered by VideoGen API
- ✏️ Editable script preview before final generation
- 📩 Email capture before video generation (optional)
- ⬇️ Downloadable final MP4 video
- 🛠 Admin dashboard to track user stories, video links & emails
- 🌄 Custom background and logo branding

---

## 💡 How It Works

1. User begins a short chat-based interview (4 questions)
2. AI turns answers into a 5–7 line voiceover script
3. User can edit the script (optional)
4. Final script is sent to VideoGen to generate a cinematic video
5. User gets a download link after email input (or can skip email)
6. Admin can view all submissions and video links

---

## 🛠 Tech Stack

| Layer            | Technology             |
|------------------|------------------------|
| Backend          | Django (Python)        |
| Frontend         | Bootstrap 5, Vanilla JS|
| AI Integration   | OpenAI GPT-4 / GPT-4o  |
| Video Generator  | VideoGen API           |
| Database         | SQLite / PostgreSQL    |
| Hosting          | Render / Supabase      |

---
