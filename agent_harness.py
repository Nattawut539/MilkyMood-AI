# agent_harness.py
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from google import genai

from agent_tools import TOOLS

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """คุณคือ Demi ผู้ช่วย AI ของร้าน MilkLab°

**หน้าที่**: แปลงคำสั่งภาษาไทยให้เป็น JSON action

**กฎ**:
1. ตอบออกมาเป็น JSON เท่านั้น (ไม่ต้องมีข้อความอื่น)
2. ถ้าคำสั่งเป็นการบันทึกยอดขาย (เช่น "บันทึก", "ขาย", "โอเดอร์"): ตอบ {"action": "log_sale", "args": {"menu": "ชื่อเมนู", "quantity": จำนวน, "price": ราคา}}
3. ถ้าคำสั่งเป็นการสั่งเมนู: ตอบ {"action": "order", "args": {"menu": "ชื่อเมนู", "quantity": จำนวน, "price": ราคา, "notes": "หมายเหตุ"}}
4. ถ้าคำสั่งเป็นการดึงสรุป: ตอบ {"action": "get_summary", "args": {}}
5. ถ้าคำสั่งไม่ใช่ข้างต้น: ตอบ {"action": "unknown", "args": {}}

**ตัวอย่าง**:
- "บันทึกชานม 10 แก้ว 45 บาท" → {"action": "log_sale", "args": {"menu": "ชานม", "quantity": 10, "price": 45}}
- "สั่งลาเต้ 5 แก้ว ราคา 65" → {"action": "order", "args": {"menu": "ลาเต้", "quantity": 5, "price": 65}}
- "วันนี้ขายได้เท่าไหร่" → {"action": "get_summary", "args": {}}
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


def extract_json_from_text(text: str) -> dict | None:
    """ดึง JSON จากข้อความ แม้มี markdown code block หรืออักขระอื่น"""
    # หา `{` แรก
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    # Track bracket นับเพื่อหาจุดสิ้นสุด JSON
    bracket_count = 0
    end_idx = start_idx
    
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            bracket_count += 1
        elif text[i] == '}':
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i + 1
                break
    
    if end_idx <= start_idx:
        return None
    
    json_str = text[start_idx:end_idx]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def run_agent(user_input: str) -> str:
    write_trace("user_input", {"message": user_input})

    response = client.models.generate_content(
        model=MODEL,
        contents=f"{SYSTEM_INSTRUCTION}\n\nคำสั่ง: {user_input}",
    )
    raw = response.text.strip()
    write_trace("llm_response", {"raw": raw})

    # ดึง JSON จากการตอบของ AI
    action_data = extract_json_from_text(raw)
    if not action_data:
        write_trace("parse_error", {"raw": raw})
        return "❌ ไม่สามารถแปลงคำสั่งได้ (JSON parsing failed)"

    action = action_data.get("action")
    args = action_data.get("args", {})

    if action not in TOOLS:
        write_trace("unknown_action", {"action": action})
        return f"⚠️ ไม่รู้จัก action: {action}"

    try:
        result = TOOLS[action](**args)
        write_trace("tool_result", {"action": action, "result": result})
        
        # ตอบขึ้นอยู่กับ tool
        if action == "log_sale" or action == "order":
            return (
                f"✅ บันทึกสำเร็จ: {result['menu']} "
                f"x{result['quantity']} = {result['total']} บาท"
            )
        elif action == "get_summary":
            return f"✅ {result.get('period', 'N/A')} - ยอดขายรวม {result.get('total_sales', 0)} บาท"
        else:
            return f"✅ สำเร็จ: {result}"
    except (ValueError, TypeError) as e:
        write_trace("tool_error", {"action": action, "error": str(e)})
        return f"❌ ข้อมูลไม่ถูกต้อง: {e}"


if __name__ == "__main__":
    print("Demi Agent พร้อมรับคำสั่ง (พิมพ์ 'exit' เพื่อออก)\n")
    print("💡 คำสั่งพิเศษ: 'trace' = ดู trace log, 'clear' = ลบ trace log\n")
    
    while True:
        user_input = input("คุณ: ").strip()
        
        if user_input.lower() == "exit":
            break
        elif user_input.lower() == "trace":
            # แสดง trace log
            if os.path.exists(TRACE_FILE):
                with open(TRACE_FILE, "r", encoding="utf-8") as f:
                    print("\n📋 Trace Log:")
                    for line in f.readlines()[-10:]:  # แสดง 10 บรรทัดสุดท้าย
                        print("  " + line.strip())
            else:
                print("❌ ไม่มี trace log")
            print()
        elif user_input.lower() == "clear":
            # ลบ trace log
            if os.path.exists(TRACE_FILE):
                os.remove(TRACE_FILE)
                print("✅ ลบ trace log สำเร็จ\n")
            else:
                print("❌ ไม่มี trace log\n")
        else:
            print(f"Demi: {run_agent(user_input)}\n")