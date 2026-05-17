from __future__ import annotations

import argparse
import os
import traceback
from datetime import datetime
from pathlib import Path

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


BASE_DIR = Path(__file__).resolve().parent

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_worksheet():
    # โหลด .env จากโฟลเดอร์เดียวกับไฟล์นี้โดยตรง
    load_dotenv(BASE_DIR / ".env")

    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")

    # แปลงชื่อไฟล์ credentials ให้เป็น path ที่ชัดเจน
    credentials_path = Path(credentials_file)

    # ถ้าใน .env ใส่แค่ credentials.json ให้ไปหาในโฟลเดอร์โปรเจกต์
    if not credentials_path.is_absolute():
        credentials_path = BASE_DIR / credentials_path

    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_ID ในไฟล์ .env")

    if not credentials_path.exists():
        raise RuntimeError(f"ไม่พบไฟล์ credentials: {credentials_path}")

    credentials = Credentials.from_service_account_file(
        str(credentials_path),
        scopes=SCOPES,
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    return worksheet


def ensure_header(worksheet):
    header = [
        "date",
        "destination",
        "people",
        "budget",
        "trip_style",
        "trip_type",
        "days",
        "total_estimate",
    ]

    first_row = worksheet.row_values(1)

    if first_row != header:
        worksheet.update("A1:H1", [header])


def add_trip_interest(
    destination: str,
    people: int,
    budget: float,
    trip_style: str,
    trip_type: str = "ไม่ระบุ",
    days: int = 1,
    total_estimate: float | None = None,
):
    worksheet = get_worksheet()
    ensure_header(worksheet)

    today = datetime.now().strftime("%Y-%m-%d")
    estimate = total_estimate if total_estimate is not None else budget

    row = [
        today,
        destination,
        people,
        budget,
        trip_style,
        trip_type,
        days,
        estimate,
    ]

    worksheet.append_row(row, value_input_option="USER_ENTERED")

    return row


def main():
    parser = argparse.ArgumentParser(
        description="บันทึกแพลนท่องเที่ยวที่ผู้ใช้สนใจลง Google Sheet"
    )

    parser.add_argument("destination", help="จังหวัดหรือสถานที่ท่องเที่ยว")
    parser.add_argument("people", type=int, help="จำนวนคน")
    parser.add_argument("budget", type=float, help="งบประมาณรวม")
    parser.add_argument("trip_style", help="สไตล์ เช่น ประหยัด สมดุล สบาย")
    parser.add_argument("--trip-type", default="ไม่ระบุ", help="ภูเขา/ทะเล/ยังไม่แน่ใจ")
    parser.add_argument("--days", type=int, default=1, help="จำนวนวัน")

    args = parser.parse_args()

    try:
        row = add_trip_interest(
            destination=args.destination,
            people=args.people,
            budget=args.budget,
            trip_style=args.trip_style,
            trip_type=args.trip_type,
            days=args.days,
            total_estimate=args.budget,
        )

        print("✓ บันทึกแพลนท่องเที่ยวสำเร็จ")
        print(f"วันที่: {row[0]}")
        print(f"ปลายทาง: {row[1]}")
        print(f"จำนวนคน: {row[2]}")
        print(f"งบรวม: {row[3]} บาท")
        print(f"สไตล์: {row[4]}")
        print(f"แนวเที่ยว: {row[5]}")
        print(f"จำนวนวัน: {row[6]}")
        print(f"ยอดประมาณการ: {row[7]} บาท")

    except Exception as error:
        print(f"✗ เกิดข้อผิดพลาด: {error}")
        traceback.print_exc()


if __name__ == "__main__":
    main()