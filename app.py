# app.py
from __future__ import annotations

import os
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


@dataclass
class TripRequest:
    theme: str
    province: str
    people: int
    days: int
    budget: int
    transport: str
    crowd: str
    style: str
    extra: str
    rain_backup: bool
    no_car_mode: bool
    share_summary: bool


def money(value: float) -> str:
    return f"{value:,.0f} บาท"


def normalize_theme_filter(theme: str) -> str:
    """แปลงค่าตัวกรองให้ใช้ร่วมกันทั้ง dropdown และหน้าไฮไลท์"""
    if theme in ["ทั้งหมด", "ยังไม่แน่ใจ", ""]:
        return "ทั้งหมด"
    return theme


def get_destinations_by_theme(theme: str) -> list[str]:
    """แหล่งข้อมูลกลาง: dropdown จังหวัดที่สนใจและหน้าไฮไลท์ต้องใช้ฟังก์ชันนี้เท่านั้น"""
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
    return ["ยังไม่ระบุ"] + get_destinations_by_theme(theme)


def get_filtered_destinations(filter_type: str) -> list[str]:
    # คงชื่อเดิมไว้เพื่อไม่ให้ส่วน compare/highlight พัง แต่ให้เรียกฟังก์ชันกลางตัวเดียวกัน
    return get_destinations_by_theme(filter_type)


def build_extra_feature_prompt(req: TripRequest) -> str:
    features: list[str] = []

    if req.rain_backup:
        features.append(
            """
- Rain Backup Plan:
  ถ้าฝนตก ให้เสนอแผนสำรอง เช่น คาเฟ่ พิพิธภัณฑ์ ตลาดในร่ม
  ร้านอาหารท้องถิ่น จุดถ่ายรูปในร่ม หรือกิจกรรมที่ไม่ต้องอยู่กลางแจ้ง
"""
        )

    if req.no_car_mode or req.transport == "ไม่มีรถส่วนตัว":
        features.append(
            """
- No Car Mode:
  จัดแพลนสำหรับคนไม่มีรถส่วนตัว
  ให้เน้นรถไฟ รถตู้ รถโดยสาร เครื่องบิน หรือการเดินทางที่ต่อรถไม่ซับซ้อน
  หลีกเลี่ยงสถานที่ที่ต้องขับรถเองหรืออยู่ไกลจากจุดขนส่งมากเกินไป
"""
        )

    if req.crowd != "ยังไงก็ได้":
        features.append(
            f"""
- Crowd Filter:
  ผู้ใช้ต้องการรูปแบบผู้คน: "{req.crowd}"
  ให้เลือกสถานที่และอธิบายเหตุผลตามระดับความหนาแน่นของผู้คน
"""
        )

    if req.share_summary:
        features.append(
            """
- Share Summary:
  หลังจากจัดแพลนแล้ว ให้สรุปสั้น ๆ แบบส่งให้เพื่อนได้
  โดยมีปลายทาง จำนวนคน จำนวนวัน งบประมาณ สถานที่หลัก และเหตุผลที่เลือก
"""
        )

    return "\n".join(features) if features else "ไม่มีฟังก์ชันเสริมเพิ่มเติม"


def recommend_destinations(req: TripRequest) -> list[str]:
    candidates = []

    for province, data in DESTINATIONS.items():
        if not is_matching_theme(province, req.theme):
            continue

        score = 0

        if req.transport == "ไม่มีรถส่วนตัว" or req.no_car_mode:
            if data["ease"] == "สูง":
                score += 4
            elif data["ease"] == "กลาง":
                score += 2
            else:
                score -= 1

        if req.crowd == "ไม่อยากเจอคนเยอะ":
            if "น้อย" in data["crowd"]:
                score += 4
            elif data["crowd"] == "กลาง":
                score += 2
            elif "เยอะ" in data["crowd"]:
                score -= 2

        if req.crowd == "รับได้ถ้าคนเยอะ" and data["crowd"] in ["เยอะ", "กลาง-เยอะ"]:
            score += 2

        if req.style == "ประหยัด" and "ประหยัด" in data["budget"]:
            score += 3
        elif req.style == "สมดุล" and data["budget"] in ["กลาง", "ประหยัด-กลาง", "กลาง-สูง"]:
            score += 2
        elif req.style == "สบาย" and data["ease"] == "สูง":
            score += 2

        if req.province and req.province == province:
            score += 10

        candidates.append((score, province))

    if not candidates:
        candidates = [(1, p) for p in DESTINATIONS.keys()]

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [province for _, province in candidates[:3]]


