# telegram_notifier.py
import html
import os
from datetime import datetime

import requests
from dotenv import load_dotenv


def get_now_thailand() -> datetime:
    """คืนค่าเวลาปัจจุบันตามโซนเวลาไทย ถ้าใช้ไม่ได้จะ fallback เป็นเวลาปกติ"""
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Asia/Bangkok"))
    except Exception:
        return datetime.now()


def send_sale_notification(menu: str, quantity: int, price: float, total: float) -> bool:
    """ส่ง Telegram notification เมื่อมีการบันทึกยอดขาย"""
    try:
        # โหลดตัวแปรสภาพแวดล้อม ที่เวลาของการเรียกฟังก์ชัน ไม่ใช่เวลานำเข้า
        load_dotenv()
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            print("❌ ไม่พบ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID")
            return False

        timestamp = get_now_thailand().strftime("%H:%M:%S")
        safe_menu = html.escape(str(menu))

        message = (
            "🥛 <b>MilkyMood AI - ยอดขาย</b>\n\n"
            f"📊 <b>บันทึกยอดขาย</b> [{timestamp}]\n"
            f"🍵 เมนู: {safe_menu}\n"
            f"📦 จำนวน: {quantity} รายการ\n"
            f"💰 ราคา: {price} บาท/ชิ้น\n"
            f"💵 รวม: {total} บาท\n\n"
            "✅ บันทึกลงระบบแล้ว"
        )

        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        response = requests.post(telegram_api_url, json=payload, timeout=15)

        if response.status_code == 200:
            return True

        print(f"❌ Telegram error: {response.text}")
        return False

    except Exception as e:
        print(f"❌ ข้อผิดพลาด Telegram: {e}")
        return False
