# app.py
from __future__ import annotations

import os
import random
import re
import math
from dataclasses import dataclass
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from google import genai

from rag_engine import RAGEngine

try:
    from agent_tools import TOOLS
except Exception:
    TOOLS = {}

load_dotenv()

st.set_page_config(
    page_title="TripMate Thailand AI",
    page_icon="🧭",
    layout="wide",
)

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
MODEL = os.getenv("GOOGLE_MODEL_NAME", "models/gemini-2.5-flash-lite")


@st.cache_resource
def load_rag() -> RAGEngine:
    return RAGEngine("knowledge/tripmate_kb.txt")


rag = load_rag()


DESTINATIONS: dict[str, dict[str, Any]] = {
    "ชลบุรี": {
        "type": ["ทะเล"],
        "crowd": "เยอะ",
        "ease": "สูง",
        "budget": "ประหยัด-กลาง",
        "highlights": ["บางแสน", "พัทยา", "เกาะล้าน", "เขาสามมุข"],
        "best_for": "ทริปสั้น ใกล้กรุงเทพฯ เดินทางง่าย เหมาะกับมือใหม่",
        "image": "images/sea_demo.png",
    },
    "ระยอง": {
        "type": ["ทะเล"],
        "crowd": "กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["เกาะเสม็ด", "หาดแม่รำพึง", "แหลมแม่พิมพ์", "สวนผลไม้"],
        "best_for": "คนอยากพักผ่อนริมทะเล ไม่ไกลมาก และคนไม่แน่นเท่าพัทยา",
        "image": "images/sea_demo.png",
    },
    "จันทบุรี": {
        "type": ["ทะเล", "ภูเขา", "น้ำตก"],
        "crowd": "กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["หาดเจ้าหลาว", "เนินนางพญา", "น้ำตกพลิ้ว", "ชุมชนริมน้ำ"],
        "best_for": "คนอยากได้ทะเล ธรรมชาติ ของกิน และเมืองเก่าในทริปเดียว",
        "image": "images/sea_demo.png",
    },
    "ประจวบคีรีขันธ์": {
        "type": ["ทะเล", "ภูเขา"],
        "crowd": "กลาง",
        "ease": "สูง",
        "budget": "กลาง",
        "highlights": ["หัวหิน", "ปราณบุรี", "สามร้อยยอด", "อ่าวมะนาว"],
        "best_for": "ครอบครัว คู่รัก และคนอยากได้ทะเลที่เดินทางสะดวก",
        "image": "images/sea_demo.png",
    },
    "ภูเก็ต": {
        "type": ["ทะเล"],
        "crowd": "เยอะ",
        "ease": "สูง",
        "budget": "กลาง-สูง",
        "highlights": ["ป่าตอง", "กะตะ", "กะรน", "แหลมพรหมเทพ", "เมืองเก่า"],
        "best_for": "คนอยากได้ความสะดวก กิจกรรมเยอะ ร้านอาหารและโรงแรมเยอะ",
        "image": "images/sea_demo.png",
    },
    "กระบี่": {
        "type": ["ทะเล", "ภูเขา"],
        "crowd": "กลาง-เยอะ",
        "ease": "กลาง",
        "budget": "กลาง-สูง",
        "highlights": ["อ่าวนาง", "ไร่เลย์", "เกาะพีพี", "ทะเลแหวก"],
        "best_for": "ทะเลสวย ภูเขาหินปูน กิจกรรมทางน้ำ และสายถ่ายรูป",
        "image": "images/sea_demo.png",
    },
    "ตราด": {
        "type": ["ทะเล"],
        "crowd": "กลาง",
        "ease": "กลาง",
        "budget": "กลาง-สูง",
        "highlights": ["เกาะช้าง", "เกาะกูด", "เกาะหมาก", "หาดทรายขาว"],
        "best_for": "ทะเลเกาะสวย เหมาะกับทริปพักผ่อนยาวและคนที่อยากได้บรรยากาศชิล",
        "image": "images/sea_demo.png",
    },
    "ชุมพร": {
        "type": ["ทะเล"],
        "crowd": "น้อย-กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["หาดทรายรี", "เกาะง่าม", "จุดดำน้ำ", "จุดชมวิวเขามัทรี"],
        "best_for": "คนอยากได้ทะเลเงียบกว่าจังหวัดยอดนิยม เหมาะกับสายดำน้ำและพักผ่อน",
        "image": "images/sea_demo.png",
    },
    "สุราษฎร์ธานี": {
        "type": ["ทะเล", "ภูเขา"],
        "crowd": "กลาง-เยอะ",
        "ease": "กลาง",
        "budget": "กลาง-สูง",
        "highlights": ["เกาะสมุย", "เกาะพะงัน", "เกาะเต่า", "เขื่อนเชี่ยวหลาน"],
        "best_for": "คนอยากได้ทั้งทะเลสวยและธรรมชาติแบบเขื่อนภูเขาน้ำในจังหวัดเดียว",
        "image": "images/sea_demo.png",
    },
    "พังงา": {
        "type": ["ทะเล", "ภูเขา"],
        "crowd": "กลาง",
        "ease": "กลาง",
        "budget": "กลาง-สูง",
        "highlights": ["อ่าวพังงา", "เขาตะปู", "เสม็ดนางชี", "เขาหลัก"],
        "best_for": "วิวทะเลและภูเขาหินปูนอลังการ เหมาะกับคนชอบธรรมชาติและจุดชมวิว",
        "image": "images/sea_demo.png",
    },
    "ตรัง": {
        "type": ["ทะเล"],
        "crowd": "น้อย-กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["เกาะมุก", "ถ้ำมรกต", "เกาะกระดาน", "หาดปากเมง"],
        "best_for": "ทะเลใต้ที่สวยและคนน้อยกว่าภูเก็ต เหมาะกับคนอยากพักผ่อนจริง ๆ",
        "image": "images/sea_demo.png",
    },
    "สตูล": {
        "type": ["ทะเล"],
        "crowd": "กลาง",
        "ease": "ต่ำ-กลาง",
        "budget": "กลาง-สูง",
        "highlights": ["เกาะหลีเป๊ะ", "อุทยานตะรุเตา", "เกาะไข่", "หาดพัทยาหลี่เป๊ะ"],
        "best_for": "ทะเลสวยมาก เหมาะกับทริปหลายวัน แต่ต้องเผื่อเวลาและงบเดินทางมากขึ้น",
        "image": "images/sea_demo.png",
    },
    "เชียงใหม่": {
        "type": ["ภูเขา"],
        "crowd": "เยอะ",
        "ease": "สูง",
        "budget": "กลาง",
        "highlights": ["ดอยอินทนนท์", "ดอยสุเทพ", "ม่อนแจ่ม", "แม่กำปอง", "นิมมาน"],
        "best_for": "มือใหม่สายภูเขา คาเฟ่เยอะ เดินทางสะดวก ที่เที่ยวหลากหลาย",
        "image": "images/mountain_demo.png",
    },
    "น่าน": {
        "type": ["ภูเขา"],
        "crowd": "น้อย-กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["ดอยเสมอดาว", "บ่อเกลือ", "สะปัน", "วัดภูมินทร์"],
        "best_for": "คนอยากเที่ยวช้า ๆ สงบ วิวภูเขา วัฒนธรรม และคนน้อยกว่าเชียงใหม่",
        "image": "images/mountain_demo.png",
    },
    "เพชรบูรณ์": {
        "type": ["ภูเขา"],
        "crowd": "กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["เขาค้อ", "ภูทับเบิก", "วัดผาซ่อนแก้ว"],
        "best_for": "วิวหมอก อากาศเย็น เหมาะกับคนมีรถส่วนตัว",
        "image": "images/mountain_demo.png",
    },
    "เลย": {
        "type": ["ภูเขา"],
        "crowd": "กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["ภูกระดึง", "ภูเรือ", "เชียงคาน"],
        "best_for": "สายภูเขา อากาศเย็น เดินป่า และเมืองริมโขง",
        "image": "images/mountain_demo.png",
    },
    "กาญจนบุรี": {
        "type": ["ภูเขา", "น้ำตก"],
        "crowd": "กลาง",
        "ease": "สูง",
        "budget": "ประหยัด-กลาง",
        "highlights": ["น้ำตกเอราวัณ", "สังขละบุรี", "เขื่อนศรีนครินทร์", "ทางรถไฟสายมรณะ"],
        "best_for": "ธรรมชาติ น้ำตก ภูเขา และเดินทางจากกรุงเทพฯ ได้ไม่ยาก",
        "image": "images/mountain_demo.png",
    },
    "นครนายก": {
        "type": ["ภูเขา", "น้ำตก"],
        "crowd": "กลาง",
        "ease": "สูง",
        "budget": "ประหยัด",
        "highlights": ["เขื่อนขุนด่าน", "น้ำตกสาริกา", "วังตะไคร้"],
        "best_for": "ทริปสั้นใกล้กรุงเทพฯ งบน้อย เหมาะกับวันเดียวหรือ 2 วัน 1 คืน",
        "image": "images/mountain_demo.png",
    },
    "เชียงราย": {
        "type": ["ภูเขา"],
        "crowd": "กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["ภูชี้ฟ้า", "ดอยแม่สลอง", "สิงห์ปาร์ค", "วัดร่องขุ่น"],
        "best_for": "สายภูเขา วัฒนธรรม และอากาศเย็น เหมาะกับทริปเหนือที่คนไม่แน่นเท่าเชียงใหม่",
        "image": "images/mountain_demo.png",
    },
    "แม่ฮ่องสอน": {
        "type": ["ภูเขา"],
        "crowd": "น้อย-กลาง",
        "ease": "ต่ำ-กลาง",
        "budget": "กลาง",
        "highlights": ["ปาย", "บ้านรักไทย", "ปางอุ๋ง", "สะพานซูตองเป้"],
        "best_for": "คนอยากได้ธรรมชาติ ความสงบ วิวภูเขา และบรรยากาศพักใจ แต่ควรเผื่อเวลาเดินทาง",
        "image": "images/mountain_demo.png",
    },
    "ตาก": {
        "type": ["ภูเขา", "น้ำตก"],
        "crowd": "น้อย-กลาง",
        "ease": "ต่ำ-กลาง",
        "budget": "กลาง",
        "highlights": ["ดอยมูเซอ", "น้ำตกทีลอซู", "อุ้มผาง", "เขื่อนภูมิพล"],
        "best_for": "สายธรรมชาติจริงจัง น้ำตกใหญ่ ภูเขา และทริปผจญภัยที่ต้องวางแผนดี",
        "image": "images/mountain_demo.png",
    },
    "อุตรดิตถ์": {
        "type": ["ภูเขา"],
        "crowd": "น้อย",
        "ease": "กลาง",
        "budget": "ประหยัด-กลาง",
        "highlights": ["ภูสอยดาว", "เขื่อนสิริกิติ์", "ลับแล", "น้ำตกแม่พูล"],
        "best_for": "คนอยากได้ภูเขา คนไม่เยอะ และบรรยากาศเมืองรองที่ค่าใช้จ่ายไม่แรงมาก",
        "image": "images/mountain_demo.png",
    },
    "พิษณุโลก": {
        "type": ["ภูเขา", "น้ำตก"],
        "crowd": "น้อย-กลาง",
        "ease": "กลาง",
        "budget": "กลาง",
        "highlights": ["ภูหินร่องกล้า", "น้ำตกแก่งซอง", "ล่องแก่งลำน้ำเข็ก", "วัดพระศรีรัตนมหาธาตุ"],
        "best_for": "สายภูเขา น้ำตก ประวัติศาสตร์ และกิจกรรมล่องแก่งตามฤดูกาล",
        "image": "images/mountain_demo.png",
    },
}

