import os
from flask import Flask, request, jsonify
import requests
from google import genai
from google.genai import types  # <-- Required for configuration classes in the new SDK!

app = Flask(__name__)

# Fetch configurations from Environment Variables
TELEGRAM_TOKEN = os.environ.get("8539050051:AAE8JmT5HgTbgdJ9lnjChKc9baGyDS3PB8k")
GEMINI_API_KEY = os.environ.get("AIzaSyBnYZeaZw6Qvsx3fy01RKsZoRVCxIVISxM")
GROUP_CHAT_ID = os.environ.get("-1003977136118")

BASE_TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Initialize Gemini Client cleanly using the new SDK standard
try:
    if GEMINI_API_KEY:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        ai_client = genai.Client()
except Exception as e:
    print(f"Initialization Error: {e}")
    ai_client = None

def analyze_message_with_ai(text: str) -> str:
    if not ai_client:
        print("AI Client not initialized, passing message through as safe.")
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
        # Correct google-genai SDK implementation using types.GenerateContentConfig
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0
            )
        )
        result = response.text.strip().upper()
        print(f"AI Evaluation for phrase [{text}]: {result}")
        return result
    except Exception as e:
        print(f"Gemini API Runtime Error: {e}")
        return "SAFE"

# --- MAIN REAL-TIME WEBHOOK FOR MODERATION ---
@app.route('/', methods=['POST', 'GET'])
def handle_webhook():
    if request.method == 'GET':
        return "Bot system is active and monitoring.", 200

    try:
        update_json = request.get_json()
        
        # DEBUG STAGE 1: Tell the group we received data!
        if update_json:
            debug_info = f"🤖 Received payload type: {'message' in update_json}"
            requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={"chat_id": GROUP_CHAT_ID, "text": debug_info})
        
        if update_json and "message" in update_json and "text" in update_json["message"]:
            msg = update_json["message"]
            chat_id = msg["chat"]["id"]
            message_id = msg["message_id"]
            user_text = msg["text"]
            user_name = msg["from"].get("username", msg["from"].get("first_name", "User"))

            # DEBUG STAGE 2: Tell the group what text we are analyzing
            requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={"chat_id": chat_id, "text": f"🔍 Analyzing text: {user_text}"})

            ai_verdict = analyze_message_with_ai(user_text)
            
            # DEBUG STAGE 3: Tell the group what Gemini decided
            requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={"chat_id": chat_id, "text": f"🤖 Gemini Verdict: {ai_verdict}"})

            if "VIOLATION" in ai_verdict:
                # 1. Delete the bad message
                requests.post(f"{BASE_TELEGRAM_URL}/deleteMessage", json={"chat_id": chat_id, "message_id": message_id})
                # 2. Issue formal warning
                warning_text = f"⚠️ @{user_name}, message removed! No cash/popularity deals or promotions allowed."
                requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={"chat_id": chat_id, "text": warning_text})
                
    except Exception as e:
        # DEBUG STAGE 4: Print the exact crash reason directly in the chat layout
        error_msg = f"❌ Webhook crash log: {str(e)}"
        requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={"chat_id": GROUP_CHAT_ID, "text": error_msg})

    return jsonify({"status": "handled"}), 200


# --- SECRET ROUTE: TRIGGER LOCK FROM GITHUB ---
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

# --- SECRET ROUTE: TRIGGER UNLOCK FROM GITHUB ---
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
        
        rules_text = (
            "📜 **BGMI Card Exchange Rules:**\n\n"
            "1️⃣ Card-for-Card trades only.\n"
            "2️⃣ **NO** cash deals (UPI/Paytm) or trading for Popularity (Pops).\n"
            "3️⃣ **NO** self-promotion or external links allowed by anyone.\n\n"
            "👉 Keep it clean, use the group responsibly!"
        )
        requests.post(f"{BASE_TELEGRAM_URL}/sendMessage", json={
            "chat_id": GROUP_CHAT_ID,
            "text": rules_text,
            "parse_mode": "Markdown"
        })
        return "Unlocked and Rules Distributed", 200
    except Exception as e:
        return f"Unlock error: {e}", 500
