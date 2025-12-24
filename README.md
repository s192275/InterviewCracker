# Interview Crasher

**Interview Crasher** is a desktop application that listens to interview questions in real time, detects the intent of the question, and generates **text-based answers using Google Gemini**.

The application:
- Listens to live audio
- Converts speech to text
- Identifies interview questions
- Generates clear, relevant answers via Gemini

All processes run on an **asynchronous, event-driven architecture**.

---

## 🚀 Features

- 🎧 Real-time audio capture (PyAudio)
- 🧠 Interview question detection
- 🤖 AI-powered answer generation (Google Gemini)
- ⚡ Async architecture (asyncio)
- 🖥️ Desktop UI built with Flet
- 📦 Prebuilt Windows `.exe` available

---

## 🛠️ Tech Stack

- Python 3.10+
- Flet (UI)
- asyncio
- PyAudio
- Google Gemini API

---

## 📦 Installation

### Option 1: Run the EXE (Recommended)

1. Download the latest `.exe` file from the **Dist** folder.
2. Run the application.
3. Enter your **Gemini API Key**.
4. Start listening and generating answers.

> No Python installation required.

---

### Option 2: Run from Source

```bash
git clone https://github.com/your-username/interview-crasher.git
cd interview-crasher
pip install -r requirements.txt
cd src
python app.py
