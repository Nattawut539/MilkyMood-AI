---
title: TripMate-Thailand-AI
emoji: 🧭
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.57.0
app_file: app.py
pinned: false
---

# TripMate Thailand AI

TripMate Thailand AI คือระบบผู้ช่วย AI สำหรับวางแผนท่องเที่ยวก่อนเดินทาง โดยเน้นทริปภูเขาและทะเลในประเทศไทย ผู้ใช้สามารถบอกงบประมาณ จำนวนคน จำนวนวัน สไตล์การเที่ยว และความสะดวกในการเดินทาง ระบบจะช่วยแนะนำจังหวัด สถานที่เที่ยว ที่พักใกล้เคียง ค่าใช้จ่ายโดยประมาณ แผนไป-กลับ และสรุปตัวเลือกที่เหมาะสม

## Features

- AI Travel Planner วางแพลนเที่ยวตามงบ จำนวนคน จำนวนวัน และสไตล์การเที่ยว
- แนะนำทริปภูเขาและทะเลในประเทศไทย
- ประเมินค่าใช้จ่ายเบื้องต้น เช่น เดินทาง ที่พัก อาหาร ค่าเข้าชม และเงินสำรอง
- แนะนำประเภทที่พักใกล้สถานที่ เช่น โฮสเทล โรงแรม รีสอร์ต หรือที่พักวิวธรรมชาติ
- เปรียบเทียบสถานที่ เช่น ภูเขา vs ทะเล หรือจังหวัดหนึ่งกับอีกจังหวัดหนึ่ง
- สรุปแผนไปและแผนกลับให้ครบ
- แสดงไฮไลท์สถานที่พร้อมรูปประกอบแบบ demo
- บันทึกแพลนที่ผู้ใช้สนใจลง Google Sheets และแจ้งเตือนผ่าน Telegram ได้ ถ้าเชื่อม Secrets ครบ

## ตัวอย่างคำถาม

```text
มีงบ 5000 บาท ไปทะเล 2 คน 2 วัน 1 คืน ไม่มีรถส่วนตัว แนะนำที่ไหนดี
```

```text
เปรียบเทียบเชียงใหม่กับน่าน งบ 6000 บาท ไป 3 วัน 2 คืน
```

```text
อยากเที่ยวภูเขา คนน้อย งบประหยัด ไปกับเพื่อน 3 คน
```

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Environment Variables

```env
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_MODEL_NAME=models/gemini-2.5-flash-lite
GOOGLE_SHEETS_ID=your_google_sheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Demo Day Self-Check

- [ ] Deploy URL ใช้งานได้ (เปิดทดสอบล่าสุด: __________)
- [ ] ไม่มี `.env` หรือ `*.json` ใน git history
- [ ] PIVOT.md ครบ 3 ข้อ
- [ ] README อธิบายระบบของ domain ตัวเอง ไม่ใช่ MilkLab หรือ MilkyMood
- [ ] knowledge base, prompt, UI ปรับเป็น TripMate Thailand AI แล้ว

## หมายเหตุเรื่องข้อมูล

ราคาที่พัก ค่าเดินทาง ค่าอาหาร และค่าเข้าสถานที่ในระบบนี้เป็นการประเมินเบื้องต้นสำหรับการวางแผน ผู้ใช้ควรตรวจสอบราคาจริง เวลาเปิด-ปิด และเงื่อนไขการเดินทางอีกครั้งก่อนจองหรือเดินทางจริง
