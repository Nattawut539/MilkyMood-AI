# app.py
import os
import random
import re
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from google import genai

from rag_engine import RAGEngine

# ถ้ามี agent_tools.py จาก Lab 2.5 ระบบจะพยายามบันทึก Google Sheet / Telegram จริง
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


# =========================================================
# เมนูร้าน MilkyMood
# =========================================================

MILK_DRINKS = {
    "ลาเต้น้ำผึ้ง": 65,
    "มิลค์ทีออริจินัล": 55,
    "สตรอว์เบอร์รี่มิลค์": 60,
    "โกโก้ภูเขาไฟ": 60,
    "มัทฉะลาเต้": 70,
    "คาราเมลมิลค์": 55,
    "นมสดโอริโอ้": 65,
    "นมสดวานิลลา": 55,
}

COFFEE_DRINKS = {
    "อเมริกาโน่เย็น": 55,
    "ลาเต้เย็น": 65,
    "คาปูชิโน่เย็น": 65,
    "มอคค่าเย็น": 70,
    "คาราเมลมัคคิอาโต": 75,
    "เอสเพรสโซ่เย็น": 60,
    "กาแฟส้ม": 75,
    "อเมริกาโน่น้ำผึ้ง": 65,
}

CAKES = {
    "เค้กสตรอว์เบอร์รี่": 75,
    "เค้กช็อกโกแลต": 70,
    "ชีสเค้กหน้าไหม้": 80,
    "เค้กนมสดวานิลลา": 70,
    "เค้กชาไทย": 75,
    "เค้กมัทฉะ": 80,
    "เค้กบลูเบอร์รี่": 75,
    "บราวนี่ช็อกโกแลต": 65,
}

TOASTS = {
    "ปังปิ้งเนยนม": 35,
    "ปังปิ้งช็อกโกแลต": 40,
    "ปังปิ้งสตรอว์เบอร์รี่": 45,
    "ปังปิ้งคาราเมล": 45,
    "ปังปิ้งโอริโอ้": 50,
    "ปังปิ้งวิปครีม": 55,
}

BINGSU_BREAD = {
    "ปังเย็นนมชมพู": 69,
    "ปังเย็นโกโก้": 75,
    "ปังเย็นชาไทย": 75,
    "ปังเย็นโอริโอ้": 79,
    "ปังเย็นสตรอว์เบอร์รี่": 79,
    "ปังเย็นมัทฉะ": 85,
}

