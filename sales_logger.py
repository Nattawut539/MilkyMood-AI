from __future__ import annotations

import argparse
import os
import traceback
from datetime import datetime

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_worksheet():
    load_dotenv()

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
    header = ["date", "menu", "quantity", "price", "total"]
    first_row = worksheet.row_values(1)

    if first_row != header:
        worksheet.update("A1:E1", [header])


def add_sale(menu: str, quantity: int, price: float):
    worksheet = get_worksheet()
    ensure_header(worksheet)

    today = datetime.now().strftime("%Y-%m-%d")
    total = quantity * price

    row = [
        today,
        menu,
        quantity,
        price,
        total,
    ]

    worksheet.append_row(row, value_input_option="USER_ENTERED")

    return row


def main():
    parser = argparse.ArgumentParser(description="บันทึกยอดขายลง Google Sheet")
    parser.add_argument("menu", help="ชื่อเมนู")
    parser.add_argument("quantity", type=int, help="จำนวนที่ขาย")
    parser.add_argument("price", type=float, help="ราคาต่อแก้ว")

    args = parser.parse_args()

    try:
        row = add_sale(args.menu, args.quantity, args.price)

        print("✓ บันทึกยอดขายสำเร็จ")
        print(f"วันที่: {row[0]}")
        print(f"เมนู: {row[1]}")
        print(f"จำนวน: {row[2]}")
        print(f"ราคา: {row[3]}")
        print(f"ยอดรวม: {row[4]} บาท")

    except Exception as error:
        print(f"✗ เกิดข้อผิดพลาด: {error}")
        traceback.print_exc()


if __name__ == "__main__":
    main()