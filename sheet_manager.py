# sheet_manager.py
import json
import os
from datetime import datetime
from pathlib import Path

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Google Sheets Credentials
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = ["date", "menu", "quantity", "price", "total", "status"]


def get_now_thailand() -> datetime:
    """คืนค่าเวลาปัจจุบันตามโซนเวลาไทย ถ้าใช้ไม่ได้จะ fallback เป็นเวลาปกติ"""
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Asia/Bangkok"))
    except Exception:
        return datetime.now()


def get_service_account_info_from_env() -> dict | None:
    """
    อ่าน service account จาก Secret ชื่อ GOOGLE_SERVICE_ACCOUNT_JSON

    เหมาะกับ Hugging Face Spaces เพราะไม่ต้องอัปโหลดไฟล์ credentials.json เข้า repo
    """
    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not service_json:
        return None

    service_json = service_json.strip()

    try:
        return json.loads(service_json)
    except json.JSONDecodeError:
        # รองรับกรณี private_key ถูก escape ซ้ำในบาง environment
        fixed_json = service_json.replace("\\n", "\n")
        return json.loads(fixed_json)


def get_service_account_file_path() -> str:
    """
    หาไฟล์ service account แบบเดิม
    ลำดับที่รองรับ:
    1. GOOGLE_SERVICE_ACCOUNT_FILE
    2. credentials.json
    3. service-account.json
    """
    file_from_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    candidates = [
        file_from_env,
        "credentials.json",
        "service-account.json",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    raise FileNotFoundError(
        "ไม่พบไฟล์ credentials: กรุณาตั้ง GOOGLE_SERVICE_ACCOUNT_JSON "
        "หรือ GOOGLE_SERVICE_ACCOUNT_FILE หรือวาง credentials.json/service-account.json"
    )


def get_sheets_client():
    """เชื่อมต่อ Google Sheets"""
    load_dotenv()

    service_info = get_service_account_info_from_env()

    if service_info:
        creds = Credentials.from_service_account_info(service_info, scopes=SCOPES)
    else:
        service_account_file = get_service_account_file_path()
        creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)

    client = gspread.authorize(creds)
    return client


def get_sheet_id() -> str:
    """อ่าน Google Sheet ID จาก environment"""
    load_dotenv()

    sheet_id = os.getenv("GOOGLE_SHEETS_ID")

    if not sheet_id:
        raise ValueError("ไม่พบ GOOGLE_SHEETS_ID ใน Environment Variables หรือ Hugging Face Secrets")

    return sheet_id.strip()


def ensure_headers(worksheet) -> None:
    """เพิ่มหัวตารางถ้าชีตยังว่าง"""
    try:
        first_row = worksheet.row_values(1)

        if not first_row:
            worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
            return

        normalized = [str(x).strip().lower() for x in first_row[: len(HEADERS)]]
        expected = [x.lower() for x in HEADERS]

        if normalized != expected:
            # ไม่ลบข้อมูลเดิม เพียงอัปเดตหัวแถวแรกให้ตรงกับระบบ
            worksheet.update("A1:F1", [HEADERS])
    except Exception as e:
        print(f"⚠️ ตรวจสอบหัวตารางไม่สำเร็จ: {e}")


def append_sale_to_sheet(menu: str, quantity: int, price: float, total: float) -> bool:
    """เพิ่มบันทึกยอดขายลง Google Sheets"""
    try:
        client = get_sheets_client()
        sheet_id = get_sheet_id()

        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.sheet1  # แผ่นแรก

        ensure_headers(worksheet)

        # เตรียมข้อมูล
        timestamp = get_now_thailand()
        date_str = timestamp.strftime("%Y-%m-%d")

        row_data = [
            date_str,           # A: date
            menu,               # B: menu
            quantity,           # C: quantity
            price,              # D: price
            total,              # E: total
            "pending",          # F: status
        ]

        # เพิ่มแถวใหม่
        worksheet.append_row(row_data, value_input_option="USER_ENTERED")
        return True

    except Exception as e:
        print(f"❌ ข้อผิดพลาด Google Sheets: {e}")
        return False
