import os

import asyncio

from telegram import Bot, ChatPermissions



async def main():

    bot = Bot(token=os.environ.get("8539050051:AAE8JmT5HgTbgdJ9lnjChKc9baGyDS3PB8k"))

    chat_id = os.environ.get("-5147212177")

    

    # Re-enable sending messages

    unlock_perms = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)

    await bot.set_chat_permissions(chat_id=chat_id, permissions=unlock_perms)

    await bot.send_message(chat_id=chat_id, text="☀️ Good morning! The group is now UNLOCKED.")

    

    # Post Group Rules

    rules_text = (

        "📜 **BGMI Card Exchange Rules:**\n\n"

        "1️⃣ Card-for-Card trades only.\n"

        "2️⃣ **NO** cash deals (UPI/Paytm) or trading for Popularity (Pops).\n"

        "3️⃣ **NO** self-promotion or external links (YouTube/Telegram channels) allowed by anyone.\n\n"

        "👉 Keep it clean, use the group responsibly!"

    )

    await bot.send_message(chat_id=chat_id, text=rules_text, parse_mode="Markdown")



if __name__ == "__main__":

    asyncio.run(main())
