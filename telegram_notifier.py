from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def send_telegram_message(message: str) -> None:
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

    last_error = None

    # ลองส่ง 3 รอบ เผื่อ Hugging Face หรือ Telegram ช้า
    for attempt in range(1, 4):
        try:
            response = requests.post(
                url,
                data=payload,
                timeout=45,
            )

            if response.ok:
                return

            raise RuntimeError(
                f"Telegram ส่งไม่สำเร็จ: {response.status_code} {response.text}"
            )

        except requests.exceptions.Timeout as error:
            last_error = f"request timeout รอบที่ {attempt}"
            time.sleep(2)

        except requests.exceptions.RequestException as error:
            last_error = str(error)
            time.sleep(2)

    raise RuntimeError(f"Telegram ส่งไม่สำเร็จ: {last_error}")


def test_send() -> None:
    send_telegram_message(
        "🧭 <b>TripMate Thailand AI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ ทดสอบส่งข้อความ Telegram สำเร็จ"
    )
    print("✓ ส่ง Telegram สำเร็จ")


if __name__ == "__main__":
    test_send()