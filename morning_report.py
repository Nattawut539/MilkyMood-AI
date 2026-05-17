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


def safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).replace(",", "").strip()))
    except (ValueError, TypeError):
        return default


def summarize_for_date(rows: list[dict], target_date: str) -> dict:
    today_rows = []

    for row in rows:
        if str(row.get("date", "")).strip() == target_date:
            today_rows.append(row)

    destination_counter = Counter()
    trip_type_counter = Counter()
    style_counter = Counter()

    total_budget = 0
    total_people = 0
    total_days = 0

    for row in today_rows:
        destination = str(row.get("destination", "")).strip()
        trip_type = str(row.get("trip_type", "")).strip()
        trip_style = str(row.get("trip_style", "")).strip()

        people = safe_int(row.get("people", 0))
        days = safe_int(row.get("days", 0))
        budget = safe_int(row.get("budget", 0))

        if destination:
            destination_counter[destination] += 1

        if trip_type:
            trip_type_counter[trip_type] += 1

        if trip_style:
            style_counter[trip_style] += 1

        total_people += people
        total_days += days
        total_budget += budget

    top_destination = "-"
    if destination_counter:
        top_destination = destination_counter.most_common(1)[0][0]

    top_trip_type = "-"
    if trip_type_counter:
        top_trip_type = trip_type_counter.most_common(1)[0][0]

    top_style = "-"
    if style_counter:
        top_style = style_counter.most_common(1)[0][0]

    avg_budget = 0
    if today_rows:
        avg_budget = total_budget / len(today_rows)

    return {
        "date": target_date,
        "plan_count": len(today_rows),
        "total_budget": total_budget,
        "avg_budget": avg_budget,
        "total_people": total_people,
        "total_days": total_days,
        "top_destination": top_destination,
        "top_trip_type": top_trip_type,
        "top_style": top_style,
    }


def build_report(summary: dict) -> str:
    return (
        "🧭 <b>TripMate Thailand AI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>วันที่:</b> {summary['date']}\n\n"
        "📌 <b>สรุปแพลนวันนี้</b>\n"
        f"• จำนวนแพลนที่บันทึก: <b>{summary['plan_count']}</b> แพลน\n"
        f"• จำนวนผู้เดินทางรวม: <b>{summary['total_people']}</b> คน\n\n"
        "💰 <b>สรุปงบประมาณ</b>\n"
        f"• งบรวมโดยประมาณ: <b>{summary['total_budget']:,.2f}</b> บาท\n"
        f"• งบเฉลี่ยต่อแพลน: <b>{summary['avg_budget']:,.2f}</b> บาท\n\n"
        "🏆 <b>ข้อมูลยอดนิยม</b>\n"
        f"• จังหวัดที่ถูกสนใจมากที่สุด: <b>{summary['top_destination']}</b>\n"
        f"• แนวเที่ยวที่นิยม: <b>{summary['top_trip_type']}</b>\n"
        f"• สไตล์งบที่นิยม: <b>{summary['top_style']}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ รายงานนี้สรุปจากข้อมูลใน Google Sheet"
    )

def send_telegram_alert(message: str) -> None:
    load_dotenv()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise RuntimeError("ไม่พบ TELEGRAM_BOT_TOKEN ในตัวแปรสภาพแวดล้อม")

    if not chat_id:
        raise RuntimeError("ไม่พบ TELEGRAM_CHAT_ID ในตัวแปรสภาพแวดล้อม")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                },
            timeout=15,
            )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"ล้มเหลวในการส่ง Telegram: {e}")


def main():
    parser = argparse.ArgumentParser(description="สรุปแพลนท่องเที่ยวจาก Google Sheet")
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