STYLE_NOTES = {
    "ประหยัด": "เน้นควบคุมงบ เลือกที่พักราคาดี อาหารท้องถิ่น และสถานที่ที่ค่าเข้าไม่สูง",
    "สมดุล": "เที่ยวครบพอดี ไม่อัดแน่นเกินไป ที่พักสะดวกและยังคุมงบได้",
    "สบาย": "เน้นความสะดวก ที่พักดี เดินทางไม่เร่ง และมีเวลาพักผ่อน",
}
THAI_PROVINCE_COORDS: dict[str, tuple[float, float]] = {
    "กรุงเทพมหานคร": (13.7563, 100.5018),
    "กระบี่": (8.0863, 98.9063),
    "กาญจนบุรี": (14.0228, 99.5328),
    "กาฬสินธุ์": (16.4314, 103.5059),
    "กำแพงเพชร": (16.4828, 99.5220),
    "ขอนแก่น": (16.4419, 102.8350),
    "จันทบุรี": (12.6113, 102.1039),
    "ฉะเชิงเทรา": (13.6904, 101.0779),
    "ชลบุรี": (13.3611, 100.9847),
    "ชัยนาท": (15.1852, 100.1251),
    "ชัยภูมิ": (15.8068, 102.0315),
    "ชุมพร": (10.4930, 99.1800),
    "เชียงราย": (19.9105, 99.8406),
    "เชียงใหม่": (18.7883, 98.9853),
    "ตรัง": (7.5594, 99.6114),
    "ตราด": (12.2428, 102.5175),
    "ตาก": (16.8839, 99.1258),
    "นครนายก": (14.2069, 101.2131),
    "นครปฐม": (13.8199, 100.0622),
    "นครพนม": (17.3920, 104.7696),
    "นครราชสีมา": (14.9799, 102.0977),
    "นครศรีธรรมราช": (8.4304, 99.9631),
    "นครสวรรค์": (15.7047, 100.1372),
    "นนทบุรี": (13.8621, 100.5144),
    "นราธิวาส": (6.4255, 101.8253),
    "น่าน": (18.7756, 100.7730),
    "บึงกาฬ": (18.3609, 103.6464),
    "บุรีรัมย์": (14.9930, 103.1029),
    "ปทุมธานี": (14.0208, 100.5250),
    "ประจวบคีรีขันธ์": (11.8124, 99.7974),
    "ปราจีนบุรี": (14.0509, 101.3727),
    "ปัตตานี": (6.8695, 101.2501),
    "พระนครศรีอยุธยา": (14.3692, 100.5877),
    "พะเยา": (19.1665, 99.9019),
    "พังงา": (8.4501, 98.5255),
    "พัทลุง": (7.6167, 100.0740),
    "พิจิตร": (16.4429, 100.3488),
    "พิษณุโลก": (16.8211, 100.2659),
    "เพชรบุรี": (13.1112, 99.9397),
    "เพชรบูรณ์": (16.4190, 101.1606),
    "แพร่": (18.1446, 100.1403),
    "ภูเก็ต": (7.8804, 98.3923),
    "มหาสารคาม": (16.1851, 103.3026),
    "มุกดาหาร": (16.5453, 104.7235),
    "แม่ฮ่องสอน": (19.3020, 97.9654),
    "ยโสธร": (15.7926, 104.1453),
    "ยะลา": (6.5411, 101.2804),
    "ร้อยเอ็ด": (16.0538, 103.6520),
    "ระนอง": (9.9529, 98.6085),
    "ระยอง": (12.6814, 101.2816),
    "ราชบุรี": (13.5283, 99.8134),
    "ลพบุรี": (14.7995, 100.6534),
    "ลำปาง": (18.2888, 99.4909),
    "ลำพูน": (18.5745, 99.0087),
    "เลย": (17.4860, 101.7223),
    "ศรีสะเกษ": (15.1186, 104.3220),
    "สกลนคร": (17.1546, 104.1348),
    "สงขลา": (7.1898, 100.5951),
    "สตูล": (6.6238, 100.0674),
    "สมุทรปราการ": (13.5991, 100.5998),
    "สมุทรสงคราม": (13.4098, 100.0023),
    "สมุทรสาคร": (13.5475, 100.2744),
    "สระแก้ว": (13.8240, 102.0646),
    "สระบุรี": (14.5289, 100.9101),
    "สิงห์บุรี": (14.8936, 100.3967),
    "สุโขทัย": (17.0056, 99.8264),
    "สุพรรณบุรี": (14.4745, 100.1177),
    "สุราษฎร์ธานี": (9.1382, 99.3215),
    "สุรินทร์": (14.8818, 103.4936),
    "หนองคาย": (17.8783, 102.7413),
    "หนองบัวลำภู": (17.2218, 102.4260),
    "อ่างทอง": (14.5896, 100.4551),
    "อำนาจเจริญ": (15.8657, 104.6258),
    "อุดรธานี": (17.4138, 102.7872),
    "อุตรดิตถ์": (17.6200, 100.0993),
    "อุทัยธานี": (15.3835, 100.0246),
    "อุบลราชธานี": (15.2448, 104.8473),
}


