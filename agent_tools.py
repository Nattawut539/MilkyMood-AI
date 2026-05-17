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
    if send_telegram_message:
        try:
            send_telegram_message(
                "🧭 TripMate มีแพลนใหม่\n"
                f"ปลายทาง: {destination}\n"
                f"จำนวนคน: {people}\n"
                f"งบ: {budget} บาท\n"
                f"แนวเที่ยว: {trip_type}\n"
                f"สไตล์: {trip_style}\n"
                f"จำนวนวัน: {days}"
            )
            telegram_sent = True
        except Exception:
            telegram_sent = False

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
