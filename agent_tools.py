# agent_tools.py
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sheet_manager import append_sale_to_sheet
from telegram_notifier import send_sale_notification

SALES_FILE = "sales_data.json"


def get_now_thailand() -> datetime:
    """คืนค่าเวลาปัจจุบันตามโซนเวลาไทย ถ้าใช้ไม่ได้จะ fallback เป็นเวลาปกติ"""
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Asia/Bangkok"))
    except Exception:
        return datetime.now()


def load_sales() -> list:
    """โหลดข้อมูลยอดขายจากไฟล์ JSON"""
    if Path(SALES_FILE).exists():
        try:
            with open(SALES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data

            return []
        except Exception:
            return []

    return []


def save_sales(sales: list) -> None:
    """บันทึกข้อมูลยอดขายลงไฟล์ JSON"""
    with open(SALES_FILE, "w", encoding="utf-8") as f:
        json.dump(sales, f, ensure_ascii=False, indent=2)


def validate_sale(menu: str, quantity: int, price: float) -> None:
    """Guardrails: raise ValueError ถ้าข้อมูลไม่ถูกต้อง"""
    if not menu or not str(menu).strip():
        raise ValueError("ชื่อเมนูห้ามว่าง")

    if quantity <= 0:
        raise ValueError("จำนวนต้องมากกว่า 0")

    if price <= 0:
        raise ValueError("ราคาต้องมากกว่า 0")


def normalize_number(value: Any, default: float = 0) -> float:
    """แปลงค่าตัวเลขให้ปลอดภัย ใช้ช่วยกันปัญหาค่า string จากหน้าเว็บ"""
    try:
        return float(value)
    except Exception:
        return default


def log_sale(menu: str, quantity: int, price: float) -> dict:
    """บันทึกยอดขายและเก็บลงไฟล์ JSON + Google Sheets + Telegram"""
    quantity = int(normalize_number(quantity, 0))
    price = normalize_number(price, 0)

    validate_sale(menu, quantity, price)

    total = quantity * price
    timestamp = get_now_thailand().isoformat()

    record = {
        "menu": menu,
        "quantity": quantity,
        "price": price,
        "total": total,
        "timestamp": timestamp,
    }

    json_saved = False
    sheet_success = False
    telegram_success = False
    errors = []

    # 1. บันทึกลงไฟล์ JSON ท้องถิ่น
    try:
        sales = load_sales()
        sales.append(record)
        save_sales(sales)
        json_saved = True
    except Exception as e:
        errors.append(f"JSON error: {e}")

    # 2. อัปโหลดไป Google Sheets
    try:
        sheet_success = append_sale_to_sheet(menu, quantity, price, total)
        if not sheet_success:
            errors.append("Google Sheets returned False")
    except Exception as e:
        errors.append(f"Google Sheets error: {e}")

    # 3. ส่ง Telegram notification
    try:
        telegram_success = send_sale_notification(menu, quantity, price, total)
        if not telegram_success:
            errors.append("Telegram returned False")
    except Exception as e:
        errors.append(f"Telegram error: {e}")

    return {
        "status": "success" if json_saved else "partial_success",
        "menu": menu,
        "quantity": quantity,
        "price": price,
        "total": total,
        "timestamp": record["timestamp"],
        "json_saved": json_saved,
        "sheet_uploaded": sheet_success,
        "telegram_sent": telegram_success,
        "errors": errors,
    }


def get_sales_summary() -> dict:
    """ดึงข้อมูลยอดขายวันนี้"""
    sales = load_sales()
    today = get_now_thailand().date().isoformat()

    today_sales = [
        s for s in sales
        if str(s.get("timestamp", "")).startswith(today)
    ]

    total_revenue = sum(normalize_number(s.get("total", 0), 0) for s in today_sales)
    total_items = sum(int(normalize_number(s.get("quantity", 0), 0)) for s in today_sales)

    return {
        "status": "success",
        "date": today,
        "total_revenue": total_revenue,
        "total_items": total_items,
        "transactions": len(today_sales),
        "items": today_sales,
    }


TOOLS = {
    "log_sale": log_sale,
    "get_sales_summary": get_sales_summary,
}