@dataclass
class TripRequest:
    theme: str
    province: str
    origin_province: str
    people: int
    days: int
    budget: int
    transport: str
    crowd: str
    style: str
    extra: str
    

def money(value: float) -> str:
    return f"{value:,.0f} บาท"

def estimate_trip_distance(origin: str, destination: str) -> dict[str, float | str]:
    """
    คำนวณระยะทางโดยประมาณจากพิกัดกลางจังหวัด
    - straight_km = ระยะเส้นตรง
    - road_km = ประมาณระยะทางถนน โดยคูณ 1.25
    """

    if origin not in THAI_PROVINCE_COORDS or destination not in THAI_PROVINCE_COORDS:
        return {
            "origin": origin,
            "destination": destination,
            "straight_km": 0,
            "road_km": 0,
            "note": "ไม่มีข้อมูลพิกัดสำหรับคำนวณระยะทาง",
        }

    import math

    lat1, lon1 = THAI_PROVINCE_COORDS[origin]
    lat2, lon2 = THAI_PROVINCE_COORDS[destination]

    radius_km = 6371

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    straight_km = radius_km * c
    road_km = straight_km * 1.25

    return {
        "origin": origin,
        "destination": destination,
        "straight_km": round(straight_km, 1),
        "road_km": round(road_km, 1),
        "note": "เป็นระยะทางโดยประมาณจากพิกัดกลางจังหวัด ไม่ใช่ระยะทาง real-time",
    }


def recommend_destinations(req: TripRequest) -> list[str]:
    candidates = []
    for province, data in DESTINATIONS.items():
        if req.theme != "ยังไม่แน่ใจ" and req.theme not in data["type"]:
            continue
        score = 0
        if req.transport == "ไม่มีรถส่วนตัว" and data["ease"] == "สูง":
            score += 3
        if req.crowd == "ไม่อยากเจอคนเยอะ" and "น้อย" in data["crowd"]:
            score += 3
        if req.crowd == "รับได้ถ้าคนเยอะ" and data["crowd"] in ["เยอะ", "กลาง-เยอะ"]:
            score += 1
        if req.style == "ประหยัด" and "ประหยัด" in data["budget"]:
            score += 3
        if req.style == "สบาย" and data["ease"] == "สูง":
            score += 2
        if req.province and req.province in province:
            score += 5
        candidates.append((score, province))

    if not candidates:
        candidates = [(1, p) for p in DESTINATIONS]

    candidates.sort(reverse=True)
    return [p for _, p in candidates[:3]]


def estimate_budget(req: TripRequest) -> dict[str, float]:
    total = max(req.budget, 0)
    if total <= 0:
        total = req.people * req.days * 1500

    transport_ratio = 0.22 if req.transport == "ไม่มีรถส่วนตัว" else 0.18
    hotel_ratio = 0.32
    food_ratio = 0.24
    activity_ratio = 0.12
    reserve_ratio = 0.10

    return {
        "เดินทาง": total * transport_ratio,
        "ที่พัก": total * hotel_ratio,
        "อาหาร": total * food_ratio,
        "กิจกรรม/ค่าเข้า": total * activity_ratio,
        "เงินสำรอง": total * reserve_ratio,
    }


def match_score(req: TripRequest, province: str) -> tuple[float, list[str]]:
    data = DESTINATIONS[province]
    score = 6.0
    reasons = []

    if req.theme in data["type"] or req.theme == "ยังไม่แน่ใจ":
        score += 1.0
        reasons.append("ตรงกับแนวเที่ยวที่เลือก")
    if req.transport == "ไม่มีรถส่วนตัว" and data["ease"] == "สูง":
        score += 1.0
        reasons.append("เดินทางค่อนข้างสะดวกสำหรับคนไม่มีรถ")
    if req.crowd == "ไม่อยากเจอคนเยอะ" and "น้อย" in data["crowd"]:
        score += 1.0
        reasons.append("เหมาะกับคนที่ไม่อยากเจอคนเยอะ")
    if req.style == "ประหยัด" and "ประหยัด" in data["budget"]:
        score += 1.0
        reasons.append("ควบคุมงบได้ง่าย")
    if req.budget >= req.people * req.days * 1500:
        score += 0.7
        reasons.append("งบประมาณพอวางแผนได้ค่อนข้างสบาย")
    else:
        reasons.append("งบค่อนข้างจำกัด ควรลดค่าที่พักหรือกิจกรรมเสียเงิน")

    return min(score, 10), reasons


def build_fallback_plan(req: TripRequest, province: str) -> str:
    data = DESTINATIONS[province]
    budget = estimate_budget(req)
    score, reasons = match_score(req, province)
    nights = max(req.days - 1, 0)
    distance = estimate_trip_distance(req.origin_province, province)

    lines = [
    f"## 🧭 แพลนแนะนำ: {province}",
    f"**ต้นทาง:** {req.origin_province} → **ปลายทาง:** {province}",
    f"**ระยะทางโดยประมาณ:** {distance['road_km']} กม. ทางถนน / {distance['straight_km']} กม. เส้นตรง",
    f"**หมายเหตุระยะทาง:** {distance['note']}",
    f"**Trip Match Score:** {score:.1f}/10",
    "",
    "**เหตุผลที่เหมาะ:**",
    ]
    lines += [f"- {r}" for r in reasons]
    lines += [
        "",
        f"**จุดเด่น:** {data['best_for']}",
        f"**ไฮไลท์:** {', '.join(data['highlights'])}",
        f"**จำนวนคน:** {req.people} คน | **จำนวนวัน:** {req.days} วัน {nights} คืน | **งบรวม:** {money(req.budget)}",
        "",
        "### 💰 แบ่งงบประมาณโดยประมาณ",
    ]
    for k, v in budget.items():
        lines.append(f"- {k}: {money(v)}")

    lines += [
        "",
        "### 🏨 ที่พักที่เหมาะ",
        "- ถ้างบประหยัด: โฮสเทล เกสต์เฮาส์ หรือโรงแรมขนาดเล็กใกล้จุดเดินทางหลัก",
        "- ถ้างบสมดุล: โรงแรม 2–3 ดาว ใกล้สถานที่เที่ยวหรือจุดขึ้นรถ",
        "- ถ้าอยากพักสบาย: รีสอร์ตติดทะเล/วิวภูเขา หรือที่พักใกล้จุดชมวิว",
        "",
        "### 🚗 แผนเดินทางไป",
        "- ออกเดินทางช่วงเช้า ประมาณ 06:00–08:00 น. เพื่อให้มีเวลาเที่ยววันแรก",
        f"- รูปแบบเดินทาง: {req.transport}",
        "- ถึงแล้วให้เริ่มจากจุดเที่ยวหลักที่ใกล้ที่สุดก่อน แล้วค่อยเช็กอิน",
    ]

    for day in range(1, req.days + 1):
        if day == 1:
            lines += [
                "",
                f"### Day {day}",
                f"- เช้า: เดินทางไป {province}",
                f"- กลางวัน: กินอาหารท้องถิ่นหรือร้านใกล้จุดแรก",
                f"- บ่าย: เที่ยว {data['highlights'][0]}",
                "- เย็น: เช็กอินที่พัก เดินเล่นหรือพักผ่อน",
            ]
        elif day == req.days:
            lines += [
                "",
                f"### Day {day} / วันกลับ",
                f"- เช้า: เที่ยวจุดเบา ๆ เช่น {data['highlights'][-1]} หรือคาเฟ่ใกล้ที่พัก",
                "- กลางวัน: กินข้าว ซื้อของฝาก",
                "- บ่าย: เริ่มเดินทางกลับ ไม่ควรออกช้าเกินไป",
            ]
        else:
            lines += [
                "",
                f"### Day {day}",
                f"- เช้า: เที่ยว {data['highlights'][1] if len(data['highlights']) > 1 else data['highlights'][0]}",
                "- กลางวัน: พักกินข้าวใกล้สถานที่เที่ยว",
                f"- บ่าย: เที่ยว {data['highlights'][2] if len(data['highlights']) > 2 else data['highlights'][0]}",
                "- เย็น: กลับที่พักหรือเดินเล่นย่านใกล้เคียง",
            ]

    lines += [
        "",
        "### 🛟 แผนสำรองถ้าฝนตก",
        "- เปลี่ยนจากชายหาด/จุดชมวิวกลางแจ้ง เป็นคาเฟ่ ร้านอาหารท้องถิ่น ตลาด พิพิธภัณฑ์ หรือย่านเมืองเก่า",
        "",
        "### ✅ สรุป",
        f"จากงบ จำนวนคน และสไตล์แบบ{req.style} แนะนำให้เลือก {province} เพราะ{data['best_for']} แต่ควรตรวจสอบราคาที่พักและเวลาเปิด-ปิดจริงก่อนเดินทาง",
    ]

    return "\n".join(lines)


