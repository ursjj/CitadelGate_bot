import os

from flask import Flask, request, jsonify

import requests

from google import genai



app = Flask(__name__)



# Fetch configurations from Environment Variables

TELEGRAM_TOKEN = os.environ.get("8539050051:AAE8JmT5HgTbgdJ9lnjChKc9baGyDS3PB8k")

GEMINI_API_KEY = os.environ.get("AIzaSyBrWMR6TEpJqXTyze_d9D8mn4ZInt4dr0o")



# Initialize Gemini Client

ai_client = genai.Client(api_key=GEMINI_API_KEY)



def analyze_message_with_ai(text: str) -> str:

    system_instruction = (

        "You are an advanced moderation AI for a BGMI Card Exchange Telegram group. "

        "Users are ONLY allowed to trade game cards for other cards. "

        "Selling cards for real cash or in-game popularity (pops) is banned. "

        "External channel promotion or social media links are banned. "

        "CRITICAL: If someone says 'no money' or 'no pops', they are complying with rules. That is SAFE. "

        "Analyze the intent. Respond with exactly one word: 'SAFE' or 'VIOLATION'."

    )

    try:

        response = ai_client.models.generate_content(

            model='gemini-2.5-flash',

            contents=text,

            config={"system_instruction": system_instruction, "temperature": 0.0}

        )

        return response.text.strip().upper()

    except Exception as e:

        print(f"Gemini Error: {e}")

        return "SAFE"



@app.route('/', methods=['POST', 'GET'])

def handle_webhook():

    if request.method == 'GET':

        return "Bot system is active and monitoring.", 200



    update_json = request.get_json()

    

    # Safely verify it's a standard text message

    if update_json and "message" in update_json and "text" in update_json["message"]:

        msg = update_json["message"]

        chat_id = msg["chat"]["id"]

        message_id = msg["message_id"]

        user_text = msg["text"]

        user_name = msg["from"].get("username", msg["from"].get("first_name", "User"))



        # Fire up the AI engine evaluation

        verdict = analyze_message_with_ai(user_text)



        if "VIOLATION" in verdict:

            base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

            

            # 1. Delete the message

            requests.post(f"{base_url}/deleteMessage", json={

                "chat_id": chat_id,

                "message_id": message_id

            })

            

            # 2. Fire the warning notification tag

            warning_text = f"⚠️ @{user_name}, message removed! No cash/popularity deals or promotions allowed here."

            requests.post(f"{base_url}/sendMessage", json={

                "chat_id": chat_id,

                "text": warning_text

            })



    return jsonify({"status": "handled"}), 200
