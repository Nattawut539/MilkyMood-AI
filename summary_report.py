from __future__ import annotations

import argparse
import os
import traceback
from datetime import datetime
from collections import Counter

import gspread
import requests
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


def get_summary_all(rows: list[dict]) -> dict:
    """สรุปยอดขายทั้งหมด"""
    total_sales = 0
    menu_counter = Counter()
    date_counter = Counter()
    all_menus = {}

    for row in rows:
        menu = str(row.get("menu", "")).strip()
        quantity = int(float(row.get("quantity", 0) or 0))
        total = float(row.get("total", 0) or 0)
        date = str(row.get("date", "")).strip()

        if menu and total > 0:
            total_sales += total
            menu_counter[menu] += quantity
            date_counter[date] += 1
            
            if menu not in all_menus:
                all_menus[menu] = {"quantity": 0, "sales": 0}
            all_menus[menu]["quantity"] += quantity
            all_menus[menu]["sales"] += total

    best_seller = "-"
    if menu_counter:
        best_seller = menu_counter.most_common(1)[0][0]

    return {
        "total_sales": total_sales,
        "order_count": sum(date_counter.values()),
        "unique_dates": len(date_counter),
        "best_seller": best_seller,
        "all_menus": all_menus,
    }


def build_report(summary: dict) -> str:
    """สร้างรายงานสรุปทั้งหมด"""
    report = (
        "📊 รายงานยอดขายทั้งหมด\n"
        f"{'='*40}\n"
        f"ยอดขายรวมทั้งหมด: {summary['total_sales']:.2f} บาท\n"
        f"จำนวนรายการขายทั้งหมด: {summary['order_count']} รายการ\n"
        f"จำนวนวันขาย: {summary['unique_dates']} วัน\n"
        f"เมนูขายดี: {summary['best_seller']}\n"
        f"{'='*40}\n\n"
        "📋 รายละเอียดเมนู:\n"
    )

    # เรียงลำดับเมนูตามยอดขาย
    sorted_menus = sorted(
        summary['all_menus'].items(),
        key=lambda x: x[1]['sales'],
        reverse=True
    )

    for idx, (menu, stats) in enumerate(sorted_menus, 1):
        report += (
            f"{idx}. {menu}\n"
            f"   จำนวน: {stats['quantity']} แก้ว\n"
            f"   ยอดขาย: {stats['sales']:.2f} บาท\n"
        )

    return report


def send_telegram_alert(message: str) -> None:
    """ส่งรายงานไปยัง Telegram"""
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
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"ล้มเหลวในการส่ง Telegram: {e}")


def main():
    parser = argparse.ArgumentParser(description="สรุปยอดขายทั้งหมดพร้อมส่ง Telegram")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="แสดงรายงานอย่างเดียว ไม่ส่ง Telegram",
    )

    args = parser.parse_args()

    try:
        worksheet = get_worksheet()
        rows = worksheet.get_all_records()

        if not rows:
            print("✗ ยังไม่มีข้อมูลในแผ่นงาน")
            return

        summary = get_summary_all(rows)
        report = build_report(summary)

        print(report)

        if args.dry_run:
            print("DRY RUN: ยังไม่ส่ง Telegram")
        else:
            print("\n📤 กำลังส่งรายงานไปยัง Telegram...")
            send_telegram_alert(report)
            print("✓ ส่งรายงานเข้า Telegram สำเร็จ")

    except Exception as error:
        print(f"✗ เกิดข้อผิดพลาด: {error}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
