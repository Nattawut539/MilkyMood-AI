# sheet_manager.py
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# Google Sheets Credentials
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")


def get_sheets_client():
    """เชื่อมต่อ Google Sheets"""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client


def append_sale_to_sheet(menu: str, quantity: int, price: float, total: float) -> bool:
    """เพิ่มบันทึกยอดขายลง Google Sheets"""
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(SHEETS_ID)
        worksheet = sheet.sheet1  # แผ่นแรก
        
        # เตรียมข้อมูล
        timestamp = datetime.now()
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
        worksheet.append_row(row_data)
        return True
        
    except Exception as e:
        print(f"❌ ข้อผิดพลาด Google Sheets: {e}")
        return False