def estimate_budget(req: TripRequest) -> dict[str, float]:
    total = max(req.budget, 0)
    if total <= 0:
        total = req.people * req.days * 1500

    transport_ratio = 0.22 if req.transport == "ไม่มีรถส่วนตัว" or req.no_car_mode else 0.18

    return {
        "เดินทาง": total * transport_ratio,
        "ที่พัก": total * 0.32,
        "อาหาร": total * 0.24,
        "กิจกรรม/ค่าเข้า": total * 0.12,
        "เงินสำรอง": total * 0.10,
    }


def match_score(req: TripRequest, province: str) -> tuple[float, list[str]]:
    data = DESTINATIONS[province]
    score = 6.0
    reasons: list[str] = []

    if is_matching_theme(province, req.theme):
        score += 1.0
        reasons.append("ตรงกับแนวเที่ยวที่เลือก")

    if req.transport == "ไม่มีรถส่วนตัว" or req.no_car_mode:
        if data["ease"] == "สูง":
            score += 1.2
            reasons.append("เดินทางค่อนข้างสะดวกสำหรับคนไม่มีรถ")
        elif data["ease"] == "กลาง":
            score += 0.5
            reasons.append("พอเดินทางได้ แต่ควรวางแผนต่อรถล่วงหน้า")

    if req.crowd == "ไม่อยากเจอคนเยอะ" and "น้อย" in data["crowd"]:
        score += 1.0
        reasons.append("เหมาะกับคนที่ไม่อยากเจอคนเยอะ")
    elif req.crowd == "รับได้ถ้าคนเยอะ" and "เยอะ" in data["crowd"]:
        score += 0.5
        reasons.append("เหมาะกับคนที่ชอบบรรยากาศคึกคัก")

    if req.style == "ประหยัด" and "ประหยัด" in data["budget"]:
        score += 1.0
        reasons.append("ควบคุมงบได้ง่าย")

    if req.budget >= req.people * req.days * 1500:
        score += 0.7
        reasons.append("งบประมาณพอวางแผนได้ค่อนข้างสบาย")
    else:
        reasons.append("งบค่อนข้างจำกัด ควรลดค่าที่พักหรือกิจกรรมเสียเงิน")

    return min(score, 10), reasons


def build_share_summary(req: TripRequest, province: str) -> str:
    data = DESTINATIONS[province]
    nights = max(req.days - 1, 0)
    return (
        f"📤 **Share Summary สำหรับส่งให้เพื่อน**\n\n"
        f"ทริปนี้ไป **{province}** {req.days} วัน {nights} คืน / {req.people} คน "
        f"งบรวมประมาณ {money(req.budget)} แนวเที่ยว {req.theme} สไตล์ {req.style} "
        f"ไฮไลท์คือ {', '.join(data['highlights'][:3])} "
        f"เหมาะเพราะ {data['best_for']} "
        f"ราคาและเวลาเป็นการประเมินเบื้องต้น ควรเช็กข้อมูลจริงก่อนเดินทาง"
    )


