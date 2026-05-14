# agent_tools.py
"""
Agent Tools Module - ต่อกับ Google Sheets และ Telegram Bot

tools ที่ใช้ได้:
- log_sale: บันทึกยอดขายลง Google Sheets
- order: สั่งเมนูแล้วส่งแจ้งเตือน Telegram
- get_summary: ดึงสรุปรายงานจาก Google Sheets
- send_notification: ส่งแจ้งเตือน Telegram

ใช้ Google Sheets API + Telegram Bot API จริง
"""

import os
import asyncio
from datetime import datetime
from collections import Counter

import gspread
import requests
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from telegram import Bot


load_dotenv()

# ===== Setup Google Sheets =====

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_worksheet():
    """เชื่อมต่อ Google Sheets"""
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")

    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_ID ในไฟล์ .env")

    if not os.path.exists(credentials_file):
        raise RuntimeError(f"ไม่พบไฟล์ credentials: {credentials_file}")

    credentials = Credentials.from_service_account_file(
        credentials_file,
        scopes=SCOPES,
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    return worksheet


def ensure_header(worksheet):
    """ตรวจสอบและเพิ่ม header ถ้ายังไม่มี"""
    header = ["date", "menu", "quantity", "price", "total", "status"]
    first_row = worksheet.row_values(1)

    if first_row != header:
        worksheet.update(values=[header], range_name="A1:F1")


# ===== Validation Functions =====

def validate_sale(menu: str, quantity: int, price: float) -> None:
    """Guardrails: raise ValueError ถ้าข้อมูลไม่ถูกต้อง"""
    if not menu or not menu.strip():
        raise ValueError("ชื่อเมนูห้ามว่าง")
    if quantity <= 0:
        raise ValueError("จำนวนต้องมากกว่า 0")
    if price <= 0:
        raise ValueError("ราคาต้องมากกว่า 0")


def validate_order(menu: str, quantity: int, price: float, notes: str = None) -> None:
    """Guardrails สำหรับการสั่งเมนู"""
    validate_sale(menu, quantity, price)
    if notes and len(notes) > 500:
        raise ValueError("หมายเหตุไม่ควรเกิน 500 ตัวอักษร")


# ===== Tool Functions =====

def log_sale(menu: str, quantity: int, price: float) -> dict:
    """บันทึกยอดขายลง Google Sheets"""
    validate_sale(menu, quantity, price)
    
    try:
        worksheet = get_worksheet()
        ensure_header(worksheet)
        
        total = quantity * price
        date = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().isoformat()
        
        # เพิ่มแถวใหม่ลง Google Sheets
        row = [date, menu, quantity, price, total, "completed"]
        worksheet.append_row(row)
        
        return {
            "status": "success",
            "menu": menu,
            "quantity": quantity,
            "price": price,
            "total": total,
            "date": date,
            "timestamp": timestamp,
        }
    except Exception as e:
        raise RuntimeError(f"เชื่อมต่อ Google Sheets ไม่ได้: {e}")


def order(menu: str, quantity: int, price: float, notes: str = None) -> dict:
    """สั่งเมนูและแจ้งเตือน Telegram"""
    validate_order(menu, quantity, price, notes)
    
    timestamp = datetime.now().isoformat()
    order_id = f"ORD-{timestamp.replace(':', '').replace('-', '')[:14]}"
    total = quantity * price
    
    # บันทึกลง Google Sheets
    try:
        worksheet = get_worksheet()
        ensure_header(worksheet)
        
        date = datetime.now().strftime("%Y-%m-%d")
        row = [date, menu, quantity, price, total, "pending"]
        worksheet.append_row(row)
    except Exception as e:
        raise RuntimeError(f"บันทึกลง Google Sheets ไม่ได้: {e}")
    
    # ส่ง Telegram notification
    try:
        message = f"🛒 Order #{order_id}\n{menu} x{quantity}\nราคา: {total} บาท"
        if notes:
            message += f"\n📝 {notes}"
        
        asyncio.run(send_telegram_notification(message))
    except Exception as e:
        raise RuntimeError(f"ส่ง Telegram ไม่ได้: {e}")
    
    return {
        "status": "success",
        "order_id": order_id,
        "menu": menu,
        "quantity": quantity,
        "price": price,
        "total": total,
        "notes": notes,
        "timestamp": timestamp,
    }


def get_summary(start_date: str = None, end_date: str = None) -> dict:
    """ดึงสรุปรายงานจาก Google Sheets"""
    try:
        worksheet = get_worksheet()
        ensure_header(worksheet)
        
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = start_date
        
        # ดึงข้อมูลทั้งหมดจาก Google Sheets
        rows = worksheet.get_all_records()
        
        # Filter ตามช่วงวันที่
        filtered_rows = [
            r for r in rows
            if start_date <= r.get("date", "") <= end_date
        ]
        
        total_sales = sum(float(r.get("total", 0)) for r in filtered_rows)
        total_orders = len(filtered_rows)
        
        # นับเมนูต่อชนิด
        menu_counter = Counter(r.get("menu", "") for r in filtered_rows)
        menus = {menu: {"quantity": count, "total": 0} for menu, count in menu_counter.items()}
        
        # คำนวณยอดขายต่อเมนู
        for row in filtered_rows:
            menu = row.get("menu", "")
            if menu in menus:
                menus[menu]["total"] += float(row.get("total", 0))
        
        average_order = total_sales / total_orders if total_orders > 0 else 0
        top_menu = menu_counter.most_common(1)[0][0] if menu_counter else "N/A"
        
        return {
            "status": "success",
            "period": f"{start_date} - {end_date}",
            "total_sales": total_sales,
            "total_orders": total_orders,
            "menus": menus,
            "top_menu": top_menu,
            "average_order": round(average_order, 2)
        }
    except Exception as e:
        raise RuntimeError(f"ดึงข้อมูลจาก Google Sheets ไม่ได้: {e}")


async def send_telegram_notification(message: str) -> dict:
    """ส่งแจ้งเตือน Telegram (async)"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        raise RuntimeError("ไม่พบ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID ในไฟล์ .env")
    
    bot = Bot(token=token)
    msg = await bot.send_message(chat_id=chat_id, text=message)
    
    return {
        "status": "success",
        "channel": "telegram",
        "message": message,
        "sent_at": datetime.now().isoformat(),
        "message_id": msg.message_id
    }


def send_notification(message: str, channel: str = "telegram") -> dict:
    """ส่งแจ้งเตือน (sync wrapper)"""
    if not message or not message.strip():
        raise ValueError("ข้อความแจ้งเตือนห้ามว่าง")
    
    if channel == "telegram":
        try:
            return asyncio.run(send_telegram_notification(message))
        except Exception as e:
            raise RuntimeError(f"ส่ง Telegram ไม่ได้: {e}")
    else:
        raise ValueError(f"ไม่รู้จัก channel: {channel}")


# ===== Tools Registry =====

TOOLS = {
    "log_sale": log_sale,
    "order": order,
    "get_summary": get_summary,
    "send_notification": send_notification,
}


def get_tool(tool_name: str):
    """ดึง tool ด้วยชื่อ"""
    return TOOLS.get(tool_name)


def list_tools():
    """แสดงรายชื่อ tools ทั้งหมด"""
    return list(TOOLS.keys())