def ask_gemini(req: TripRequest, province: str) -> str:
    context_chunks = rag.search(
        f"{req.theme} {province} {req.budget} บาท {req.people} คน {req.days} วัน {req.transport} {req.crowd} {req.style}",
        top_k=5,
    )
    context = "\n---\n".join(context_chunks)
    full_prompt = f"""
คุณคือ Matey ผู้ช่วย AI ของ TripMate Thailand AI
หน้าที่คือวางแผนเที่ยวก่อนการจองจริง โดยเน้นภูเขาและทะเลในประเทศไทย

ข้อมูลจากฐานความรู้:
{context}

ข้อมูลผู้ใช้:
- แนวเที่ยว: {req.theme}
- จังหวัดที่สนใจ: {req.province or 'ยังไม่ระบุ'}
- จังหวัดที่ระบบเลือก: {province}
- จำนวนคน: {req.people}
- จำนวนวัน: {req.days}
- งบรวม: {req.budget} บาท
- การเดินทาง: {req.transport}
- ความหนาแน่นของผู้คน: {req.crowd}
- สไตล์งบ: {req.style}
- รายละเอียดเพิ่ม: {req.extra or '-'}

ให้ตอบเป็นภาษาไทยในรูปแบบนี้:
1. สรุปจังหวัดที่แนะนำและเหตุผล
2. Trip Match Score /10 พร้อมเหตุผล
3. ค่าใช้จ่ายโดยประมาณ แยก เดินทาง ที่พัก อาหาร กิจกรรม เงินสำรอง
4. แนะนำประเภทที่พักใกล้แหล่งเที่ยว
5. แผนเดินทางไป
6. ตารางแพลนเที่ยวรายวันแบบ เช้า กลางวัน บ่าย เย็น
7. แผนเดินทางกลับ
8. แผนสำรองถ้าฝนตก
9. สรุปว่าคุ้มไหมและควรปรับอะไรถ้างบไม่พอ

ห้ามอ้างว่าราคาที่พักหรือเวลาเปิดปิดเป็นข้อมูล real-time ให้ย้ำว่าเป็นการประเมินเบื้องต้น
"""
    if not client:
        return build_fallback_plan(req, province)
    try:
        response = client.models.generate_content(model=MODEL, contents=full_prompt)
        return response.text
    except Exception:
        return build_fallback_plan(req, province)


def log_trip_if_possible(req: TripRequest, province: str, estimate_total: int) -> str:
    if "log_trip_interest" not in TOOLS:
        return "โหมดตัวอย่าง: ยังไม่ได้เชื่อม tool บันทึกแพลนจริงใน app.py"
    try:
        result = TOOLS["log_trip_interest"](
            destination=province,
            people=req.people,
            budget=req.budget,
            trip_style=req.style,
            trip_type=req.theme,
            days=req.days,
            total_estimate=estimate_total,
        )
        sheet = "บันทึก Google Sheet แล้ว" if result.get("sheet_uploaded") else "ยังบันทึก Google Sheet ไม่สำเร็จ"
        telegram = "แจ้ง Telegram แล้ว" if result.get("telegram_sent") else "ยังแจ้ง Telegram ไม่สำเร็จ"
        return f"{sheet} และ {telegram}"
    except Exception as e:
        return f"ยังบันทึกจริงไม่สำเร็จ: {e}"


def render_destination_card(province: str) -> None:
    data = DESTINATIONS[province]
    img = data.get("image")
    with st.container(border=True):
        cols = st.columns([1, 2])
        with cols[0]:
            if img and os.path.exists(img):
                st.image(img, use_container_width=True)
            else:
                st.markdown("### 🏝️🏔️")
        with cols[1]:
            st.markdown(f"### {province}")
            st.write(data["best_for"])
            st.caption(f"แนว: {', '.join(data['type'])} | คน: {data['crowd']} | ความสะดวก: {data['ease']} | งบ: {data['budget']}")
            st.write("**ไฮไลท์:** " + ", ".join(data["highlights"]))


def compare_destinations(a: str, b: str, req_text: str = "") -> str:
    da, db = DESTINATIONS[a], DESTINATIONS[b]

    return f"""
<div class="compare-result-card">
  <div class="compare-title">
    <div class="compare-title-icon">⚖️</div>
    <div class="compare-title-text">
      <h2>เปรียบเทียบ {a} vs {b}</h2>
      <p>สรุปจุดเด่น ความสะดวก ผู้คน งบประมาณ และไฮไลท์ของแต่ละจังหวัด</p>
    </div>
  </div>

  <div class="compare-table-wrap">
    <table class="compare-table">
      <thead>
        <tr>
          <th>หัวข้อ</th>
          <th>📍 {a}</th>
          <th>📍 {b}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>🏷️ แนวเที่ยว</td>
          <td>{", ".join(da["type"])}</td>
          <td>{", ".join(db["type"])}</td>
        </tr>
        <tr>
          <td>✨ จุดเด่น</td>
          <td>{da["best_for"]}</td>
          <td>{db["best_for"]}</td>
        </tr>
        <tr>
          <td>👥 ผู้คน</td>
          <td>{da["crowd"]}</td>
          <td>{db["crowd"]}</td>
        </tr>
        <tr>
          <td>🚗 ความสะดวก</td>
          <td>{da["ease"]}</td>
          <td>{db["ease"]}</td>
        </tr>
        <tr>
          <td>💰 งบประมาณ</td>
          <td>{da["budget"]}</td>
          <td>{db["budget"]}</td>
        </tr>
        <tr>
          <td>📌 ไฮไลท์</td>
          <td>{", ".join(da["highlights"])}</td>
          <td>{", ".join(db["highlights"])}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="compare-summary-box">
    <h3>✅ สรุปคำแนะนำ</h3>
    <ul>
      <li>ถ้าเน้นความสะดวก ให้เลือกจังหวัดที่มีระดับความสะดวกสูงกว่า</li>
      <li>ถ้าไม่อยากเจอคนเยอะ ให้เลือกจังหวัดที่มีระดับผู้คนน้อยกว่า</li>
      <li>ถ้างบจำกัด ให้เลือกจังหวัดที่ควบคุมค่าเดินทางและค่าที่พักได้ง่ายกว่า</li>
    </ul>
    <div class="compare-user-note">
      <b>เงื่อนไขเพิ่มเติม:</b> {req_text or "ยังไม่มีเงื่อนไขเพิ่มเติม"}
    </div>
  </div>
</div>
"""

def normalize_theme_filter(theme: str) -> str:
    """ใช้สำหรับกรองจังหวัดใน dropdown และหน้าไฮไลท์ให้ตรงกัน"""
    if theme in ["ทั้งหมด", "ยังไม่แน่ใจ", ""]:
        return "ทั้งหมด"
    return theme


def get_destinations_by_theme(theme: str) -> list[str]:
    """คืนรายชื่อจังหวัดตามแนวเที่ยวที่เลือก: ทั้งหมด / ทะเล / ภูเขา"""
    normalized_theme = normalize_theme_filter(theme)

    if normalized_theme == "ทั้งหมด":
        return sorted(DESTINATIONS.keys())

    return sorted(
        province
        for province, data in DESTINATIONS.items()
        if normalized_theme in data["type"]
    )


def is_matching_theme(province: str, theme: str) -> bool:
    return province in get_destinations_by_theme(theme)