def build_fallback_plan(req: TripRequest, province: str) -> str:
    data = DESTINATIONS[province]
    budget = estimate_budget(req)
    score, reasons = match_score(req, province)
    nights = max(req.days - 1, 0)

    lines = [
        f"## 🧭 แพลนแนะนำ: {province}",
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
        f"**สไตล์งบ:** {req.style} — {STYLE_NOTES[req.style]}",
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

    if req.no_car_mode or req.transport == "ไม่มีรถส่วนตัว":
        lines += [
            "",
            "### 🚌 No Car Mode",
            "- เลือกจุดเที่ยวที่ต่อรถง่าย เช่น จุดใกล้สถานีขนส่ง สถานีรถไฟ ท่าเรือ หรือจุดเรียกรถ",
            "- ไม่ควรวางจุดเที่ยวกระจายหลายอำเภอในวันเดียว",
            "- เผื่อเวลาเดินทางและรอรถมากกว่าปกติ",
        ]

    for day in range(1, req.days + 1):
        if day == 1:
            lines += [
                "",
                f"### Day {day}",
                f"- เช้า: เดินทางไป {province}",
                "- กลางวัน: กินอาหารท้องถิ่นหรือร้านใกล้จุดแรก",
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
            first = data["highlights"][1] if len(data["highlights"]) > 1 else data["highlights"][0]
            second = data["highlights"][2] if len(data["highlights"]) > 2 else data["highlights"][0]
            lines += [
                "",
                f"### Day {day}",
                f"- เช้า: เที่ยว {first}",
                "- กลางวัน: พักกินข้าวใกล้สถานที่เที่ยว",
                f"- บ่าย: เที่ยว {second}",
                "- เย็น: กลับที่พักหรือเดินเล่นย่านใกล้เคียง",
            ]

    if req.rain_backup:
        lines += [
            "",
            "### 🌧️ Rain Backup Plan",
            "- ถ้าฝนตก ให้เปลี่ยนจากชายหาด/จุดชมวิวกลางแจ้ง เป็นคาเฟ่ ร้านอาหารท้องถิ่น ตลาดในร่ม พิพิธภัณฑ์ หรือย่านเมืองเก่า",
            "- เลือกกิจกรรมที่เดินทางไม่ไกลจากที่พัก เพื่อลดปัญหารถติดหรือเปียกฝน",
        ]

    lines += [
        "",
        "### ✅ สรุป",
        f"จากงบ จำนวนคน และสไตล์แบบ{req.style} แนะนำให้เลือก {province} เพราะ{data['best_for']} แต่ควรตรวจสอบราคาที่พักและเวลาเปิด-ปิดจริงก่อนเดินทาง",
    ]

    if req.share_summary:
        lines += ["", build_share_summary(req, province)]

    return "\n".join(lines)


def ask_gemini(req: TripRequest, province: str) -> str:
    context_chunks = rag.search(
        f"{req.theme} {province} {req.budget} บาท {req.people} คน {req.days} วัน {req.transport} {req.crowd} {req.style}",
        top_k=5,
    )
    context = "\n---\n".join(context_chunks)
    extra_feature_prompt = build_extra_feature_prompt(req)

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

ฟังก์ชันเสริมที่ต้องนำไปใช้:
{extra_feature_prompt}

ให้ตอบเป็นภาษาไทยในรูปแบบนี้:
1. สรุปจังหวัดที่แนะนำและเหตุผล
2. Trip Match Score /10 พร้อมเหตุผล
3. ค่าใช้จ่ายโดยประมาณ แยก เดินทาง ที่พัก อาหาร กิจกรรม เงินสำรอง
4. แนะนำประเภทที่พักใกล้แหล่งเที่ยว
5. แผนเดินทางไป
6. ตารางแพลนเที่ยวรายวันแบบ เช้า กลางวัน บ่าย เย็น
7. แผนเดินทางกลับ
8. Rain Backup Plan ถ้าผู้ใช้เปิดใช้
9. No Car Mode ถ้าผู้ใช้ไม่มีรถส่วนตัวหรือเปิดใช้
10. Crowd Filter ตามความต้องการเรื่องผู้คน
11. Share Summary ถ้าผู้ใช้เปิดใช้
12. สรุปว่าคุ้มไหมและควรปรับอะไรถ้างบไม่พอ

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
                icon = "🏖️" if "ทะเล" in data["type"] else "🏔️"
                st.markdown(f"<div class='image-fallback'>{icon}</div>", unsafe_allow_html=True)

        with cols[1]:
            tags = "".join([f"<span class='mini-tag'>{t}</span>" for t in data["type"]])
            st.markdown(f"### {province}")
            st.markdown(tags, unsafe_allow_html=True)
            st.write(data["best_for"])
            st.caption(f"ผู้คน: {data['crowd']} | ความสะดวก: {data['ease']} | งบ: {data['budget']}")
            st.write("**ไฮไลท์:** " + ", ".join(data["highlights"]))


def compare_destinations(a: str, b: str, req_text: str = "") -> str:
    da, db = DESTINATIONS[a], DESTINATIONS[b]
    return f"""
## เปรียบเทียบ {a} vs {b}

| หัวข้อ | {a} | {b} |
|---|---|---|
| แนวเที่ยว | {', '.join(da['type'])} | {', '.join(db['type'])} |
| จุดเด่น | {da['best_for']} | {db['best_for']} |
| ผู้คน | {da['crowd']} | {db['crowd']} |
| ความสะดวก | {da['ease']} | {db['ease']} |
| งบประมาณ | {da['budget']} | {db['budget']} |
| ไฮไลท์ | {', '.join(da['highlights'])} | {', '.join(db['highlights'])} |

### สรุป
- ถ้าเน้นความสะดวก ให้เลือกจังหวัดที่ความสะดวกสูงกว่า
- ถ้าไม่อยากเจอคนเยอะ ให้เลือกจังหวัดที่ผู้คนน้อยกว่า
- ถ้างบจำกัด ให้เลือกจังหวัดที่ควบคุมค่าเดินทางและที่พักได้ง่ายกว่า

จากข้อมูลที่ให้มา: {req_text or 'ยังไม่มีเงื่อนไขเพิ่มเติม'}
"""


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700;800&display=swap');
.stApp {
    background:
        radial-gradient(circle at top left, rgba(61, 180, 242, .18), transparent 34%),
        radial-gradient(circle at top right, rgba(49, 190, 121, .18), transparent 28%),
        linear-gradient(135deg, #eef8ff 0%, #f4fff4 48%, #fff9ed 100%);
    font-family: 'Prompt', 'Segoe UI', sans-serif;
}
.block-container { padding-top: 2rem; max-width: 1240px; }
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, rgba(255,255,255,.95), rgba(255,255,255,.78)), linear-gradient(120deg, #d9f2ff, #e7ffe7);
    border: 1px solid rgba(255,255,255,.9);
    box-shadow: 0 24px 70px rgba(55, 95, 120, .16);
    padding: 34px;
    border-radius: 32px;
    margin-bottom: 22px;
}
.hero::after {
    content: "🏝️";
    position: absolute;
    right: 30px;
    top: 22px;
    font-size: 84px;
    opacity: .18;
}
.hero h1 { margin: 0; font-size: clamp(32px, 4vw, 50px); color: #133b5c; font-weight: 900; }
.hero p { max-width: 820px; font-size: 16px; color: #456; line-height: 1.9; }
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
}
.trip-mode-box {
    background: rgba(255,255,255,.82);
    border: 1px solid rgba(190, 226, 238, .9);
    border-radius: 26px;
    padding: 20px 22px;
    box-shadow: 0 14px 32px rgba(34, 92, 120, .08);
    margin-bottom: 18px;
}
.image-fallback {
    height: 130px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius: 18px;
    background: linear-gradient(135deg, #e7f7ff, #eefde9);
    font-size: 58px;
}
.mini-tag {
    display: inline-block;
    padding: 5px 10px;
    margin: 0 5px 8px 0;
    border-radius: 999px;
    background: #edf8ff;
    color: #1a6388;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #d3edf8;
}
[data-testid="stForm"] {
    background: rgba(255,255,255,.72);
    border: 1px solid rgba(217, 238, 247, .95);
    border-radius: 28px;
    padding: 18px;
    box-shadow: 0 14px 34px rgba(34, 92, 120, .08);
}
[data-testid="stTabs"] button { font-weight: 800; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #f7fcff, #f8fff5); }

.mini-chip {
    display: inline-block;
    padding: 6px 10px;
    margin: 4px 4px 4px 0;
    border-radius: 999px;
    background: rgba(232,245,255,.92);
    border: 1px solid #bde4ff;
    color: #17415e;
    font-size: 13px;
    font-weight: 700;
}
@media (max-width: 768px) {
    .hero { padding: 24px; }
    .hero::after { display: none; }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
    <h1>🧭 TripMate Thailand AI</h1>
    <p>
        ผู้ช่วยวางแผนเที่ยวก่อนจองจริง เน้นภูเขาและทะเลในประเทศไทย
        วิเคราะห์จากงบ จำนวนคน จำนวนวัน ความสะดวก ผู้คน การเดินทาง และสไตล์การเที่ยว
    </p>
    <span class="pill">🏔️ ภูเขา</span>
    <span class="pill">🏖️ ทะเล</span>
    <span class="pill">💰 คำนวณงบ</span>
    <span class="pill">🏨 ที่พักใกล้เคียง</span>
    <span class="pill">🚗 แผนไป-กลับ</span>
    <span class="pill">🌧️ Rain Backup</span>
    <span class="pill">🚌 No Car Mode</span>
    <span class="pill">👥 Crowd Filter</span>
    <span class="pill">📤 Share Summary</span>
</div>
""",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

planner_tab, compare_tab, highlights_tab, chat_tab = st.tabs(
    ["🧭 วางแพลนเที่ยว", "⚖️ เปรียบเทียบสถานที่", "📍 ไฮไลท์จังหวัด", "💬 ถาม AI เพิ่มเติม"]
)

with planner_tab:
    st.markdown(
        """
<div class="trip-mode-box">
    <h3 style="margin-top:0;color:#163b57;">อยากไปเที่ยวไหน?</h3>
    <p style="margin-bottom:0;color:#52636c;">
        เลือกก่อนว่าอยากไป <b>ทะเล</b> หรือ <b>ภูเขา</b>
        แล้วช่องจังหวัดจะแสดงเฉพาะจังหวัดที่ตรงกับแนวที่เลือกเท่านั้น
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

    theme = st.radio("อยากไปเที่ยวไหน", ["ทะเล", "ภูเขา", "ยังไม่แน่ใจ"], horizontal=True, key="theme_radio")
    province_options = get_province_options(theme)
    available_provinces = province_options[1:]

    with st.form("planner_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            province_choice = st.selectbox("จังหวัดที่สนใจ", province_options)
            people = st.number_input("ไปกี่คน", min_value=1, max_value=30, value=2, step=1)
            days = st.number_input("ไปกี่วัน", min_value=1, max_value=10, value=2, step=1)
        with c2:
            budget = st.number_input("งบรวมทั้งหมด (บาท)", min_value=0, max_value=5000000, value=5000, step=500)
            style = st.selectbox("สไตล์งบ", ["ประหยัด", "สมดุล", "สบาย"])
            transport = st.selectbox("การเดินทาง", ["ไม่มีรถส่วนตัว", "มีรถส่วนตัว", "เครื่องบิน/รถเช่า", "ยังไม่แน่ใจ"])
        with c3:
            crowd = st.selectbox("Crowd Filter / เรื่องผู้คน", ["ไม่อยากเจอคนเยอะ", "รับได้ถ้าคนเยอะ", "ยังไงก็ได้"])
            rain_backup = st.checkbox("🌧️ Rain Backup Plan", value=True)
            no_car_mode = st.checkbox("🚌 No Car Mode", value=(transport == "ไม่มีรถส่วนตัว"))
            share_summary = st.checkbox("📤 Share Summary", value=True)
            extra = st.text_area("รายละเอียดเพิ่มเติม", placeholder="เช่น อยากมีคาเฟ่ ไม่เอาเดินเยอะ อยากได้ที่พักใกล้ทะเล")

        submitted = st.form_submit_button("✨ ให้ AI วางแพลน", use_container_width=True)

    if submitted:
        req = TripRequest(
            theme=theme,
            province="" if province_choice == "ยังไม่ระบุ" else province_choice,
            people=int(people),
            days=int(days),
            budget=int(budget),
            transport=transport,
            crowd=crowd,
            style=style,
            extra=extra,
            rain_backup=rain_backup,
            no_car_mode=no_car_mode,
            share_summary=share_summary,
        )

        picks = recommend_destinations(req)
        selected = req.province if req.province in DESTINATIONS else picks[0]

        st.subheader("จังหวัดที่ระบบแนะนำ")
        cols = st.columns(min(len(picks), 3))
        for idx, p in enumerate(picks):
            with cols[idx]:
                render_destination_card(p)

        st.subheader("แพลนเที่ยวของคุณ")
        answer = ask_gemini(req, selected)
        st.markdown(answer)

        status = log_trip_if_possible(req, selected, int(budget))
        st.info(status)

        st.session_state.history.append(
            {"province": selected, "theme": theme, "people": int(people), "days": int(days), "budget": int(budget), "style": style}
        )

with compare_tab:
    st.subheader("เปรียบเทียบสถานที่")
    compare_filter = st.radio("กรองประเภทสถานที่สำหรับเปรียบเทียบ", ["ทั้งหมด", "ทะเล", "ภูเขา"], horizontal=True, key="compare_filter")
    compare_options = get_filtered_destinations(compare_filter)

    c1, c2 = st.columns(2)
    with c1:
        place_a = st.selectbox("สถานที่ A", compare_options, index=0)
    with c2:
        default_b_index = 1 if len(compare_options) > 1 else 0
        place_b = st.selectbox("สถานที่ B", compare_options, index=default_b_index)

    req_text = st.text_input("เงื่อนไขเพิ่มเติม", placeholder="เช่น งบ 6000 ไม่มีรถส่วนตัว ไม่อยากเจอคนเยอะ")

    if st.button("เปรียบเทียบ", use_container_width=True):
        st.markdown(compare_destinations(place_a, place_b, req_text))

with highlights_tab:
    st.subheader("จังหวัดและไฮไลท์ที่ระบบรู้จัก")
    filter_type = st.radio(
        "กรองตามแนวเที่ยว",
        ["ทั้งหมด", "ทะเล", "ภูเขา"],
        horizontal=True,
        key="highlight_filter",
    )

    shown = get_filtered_destinations(filter_type)

    for i in range(0, len(shown), 2):
        cols = st.columns(2)
        for col, province in zip(cols, shown[i : i + 2]):
            with col:
                render_destination_card(province)

with chat_tab:
    st.subheader("ถาม AI เพิ่มเติม")
    question = st.chat_input("เช่น มีงบ 3000 ไม่มีรถส่วนตัว อยากเที่ยวทะเลที่คนไม่เยอะ")

    if question:
        st.chat_message("user").markdown(question)
        context_chunks = rag.search(question, top_k=5)
        context = "\n---\n".join(context_chunks)

        if client:
            prompt = f"""
คุณคือ Matey ผู้ช่วย AI วางแผนเที่ยวของ TripMate Thailand AI
ตอบเป็นภาษาไทย กระชับ ชัดเจน และใช้ข้อมูลจากฐานความรู้เท่านั้นถ้าเป็นข้อมูลเฉพาะ
ถ้าเป็นราคา ให้บอกว่าเป็นการประเมินเบื้องต้น

ข้อมูล:
{context}

คำถาม:
{question}
"""
            try:
                resp = client.models.generate_content(model=MODEL, contents=prompt)
                ai_answer = resp.text
            except Exception:
                ai_answer = "ตอนนี้เรียก Gemini API ไม่สำเร็จ จึงแสดงข้อมูลจากฐานความรู้แทน:\n\n" + context
        else:
            ai_answer = "ยังไม่ได้ตั้งค่า GOOGLE_API_KEY จึงแสดงข้อมูลจากฐานความรู้แทน:\n\n" + context

        st.chat_message("assistant").markdown(ai_answer)

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
