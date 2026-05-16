#!/usr/bin/env python3
"""
ส่งแจ้งเตือน Telegram จริง
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import requests

def send_real_notification(title: str, message: str) -> bool:
    """ส่งแจ้งเตือน Telegram จริง"""
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ ไม่พบ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID")
        print("   กรุณาตั้งค่า environment variables ใน .env file")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    full_message = f"{title}\n\n{message}"
    
    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": full_message,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        
        if response.status_code == 200:
            print(f"✅ ส่งแจ้งเตือนสำเร็จ!")
            print(f"📨 ข้อความ:\n{full_message}")
            return True
        else:
            print(f"❌ ล้มเหลว: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ข้อผิดพลาด: {e}")
        return False


def main():
    print("🔔 ส่งแจ้งเตือน Telegram\n")
    
    # สร้างข้อความแจ้งเตือน
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    message = (
        f"📊 <b>บันทึกยอดขาย [{timestamp}]</b>\n\n"
        f"🍵 <b>เมนู:</b> Iced Latte\n"
        f"📦 <b>จำนวน:</b> 5 แก้ว\n"
        f"💰 <b>ราคา:</b> 65 บาท/แก้ว\n"
        f"💵 <b>รวม:</b> 325 บาท\n\n"
        f"✅ บันทึกลงระบบแล้ว"
    )
    
    title = "🥛 MilkyMood AI - ยอดขาย"
    
    success = send_real_notification(title, message)
    
    if not success:
        print("\n💡 วิธีแก้:")
        print("   1. สร้างไฟล์ .env ที่โปรเจกต์")
        print("   2. เพิ่มบรรทัดต่อไปนี้:")
        print("      TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("      TELEGRAM_CHAT_ID=your_chat_id_here")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