LUCKY_DRINKS = {
    "วันจันทร์": [
        {"menu": "Moon Milk", "price": 69, "meaning": "เสริมความใจเย็น ความรักตัวเอง และพลังอ่อนโยน"},
        {"menu": "Vanilla Calm Milk", "price": 65, "meaning": "เสริมความสงบ ลดความกังวล และเพิ่มความสบายใจ"},
        {"menu": "Pearl Moon Latte", "price": 75, "meaning": "เสริมเสน่ห์แบบนุ่มนวล และช่วยให้คนรอบข้างเอ็นดู"},
        {"menu": "Honey Moon Tea", "price": 70, "meaning": "เสริมคำพูดหวาน ๆ การสื่อสาร และความสัมพันธ์ที่ดี"},
        {"menu": "Soft Blue Milk", "price": 69, "meaning": "เสริมความใจเย็น ความละมุน และพลังบวกในวันใหม่"},
    ],
    "วันอังคาร": [
        {"menu": "Ruby Cocoa", "price": 75, "meaning": "เสริมความมั่นใจ กล้าตัดสินใจ และพลังในการเริ่มต้น"},
        {"menu": "Red Velvet Milk", "price": 79, "meaning": "เสริมความโดดเด่น ความกล้า และเสน่ห์ที่น่าจดจำ"},
        {"menu": "Spicy Mocha", "price": 75, "meaning": "เสริมพลังลุยงาน ความขยัน และความกระตือรือร้น"},
        {"menu": "Rose Power Latte", "price": 79, "meaning": "เสริมพลังใจ ความรักตัวเอง และความมั่นใจจากข้างใน"},
        {"menu": "Choco Brave", "price": 70, "meaning": "เสริมความกล้า ความหนักแน่น และความพร้อมในการตัดสินใจ"},
    ],
    "วันพุธ": [
        {"menu": "Matcha Wisdom", "price": 75, "meaning": "เสริมสติ ความคิด การเรียน และการสื่อสาร"},
        {"menu": "Mint Study Milk", "price": 69, "meaning": "เสริมความสดชื่น ความจำ และสมาธิในการเรียน"},
        {"menu": "Green Tea Focus", "price": 70, "meaning": "เสริมสมาธิ ความนิ่ง และการจัดการความคิด"},
        {"menu": "Honey Matcha Cloud", "price": 79, "meaning": "เสริมความนุ่มนวลในการพูด และโอกาสดี ๆ จากการสื่อสาร"},
        {"menu": "Book Club Latte", "price": 75, "meaning": "เสริมการเรียน ความรู้ และแรงบันดาลใจใหม่ ๆ"},
    ],
    "วันพฤหัสบดี": [
        {"menu": "Honey Bless Latte", "price": 79, "meaning": "เสริมโชคด้านผู้ใหญ่ การเรียน และโอกาสดี ๆ"},
        {"menu": "Golden Milk Tea", "price": 70, "meaning": "เสริมความสำเร็จ ความเมตตา และความน่าเชื่อถือ"},
        {"menu": "Teacher Choice Latte", "price": 75, "meaning": "เสริมดวงด้านการเรียน การสอบ และคำแนะนำจากผู้ใหญ่"},
        {"menu": "Lucky Caramel Milk", "price": 69, "meaning": "เสริมโชคเล็ก ๆ ในชีวิตประจำวัน และความอบอุ่นใจ"},
        {"menu": "Wisdom Cocoa", "price": 75, "meaning": "เสริมปัญญา การคิดวิเคราะห์ และความมั่นคงทางใจ"},
    ],
    "วันศุกร์": [
        {"menu": "Pink Lover Milk", "price": 69, "meaning": "เสริมเสน่ห์ ความสัมพันธ์ และความสดใสน่ารัก"},
        {"menu": "Strawberry Charm", "price": 75, "meaning": "เสริมเสน่ห์ ความน่ารัก และการเป็นที่สนใจ"},
        {"menu": "Rose Milk Tea", "price": 70, "meaning": "เสริมความรัก ความอ่อนโยน และบรรยากาศดี ๆ รอบตัว"},
        {"menu": "Sweetheart Cocoa", "price": 75, "meaning": "เสริมความอบอุ่น ความรัก และมิตรภาพที่จริงใจ"},
        {"menu": "Peachy Milk", "price": 69, "meaning": "เสริมความสดใส ความน่าคุย และโอกาสดีด้านความสัมพันธ์"},
    ],
    "วันเสาร์": [
        {"menu": "Dark Choco Shield", "price": 75, "meaning": "เสริมความหนักแน่น ความมั่นคง และป้องกันพลังลบ"},
        {"menu": "Black Cocoa", "price": 70, "meaning": "เสริมความแข็งแรงทางใจ และความอดทน"},
        {"menu": "Midnight Milk Tea", "price": 75, "meaning": "เสริมความนิ่ง ความรอบคอบ และการตัดสินใจที่ดี"},
        {"menu": "Charcoal Vanilla Milk", "price": 79, "meaning": "เสริมการปล่อยพลังลบ และเริ่มต้นใหม่อย่างสงบ"},
        {"menu": "Strong Heart Latte", "price": 75, "meaning": "เสริมกำลังใจ ความมั่นคง และความกล้าที่จะไปต่อ"},
    ],
    "วันอาทิตย์": [
        {"menu": "Sunny Orange Coffee", "price": 79, "meaning": "เสริมพลัง ความสดใส โอกาสใหม่ และความมั่นใจ"},
        {"menu": "Orange Honey Tea", "price": 70, "meaning": "เสริมความสดชื่น โชคดี และความสบายใจ"},
        {"menu": "Sunflower Latte", "price": 75, "meaning": "เสริมพลังบวก ความมั่นใจ และความโดดเด่น"},
        {"menu": "Bright Cocoa", "price": 70, "meaning": "เสริมความสุขเล็ก ๆ และพลังใจที่อบอุ่น"},
        {"menu": "Golden Vanilla Milk", "price": 69, "meaning": "เสริมโอกาสใหม่ ความสดใส และความอ่อนโยน"},
    ],
}


