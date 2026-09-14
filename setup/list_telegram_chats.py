"""
Run this ONCE to list your Telegram chats/channels and find the numeric ID of the
dedicated channel you created for TikTok videos (e.g. "TikTok Queue").

Reuses the same TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_SESSION as the
YouTube Auto Publisher project (same Telegram account) -- copy those three values
into this project's .env first.
"""

import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
session = os.environ["TELEGRAM_SESSION"]

with TelegramClient(StringSession(session), api_id, api_hash) as client:
    print("\nYour chats (name -> id):\n")
    for dialog in client.iter_dialogs():
        print(f"{dialog.name!r:40s} -> {dialog.id}")
    print("\nCopy the id of your TikTok channel into TELEGRAM_SOURCE_CHAT in .env / GitHub Secrets.")
