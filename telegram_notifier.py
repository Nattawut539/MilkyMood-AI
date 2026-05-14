# telegram_notifier.py
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_sale_notification(menu: str, quantity: int, price: float, total: float) -> bool:
    """ส่ง Telegram notification เมื่อมีการบันทึกยอดขาย"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message = (
            f"📊 บันทึกยอดขาย [{timestamp}]\n"
            f"🍵 เมนู: {menu}\n"
            f"📦 จำนวน: {quantity} รายการ\n"
            f"💰 ราคา: {price} บาท/ชิ้น\n"
            f"💵 รวม: {total} บาท"
        )
        
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }
        
        response = requests.post(TELEGRAM_API_URL, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Telegram error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ข้อผิดพลาด Telegram: {e}")
        return False
