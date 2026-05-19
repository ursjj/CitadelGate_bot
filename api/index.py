from flask import Flask, request, jsonify

from telegram import Bot

import os

from google import genai



app = Flask(__name__)



# Initialize APIs from Environment Variables

bot = Bot(token=os.environ.get("8539050051:AAE8JmT5HgTbgdJ9lnjChKc9baGyDS3PB8k"))

ai_client = genai.Client(api_key=os.environ.get("AIzaSyBrWMR6TEpJqXTyze_d9D8mn4ZInt4dr0o"))



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

    except Exception:

        return "SAFE"



@app.route('/', methods=['POST'])

async def handle_webhook():

    update_json = request.get_json()

    

    # Check if this is a standard text message in a group

    if "message" in update_json and "text" in update_json["message"]:

        msg = update_json["message"]

        chat_id = msg["chat"]["id"]

        message_id = msg["message_id"]

        user_text = msg["text"]

        user_name = msg["from"].get("username", msg["from"].get("id"))



        # Run AI filtering

        if "VIOLATION" in analyze_message_with_ai(user_text):

            try:

                await bot.delete_message(chat_id=chat_id, message_id=message_id)

                warning_text = f"⚠️ @{user_name}, message removed! No cash/popularity deals or promotions allowed."

                await bot.send_message(chat_id=chat_id, text=warning_text)

            except Exception as e:

                print(f"Error handling restriction: {e}")



    return jsonify({"status": "ok"}), 200
