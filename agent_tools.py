# agent_tools.py
import json
from datetime import datetime
from pathlib import Path

from sheet_manager import append_sale_to_sheet
from telegram_notifier import send_sale_notification

SALES_FILE = "sales_data.json"


def load_sales() -> list:
    """โหลดข้อมูลยอดขายจากไฟล์ JSON"""
    if Path(SALES_FILE).exists():
        with open(SALES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_sales(sales: list) -> None:
    """บันทึกข้อมูลยอดขายลงไฟล์ JSON"""
    with open(SALES_FILE, "w", encoding="utf-8") as f:
        json.dump(sales, f, ensure_ascii=False, indent=2)


def validate_sale(menu: str, quantity: int, price: float) -> None:
    """Guardrails: raise ValueError ถ้าข้อมูลไม่ถูกต้อง"""
    if not menu or not menu.strip():
        raise ValueError("ชื่อเมนูห้ามว่าง")
    if quantity <= 0:
        raise ValueError("จำนวนต้องมากกว่า 0")
    if price <= 0:
        raise ValueError("ราคาต้องมากกว่า 0")


def log_sale(menu: str, quantity: int, price: float) -> dict:
    """บันทึกยอดขายและเก็บลงไฟล์ JSON + Google Sheets + Telegram"""
    validate_sale(menu, quantity, price)
    total = quantity * price
    
    record = {
        "menu": menu,
        "quantity": quantity,
        "price": price,
        "total": total,
        "timestamp": datetime.now().isoformat(),
    }
    
    # 1. บันทึกลงไฟล์ JSON ท้องถิ่น
    sales = load_sales()
    sales.append(record)
    save_sales(sales)
    
    # 2. อัปโหลดไป Google Sheets
    sheet_success = append_sale_to_sheet(menu, quantity, price, total)
    
    # 3. ส่ง Telegram notification
    telegram_success = send_sale_notification(menu, quantity, price, total)
    
    return {
        "status": "success",
        "menu": menu,
        "quantity": quantity,
        "price": price,
        "total": total,
        "timestamp": record["timestamp"],
        "sheet_uploaded": sheet_success,
        "telegram_sent": telegram_success,
    }


def get_sales_summary() -> dict:
    """ดึงข้อมูลยอดขายวันนี้"""
    sales = load_sales()
    today = datetime.now().date().isoformat()
    
    today_sales = [s for s in sales if s["timestamp"].startswith(today)]
    
    total_revenue = sum(s["total"] for s in today_sales)
    total_items = sum(s["quantity"] for s in today_sales)
    
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