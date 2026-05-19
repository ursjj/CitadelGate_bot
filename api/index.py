import os
from flask import Flask, request, jsonify
import requests
from google import genai
from google.genai import types  # <-- Required for configuration classes in the new SDK!

app = Flask(__name__)

# Fetch configurations from Environment Variables
TELEGRAM_TOKEN = os.environ.get("8539050051:AAE8JmT5HgTbgdJ9lnjChKc9baGyDS3PB8k")
GEMINI_API_KEY = os.environ.get("AIzaSyBnYZeaZw6Qvsx3fy01RKsZoRVCxIVISxM")
GROUP_CHAT_ID = "-1003977136118" 

BASE_TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

try:
    if GEMINI_API_KEY:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        ai_client = genai.Client()
except Exception as e:
    print(f"AI Client Init Error: {e}")
    ai_client = None

def analyze_message_with_ai(text: str) -> str:
    if not ai_client:
        return "SAFE"
        
    system_instruction = (
        "You are an advanced moderation AI for a BGMI Card Exchange Telegram group. "
        "Users are ONLY allowed to trade game cards for other cards. "
        "Selling cards for real cash, UPI, or in-game popularity (pops) is banned. "
        "External channel promotion or social media links are banned. "
        "CRITICAL: If someone says 'no money' or 'no pops', they are complying with rules. That is SAFE. "
        "Analyze the intent. Respond with exactly one word: 'SAFE' or 'VIOLATION'."
    )
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0
            )
        )
        return response.text.strip().upper()
    except Exception as e:
        print(f"Gemini API Runtime Error: {e}")
        return "SAFE"

# --- FIX: ACCEPT BOTH ROOT AND WEBHOOK PATHS ---
@app.route('/', methods=['POST', 'GET'])
@app.route('/webhook', methods=['POST', 'GET'])
def handle_webhook():
    if request.method == 'GET':
        return "Bot system is active and monitoring.", 200

    try:
        update_json = request.get_json()
        if not update_json:
            return jsonify({"status": "no data"}), 200
            
        # Target messages cleanly
        if "message" in update_json and "text" in update_json["message"]:
            msg = update_json["message"]
            chat_id = str(msg["chat"]["id"])
            message_id = msg["message_id"]
            user_text = msg["text"]
            user_name = msg["from"].get("username", msg["from"].get("first_name", "User"))

            ai_verdict = analyze_message_with_ai(user_text)

            if "VIOLATION" in ai_verdict:
                # 1. Action: Delete message
                requests.post(f"{BASE_TELEGRAM_URL}/deleteMessage", json={
                    "chat_id": chat_id, 
                    "message_id": message_id
                })
                # 2. Action: Warn user
                warning_text = f"⚠️ @{user_name}, message removed! No cash/popularity deals or promotions allowed."
                requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={
                    "chat_id": chat_id, 
                    "text": warning_text
                })
    except Exception as e:
        print(f"Execution failed: {e}")

    return jsonify({"status": "handled"}), 200

# --- CRON ROUTE: LOCK ---
@app.route('/secret-lock-endpoint', methods=['POST', 'GET'])
def cron_lock():
    try:
        requests.post(f"{BASE_TELEGRAM_URL}/setChatPermissions", json={
            "chat_id": GROUP_CHAT_ID,
            "permissions": {"can_send_messages": False}
        })
        requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={
            "chat_id": GROUP_CHAT_ID,
            "text": "🌙 Night mode activated! Group is now LOCKED. Good night ppl! ✨"
        })
        return "Locked Successfully", 200
    except Exception as e:
        return f"Lock error: {e}", 500

# --- CRON ROUTE: UNLOCK ---
@app.route('/secret-unlock-endpoint', methods=['POST', 'GET'])
def cron_unlock():
    try:
        requests.post(f"{BASE_TELEGRAM_URL}/setChatPermissions", json={
            "chat_id": GROUP_CHAT_ID,
            "permissions": {
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_other_messages": True
            }
        })
        requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={
            "chat_id": GROUP_CHAT_ID,
            "text": "☀️ Good morning! The group is now UNLOCKED."
        })
        return "Unlocked Successfully", 200
    except Exception as e:
        return f"Unlock error: {e}", 500