def get_province_options(theme: str) -> list[str]:
    """ตัวเลือกในช่อง 'จังหวัดที่สนใจ' ของหน้าวางแพลนเที่ยว"""
    return ["ยังไม่ระบุ"] + get_destinations_by_theme(theme)


def get_filtered_destinations(filter_type: str) -> list[str]:
    """ตัวเลือกสำหรับหน้าไฮไลท์จังหวัด/เปรียบเทียบ ให้มีตัวกรองของตัวเอง"""
    return get_destinations_by_theme(filter_type)




def is_travel_related_question(question: str) -> bool:
    """
    ตรวจว่าคำถามเกี่ยวกับการท่องเที่ยวหรือไม่
    ถ้าไม่เกี่ยว ให้ตอบปฏิเสธแบบสุภาพและชวนกลับเข้าเรื่องท่องเที่ยว
    """
    q = question.lower().strip()

    travel_keywords = [
        "เที่ยว", "ท่องเที่ยว", "ทริป", "แพลน", "เดินทาง", "ไปไหนดี",
        "ทะเล", "ภูเขา", "น้ำตก", "คาเฟ่", "ที่พัก", "โรงแรม", "รีสอร์ต",
        "งบ", "ค่าใช้จ่าย", "จังหวัด", "ระยะทาง", "รถ", "ไม่มีรถ",
        "รถไฟ", "รถตู้", "เครื่องบิน", "วันกลับ", "ฝนตก", "แผนสำรอง",
        "คนเยอะ", "คนน้อย", "เปรียบเทียบ", "ไฮไลท์",
        "ชลบุรี", "ระยอง", "จันทบุรี", "ตราด", "ชุมพร", "ตรัง", "สตูล",
        "ภูเก็ต", "กระบี่", "พังงา", "เชียงใหม่", "น่าน", "เชียงราย",
        "แม่ฮ่องสอน", "เพชรบูรณ์", "กาญจนบุรี", "นครนายก", "เลย",
        "ตาก", "ประจวบ", "สุราษฎร์", "พัทยา", "บางแสน", "เกาะล้าน",
        "เกาะเสม็ด", "เกาะช้าง", "เกาะกูด", "หัวหิน", "เขาค้อ", "ดอย",
    ]

    return any(keyword in q for keyword in travel_keywords)


def is_ambiguous_travel_question(question: str) -> bool:
    """
    ตรวจคำถามที่เกี่ยวกับเที่ยว แต่ข้อมูลยังไม่ชัดพอสำหรับวางแผน
    """
    q = question.strip().lower()

    ambiguous_phrases = [
        "ไปไหนดี",
        "เที่ยวไหนดี",
        "แนะนำหน่อย",
        "จัดทริปให้หน่อย",
        "อยากเที่ยว",
        "ช่วยวางแผนให้หน่อย",
        "ไปทะเล",
        "ไปภูเขา",
        "ทะเล",
        "ภูเขา",
    ]

    if q in ambiguous_phrases:
        return True

    if len(q) <= 15 and is_travel_related_question(q):
        return True

    return False


def rewrite_ambiguous_question(question: str) -> str:
    """
    เรียบเรียงคำถามกำกวมให้ผู้ใช้เข้าใจว่าควรระบุข้อมูลอะไรเพิ่ม
    """
    return f"""
ผมเข้าใจว่าคุณต้องการถามเรื่องท่องเที่ยวจากข้อความนี้:

**"{question}"**

แต่ข้อมูลยังไม่ครบพอที่จะวางแพลนให้แม่นยำครับ  
ลองพิมพ์ใหม่ให้ชัดขึ้นประมาณนี้ได้เลย:

**ตัวอย่างคำถามที่ชัดเจนกว่า**
- มีงบ 3,000 บาท ไป 2 คน ไม่มีรถส่วนตัว อยากเที่ยวทะเลที่คนไม่เยอะ
- อยากไปภูเขา 3 วัน 2 คืน งบ 6,000 บาท เริ่มเดินทางจากกรุงเทพมหานคร
- มีรถส่วนตัว อยากเที่ยวธรรมชาติแบบไม่เร่ง ไป 2 วัน ควรไปจังหวัดไหนดี

**ข้อมูลที่แนะนำให้ระบุ**
1. อยากไปทะเลหรือภูเขา  
2. งบประมาณ  
3. จำนวนคน  
4. จำนวนวัน  
5. จังหวัดต้นทาง  
6. มีรถส่วนตัวหรือไม่มีรถ  
7. อยากเจอคนเยอะหรืออยากได้ที่สงบ
"""


def polite_off_topic_reply(question: str) -> str:
    """
    ตอบปฏิเสธคำถามนอกเรื่องแบบสุภาพ และพากลับเข้าเรื่องท่องเที่ยว
    """
    return f"""
ขอโทษครับ Matey ถูกออกแบบมาเพื่อช่วยเรื่อง **การวางแผนท่องเที่ยวในประเทศไทย** เป็นหลัก  
คำถามนี้อาจอยู่นอกขอบเขตของระบบ:

**"{question}"**

แต่ถ้าคุณอยากวางแผนเที่ยว ผมช่วยได้ เช่น:
- มีงบ 5,000 บาท ไปทะเล 2 คน ไม่มีรถส่วนตัว ควรไปไหนดี
- อยากเที่ยวภูเขา 3 วัน 2 คืน เริ่มจากกรุงเทพมหานคร แนะนำจังหวัดไหน
- เปรียบเทียบชลบุรีกับระยองให้หน่อย
- ถ้าฝนตกควรมีแผนสำรองยังไง

ลองถามใหม่เป็นเรื่องท่องเที่ยวได้เลยครับ 🧭
"""


def render_trip_overview(req: TripRequest, province: str) -> None:
    data = DESTINATIONS[province]
    score, reasons = match_score(req, province)
    nights = max(req.days - 1, 0)
    distance = estimate_trip_distance(req.origin_province, province)
    tags = "".join([f"<span class='mini-tag'>{tag}</span>" for tag in data["type"]])
    reason_html = "".join([f"<li>{reason}</li>" for reason in reasons[:4]])
    st.markdown(f"""
<div class="plan-hero-card">
  <div class="plan-hero-left">
    <div class="plan-eyebrow">🧭 แพลนเที่ยวของคุณ</div>
    <h2>แพลนแนะนำ: {province}</h2>
    <div>{tags}</div>
    <p>{data['best_for']}</p>
    <div class="distance-chip">
        🚗 {req.origin_province} → {province} ประมาณ {distance['road_km']} กม.
    </div>
    <ul>{reason_html}</ul>
  </div>
  <div class="plan-score-box">
    <div class="score-number">{score:.1f}</div>
    <div class="score-label">Trip Match Score / 10</div>
    <div class="score-sub">เหมาะกับเงื่อนไขที่เลือก</div>
  </div>
</div>
""", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"<div class='stat-card'>👥<span>จำนวนคน</span><b>{req.people} คน</b></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='stat-card'>📅<span>ระยะเวลา</span><b>{req.days} วัน {nights} คืน</b></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='stat-card'>💰<span>งบรวม</span><b>{money(req.budget)}</b></div>", unsafe_allow_html=True)
    with m4:
        st.markdown(f"<div class='stat-card'>🎒<span>สไตล์</span><b>{req.style}</b></div>", unsafe_allow_html=True)


def render_budget_breakdown(req: TripRequest) -> None:
    budget = estimate_budget(req)
    total = sum(budget.values()) or 1
    icons = {"เดินทาง": "🚗", "ที่พัก": "🏨", "อาหาร": "🍜", "กิจกรรม/ค่าเข้า": "🎟️", "เงินสำรอง": "🛟"}
    rows = []
    for name, value in budget.items():
        percent = max(3, min(100, (value / total) * 100))
        rows.append(f"""
<div class="budget-row">
  <div class="budget-label">{icons.get(name, '•')} <b>{name}</b><span>{money(value)}</span></div>
  <div class="budget-track"><div class="budget-fill" style="width:{percent:.1f}%"></div></div>
</div>
""")
    st.markdown(f"""
<div class="budget-card">
  <div class="section-title">💰 ภาพรวมงบประมาณโดยประมาณ</div>
  <p>ระบบแบ่งงบให้เห็นเป็นสัดส่วน เพื่อช่วยตัดสินใจก่อนจองจริง</p>
  {''.join(rows)}
</div>
""", unsafe_allow_html=True)


