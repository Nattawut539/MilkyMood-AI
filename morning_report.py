from __future__ import annotations

import argparse
import os
import requests
from collections import Counter
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


def summarize_for_date(rows: list[dict], target_date: str) -> dict:
    today_rows = []

    for row in rows:
        if str(row.get("date", "")).strip() == target_date:
            today_rows.append(row)

    total_sales = 0
    menu_counter = Counter()

    for row in today_rows:
        menu = str(row.get("menu", "")).strip()

        quantity = int(float(row.get("quantity", 0) or 0))
        total = float(row.get("total", 0) or 0)

        total_sales += total
        menu_counter[menu] += quantity

    best_seller = "-"
    if menu_counter:
        best_seller = menu_counter.most_common(1)[0][0]

    return {
        "date": target_date,
        "order_count": len(today_rows),
        "total_sales": total_sales,
        "best_seller": best_seller,
    }


def build_report(summary: dict) -> str:
    return (
        "MilkyAI Morning Report 🥛\n"
        f"วันที่: {summary['date']}\n"
        f"จำนวนรายการขาย: {summary['order_count']} รายการ\n"
        f"ยอดขายรวม: {summary['total_sales']:.2f} บาท\n"
        f"เมนูขายดี: {summary['best_seller']}"
    )


def send_telegram_alert(message: str) -> None:
    load_dotenv()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise RuntimeError("ไม่พบ TELEGRAM_BOT_TOKEN ในไฟล์ .env")

    if not chat_id:
        raise RuntimeError("ไม่พบ TELEGRAM_CHAT_ID ในไฟล์ .env")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=15,
    )

    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="สรุปยอดขายจาก Google Sheet")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="วันที่ที่ต้องการสรุป รูปแบบ YYYY-MM-DD",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="แสดงรายงานอย่างเดียว ไม่ส่ง Telegram",
    )

    args = parser.parse_args()

    try:
        worksheet = get_worksheet()
        rows = worksheet.get_all_records()

        summary = summarize_for_date(rows, args.date)
        report = build_report(summary)

        print(report)

        if args.dry_run:
            print("\nDRY RUN: ยังไม่ส่ง Telegram")
        else:
            send_telegram_alert(report)
            print("\n✓ ส่งรายงานเข้า Telegram สำเร็จ")

    except Exception as error:
        print(f"✗ เกิดข้อผิดพลาด: {error}")


if __name__ == "__main__":
    main()