from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

# ใช้สำหรับ local development
# บน Hugging Face จะอ่านจาก Secrets ผ่าน os.getenv ได้อยู่แล้ว
load_dotenv(BASE_DIR / ".env")


def send_telegram_message(message: str) -> None:
    """
    ส่งข้อความเข้า Telegram ผ่าน Bot API

    ต้องมีค่าใน .env หรือ Hugging Face Secrets:
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_CHAT_ID
    """

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise RuntimeError("ไม่พบ TELEGRAM_BOT_TOKEN ใน .env หรือ Hugging Face Secrets")

    if not chat_id:
        raise RuntimeError("ไม่พบ TELEGRAM_CHAT_ID ใน .env หรือ Hugging Face Secrets")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(
            url,
            data=payload,
            timeout=15,
        )

        if not response.ok:
            raise RuntimeError(
                f"Telegram ส่งไม่สำเร็จ: {response.status_code} {response.text}"
            )

    except requests.exceptions.Timeout:
        raise RuntimeError("Telegram ส่งไม่สำเร็จ: request timeout")

    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"Telegram ส่งไม่สำเร็จ: {error}")


def test_send() -> None:
    """
    ใช้ทดสอบไฟล์นี้โดยตรง:
    python telegram_notifier.py
    """

    send_telegram_message(
        "🧭 <b>TripMate Thailand AI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ ทดสอบส่งข้อความ Telegram สำเร็จ"
    )
    print("✓ ส่ง Telegram สำเร็จ")


if __name__ == "__main__":
    test_send()