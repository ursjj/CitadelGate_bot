import os

import asyncio

from telegram import Bot, ChatPermissions



async def main():

    bot = Bot(token=os.environ.get("8539050051:AAE8JmT5HgTbgdJ9lnjChKc9baGyDS3PB8k"))

    chat_id = os.environ.get("-5147212177")

    

    lock_perms = ChatPermissions(can_send_messages=False)

    await bot.set_chat_permissions(chat_id=chat_id, permissions=lock_perms)

    await bot.send_message(chat_id=chat_id, text="🌙 Night mode activated! Group is now LOCKED. Good night ppl! ✨")



if __name__ == "__main__":

    asyncio.run(main())
