# app.py
import json
import os
import random
import re
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from google import genai

from rag_engine import RAGEngine

# พยายาม import tool เดิมจาก Lab 2.5
# ถ้ามี agent_tools.py และตั้งค่า Google Sheet / Telegram ถูก ระบบจะบันทึกจริงได้
try:
    from agent_tools import TOOLS
except Exception:
    TOOLS = {}

load_dotenv()

st.set_page_config(
    page_title="MilkyMood AI",
    page_icon="🥛",
    layout="centered",
)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("ไม่พบ GOOGLE_API_KEY กรุณาเพิ่มใน HuggingFace Secrets หรือไฟล์ .env")
    st.stop()

client = genai.Client(api_key=api_key)
MODEL = "gemini-3.1-flash-lite-preview"


@st.cache_resource
def load_rag():
    return RAGEngine("knowledge/milklab_kb.txt")


rag = load_rag()


# -----------------------------
# Style
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fff7ec 0%, #ffeef7 48%, #eef7ff 100%);
        font-family: 'Prompt', 'Segoe UI', sans-serif;
    }

    .main-card {
        background: rgba(255, 255, 255, 0.88);
        border-radius: 30px;
        padding: 30px;
        box-shadow: 0 20px 60px rgba(150, 105, 80, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.95);
        margin-bottom: 20px;
    }

    .title {
        font-size: 42px;
        font-weight: 900;
        color: #6c4d3c;
        margin-bottom: 8px;
    }

    .subtitle {
        color: #8b6f60;
        font-size: 16px;
        line-height: 1.7;
        margin-bottom: 18px;
    }

    .tag {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        background: #fff1c7;
        color: #7a5731;
        font-weight: 700;
        margin: 4px 4px 4px 0;
        font-size: 14px;
    }

    .menu-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 14px 0 20px 0;
    }

    .menu-box {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 22px;
        padding: 17px;
        border: 1px solid #ffe1ef;
        box-shadow: 0 10px 25px rgba(255, 170, 205, 0.16);
        min-height: 118px;
    }

    .menu-title {
        font-size: 16px;
        font-weight: 900;
        color: #6c4d3c;
        margin-bottom: 6px;
    }

    .menu-desc {
        font-size: 13px;
        color: #8b6f60;
        line-height: 1.55;
    }

    .lucky-card {
        background: linear-gradient(135deg, #fff2b8, #ffe5f3);
        border-radius: 24px;
        padding: 18px;
        border: 1px solid #ffeaa0;
        color: #6c4d3c;
        margin-bottom: 18px;
        box-shadow: 0 12px 28px rgba(255, 190, 120, 0.16);
    }

    .small-note {
        font-size: 13px;
        color: #9a7a6a;
        margin-top: 8px;
    }

    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.78);
        border-radius: 18px;
        padding: 12px;
        border: 1px solid rgba(255, 220, 235, 0.9);
        box-shadow: 0 8px 20px rgba(145, 100, 80, 0.08);
    }

    @media (max-width: 800px) {
        .menu-grid {
            grid-template-columns: 1fr;
        }
        .title {
            font-size: 31px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# UI Header
# -----------------------------
st.markdown(
    """
    <div class="main-card">
        <div class="title">🥛 Demi ผู้ช่วย AI ของ MilkyMood</div>
        <div class="subtitle">
            คาเฟ่มินิมอลน่ารักธีม High School  
            มีเครื่องดื่ม กาแฟ เค้ก ขนมปังปิ้ง ปังเย็น เมนูมิกซ์เอง และเมนูเสริมดวงประจำวันเกิด
        </div>
        <span class="tag">☕ กาแฟ</span>
        <span class="tag">🥛 เครื่องดื่มนม</span>
        <span class="tag">🍰 เค้ก</span>
        <span class="tag">🍞 ขนมปังปิ้ง</span>
        <span class="tag">🍧 ปังเย็น</span>
        <span class="tag">🔮 เมนูเสริมดวง</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="menu-grid">
        <div class="menu-box">
            <div class="menu-title">🍯 ลาเต้น้ำผึ้ง</div>
            <div class="menu-desc">นมสด + น้ำผึ้ง + เอสเพรสโซ หอมละมุน ไม่มีน้ำตาลเพิ่ม</div>
        </div>
        <div class="menu-box">
            <div class="menu-title">🍰 เค้ก & ขนม</div>
            <div class="menu-desc">มีเค้ก ขนมปังปิ้ง และปังเย็น เหมาะกับสายหวาน</div>
        </div>
        <div class="menu-box">
            <div class="menu-title">🔮 Lucky Birthday Drink</div>
            <div class="menu-desc">บอกวันเกิด แล้ว Demi จะแนะนำเมนูเสริมดวงพร้อมไพ่ยิปซี</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="lucky-card">
        🔮 <b>ลูกเล่นเมนูเสริมดวง</b><br>
        ถ้าลูกค้าบอกวันเกิด เช่น “เกิดวันศุกร์ อยากได้เมนูเสริมดวง”
        Demi จะช่วยแนะนำเมนู พร้อมสุ่มไพ่ยิปซีและคำอวยพรสั้น ๆ ให้
        <div class="small-note">ตัวอย่าง: เกิดวันศุกร์ / เกิดวันจันทร์ / อยากได้เมนูเสริมดวง</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helper functions
# -----------------------------
def clean_json(text: str) -> dict[str, Any] | None:
    """แปลงคำตอบจาก Gemini ให้เป็น JSON ถ้าเป็นไปได้"""
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def lucky_tarot() -> tuple[str, str]:
    cards = [
        ("The Star", "วันนี้เหมาะกับการเริ่มต้นสิ่งดี ๆ ขอให้มีแสงนำทางและเจอเรื่องน่ารัก ๆ ✨"),
        ("The Sun", "วันนี้พลังสดใสมาก ขอให้มีความสุขและมีโอกาสดี ๆ เข้ามา ☀️"),
        ("The Lovers", "วันนี้ดวงความสัมพันธ์ดี เหมาะกับเมนูโทนหวานละมุน เติมใจให้ฟู 💕"),
        ("Wheel of Fortune", "วันนี้มีจังหวะดี ๆ กำลังเข้ามา ขอให้โชคหมุนไปทางที่ใช่ 🔮"),
        ("The Empress", "วันนี้เหมาะกับการดูแลตัวเอง ขอให้ได้รับพลังอบอุ่นและความอุดมสมบูรณ์ 🌷"),
    ]
    return random.choice(cards)


def estimate_wait(menu_text: str) -> str:
    if any(word in menu_text for word in ["เค้ก", "ปัง", "ขนม", "มิกซ์", "เสริมดวง"]):
        return "ประมาณ 10–15 นาที"
    return "ประมาณ 5–10 นาที"


def extract_order_action(user_prompt: str, context: str) -> dict[str, Any] | None:
    """
    ให้ Gemini ช่วยแปลงคำสั่งลูกค้าเป็น JSON action
    ใช้เฉพาะกรณีเหมือนมีการสั่งซื้อ
    """
    order_keywords = ["สั่ง", "เอา", "ขอ", "ซื้อ", "แก้ว", "ชิ้น", "ที่", "ออเดอร์"]
    if not any(k in user_prompt for k in order_keywords):
        return None

    extract_prompt = f"""
คุณคือระบบแปลงคำสั่งซื้อของร้าน MilkyMood เป็น JSON เท่านั้น

ถ้าผู้ใช้กำลังสั่งเมนู ให้ตอบ JSON รูปแบบนี้:
{{"is_order": true, "menu": "...", "quantity": 1, "price": 0}}

กติกา:
- quantity ต้องเป็นตัวเลข ถ้าไม่พบให้ใส่ 1
- price ต้องอ้างอิงจากข้อมูลร้านเท่านั้น
- ถ้าหาเมนูหรือราคาไม่พบ ให้ใส่ is_order เป็น false
- ห้ามใส่ markdown
- ตอบ JSON เท่านั้น

ข้อมูลร้าน:
{context}

คำสั่งลูกค้า:
{user_prompt}
"""
    try:
        res = client.models.generate_content(model=MODEL, contents=extract_prompt)
        data = clean_json(res.text)
        if data and data.get("is_order"):
            return data
    except Exception:
        return None

    return None


def save_order_if_possible(order: dict[str, Any]) -> tuple[bool, str]:
    """
    บันทึกออเดอร์จริงผ่าน agent_tools.py ถ้ามี TOOLS["log_sale"]
    ถ้าไม่มีหรือ error จะตอบเป็นข้อความ fallback
    """
    if "log_sale" not in TOOLS:
        return False, "ยังไม่ได้เชื่อม tool บันทึกจริงใน app.py แต่ระบบสามารถสรุปออเดอร์ให้ลูกค้าได้"

    try:
        result = TOOLS["log_sale"](
            menu=order["menu"],
            quantity=int(order["quantity"]),
            price=float(order["price"]),
        )

        sheet_status = "บันทึกลง Google Sheet แล้ว" if result.get("sheet_uploaded") else "ยังบันทึกลง Google Sheet ไม่สำเร็จ"
        telegram_status = "แจ้งเตือนผ่าน Telegram แล้ว" if result.get("telegram_sent") else "ยังแจ้งเตือน Telegram ไม่สำเร็จ"

        return True, f"{sheet_status} และ {telegram_status}"
    except Exception as e:
        return False, f"ยังบันทึกจริงไม่สำเร็จ: {e}"


# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "สวัสดีค่าา ยินดีต้อนรับสู่ MilkyMood 🥛 วันนี้อยากดูเมนู สั่งเครื่องดื่ม หรือดูเมนูเสริมดวงดีคะ?"
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# -----------------------------
# Chat input
# -----------------------------
if prompt := st.chat_input("ถามหรือสั่งเมนูได้เลย เช่น สั่งลาเต้น้ำผึ้ง 1 แก้ว / เกิดวันศุกร์อยากได้เมนูเสริมดวง"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    # RAG Search
    context_chunks = rag.search(prompt, top_k=3)
    context = "\n---\n".join(context_chunks)

    tarot_card, tarot_blessing = lucky_tarot()

    # พยายามจับว่าเป็นคำสั่งซื้อหรือไม่
    order = extract_order_action(prompt, context)

    if order:
        menu = str(order.get("menu", "")).strip()
        quantity = int(order.get("quantity", 1))
        price = float(order.get("price", 0))
        total = quantity * price
        wait_time = estimate_wait(menu)

        saved, save_message = save_order_if_possible(
            {"menu": menu, "quantity": quantity, "price": price}
        )

        is_lucky = any(word in prompt for word in ["เสริมดวง", "วันเกิด", "ไพ่", "ดวง"])

        lucky_text = ""
        if is_lucky:
            lucky_text = (
                f"\n\n🔮 ไพ่ยิปซีของออเดอร์นี้: {tarot_card}\n"
                f"คำอวยพร: {tarot_blessing}"
            )

        answer = (
            f"รับออเดอร์เรียบร้อยแล้วค่ะ 🥛\n\n"
            f"รายการ: {menu}\n"
            f"จำนวน: {quantity}\n"
            f"ราคา: {price:.0f} บาท\n"
            f"ยอดรวม: {total:.0f} บาท\n"
            f"เวลารอ: {wait_time}\n\n"
            f"สถานะระบบ: {save_message}"
            f"{lucky_text}"
        )

    else:
        full_prompt = f"""
คุณคือ Demi ผู้ช่วย AI ของร้าน MilkyMood คาเฟ่มินิมอลน่ารักธีม High School

กติกาการตอบ:
1. ตอบเป็นภาษาไทย น้ำเสียงน่ารัก สุภาพ เป็นกันเอง
2. ตอบเฉพาะจากข้อมูลร้านด้านล่าง ถ้าไม่มีข้อมูลให้บอกว่า "ไม่ทราบจากข้อมูลร้านตอนนี้"
3. ถ้าลูกค้าถามเมนู ให้สรุปเมนูและราคาให้ชัดเจน
4. ถ้าลูกค้าถามเรื่องสั่งซื้อ ให้อธิบายว่าระบบสามารถสรุปรายการ ราคา และเวลารอได้
5. ถ้าถามเมนูเสริมดวง ให้แนะนำตามวันเกิด และอธิบายลูกเล่นไพ่ยิปซี
6. ห้ามแต่งเมนูหรือราคาที่ไม่มีในข้อมูลร้าน

ข้อมูลร้าน:
{context}

คำถามลูกค้า:
{prompt}
"""
        try:
            response = client.models.generate_content(model=MODEL, contents=full_prompt)
            answer = response.text
        except Exception:
            answer = "ตอนนี้เรียก Gemini API ไม่สำเร็จ จึงแสดงข้อมูลที่ค้นเจอจากฐานความรู้แทน:\n\n" + context

    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.write(answer)