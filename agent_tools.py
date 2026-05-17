from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from sales_logger import add_trip_interest
    from morning_report import summarize_for_date, get_worksheet
except Exception:
    add_trip_interest = None
    summarize_for_date = None
    get_worksheet = None

try:
    from telegram_notifier import send_telegram_message
except Exception:
    send_telegram_message = None


def log_trip_interest(
    destination: str,
    people: int,
    budget: float,
    trip_style: str,
    trip_type: str = "ไม่ระบุ",
    days: int = 1,
    total_estimate: float | None = None,
) -> dict[str, Any]:
    if add_trip_interest is None:
        return {
            "destination": destination,
            "people": people,
            "budget": budget,
            "trip_style": trip_style,
            "trip_type": trip_type,
            "days": days,
            "total_estimate": total_estimate or budget,
            "sheet_uploaded": False,
            "telegram_sent": False,
            "telegram_error": "ไม่พบฟังก์ชัน add_trip_interest",
        }

    row = add_trip_interest(
        destination=destination,
        people=people,
        budget=budget,
        trip_style=trip_style,
        trip_type=trip_type,
        days=days,
        total_estimate=total_estimate or budget,
    )

    telegram_sent = False
    telegram_error = ""

    if send_telegram_message:
        try:
            send_telegram_message(
                "🧭 <b>TripMate มีแพลนใหม่</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📍 <b>ปลายทาง:</b> {destination}\n"
                f"👥 <b>จำนวนคน:</b> {people} คน\n"
                f"💰 <b>งบ:</b> {budget:,.0f} บาท\n"
                f"🏷️ <b>แนวเที่ยว:</b> {trip_type}\n"
                f"🎒 <b>สไตล์:</b> {trip_style}\n"
                f"📅 <b>จำนวนวัน:</b> {days} วัน\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "✅ บันทึกลง Google Sheet แล้ว"
            )
            telegram_sent = True

        except Exception as e:
            telegram_error = str(e)
            print(f"Telegram error: {telegram_error}")
            telegram_sent = False
    else:
        telegram_error = "ไม่พบฟังก์ชัน send_telegram_message จาก telegram_notifier.py"
        print(f"Telegram error: {telegram_error}")

    return {
        "date": row[0],
        "destination": row[1],
        "people": row[2],
        "budget": row[3],
        "trip_style": row[4],
        "trip_type": row[5],
        "days": row[6],
        "total_estimate": row[7],
        "sheet_uploaded": True,
        "telegram_sent": telegram_sent,
        "telegram_error": telegram_error,
    }


def get_trip_summary(date: str | None = None) -> dict[str, Any]:
    if get_worksheet is None or summarize_for_date is None:
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "request_count": 0,
            "total_people": 0,
            "total_budget": 0,
            "avg_budget": 0,
            "top_destination": "-",
            "top_type": "-",
        }
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    worksheet = get_worksheet()
    rows = worksheet.get_all_records()
    return summarize_for_date(rows, target_date)


TOOLS = {
    "log_trip_interest": log_trip_interest,
    "get_trip_summary": get_trip_summary,
}
