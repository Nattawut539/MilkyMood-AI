# app.py
import os
import random
import re
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
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

# เพิ่ม ingredients ให้ทุกเมนูเสริมดวง เพื่อให้ Demi ตอบรายละเอียดส่วนผสมได้ทันที
LUCKY_DRINKS = {
    "วันจันทร์": [
        {
            "menu": "Moon Milk",
            "price": 69,
            "meaning": "เสริมความใจเย็น ความรักตัวเอง และพลังอ่อนโยน",
            "ingredients": "นมสด, วานิลลา, ไซรัปนม, วิปครีมเล็กน้อย, ไข่มุกขาว",
        },
        {
            "menu": "Vanilla Calm Milk",
            "price": 65,
            "meaning": "เสริมความสงบ ลดความกังวล และเพิ่มความสบายใจ",
            "ingredients": "นมสด, วานิลลา, ครีมนม, น้ำแข็ง, กลิ่นนมอ่อน ๆ",
        },
        {
            "menu": "Pearl Moon Latte",
            "price": 75,
            "meaning": "เสริมเสน่ห์แบบนุ่มนวล และช่วยให้คนรอบข้างเอ็นดู",
            "ingredients": "เอสเพรสโซ, นมสด, ไซรัปวานิลลา, ไข่มุก, ฟองนมนุ่ม",
        },
        {
            "menu": "Honey Moon Tea",
            "price": 70,
            "meaning": "เสริมคำพูดหวาน ๆ การสื่อสาร และความสัมพันธ์ที่ดี",
            "ingredients": "ชาดำ, นมสด, น้ำผึ้ง, ไซรัปนม, น้ำแข็ง",
        },
        {
            "menu": "Soft Blue Milk",
            "price": 69,
            "meaning": "เสริมความใจเย็น ความละมุน และพลังบวกในวันใหม่",
            "ingredients": "นมสด, ไซรัปบลูฮาวาย, วานิลลา, วิปครีม, เยลลี่ฟ้า",
        },
    ],
    "วันอังคาร": [
        {
            "menu": "Ruby Cocoa",
            "price": 75,
            "meaning": "เสริมความมั่นใจ กล้าตัดสินใจ และพลังในการเริ่มต้น",
            "ingredients": "โกโก้เข้มข้น, นมสด, ซอสสตรอว์เบอร์รี่, ผงโกโก้, น้ำแข็ง",
        },
        {
            "menu": "Red Velvet Milk",
            "price": 79,
            "meaning": "เสริมความโดดเด่น ความกล้า และเสน่ห์ที่น่าจดจำ",
            "ingredients": "นมสด, ซอสเรดเวลเวท, ครีมชีสโฟม, ครัมเบิลเค้ก, น้ำแข็ง",
        },
        {
            "menu": "Spicy Mocha",
            "price": 75,
            "meaning": "เสริมพลังลุยงาน ความขยัน และความกระตือรือร้น",
            "ingredients": "เอสเพรสโซ, โกโก้, นมสด, ซินนามอนเล็กน้อย, น้ำแข็ง",
        },
        {
            "menu": "Rose Power Latte",
            "price": 79,
            "meaning": "เสริมพลังใจ ความรักตัวเอง และความมั่นใจจากข้างใน",
            "ingredients": "เอสเพรสโซ, นมสด, ไซรัปกุหลาบ, ฟองนม, กลีบกุหลาบตกแต่ง",
        },
        {
            "menu": "Choco Brave",
            "price": 70,
            "meaning": "เสริมความกล้า ความหนักแน่น และความพร้อมในการตัดสินใจ",
            "ingredients": "โกโก้เข้มข้น, นมสด, ซอสช็อกโกแลต, ช็อกโกแลตชิพ",
        },
    ],
    "วันพุธ": [
        {
            "menu": "Matcha Wisdom",
            "price": 75,
            "meaning": "เสริมสติ ความคิด การเรียน และการสื่อสาร",
            "ingredients": "ผงมัทฉะ, นมสด, ไซรัปนม, ฟองนม, น้ำแข็ง",
        },
        {
            "menu": "Mint Study Milk",
            "price": 69,
            "meaning": "เสริมความสดชื่น ความจำ และสมาธิในการเรียน",
            "ingredients": "นมสด, ไซรัปมิ้นต์, เยลลี่น้ำผึ้ง, น้ำแข็ง, ฟองนม",
        },
        {
            "menu": "Green Tea Focus",
            "price": 70,
            "meaning": "เสริมสมาธิ ความนิ่ง และการจัดการความคิด",
            "ingredients": "ชาเขียว, นมสด, น้ำผึ้งเล็กน้อย, น้ำแข็ง",
        },
        {
            "menu": "Honey Matcha Cloud",
            "price": 79,
            "meaning": "เสริมความนุ่มนวลในการพูด และโอกาสดี ๆ จากการสื่อสาร",
            "ingredients": "มัทฉะ, นมสด, น้ำผึ้ง, ครีมโฟมนุ่ม, เยลลี่น้ำผึ้ง",
        },
        {
            "menu": "Book Club Latte",
            "price": 75,
            "meaning": "เสริมการเรียน ความรู้ และแรงบันดาลใจใหม่ ๆ",
            "ingredients": "เอสเพรสโซ, นมสด, ไซรัปวานิลลา, คาราเมลบาง ๆ, น้ำแข็ง",
        },
    ],
    "วันพฤหัสบดี": [
        {
            "menu": "Honey Bless Latte",
            "price": 79,
            "meaning": "เสริมโชคด้านผู้ใหญ่ การเรียน และโอกาสดี ๆ",
            "ingredients": "เอสเพรสโซ, นมสด, น้ำผึ้ง, ฟองนม, คาราเมลเล็กน้อย",
        },
        {
            "menu": "Golden Milk Tea",
            "price": 70,
            "meaning": "เสริมความสำเร็จ ความเมตตา และความน่าเชื่อถือ",
            "ingredients": "ชาไทย, นมสด, น้ำผึ้ง, ไข่มุกสีทอง, น้ำแข็ง",
        },
        {
            "menu": "Teacher Choice Latte",
            "price": 75,
            "meaning": "เสริมดวงด้านการเรียน การสอบ และคำแนะนำจากผู้ใหญ่",
            "ingredients": "เอสเพรสโซ, นมสด, วานิลลา, ฟองนม, ผงโกโก้โรยหน้า",
        },
        {
            "menu": "Lucky Caramel Milk",
            "price": 69,
            "meaning": "เสริมโชคเล็ก ๆ ในชีวิตประจำวัน และความอบอุ่นใจ",
            "ingredients": "นมสด, ซอสคาราเมล, วิปครีม, คาราเมลครัมเบิล",
        },
        {
            "menu": "Wisdom Cocoa",
            "price": 75,
            "meaning": "เสริมปัญญา การคิดวิเคราะห์ และความมั่นคงทางใจ",
            "ingredients": "โกโก้เข้มข้น, นมสด, น้ำผึ้ง, ผงโกโก้, น้ำแข็ง",
        },
    ],
    "วันศุกร์": [
        {
            "menu": "Pink Lover Milk",
            "price": 69,
            "meaning": "เสริมเสน่ห์ ความสัมพันธ์ และความสดใสน่ารัก",
            "ingredients": "นมสด, ไซรัปสตรอว์เบอร์รี่, ซอสนมชมพู, วิปครีม, เยลลี่หัวใจ",
        },
        {
            "menu": "Strawberry Charm",
            "price": 75,
            "meaning": "เสริมเสน่ห์ ความน่ารัก และการเป็นที่สนใจ",
            "ingredients": "นมสด, สตรอว์เบอร์รี่สด, ซอสสตรอว์เบอร์รี่, วิปครีม",
        },
        {
            "menu": "Rose Milk Tea",
            "price": 70,
            "meaning": "เสริมความรัก ความอ่อนโยน และบรรยากาศดี ๆ รอบตัว",
            "ingredients": "ชานม, ไซรัปกุหลาบ, นมสด, ฟองนม, กลิ่นดอกไม้เบา ๆ",
        },
        {
            "menu": "Sweetheart Cocoa",
            "price": 75,
            "meaning": "เสริมความอบอุ่น ความรัก และมิตรภาพที่จริงใจ",
            "ingredients": "โกโก้, นมสด, ซอสช็อกโกแลต, วิปครีม, มาร์ชเมลโลว์",
        },
        {
            "menu": "Peachy Milk",
            "price": 69,
            "meaning": "เสริมความสดใส ความน่าคุย และโอกาสดีด้านความสัมพันธ์",
            "ingredients": "นมสด, ไซรัปพีช, เยลลี่พีช, น้ำแข็ง, ฟองนม",
        },
    ],
    "วันเสาร์": [
        {
            "menu": "Dark Choco Shield",
            "price": 75,
            "meaning": "เสริมความหนักแน่น ความมั่นคง และป้องกันพลังลบ",
            "ingredients": "ดาร์กโกโก้, นมสด, ซอสช็อกโกแลตเข้ม, ช็อกโกแลตชิพ",
        },
        {
            "menu": "Black Cocoa",
            "price": 70,
            "meaning": "เสริมความแข็งแรงทางใจ และความอดทน",
            "ingredients": "แบล็กโกโก้, นมสด, น้ำแข็ง, ผงโกโก้โรยหน้า",
        },
        {
            "menu": "Midnight Milk Tea",
            "price": 75,
            "meaning": "เสริมความนิ่ง ความรอบคอบ และการตัดสินใจที่ดี",
            "ingredients": "ชาดำเข้ม, นมสด, ไข่มุก, ไซรัปบราวน์ชูการ์",
        },
        {
            "menu": "Charcoal Vanilla Milk",
            "price": 79,
            "meaning": "เสริมการปล่อยพลังลบ และเริ่มต้นใหม่อย่างสงบ",
            "ingredients": "นมสด, วานิลลา, ชาร์โคล, วิปครีม, คุกกี้ครัมเบิล",
        },
        {
            "menu": "Strong Heart Latte",
            "price": 75,
            "meaning": "เสริมกำลังใจ ความมั่นคง และความกล้าที่จะไปต่อ",
            "ingredients": "เอสเพรสโซ, นมสด, คาราเมล, ฟองนม, ผงโกโก้",
        },
    ],
    "วันอาทิตย์": [
        {
            "menu": "Sunny Orange Coffee",
            "price": 79,
            "meaning": "เสริมพลัง ความสดใส โอกาสใหม่ และความมั่นใจ",
            "ingredients": "อเมริกาโน่, น้ำส้ม, น้ำผึ้งเล็กน้อย, ส้มฝาน, น้ำแข็ง",
        },
        {
            "menu": "Orange Honey Tea",
            "price": 70,
            "meaning": "เสริมความสดชื่น โชคดี และความสบายใจ",
            "ingredients": "ชาดำ, น้ำส้ม, น้ำผึ้ง, ส้มฝาน, น้ำแข็ง",
        },
        {
            "menu": "Sunflower Latte",
            "price": 75,
            "meaning": "เสริมพลังบวก ความมั่นใจ และความโดดเด่น",
            "ingredients": "เอสเพรสโซ, นมสด, วานิลลา, คาราเมล, ฟองนม",
        },
        {
            "menu": "Bright Cocoa",
            "price": 70,
            "meaning": "เสริมความสุขเล็ก ๆ และพลังใจที่อบอุ่น",
            "ingredients": "โกโก้, นมสด, ซอสส้มเล็กน้อย, วิปครีม, ผงโกโก้",
        },
        {
            "menu": "Golden Vanilla Milk",
            "price": 69,
            "meaning": "เสริมโอกาสใหม่ ความสดใส และความอ่อนโยน",
            "ingredients": "นมสด, วานิลลา, คาราเมล, ไข่มุกสีทอง, น้ำแข็ง",
        },
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
    ("The Magician", "ขอให้วันนี้มีไอเดียใหม่ ๆ และใช้ความสามารถของตัวเองได้อย่างมั่นใจ 🪄"),
    ("Strength", "ขอให้วันนี้มีพลังใจ เข้มแข็ง และผ่านเรื่องยาก ๆ ได้อย่างนุ่มนวล 🦁"),
    ("Temperance", "ขอให้วันนี้ทุกอย่างสมดุล ใจเย็น และค่อย ๆ ดีขึ้นทีละนิด 🕊️"),
    ("The World", "ขอให้วันนี้ได้ปิดจบสิ่งสำคัญอย่างสวยงาม และมีความสำเร็จรออยู่ 🌍"),
    ("Ace of Pentacles", "ขอให้วันนี้มีโอกาสดีเรื่องงาน เงิน หรือสิ่งใหม่ที่มั่นคงเข้ามา 🍀"),
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

    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.78);
        border-radius: 18px;
        padding: 12px;
        border: 1px solid rgba(255, 220, 235, 0.9);
        box-shadow: 0 8px 20px rgba(145, 100, 80, 0.08);
    }

    .tarot-close-toggle {
        display: none;
    }

    .tarot-close-toggle:checked + .tarot-popup {
        display: none;
    }

    .tarot-popup {
        position: fixed;
        top: 54px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 999999;
        width: min(390px, calc(100vw - 24px));
        padding: 0;
        background: transparent;
        color: white;
        text-align: center;
        animation: tarotBounceTop 0.75s cubic-bezier(.18,.89,.32,1.28);
        pointer-events: auto;
    }

    @keyframes tarotBounceTop {
        0% {
            opacity: 0;
            transform: translate(-50%, -90px) scale(0.75);
        }
        65% {
            opacity: 1;
            transform: translate(-50%, 14px) scale(1.04);
        }
        100% {
            opacity: 1;
            transform: translate(-50%, 0) scale(1);
        }
    }

    .tarot-close-btn {
        position: absolute;
        top: -12px;
        right: 6px;
        width: 38px;
        height: 38px;
        border-radius: 999px;
        background: #fff8de;
        color: #3a214b;
        border: 2px solid #f7d98d;
        box-shadow: 0 10px 24px rgba(44, 20, 70, 0.28);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
        line-height: 1;
        font-weight: 900;
        cursor: pointer;
        z-index: 3;
    }

    .flip-wrap {
        display: flex;
        justify-content: center;
        margin-top: 0;
    }

    .flip-toggle {
        display: none;
    }

    .flip-card {
        width: 300px;
        height: 450px;
        perspective: 1200px;
        cursor: pointer;
        display: block;
        margin: 0 auto;
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
        border-radius: 30px;
        backface-visibility: hidden;
        box-shadow: 0 26px 60px rgba(44, 20, 70, 0.42);
        border: 3px solid rgba(255, 230, 170, 0.98);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 28px;
        box-sizing: border-box;
        overflow: hidden;
    }

    .flip-front {
        background:
            radial-gradient(circle at center, rgba(255,255,255,0.20), transparent 36%),
            linear-gradient(145deg, #5a3379, #241033 78%);
        color: #ffeab6;
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 0.5px;
        flex-direction: column;
        gap: 24px;
    }

    .tarot-brand {
        font-size: 24px;
        line-height: 1.45;
        font-weight: 900;
        text-shadow: 0 4px 18px rgba(255, 235, 180, 0.28);
    }

    .tarot-open-text {
        font-size: 22px;
        line-height: 1.45;
        font-weight: 900;
    }

    .tarot-front-hint {
        font-size: 14px;
        line-height: 1.45;
        opacity: 0.92;
        margin-top: 6px;
    }

    .flip-back {
        background:
            radial-gradient(circle at top, rgba(255, 255, 255, 0.70), transparent 36%),
            linear-gradient(145deg, #fff8de, #ffe2f1);
        color: #5c3d2e;
        transform: rotateY(180deg);
        flex-direction: column;
        font-size: 18px;
        line-height: 1.6;
        font-weight: 700;
    }

    .tarot-card-name {
        font-size: 27px;
        margin-bottom: 18px;
        color: #7b4b1f;
        font-weight: 900;
    }

    .tarot-blessing {
        font-size: 18px;
        line-height: 1.75;
    }

    .tap-hint {
        margin-top: 14px;
        font-size: 14px;
        color: #6c4d3c;
        background: rgba(255, 248, 222, 0.92);
        border: 1px solid #f7d98d;
        border-radius: 999px;
        padding: 8px 14px;
        display: inline-block;
        box-shadow: 0 10px 22px rgba(44, 20, 70, 0.14);
        font-weight: 800;
    }

    .order-summary-box {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid #ffdceb;
        border-radius: 18px;
        padding: 14px 16px;
        margin: 10px 0;
    }

    @media (max-width: 800px) {
        .menu-grid {
            grid-template-columns: 1fr;
        }
        .title {
            font-size: 31px;
        }
        .tarot-popup {
            top: 58px;
        }
        .flip-card {
            width: min(285px, calc(100vw - 46px));
            height: 420px;
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
            <div class="menu-desc">บอกวันเกิด แล้ว Demi จะสุ่มเมนูเสริมดวง พร้อมส่วนผสม และสุ่มใหม่ได้ถ้าไม่ชอบ</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="lucky-card">
        🔮 <b>ลูกเล่นเมนูเสริมดวง</b><br>
        บอกวันเกิด เช่น “เกิดวันศุกร์ อยากได้เมนูเสริมดวง”
        Demi จะสุ่มเมนูจากวันนั้นให้ พร้อมบอกส่วนผสม
        ถ้าไม่ชอบ พิมพ์ว่า “ไม่ชอบ ขอสุ่มใหม่” ได้เลยค่ะ
        และเมื่อสั่งสำเร็จ ไพ่ยิปซีจะเด้งขึ้นด้านบนหน้าจอ
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


def is_reroll_text(text: str) -> bool:
    reroll_words = [
        "ไม่ชอบ",
        "ไม่เอา",
        "ไม่ถูกใจ",
        "สุ่มใหม่",
        "ขอใหม่",
        "เปลี่ยนเมนู",
        "เมนูใหม่",
        "เอาใหม่",
        "ไม่โดน",
    ]
    return any(word in text for word in reroll_words)


def recommend_lucky_drink(day: str, avoid_menu: str | None = None) -> dict[str, Any]:
    items = LUCKY_DRINKS[day]
    used_map = st.session_state.setdefault("lucky_used_map", {})
    used = set(used_map.get(day, []))

    candidates = [item for item in items if item["menu"] not in used]
    if avoid_menu:
        candidates = [item for item in candidates if item["menu"] != avoid_menu]

    if not candidates:
        used_map[day] = []
        candidates = [item for item in items if item["menu"] != avoid_menu] or items

    item = random.choice(candidates)
    used_map.setdefault(day, []).append(item["menu"])
    return item


def list_lucky_drinks(day: str) -> str:
    items = LUCKY_DRINKS[day]
    lines = [f"เมนูเสริมดวงสำหรับคนเกิด{day} มี 5 เมนูค่ะ 🔮"]
    for idx, item in enumerate(items, start=1):
        lines.append(
            f"{idx}. {item['menu']} ราคา {item['price']} บาท\n"
            f"   ความหมาย: {item['meaning']}\n"
            f"   ส่วนผสม: {item['ingredients']}"
        )
    lines.append("\nถ้าอยากให้ Demi สุ่มให้ พิมพ์ว่า “เกิด" + day.replace("วัน", "") + " อยากได้เมนูเสริมดวง” ได้เลยค่ะ")
    return "\n".join(lines)


def find_lucky_item(menu_name: str) -> dict[str, Any] | None:
    for items in LUCKY_DRINKS.values():
        for item in items:
            if item["menu"] == menu_name:
                return item
    return None


def format_lucky_recommendation(day: str, item: dict[str, Any], is_reroll: bool = False) -> str:
    st.session_state["last_recommended_menu"] = item["menu"]
    st.session_state["last_lucky_day"] = day
    st.session_state["last_lucky_item"] = item

    prefix = "Demi สุ่มเมนูใหม่ให้แล้วค่ะ 🔄" if is_reroll else f"สำหรับคนเกิด{day} Demi สุ่มเมนูเสริมดวงให้แล้วค่ะ 🔮"

    return (
        f"{prefix}\n\n"
        f"เมนูที่ได้: {item['menu']}\n"
        f"ราคา: {item['price']} บาท\n"
        f"ความหมาย: {item['meaning']}\n"
        f"ส่วนผสม: {item['ingredients']}\n\n"
        f"ถ้าชอบเมนูนี้ พิมพ์ว่า “สั่งเมนูนี้ 1 แก้ว” ได้เลยค่ะ\n"
        f"ถ้ายังไม่ถูกใจ พิมพ์ว่า “ไม่ชอบ ขอสุ่มใหม่” แล้ว Demi จะสุ่มเมนูใหม่ของ{day}ให้ค่ะ"
    )


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
    close_id = f"close_{card_id}"
    return f"""
    <input type="checkbox" id="{close_id}" class="tarot-close-toggle">
    <div class="tarot-popup">
        <label for="{close_id}" class="tarot-close-btn">×</label>
        <div class="flip-wrap">
            <input type="checkbox" id="{card_id}" class="flip-toggle">
            <label for="{card_id}" class="flip-card">
                <div class="flip-inner">
                    <div class="flip-front">
                        <div class="tarot-brand">✦ MilkyMood<br>Tarot ✦</div>
                        <div class="tarot-open-text">แตะเพื่อเปิดไพ่</div>
                        <div class="tarot-front-hint">ไพ่ใบนี้มีคำอวยพรของคุณซ่อนอยู่</div>
                    </div>
                    <div class="flip-back">
                        <div class="tarot-card-name">{card_name}</div>
                        <div class="tarot-blessing">{blessing}</div>
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
    lucky_item = find_lucky_item(menu)

    detail_lines = [
        "### ✅ ระบบได้ทำการรับ Order เรียบร้อยแล้ว กรุณารอสักครู่ค่ะ 🥛",
        "",
        '<div class="order-summary-box">',
        "<b>🧾 รายการ</b><br>",
        f"เมนู: {menu}<br>",
        f"จำนวน: {quantity}<br>",
        f"ราคา: {price} บาท",
        "</div>",
        "",
        '<div class="order-summary-box">',
        "<b>💰 ยอดรวม</b><br>",
        f"{total} บาท",
        "</div>",
        "",
        '<div class="order-summary-box">',
        "<b>⏰ เวลารอ</b><br>",
        f"{wait_time}",
        "</div>",
    ]

    if lucky_item:
        detail_lines.extend(
            [
                "",
                '<div class="order-summary-box">',
                "<b>🥛 ส่วนผสม</b><br>",
                lucky_item["ingredients"],
                "</div>",
                "",
                '<div class="order-summary-box">',
                "<b>🔮 ความหมายเมนู</b><br>",
                lucky_item["meaning"],
                "</div>",
            ]
        )

    detail_lines.extend(
        [
            "",
            '<div class="order-summary-box">',
            "<b>📌 สถานะระบบ</b><br>",
            status_message,
            "</div>",
        ]
    )

    tarot_html = None

    if is_lucky:
        card, blessing = random_tarot()
        detail_lines.extend(
            [
                "",
                "🔮 ระบบสุ่มไพ่ยิปซีให้แล้วค่ะ ไพ่จะเด้งขึ้นด้านบนหน้าจอ แตะที่ไพ่เพื่อดูคำอวยพร",
            ]
        )
        tarot_html = tarot_popup_html(card, blessing)

    reply = "\n".join(detail_lines)
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

if "search_history" not in st.session_state:
    st.session_state.search_history = []

# ใช้ควบคุม auto-scroll: ให้เลื่อนลงเฉพาะตอนผู้ใช้ส่งข้อความใหม่เท่านั้น
# ไม่ให้เลื่อนลงเองตอนเปิดเว็บครั้งแรก โดยเฉพาะบนมือถือ
if "should_scroll_bottom" not in st.session_state:
    st.session_state.should_scroll_bottom = False

# =========================================================
# Sidebar: search/chat history
# =========================================================

with st.sidebar:
    st.markdown("## 🕘 ประวัติการค้นหา")
    st.caption("แสดงข้อความล่าสุดที่ลูกค้าพิมพ์ในแชต")

    if st.button("🧹 ล้างประวัติ", use_container_width=True):
        st.session_state.search_history = []
        st.rerun()

    if st.session_state.search_history:
        for i, item in enumerate(reversed(st.session_state.search_history[-12:]), start=1):
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.72);border:1px solid #ffdceb;
            border-radius:14px;padding:10px 12px;margin:8px 0;font-size:13px;
            color:#6c4d3c;line-height:1.45;">
                <b>{i}.</b> {item}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ยังไม่มีประวัติการค้นหา")

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)
        popup_html = st.session_state.tarot_popups.get(idx)
        if popup_html:
            st.markdown(popup_html, unsafe_allow_html=True)


# =========================================================
# Chat input
# =========================================================

if prompt := st.chat_input("ถามหรือสั่งเมนูได้เลย เช่น สั่งลาเต้น้ำผึ้ง 1 แก้ว / เกิดวันศุกร์อยากได้เมนูเสริมดวง"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.should_scroll_bottom = True

    if not st.session_state.search_history or st.session_state.search_history[-1] != prompt:
        st.session_state.search_history.append(prompt)
        st.session_state.search_history = st.session_state.search_history[-30:]

    with st.chat_message("user"):
        st.markdown(prompt, unsafe_allow_html=True)

    birth_day = find_birth_day(prompt)
    lucky_intent = is_lucky_intent(prompt)
    order_intent = is_order_text(prompt)
    list_request = is_list_request(prompt)
    reroll_intent = is_reroll_text(prompt)

    tarot_html = None

    if reroll_intent and st.session_state.get("last_lucky_day"):
        day = st.session_state["last_lucky_day"]
        avoid_menu = st.session_state.get("last_recommended_menu")
        item = recommend_lucky_drink(day, avoid_menu=avoid_menu)
        answer = format_lucky_recommendation(day, item, is_reroll=True)

    elif lucky_intent and list_request and birth_day:
        answer = list_lucky_drinks(birth_day)

    elif lucky_intent and not order_intent:
        if birth_day:
            item = recommend_lucky_drink(birth_day)
            answer = format_lucky_recommendation(birth_day, item)
        else:
            answer = (
                "อยากได้เมนูเสริมดวงได้เลยค่ะ 🔮\n"
                "รบกวนบอกวันเกิดก่อน เช่น เกิดวันศุกร์ หรือ เกิดวันจันทร์ "
                "แล้ว Demi จะสุ่มเมนูจากวันนั้นให้ พร้อมบอกส่วนผสมค่ะ"
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
                st.session_state["last_lucky_day"] = birth_day
                st.session_state["last_lucky_item"] = item

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
4. ถ้าถามเรื่องเมนูเสริมดวง ให้อธิบายว่ามี 5 เมนูต่อวัน สามารถสุ่มตามวันเกิดได้ และถ้าไม่ชอบสามารถสุ่มใหม่ได้
5. ถ้าพูดถึงเมนูเสริมดวง ให้บอกส่วนผสมของเมนูด้วยถ้ามีในข้อมูล
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
    assistant_index = len(st.session_state.messages) - 1

    if tarot_html:
        st.session_state.tarot_popups[assistant_index] = tarot_html

    with st.chat_message("assistant"):
        st.markdown(answer, unsafe_allow_html=True)
        if tarot_html:
            st.markdown(tarot_html, unsafe_allow_html=True)


# เลื่อนลงไปยังข้อความล่าสุดอัตโนมัติ เฉพาะหลังผู้ใช้ส่งข้อความใหม่
# แก้ปัญหาเปิดเว็บบนมือถือแล้วเด้งลงล่างสุดเอง
if st.session_state.get("should_scroll_bottom"):
    components.html(
        """
        <script>
        setTimeout(function() {
            const doc = window.parent.document;
            const streamlitDoc = doc.scrollingElement || doc.documentElement || doc.body;
            streamlitDoc.scrollTo({ top: streamlitDoc.scrollHeight, behavior: "smooth" });
        }, 350);
        </script>
        """,
        height=0,
    )
    st.session_state.should_scroll_bottom = False

