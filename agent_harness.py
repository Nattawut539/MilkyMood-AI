# agent_harness.py
from __future__ import annotations

import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from google import genai

from agent_tools import TOOLS

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = os.getenv("GOOGLE_MODEL_NAME", "models/gemini-2.5-flash-lite")

SYSTEM_INSTRUCTION = """
คุณคือ Matey ผู้ช่วย AI ของ TripMate Thailand AI
หน้าที่: แปลงคำสั่งภาษาไทยเป็น JSON action สำหรับระบบวางแผนท่องเที่ยว

มี 2 action ให้เลือก:

1. log_trip_interest
ใช้เมื่อผู้ใช้ต้องการบันทึกแพลนหรือสนใจทริป เช่น
"บันทึกทริปชลบุรี 2 คน งบ 5000 บาท ทะเล 2 วัน แบบประหยัด"
ตอบรูปแบบ:
{
  "action": "log_trip_interest",
  "args": {
    "destination": "ชลบุรี",
    "people": 2,
    "budget": 5000,
    "trip_style": "ประหยัด",
    "trip_type": "ทะเล",
    "days": 2,
    "total_estimate": 5000
  }
}

2. get_trip_summary
ใช้เมื่อผู้ใช้ถามสรุปแพลนวันนี้ เช่น "วันนี้มีคนสนใจทริปอะไรบ้าง" หรือ "สรุปแพลนวันนี้"
ตอบรูปแบบ:
{"action": "get_trip_summary", "args": {}}

ถ้าคำสั่งไม่ตรงกับ 2 อันนี้:
{"action": "unknown", "args": {}}

⚠️ ตอบเป็น JSON เท่านั้น อย่าใส่ markdown code block
"""

TRACE_FILE = "agent_trace.log"


def write_trace(event: str, data: dict) -> None:
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **data,
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def clean_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())


def run_agent(user_input: str) -> str:
    write_trace("user_input", {"message": user_input})

    max_retries = 3
    raw = ""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=f"{SYSTEM_INSTRUCTION}\n\nคำสั่ง: {user_input}",
            )
            raw = response.text.strip()
            write_trace("llm_response", {"raw": raw})
            break
        except Exception as e:
            error_str = str(e)
            write_trace("api_error", {"attempt": attempt + 1, "error": error_str})
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return "❌ ข้อจำกัด API ฟรีถูกใช้หมด โปรดลองใหม่วันถัดไปหรือเปลี่ยนโมเดล"
            if "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ บริการชั่วคราว รอ {wait_time} วินาที")
                    time.sleep(wait_time)
                else:
                    return "❌ บริการ API ชั่วคราวไม่พร้อม โปรดลองใหม่ภายหลัง"
            else:
                return f"❌ เกิดข้อผิดพลาด API: {error_str[:120]}"

    try:
        action_data = clean_json(raw)
    except Exception:
        return "❌ AI ตอบกลับในรูปแบบ JSON ไม่ถูกต้อง"

    action = action_data.get("action")
    args = action_data.get("args", {})

    if action not in TOOLS:
        return f"⚠️ ไม่รู้จัก action: {action}"

    try:
        result = TOOLS[action](**args)
        write_trace("tool_result", {"action": action, "result": result})

        if action == "log_trip_interest":
            sheet_status = "✅" if result.get("sheet_uploaded") else "⚠️"
            telegram_status = "✅" if result.get("telegram_sent") else "⚠️"
            return (
                f"✅ บันทึกแพลนสำเร็จ: {result['destination']} "
                f"{result['people']} คน งบ {result['budget']} บาท\n"
                f"แนวเที่ยว: {result['trip_type']} | สไตล์: {result['trip_style']} | {result['days']} วัน\n"
                f"{sheet_status} Google Sheets | {telegram_status} Telegram"
            )

        if action == "get_trip_summary":
            if result["request_count"] == 0:
                return "📊 วันนี้ยังไม่มีแพลนที่ถูกบันทึก"
            return (
                f"📊 สรุปแพลนวันที่ {result['date']}\n"
                f"จำนวนแพลน: {result['request_count']} รายการ\n"
                f"จำนวนผู้เดินทางรวม: {result['total_people']} คน\n"
                f"งบรวมโดยประมาณ: {result['total_budget']} บาท\n"
                f"งบเฉลี่ย: {result['avg_budget']:.2f} บาท\n"
                f"ปลายทางยอดนิยม: {result['top_destination']}\n"
                f"แนวเที่ยวยอดนิยม: {result['top_type']}"
            )

        return f"✅ ดำเนินการสำเร็จ: {action}"
    except (ValueError, TypeError) as e:
        write_trace("tool_error", {"action": action, "error": str(e)})
        return f"❌ ข้อมูลไม่ถูกต้อง: {e}"


if __name__ == "__main__":
    print("Matey Agent พร้อมรับคำสั่ง (พิมพ์ 'exit' เพื่อออก)\n")
    while True:
        user_input = input("คุณ: ").strip()
        if user_input.lower() == "exit":
            break
        print(f"Matey: {run_agent(user_input)}\n")
