# agent_harness.py
import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from google import genai

from agent_tools import TOOLS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-3.1-flash-lite"

SYSTEM_INSTRUCTION = """
คุณคือ Demi ผู้ช่วย AI ของร้าน MilkyMood
หน้าที่: แปลงคำสั่งภาษาไทยเป็น JSON action

มี 2 action ให้เลือก:
1. log_sale - บันทึกยอดขาย (ตัวอย่าง: "ขายลาเต้ 5 แก้ว ราคา 65 บาท")
   ตอบ: {"action": "log_sale", "args": {"menu": "...", "quantity": N, "price": N}}

2. get_sales_summary - ดูยอดขายวันนี้ (ตัวอย่าง: "วันนี้ขายได้เท่าไหร่")
   ตอบ: {"action": "get_sales_summary", "args": {}}

ถ้าคำสั่งไม่ตรงกับ 2 อันนี้:
   ตอบ: {"action": "unknown", "args": {}}

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


def run_agent(user_input: str) -> str:
    write_trace("user_input", {"message": user_input})

    # Retry logic with exponential backoff for transient API errors
    max_retries = 3
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
            
            # Handle quota exhausted (429) - check first as it's permanent until reset
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                return "❌ ข้อจำกัด API ฟรี ถูกใช้หมด โปรดอัปเกรดเป็น Paid Plan หรือรอวันถัดไป"
            
            # Handle temporary unavailability (503)
            if "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    print(f"⏳ บริการชั่วคราว (...รอ {wait_time} วินาที)\n")
                    time.sleep(wait_time)
                else:
                    return "❌ บริการ API ชั่วคราว ไม่พร้อม โปรดลองใหม่ในภายหลัง"
            else:
                # Unknown error
                return f"❌ เกิดข้อผิดพลาด API: {error_str[:100]}"

    try:
        action_data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to strip markdown code block formatting
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove trailing ```
        cleaned = cleaned.strip()
        
        try:
            action_data = json.loads(cleaned)
        except json.JSONDecodeError:
            return "❌ AI ตอบกลับในรูปแบบที่ไม่ถูกต้อง"

    action = action_data.get("action")
    args = action_data.get("args", {})

    if action not in TOOLS:
        return f"⚠️ ไม่รู้จัก action: {action}"

    try:
        result = TOOLS[action](**args)
        write_trace("tool_result", {"action": action, "result": result})
        
        # แสดงผลตามประเภท action
        if action == "log_sale":
            sheet_status = "✅" if result.get("sheet_uploaded") else "⚠️"
            telegram_status = "✅" if result.get("telegram_sent") else "⚠️"
            return (
                f"✅ บันทึกสำเร็จ: {result['menu']} "
                f"x{result['quantity']} = {result['total']} บาท\n"
                f"{sheet_status} Google Sheets | {telegram_status} Telegram"
            )
        elif action == "get_sales_summary":
            summary = result
            if summary["transactions"] == 0:
                return f"📊 วันนี้ยังไม่มียอดขาย"
            else:
                return (
                    f"📊 วันนี้ {summary['date']}:\n"
                    f"   ยอดขาย: {summary['total_revenue']} บาท\n"
                    f"   จำนวนรายการ: {summary['total_items']} รายการ\n"
                    f"   จำนวนรายการอาหาร: {summary['transactions']} รายการ"
                )
        else:
            return f"✅ ดำเนินการสำเร็จ: {action}"
            
    except (ValueError, TypeError) as e:
        write_trace("tool_error", {"action": action, "error": str(e)})
        return f"❌ ข้อมูลไม่ถูกต้อง: {e}"


if __name__ == "__main__":
    print("Demi Agent พร้อมรับคำสั่ง (พิมพ์ 'exit' เพื่อออก)\n")
    while True:
        user_input = input("คุณ: ").strip()
        if user_input.lower() == "exit":
            break
        print(f"Demi: {run_agent(user_input)}\n")