def render_ai_answer(answer: str) -> None:
    st.markdown(
        """
<div class="ai-answer-title">
    <div class="ai-answer-icon">📋</div>
    <div>
        <h2>รายละเอียดแพลนจาก AI</h2>
        <p>สรุปแผนเที่ยว ค่าใช้จ่าย ที่พัก การเดินทาง และคำแนะนำเพิ่มเติม</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(answer)
        
    # st.markdown("<div class='ai-answer-card'>", unsafe_allow_html=True)
    # st.markdown(answer)
    # st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(61, 180, 242, .18), transparent 34%),
            radial-gradient(circle at top right, rgba(49, 190, 121, .18), transparent 28%),
            linear-gradient(135deg, #eef8ff 0%, #f4fff4 50%, #fffaf0 100%);
        font-family: 'Prompt', 'Segoe UI', sans-serif;
        color: #123044;
    }

    .block-container {
        padding-top: 2rem;
        max-width: 1180px;
    }

    .hero {
        position: relative;
        overflow: hidden;
        background:
            linear-gradient(135deg, rgba(255,255,255,.96), rgba(255,255,255,.82)),
            linear-gradient(120deg, #d9f2ff, #e7ffe7);
        border: 1px solid rgba(255,255,255,.9);
        box-shadow: 0 24px 70px rgba(55, 95, 120, .16);
        padding: 34px;
        border-radius: 32px;

        /* เพิ่ม 2 บรรทัดนี้ */
        margin-top: 50px;
        margin-bottom: 22px;
    }

    .hero::after {
        content: "🏝️";
        position: absolute;
        right: 34px;
        top: 22px;
        font-size: 86px;
        opacity: .18;
    }

    .hero h1 {
        margin: 0 0 12px 0;
        font-size: clamp(34px, 4vw, 52px);
        color: #123f63;
        font-weight: 900;
        letter-spacing: -.5px;
    }

    .hero p {
        max-width: 840px;
        font-size: 17px;
        color: #415a66;
        line-height: 1.9;
        margin-bottom: 18px;
    }

    .pill {
        display: inline-block;
        padding: 9px 14px;
        margin: 5px 4px 0 0;
        border-radius: 999px;
        background: #e8f5ff;
        color: #1d5578;
        font-weight: 800;
        font-size: 13px;
        border: 1px solid #cbeafa;
        box-shadow: 0 4px 12px rgba(39, 122, 163, .08);
    }

    /* กล่องสรุปแพลนด้านบน */
    .plan-hero-card {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 220px;
        gap: 22px;
        align-items: stretch;
        padding: 26px;
        margin: 22px 0 18px;
        border-radius: 30px;
        background:
            linear-gradient(135deg, rgba(255,255,255,.96), rgba(245,253,255,.92)),
            linear-gradient(120deg, #e7f7ff, #ecffe9);
        border: 1px solid rgba(195, 230, 244, .95);
        box-shadow: 0 18px 45px rgba(34, 92, 120, .12);
    }

    .plan-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 12px;
        border-radius: 999px;
        background: #e8f5ff;
        color: #1f6687;
        font-weight: 800;
        font-size: 13px;
        border: 1px solid #caeafd;
        margin-bottom: 10px;
    }

    .plan-hero-left h2 {
        margin: 0 0 8px;
        font-size: clamp(28px, 3.2vw, 40px);
        color: #123f63;
        line-height: 1.25;
        font-weight: 900;
    }

    .plan-hero-left p {
        font-size: 17px;
        line-height: 1.85;
        color: #354f5c;
        margin: 12px 0;
    }

    .plan-hero-left ul {
        margin: 10px 0 0 0;
        padding-left: 22px;
        font-size: 16px;
        line-height: 1.9;
        color: #244251;
    }

    .mini-tag {
        display: inline-block;
        padding: 6px 11px;
        margin: 0 6px 8px 0;
        border-radius: 999px;
        background: #edf8ff;
        color: #1a6388;
        font-size: 12px;
        font-weight: 800;
        border: 1px solid #d3edf8;
    }

    .plan-score-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 180px;
        border-radius: 26px;
        background: linear-gradient(160deg, #e9f8ff, #eefde8);
        border: 1px solid rgba(200,232,244,.9);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.8);
        text-align: center;
    }

    .score-number {
        font-size: 54px;
        line-height: 1;
        font-weight: 900;
        color: #0f5e86;
    }

    .score-label {
        margin-top: 8px;
        font-weight: 900;
        color: #173e56;
        font-size: 15px;
    }

    .score-sub {
        margin-top: 6px;
        color: #66808e;
        font-size: 13px;
    }

    /* การ์ดตัวเลข */
    .stat-card {
        min-height: 116px;
        padding: 20px 18px;
        border-radius: 24px;
        background: rgba(255,255,255,.9);
        border: 1px solid rgba(202, 235, 247, .95);
        box-shadow: 0 12px 30px rgba(34, 92, 120, .08);
        font-size: 24px;
        margin-bottom: 12px;
    }

    .stat-card span {
        display: block;
        margin-top: 8px;
        color: #617783;
        font-size: 14px;
        font-weight: 700;
    }

    .stat-card b {
        display: block;
        margin-top: 4px;
        color: #123f63;
        font-size: 21px;
        line-height: 1.35;
        font-weight: 900;
    }

    /* งบประมาณ */
    .budget-card {
        padding: 24px;
        margin: 14px 0 20px;
        border-radius: 28px;
        background: rgba(255,255,255,.92);
        border: 1px solid rgba(209, 238, 246, .95);
        box-shadow: 0 16px 42px rgba(34, 92, 120, .1);
    }

    .section-title {
        font-size: 26px;
        font-weight: 900;
        color: #123f63;
        margin-bottom: 6px;
    }

    .budget-card p {
        color: #5f7580;
        font-size: 15px;
        margin-bottom: 18px;
    }

    .budget-row {
        margin: 15px 0;
    }

    .budget-label {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        color: #18394c;
        font-size: 16px;
        margin-bottom: 8px;
    }

    .budget-label span {
        color: #0f5e86;
        font-weight: 900;
    }

    .budget-track {
        height: 14px;
        border-radius: 999px;
        background: #e8f1f5;
        overflow: hidden;
        border: 1px solid #d7e9ef;
    }

    .budget-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #6fc7f3, #69d59b);
    }

    /* รายละเอียด AI */
    .ai-answer-title {
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 28px 0 14px;
        padding: 18px 22px;
        border-radius: 24px;
        background:
            linear-gradient(135deg, rgba(255,255,255,.95), rgba(245,253,255,.92)),
            linear-gradient(120deg, #e7f7ff, #ecffe9);
        border: 1px solid rgba(202, 235, 247, .95);
        box-shadow: 0 12px 30px rgba(34, 92, 120, .08);
    }

    .ai-answer-icon {
        width: 54px;
        height: 54px;
        min-width: 54px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #e7f7ff, #eefde9);
        border: 1px solid #cbeafa;
        font-size: 28px;
    }

    .ai-answer-title h2 {
        margin: 0;
        color: #123f63;
        font-size: 28px;
        font-weight: 900;
        line-height: 1.25;
    }

    .ai-answer-title p {
        margin: 6px 0 0;
        color: #617783;
        font-size: 15px;
        line-height: 1.6;
    }

    /* กล่องข้อความคำตอบ AI */
    .ai-answer-content {
        padding: 26px 30px;
        margin-bottom: 14px;
        border-radius: 28px;
        background: rgba(255,255,255,.95);
        border: 1px solid rgba(202, 235, 247, .95);
        box-shadow: 0 18px 48px rgba(34, 92, 120, .12);
    }

    .ai-answer-content h1,
    .ai-answer-content h2,
    .ai-answer-content h3 {
        color: #123f63 !important;
        font-weight: 900 !important;
        margin-top: 20px !important;
    }

    .ai-answer-content h2 {
        font-size: 28px !important;
    }

    .ai-answer-content h3 {
        font-size: 23px !important;
    }

    .ai-answer-content p,
    .ai-answer-content li {
        font-size: 17px !important;
        line-height: 1.95 !important;
        color: #263f4b !important;
    }

    .ai-answer-content ul,
    .ai-answer-content ol {
        padding-left: 26px !important;
    }

    .ai-answer-content strong {
        color: #0f5e86;
        font-weight: 900;
    }
    
    /* การ์ดจังหวัดเดิมให้ดูดีขึ้น */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 24px !important;
        box-shadow: 0 10px 24px rgba(34, 92, 120, .06);
    }

    [data-testid="stForm"] {
        background: rgba(255,255,255,.78);
        border: 1px solid rgba(217, 238, 247, .95);
        border-radius: 28px;
        padding: 18px;
        box-shadow: 0 14px 34px rgba(34, 92, 120, .08);
    }

    [data-testid="stTabs"] button {
        font-weight: 800;
        font-size: 15px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f7fcff, #f8fff5);
    }
        /* กล่องว่างตอนยังไม่มีแชท */
    .chat-empty {
        height: 500px;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: #557080;
        padding: 24px;
        box-sizing: border-box;
    }

    .chat-empty-icon {
        width: 82px;
        height: 82px;
        border-radius: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #e7f7ff, #eefde9);
        border: 1px solid #cbeafa;
        font-size: 38px;
        margin-bottom: 18px;
        box-shadow: 0 12px 28px rgba(34, 92, 120, 0.10);
    }

    .chat-empty h3 {
        margin: 0 0 10px 0;
        color: #163b57;
        font-size: 28px;
        font-weight: 800;
    }

    .chat-empty p {
        margin: 0;
        color: #6d7f88;
        font-size: 16px;
        line-height: 1.7;
    }
    
        /* ตารางเปรียบเทียบสถานที่ */
    .compare-result-card {
        margin-top: 28px;
        padding: 28px;
        border-radius: 30px;
        background:
            linear-gradient(135deg, rgba(255,255,255,.96), rgba(247,253,255,.92)),
            linear-gradient(120deg, #e7f7ff, #ecffe9);
        border: 1px solid rgba(202, 235, 247, .95);
        box-shadow: 0 18px 48px rgba(34, 92, 120, .12);
    }

    .compare-title {
        display: grid;
        grid-template-columns: 58px minmax(0, 1fr);
        align-items: center;
        gap: 16px;
        margin-bottom: 22px;
        width: 100%;
    }

    .compare-title-icon {
        width: 54px;
        height: 54px;
        min-width: 54px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #e7f7ff, #eefde9);
        border: 1px solid #cbeafa;
        font-size: 28px;
        box-shadow: 0 10px 24px rgba(34, 92, 120, .08);
    }

    .compare-title-text {
        min-width: 0;
        width: 100%;
    }

    .compare-title-text h2 {
        margin: 0;
        color: #123f63;
        font-size: 32px;
        font-weight: 900;
        line-height: 1.25;
        white-space: normal;
        word-break: keep-all;
        overflow-wrap: normal;
    }

    .compare-title-text p {
        margin: 6px 0 0;
        color: #617783;
        font-size: 15px;
        line-height: 1.7;
    }
    .compare-table-wrap {
        overflow-x: auto;
        border-radius: 22px;
        border: 1px solid #d6edf5;
        background: white;
    }

    .compare-table {
        width: 100%;
        border-collapse: collapse;
        overflow: hidden;
        font-size: 16px;
    }

    .compare-table thead th {
        background: linear-gradient(135deg, #e8f5ff, #effdec);
        color: #123f63;
        font-weight: 900;
        font-size: 17px;
        padding: 16px 18px;
        text-align: left;
        border-bottom: 1px solid #d6edf5;
    }

    .compare-table tbody td {
        padding: 15px 18px;
        vertical-align: top;
        color: #263f4b;
        line-height: 1.8;
        border-bottom: 1px solid #e5f0f4;
    }

    .compare-table tbody tr:nth-child(even) {
        background: rgba(240, 250, 255, .62);
    }

    .compare-table tbody tr:hover {
        background: rgba(224, 246, 255, .85);
    }

    .compare-table tbody td:first-child {
        width: 180px;
        font-weight: 900;
        color: #0f5e86;
        background: rgba(232, 245, 255, .55);
    }

    .compare-summary-box {
        margin-top: 22px;
        padding: 22px 24px;
        border-radius: 24px;
        background: rgba(255,255,255,.88);
        border: 1px solid rgba(202, 235, 247, .95);
        box-shadow: 0 10px 24px rgba(34, 92, 120, .06);
    }

    .compare-summary-box h3 {
        margin: 0 0 12px;
        color: #123f63;
        font-size: 24px;
        font-weight: 900;
    }

    .compare-summary-box ul {
        margin: 0;
        padding-left: 22px;
    }

    .compare-summary-box li {
        font-size: 16px;
        line-height: 1.9;
        color: #263f4b;
    }

    .compare-user-note {
        margin-top: 16px;
        padding: 14px 16px;
        border-radius: 16px;
        background: #f2f8fb;
        color: #34515f;
        font-size: 15px;
        border: 1px solid #d9eef7;
    }

    @media (max-width: 900px) {
        .plan-hero-card {
            grid-template-columns: 1fr;
        }
        .hero::after {
            display: none;
        }
    .distance-chip {
        display: inline-block;
        margin: 6px 0 10px;
        padding: 9px 14px;
        border-radius: 999px;
        background: #f2f8fb;
        border: 1px solid #d9eef7;
        color: #0f5e86;
        font-size: 14px;
        font-weight: 800;
    }
    
    }
    </style>
    <div class="hero">
        <h1>🧭 TripMate Thailand AI</h1>
        <p>ผู้ช่วยวางแผนเที่ยวก่อนจองจริง เน้นภูเขาและทะเลในประเทศไทย วิเคราะห์จากงบ จำนวนคน จำนวนวัน ความสะดวก ผู้คน และสไตล์การเที่ยว</p>
        <span class="pill">🏔️ ภูเขา</span>
        <span class="pill">🏖️ ทะเล</span>
        <span class="pill">💰 คำนวณงบ</span>
        <span class="pill">🏨 ที่พักใกล้เคียง</span>
        <span class="pill">🚗 แผนไป-กลับ</span>
        <span class="pill">⚖️ เปรียบเทียบสถานที่</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

planner_tab, compare_tab, highlights_tab, chat_tab = st.tabs([
    "🧭 วางแพลนเที่ยว",
    "⚖️ เปรียบเทียบสถานที่",
    "📍 ไฮไลท์จังหวัด",
    "💬 ถาม AI เพิ่มเติม",
])

with planner_tab:
    planner_box = st.container(border=True)

    with planner_box:
        c1, c2, c3 = st.columns(3)

        with c1:
            origin_province = st.selectbox(
                "ต้นทางที่เริ่มเดินทาง",
                sorted(THAI_PROVINCE_COORDS.keys()),
                index=sorted(THAI_PROVINCE_COORDS.keys()).index("กรุงเทพมหานคร"),
                key="planner_origin_province",
            )

            theme = st.selectbox(
                "อยากไปเที่ยวไหน",
                ["ทะเล", "ภูเขา", "ยังไม่แน่ใจ"],
                key="planner_theme_filter",
            )

            province_choice = st.selectbox(
                "จังหวัดที่สนใจ",
                get_province_options(theme),
                key=f"planner_province_choice_{theme}",
            )

        with c2:
            people = st.number_input(
                "ไปกี่คน",
                min_value=1,
                max_value=30,
                value=2,
                step=1,
                key="planner_people",
            )

            days = st.number_input(
                "ไปกี่วัน",
                min_value=1,
                max_value=10,
                value=2,
                step=1,
                key="planner_days",
            )

            budget = st.number_input(
                "งบรวมทั้งหมด (บาท)",
                min_value=0,
                max_value=5000000,
                value=5000,
                step=500,
                key="planner_budget",
            )

            style = st.selectbox(
                "สไตล์งบ",
                ["ประหยัด", "สมดุล", "สบาย"],
                key="planner_style",
            )
            
        with c3:
            transport = st.selectbox(
                "การเดินทาง",
                ["ไม่มีรถส่วนตัว", "มีรถส่วนตัว", "เครื่องบิน/รถเช่า", "ยังไม่แน่ใจ"],
                key="planner_transport",
            )

            crowd = st.selectbox(
                "เรื่องผู้คน",
                ["ไม่อยากเจอคนเยอะ", "รับได้ถ้าคนเยอะ", "ยังไงก็ได้"],
                key="planner_crowd",
            )

            extra = st.text_area(
                "รายละเอียดเพิ่มเติม",
                placeholder="เช่น อยากมีคาเฟ่ ไม่เอาเดินเยอะ อยากได้ที่พักใกล้ทะเล",
                key="planner_extra",
            )

        submitted = st.button(
            "✨ ให้ AI วางแผน",
            use_container_width=True,
            key="planner_submit",
        )

    if submitted:
        req = TripRequest(
            theme=theme,
            province="" if province_choice == "ยังไม่ระบุ" else province_choice,
            origin_province=origin_province,
            people=int(people),
            days=int(days),
            budget=int(budget),
            transport=transport,
            crowd=crowd,
            style=style,
            extra=extra,
        )

        picks = recommend_destinations(req)
        selected = req.province if req.province in DESTINATIONS else picks[0]

        st.subheader("จังหวัดที่ระบบแนะนำ")
        cols = st.columns(min(len(picks), 3))

        for idx, p in enumerate(picks):
            with cols[idx]:
                render_destination_card(p)

        render_trip_overview(req, selected)
        render_budget_breakdown(req)

        answer = ask_gemini(req, selected)
        render_ai_answer(answer)

        status = log_trip_if_possible(req, selected, int(budget))
        st.info(status)

        st.session_state.history.append(
            {
                "province": selected,
                "theme": theme,
                "people": int(people),
                "days": int(days),
                "budget": int(budget),
                "style": style,
            }
        )
        
with compare_tab:
    st.subheader("เปรียบเทียบสถานที่")

    compare_options = get_filtered_destinations("ทั้งหมด")

    if len(compare_options) < 2:
        st.warning("ยังมีสถานที่ไม่พอสำหรับการเปรียบเทียบ")
    else:
        c1, c2 = st.columns(2)

        with c1:
            place_a = st.selectbox(
                "สถานที่ A",
                compare_options,
                index=0,
                key="compare_place_a",
            )

        with c2:
            place_b = st.selectbox(
                "สถานที่ B",
                compare_options,
                index=1 if len(compare_options) > 1 else 0,
                key="compare_place_b",
            )

        req_text = st.text_input(
            "เงื่อนไขเพิ่มเติม",
            placeholder="เช่น งบ 6000 ไม่มีรถส่วนตัว ไม่อยากเจอคนเยอะ",
            key="compare_extra_condition",
        )

        if st.button("เปรียบเทียบ", use_container_width=True):
            if place_a == place_b:
                st.warning("กรุณาเลือกสถานที่ A และ B ให้แตกต่างกัน")
            else:
                st.markdown(compare_destinations(place_a, place_b, req_text),unsafe_allow_html=True,)

with highlights_tab:
    st.subheader("จังหวัดและไฮไลท์ที่ระบบรู้จัก")
    filter_type = st.radio("กรองตามแนวเที่ยว", ["ทั้งหมด", "ทะเล", "ภูเขา"], horizontal=True)
    shown = get_filtered_destinations(filter_type)

    for i in range(0, len(shown), 2):
        cols = st.columns(2)
        for col, province in zip(cols, shown[i:i+2]):
            with col:
                render_destination_card(province)
                
                
with chat_tab:
    st.subheader("ถาม AI เพิ่มเติม")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    chat_panel = st.container(height=520, border=True)

    with chat_panel:
        if not st.session_state.chat_messages:
            st.markdown(
                """
<div class="chat-empty">
    <div class="chat-empty-icon">💬</div>
    <h3>เริ่มคุยกับ Matey ได้เลย</h3>
    <p>ตัวอย่าง: มีงบ 3000 ไม่มีรถส่วนตัว อยากเที่ยวทะเลที่คนไม่เยอะ</p>
</div>
""",
                unsafe_allow_html=True,
            )

        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    question = st.chat_input("พิมพ์คำถามเกี่ยวกับทริปของคุณที่นี่...")

    if question:
        st.session_state.chat_messages.append(
            {"role": "user", "content": question}
        )

        with chat_panel:
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Matey กำลังคิดคำตอบ..."):

                    if not is_travel_related_question(question):
                        ai_answer = polite_off_topic_reply(question)

                    elif is_ambiguous_travel_question(question):
                        ai_answer = rewrite_ambiguous_question(question)

                    else:
                        context_chunks = rag.search(question, top_k=5)
                        context = "\n---\n".join(context_chunks)

                        if client:
                            prompt = f"""
คุณคือ Matey ผู้ช่วย AI วางแผนเที่ยวของ TripMate Thailand AI

กติกาการตอบ:
- ตอบเฉพาะเรื่องการท่องเที่ยว การวางแผนทริป งบประมาณ ที่พัก การเดินทาง สถานที่เที่ยว และแผนสำรอง
- ถ้าผู้ใช้ถามนอกเรื่อง ให้ปฏิเสธอย่างสุภาพและชวนกลับมาเรื่องท่องเที่ยว
- ถ้าคำถามกำกวม ให้ช่วยเรียบเรียงคำถามใหม่ให้ผู้ใช้เข้าใจง่าย
- ตอบเป็นภาษาไทย กระชับ ชัดเจน
- ถ้าเป็นราคา ให้บอกว่าเป็นการประเมินเบื้องต้น
- ห้ามอ้างว่าราคา โรงแรม เวลาเปิดปิด หรือระยะทางเป็นข้อมูล real-time

ข้อมูลจากฐานความรู้:
{context}

คำถามผู้ใช้:
{question}

ให้ตอบแบบอ่านง่าย มีหัวข้อย่อย และแนะนำอย่างเหมาะสมกับงบ การเดินทาง และสไตล์ของผู้ใช้
"""

                            try:
                                resp = client.models.generate_content(
                                    model=MODEL,
                                    contents=prompt,
                                )
                                ai_answer = resp.text

                            except Exception as e:
                                error_text = str(e)

                                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                                    ai_answer = (
                                        "⚠️ **ตอนนี้โควตา Gemini API หมดชั่วคราว**\n\n"
                                        "แต่ Matey ยังสามารถช่วยแนะนำจากฐานความรู้ของระบบได้ครับ\n\n"
                                        "## 🧭 คำแนะนำจากฐานความรู้\n\n"
                                        f"{context}\n\n"
                                        "## ✅ หมายเหตุ\n"
                                        "- คำตอบนี้เป็นข้อมูลจากฐานความรู้ที่เตรียมไว้ในระบบ\n"
                                        "- ราคาและแผนเที่ยวเป็นการประเมินเบื้องต้น\n"
                                        "- ก่อนเดินทางจริงควรตรวจสอบราคา เวลาเปิด-ปิด และการเดินทางอีกครั้ง"
                                    )
                                else:
                                    ai_answer = (
                                        "⚠️ **ตอนนี้ระบบ AI ภายนอกเรียกใช้งานไม่สำเร็จ**\n\n"
                                        "ระบบจึงแสดงข้อมูลจากฐานความรู้ของ TripMate แทนก่อน\n\n"
                                        f"{context}"
                                    )
                        else:
                            ai_answer = (
                                "⚠️ ยังไม่ได้ตั้งค่า `GOOGLE_API_KEY`\n\n"
                                "จึงแสดงข้อมูลจากฐานความรู้แทน:\n\n"
                                + context
                            )

                    st.markdown(ai_answer)

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": ai_answer}
        )
        st.rerun()

    if st.button("ล้างแชท", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

with st.sidebar:
    st.markdown("## 🕘 ประวัติแพลน")
    if st.button("ล้างประวัติ", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    if not st.session_state.history:
        st.caption("ยังไม่มีแพลนที่สร้างในรอบนี้")

    for item in reversed(st.session_state.history[-10:]):
        st.markdown(
            f"""
<div style="background:white;border:1px solid #d9eef7;border-radius:16px;padding:12px;margin:8px 0;">
    <b>{item['province']}</b><br>
    {item['theme']} | {item['people']} คน | {item['days']} วัน<br>
    งบ {item['budget']:,} บาท | {item['style']}
</div>
""",
            unsafe_allow_html=True,
        )