def flatten_lucky_menu_prices() -> dict[str, int]:
    result = {}
    for items in LUCKY_DRINKS.values():
        for item in items:
            result[item["menu"]] = item["price"]
    return result


LUCKY_MENU_PRICES = flatten_lucky_menu_prices()

MENU_PRICES = {
    **MILK_DRINKS,
    **COFFEE_DRINKS,
    **CAKES,
    **TOASTS,
    **BINGSU_BREAD,
    **LUCKY_MENU_PRICES,
}

LUCKY_MENU_NAMES = set(LUCKY_MENU_PRICES.keys())

TAROT_CARDS = [
    ("The Star", "ขอให้วันนี้มีความหวังและเจอเรื่องดี ๆ เหมือนมีดาวนำทาง ✨"),
    ("The Sun", "ขอให้วันนี้สดใส มีพลัง และเจอความสำเร็จเล็ก ๆ ที่ทำให้ยิ้มได้ ☀️"),
    ("The Lovers", "ขอให้วันนี้มีความสัมพันธ์ที่ดี และมีคนใจดีกับเธอ 💕"),
    ("Wheel of Fortune", "ขอให้วันนี้มีจังหวะดี ๆ และโชคหมุนมาทางเธอ 🔮"),
    ("The Empress", "ขอให้วันนี้ได้ดูแลตัวเอง และได้รับพลังอบอุ่นจากสิ่งรอบตัว 🌷"),
    ("Ace of Cups", "ขอให้วันนี้มีเรื่องดี ๆ เติมใจ และได้เริ่มต้นความรู้สึกใหม่ ๆ 🩷"),
]


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fff7ec 0%, #ffeef7 48%, #eef7ff 100%);
        font-family: 'Prompt', 'Segoe UI', sans-serif;
    }

    .block-container {
        padding-top: 3rem;
        max-width: 980px;
    }

    .main-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 32px;
        padding: 34px;
        box-shadow: 0 22px 70px rgba(150, 105, 80, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.95);
        margin-bottom: 22px;
    }

    .title {
        font-size: 42px;
        font-weight: 900;
        color: #6c4d3c;
        margin-bottom: 10px;
    }

    .subtitle {
        color: #8b6f60;
        font-size: 16px;
        line-height: 1.8;
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
        gap: 14px;
        margin: 14px 0 22px 0;
    }

    .menu-box {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 24px;
        padding: 18px;
        border: 1px solid #ffe1ef;
        box-shadow: 0 10px 25px rgba(255, 170, 205, 0.16);
        min-height: 125px;
    }

    .menu-title {
        font-size: 17px;
        font-weight: 900;
        color: #6c4d3c;
        margin-bottom: 7px;
    }

    .menu-desc {
        font-size: 13px;
        color: #8b6f60;
        line-height: 1.55;
    }

    .lucky-card {
        background: linear-gradient(135deg, #fff2b8, #ffe5f3);
        border-radius: 24px;
        padding: 20px;
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

    .tarot-popup {
        margin-top: 18px;
        padding: 24px;
        border-radius: 28px;
        background: radial-gradient(circle at top, #fff7d8, #2a1838 72%);
        color: white;
        box-shadow: 0 20px 50px rgba(44, 20, 70, 0.35);
        text-align: center;
        animation: popupIn 0.6s ease-out;
    }

    @keyframes popupIn {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.94);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    .tarot-title {
        font-size: 22px;
        font-weight: 900;
        margin-bottom: 12px;
        color: #ffeab6;
    }

    .flip-wrap {
        display: flex;
        justify-content: center;
        margin-top: 14px;
    }

    .flip-toggle {
        display: none;
    }

    .flip-card {
        width: 210px;
        height: 310px;
        perspective: 1000px;
        cursor: pointer;
        display: block;
    }

    .flip-inner {
        position: relative;
        width: 100%;
        height: 100%;
        transition: transform 0.8s;
        transform-style: preserve-3d;
    }

    .flip-toggle:checked + .flip-card .flip-inner {
        transform: rotateY(180deg);
    }

    .flip-front,
    .flip-back {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 22px;
        backface-visibility: hidden;
        box-shadow: 0 18px 34px rgba(0, 0, 0, 0.28);
        border: 2px solid rgba(255, 230, 170, 0.95);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 18px;
        box-sizing: border-box;
    }

    .flip-front {
        background:
            radial-gradient(circle at center, rgba(255,255,255,0.22), transparent 35%),
            linear-gradient(145deg, #4b2a68, #1d102b);
        color: #ffeab6;
        font-size: 20px;
        font-weight: 900;
        letter-spacing: 1px;
    }

    .flip-back {
        background: linear-gradient(145deg, #fff8de, #ffe2f1);
        color: #5c3d2e;
        transform: rotateY(180deg);
        flex-direction: column;
        font-size: 15px;
        line-height: 1.55;
        font-weight: 700;
    }

    .tarot-card-name {
        font-size: 20px;
        margin-bottom: 10px;
        color: #7b4b1f;
        font-weight: 900;
    }

    .tap-hint {
        margin-top: 12px;
        font-size: 13px;
        color: #ffeab6;
        opacity: 0.9;
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


# =========================================================
# UI Header
# =========================================================

st.markdown(
    """
    <div class="main-card">
        <div class="title">🥛 Demi ผู้ช่วย AI ของ MilkyMood</div>
        <div class="subtitle">
            คาเฟ่ยินดีต้อนรับคุณลูกค้า สามารถเลือกสั่งเมนูทางร้านได้ดังนี้
            เครื่องดื่มนม กาแฟ เค้ก ขนมปังปิ้ง ปังเย็น เมนูมิกซ์เอง
            และเมนูเสริมดวงประจำวันเกิด
        </div>
        <span class="tag">🥛 เครื่องดื่มนม</span>
        <span class="tag">☕ กาแฟ</span>
        <span class="tag">🍰 เค้ก</span>
        <span class="tag">🍞 ขนมปังปิ้ง</span>
        <span class="tag">🍧 ปังเย็น</span>
        <span class="tag">🧋 มิกซ์เอง</span>
        <span class="tag">🔮 เมนูเสริมดวง</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="menu-grid">
        <div class="menu-box">
            <div class="menu-title">🥛 เครื่องดื่มนม</div>
            <div class="menu-desc">ลาเต้น้ำผึ้ง มิลค์ที โกโก้ มัทฉะ คาราเมลมิลค์ และเมนูนมสดน่ารัก ๆ</div>
        </div>
        <div class="menu-box">
            <div class="menu-title">☕ กาแฟ</div>
            <div class="menu-desc">อเมริกาโน่ ลาเต้ คาปูชิโน่ มอคค่า กาแฟส้ม และเมนูกาแฟอื่น ๆ</div>
        </div>
        <div class="menu-box">
            <div class="menu-title">🔮 Lucky Birthday Drink</div>
            <div class="menu-desc">บอกวันเกิด แล้ว Demi จะสุ่มเมนูเสริมดวงจากวันนั้นให้ พร้อมไพ่ยิปซี</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="lucky-card">
        🔮 <b>ลูกเล่นเมนูเสริมดวง</b><br>
        ลูกค้าสามารถบอกวันเกิด เช่น “เกิดวันศุกร์ อยากได้เมนูเสริมดวง”
        Demi จะสุ่มเมนูจากวันนั้นให้ และเมื่อสั่งสำเร็จจะมีไพ่ยิปซีเด้งขึ้นมา
        แตะที่ไพ่เพื่อพลิกดูคำอวยพรได้ค่ะ
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Helper functions
# =========================================================

def find_birth_day(text: str) -> str | None:
    day_aliases = {
        "วันจันทร์": "วันจันทร์",
        "จันทร์": "วันจันทร์",
        "วันอังคาร": "วันอังคาร",
        "อังคาร": "วันอังคาร",
        "วันพุธ": "วันพุธ",
        "พุธ": "วันพุธ",
        "วันพฤหัสบดี": "วันพฤหัสบดี",
        "วันพฤหัส": "วันพฤหัสบดี",
        "พฤหัสบดี": "วันพฤหัสบดี",
        "พฤหัส": "วันพฤหัสบดี",
        "วันศุกร์": "วันศุกร์",
        "ศุกร์": "วันศุกร์",
        "วันเสาร์": "วันเสาร์",
        "เสาร์": "วันเสาร์",
        "วันอาทิตย์": "วันอาทิตย์",
        "อาทิตย์": "วันอาทิตย์",
    }

    for key, value in day_aliases.items():
        if key in text:
            return value

    return None


def extract_quantity(text: str) -> int:
    match = re.search(r"(\d+)\s*(แก้ว|ชิ้น|ที่|อัน)?", text)
    if match:
        return int(match.group(1))
    return 1


def is_order_text(text: str) -> bool:
    order_words = ["สั่ง", "เอา", "ขอ", "ซื้อ", "รับ", "จัดมา", "เอาเมนูนี้", "เอาอันนี้", "ตัวนี้"]
    return any(word in text for word in order_words)


def is_list_request(text: str) -> bool:
    list_words = ["อะไรบ้าง", "ทั้งหมด", "มีอะไร", "มีเมนูอะไร", "ลิสต์", "รายการ"]
    return any(word in text for word in list_words)


def is_lucky_intent(text: str) -> bool:
    return ("เสริมดวง" in text) or ("วันเกิด" in text) or (find_birth_day(text) is not None)


def recommend_lucky_drink(day: str) -> dict[str, Any]:
    return random.choice(LUCKY_DRINKS[day])


def list_lucky_drinks(day: str) -> str:
    items = LUCKY_DRINKS[day]
    lines = [f"เมนูเสริมดวงสำหรับคนเกิด{day} มี 5 เมนูค่ะ 🔮"]
    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}. {item['menu']} ราคา {item['price']} บาท - {item['meaning']}")
    lines.append("\nถ้าอยากให้ Demi สุ่มให้ พิมพ์ว่า “เกิด" + day.replace("วัน", "") + " อยากได้เมนูเสริมดวง” ได้เลยค่ะ")
    return "\n".join(lines)


def find_menu_from_text(text: str) -> str | None:
    lowered = text.lower()

    for menu in MENU_PRICES.keys():
        if menu.lower() in lowered:
            return menu

    if any(word in text for word in ["เมนูนี้", "อันนี้", "ตัวนี้"]):
        return st.session_state.get("last_recommended_menu")

    return None


def random_tarot() -> tuple[str, str]:
    return random.choice(TAROT_CARDS)


def estimate_wait_time(menu: str) -> str:
    if menu in LUCKY_MENU_NAMES:
        return "ประมาณ 10–15 นาที"

    if any(word in menu for word in ["เค้ก", "ปัง", "มิกซ์"]):
        return "ประมาณ 10–15 นาที"

    return "ประมาณ 5–10 นาที"


def save_order_if_possible(menu: str, quantity: int, price: float) -> str:
    if "log_sale" not in TOOLS:
        return "โหมดตัวอย่าง: ระบบสรุปออเดอร์แล้ว แต่ยังไม่ได้เชื่อม tool บันทึกจริงใน app.py"

    try:
        result = TOOLS["log_sale"](menu=menu, quantity=quantity, price=price)

        sheet_status = "บันทึกลง Google Sheet แล้ว" if result.get("sheet_uploaded") else "ยังบันทึกลง Google Sheet ไม่สำเร็จ"
        telegram_status = "แจ้งเตือนผ่าน Telegram แล้ว" if result.get("telegram_sent") else "ยังแจ้งเตือน Telegram ไม่สำเร็จ"

        return f"{sheet_status} และ {telegram_status}"
    except Exception as e:
        return f"ยังบันทึกจริงไม่สำเร็จ: {e}"


def tarot_popup_html(card_name: str, blessing: str) -> str:
    card_id = f"tarot_{random.randint(10000, 99999)}"
    return f"""
    <div class="tarot-popup">
        <div class="tarot-title">🔮 ไพ่ยิปซีของออเดอร์นี้ปรากฏแล้ว</div>
        <div class="flip-wrap">
            <input type="checkbox" id="{card_id}" class="flip-toggle">
            <label for="{card_id}" class="flip-card">
                <div class="flip-inner">
                    <div class="flip-front">
                        ✦ MilkyMood Tarot ✦<br><br>
                        แตะเพื่อเปิดไพ่
                    </div>
                    <div class="flip-back">
                        <div class="tarot-card-name">{card_name}</div>
                        <div>{blessing}</div>
                    </div>
                </div>
            </label>
        </div>
        <div class="tap-hint">แตะที่ไพ่เพื่อพลิกดูคำอวยพร</div>
    </div>
    """


def build_order_reply(menu: str, quantity: int, price: int, is_lucky: bool = False) -> tuple[str, str | None]:
    total = quantity * price
    wait_time = estimate_wait_time(menu)
    status_message = save_order_if_possible(menu, quantity, price)

    reply = (
        f"ระบบได้ทำการรับ Order เรียบร้อยแล้ว กรุณารอสักครู่ค่ะ 🥛\n\n"
        f"รายการ: {menu}\n"
        f"จำนวน: {quantity}\n"
        f"ราคา: {price} บาท\n"
        f"ยอดรวม: {total} บาท\n"
        f"เวลารอ: {wait_time}\n\n"
        f"สถานะระบบ: {status_message}"
    )

    tarot_html = None

    if is_lucky:
        card, blessing = random_tarot()
        reply += (
            f"\n\n🔮 ระบบสุ่มไพ่ยิปซีให้แล้วค่ะ แตะที่ไพ่ด้านล่างเพื่อดูคำอวยพร"
        )
        tarot_html = tarot_popup_html(card, blessing)

    return reply, tarot_html


# =========================================================
# Chat state
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "สวัสดีค่าา ยินดีต้อนรับสู่ MilkyMood 🥛\n"
                "คุณลูกค้าสามารถถามเมนู สั่งเครื่องดื่ม เค้ก ขนมปังปิ้ง ปังเย็น "
                "หรือให้ Demi สุ่มเมนูเสริมดวงประจำวันเกิดได้เลยค่ะ"
            ),
        }
    ]

if "tarot_popups" not in st.session_state:
    st.session_state.tarot_popups = {}

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        popup_html = st.session_state.tarot_popups.get(idx)
        if popup_html:
            st.markdown(popup_html, unsafe_allow_html=True)


# =========================================================
# Chat input
# =========================================================

if prompt := st.chat_input("ถามหรือสั่งเมนูได้เลย เช่น สั่งลาเต้น้ำผึ้ง 1 แก้ว / เกิดวันศุกร์อยากได้เมนูเสริมดวง"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    birth_day = find_birth_day(prompt)
    lucky_intent = is_lucky_intent(prompt)
    order_intent = is_order_text(prompt)
    list_request = is_list_request(prompt)

    tarot_html = None

    if lucky_intent and list_request and birth_day:
        answer = list_lucky_drinks(birth_day)

    elif lucky_intent and not order_intent:
        if birth_day:
            item = recommend_lucky_drink(birth_day)
            menu = item["menu"]
            price = item["price"]
            meaning = item["meaning"]

            st.session_state["last_recommended_menu"] = menu

            answer = (
                f"สำหรับคนเกิด{birth_day} Demi สุ่มเมนูเสริมดวงให้แล้วค่ะ 🔮\n\n"
                f"เมนูที่ได้: {menu}\n"
                f"ราคา: {price} บาท\n"
                f"ความหมาย: {meaning}\n\n"
                f"ถ้าต้องการสั่ง พิมพ์ว่า “สั่งเมนูนี้ 1 แก้ว” "
                f"หรือ “สั่ง {menu} 1 แก้ว” ได้เลยค่ะ"
            )
        else:
            answer = (
                "อยากได้เมนูเสริมดวงได้เลยค่ะ 🔮\n"
                "รบกวนบอกวันเกิดก่อน เช่น เกิดวันศุกร์ หรือ เกิดวันจันทร์ "
                "แล้ว Demi จะสุ่มเมนูจากวันนั้นให้ค่ะ"
            )

    elif lucky_intent and order_intent:
        if birth_day:
            explicit_menu = find_menu_from_text(prompt)

            if explicit_menu and explicit_menu in MENU_PRICES:
                menu = explicit_menu
                price = MENU_PRICES[menu]
            else:
                item = recommend_lucky_drink(birth_day)
                menu = item["menu"]
                price = item["price"]

            st.session_state["last_recommended_menu"] = menu
            quantity = extract_quantity(prompt)
            answer, tarot_html = build_order_reply(menu, quantity, price, is_lucky=True)

        else:
            menu = find_menu_from_text(prompt)

            if menu and menu in MENU_PRICES:
                quantity = extract_quantity(prompt)
                price = MENU_PRICES[menu]
                answer, tarot_html = build_order_reply(menu, quantity, price, is_lucky=(menu in LUCKY_MENU_NAMES))
            else:
                answer = (
                    "ถ้าต้องการสั่งเมนูเสริมดวง รบกวนบอกวันเกิดด้วยนะคะ "
                    "เช่น “สั่งเมนูเสริมดวงวันศุกร์ 1 แก้ว”"
                )

    elif order_intent:
        menu = find_menu_from_text(prompt)

        if menu and menu in MENU_PRICES:
            quantity = extract_quantity(prompt)
            price = MENU_PRICES[menu]
            answer, tarot_html = build_order_reply(menu, quantity, price, is_lucky=(menu in LUCKY_MENU_NAMES))
        else:
            answer = (
                "ขอโทษค่ะ Demi ยังไม่พบเมนูนี้ในข้อมูลร้านตอนนี้ 🥺\n"
                "ลองพิมพ์ชื่อเมนูให้ตรงกับเมนูในร้าน เช่น ลาเต้น้ำผึ้ง, โกโก้ภูเขาไฟ, Pink Lover Milk"
            )

    else:
        context_chunks = rag.search(prompt, top_k=3)
        context = "\n---\n".join(context_chunks)

        full_prompt = f"""คุณคือ Demi ผู้ช่วย AI ของร้าน MilkyMood

กติกาการตอบ:
1. ตอบเป็นภาษาไทย น้ำเสียงน่ารัก สุภาพ เป็นกันเอง
2. ตอบเฉพาะจากข้อมูลร้านด้านล่าง ถ้าไม่มีข้อมูลให้บอกว่า "ไม่ทราบจากข้อมูลร้านตอนนี้"
3. ถ้าลูกค้าถามเมนู ให้สรุปเมนูและราคาให้ชัดเจน
4. ถ้าถามเรื่องเมนูเสริมดวง ให้อธิบายว่ามี 5 เมนูต่อวันและสามารถสุ่มตามวันเกิดได้
5. ห้ามแต่งเมนูหรือราคาที่ไม่มีในข้อมูลร้าน

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
    assistant_index = len(st.session_state.messages) - 1

    if tarot_html:
        st.session_state.tarot_popups[assistant_index] = tarot_html

    with st.chat_message("assistant"):
        st.write(answer)
        if tarot_html:
            st.markdown(tarot_html, unsafe_allow_html=True)