# app.py
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

from rag_engine import RAGEngine

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-3.1-flash-lite-preview"


@st.cache_resource
def load_rag():
    return RAGEngine("knowledge/milklab_kb.txt")


rag = load_rag()

st.title("🥛 Demi ผู้ช่วย AI ของ MilkyMood")
st.caption("ถามเรื่องเมนู เวลาเปิด หรือข้อมูลร้านได้เลย")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("ถามอะไรเกี่ยวกับร้านได้เลย..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # RAG: Search
    context_chunks = rag.search(prompt, top_k=3)
    context = "\n---\n".join(context_chunks)

    # Generate
    full_prompt = f"""คุณคือ Demi ผู้ช่วย AI ของร้าน MilkyMood ตอบเฉพาะจากข้อมูลด้านล่าง
ถ้าไม่พบข้อมูล ให้บอกว่าไม่ทราบ อย่าแต่งข้อมูลเอง

ข้อมูลร้าน:
{context}

คำถาม: {prompt}
"""
    try:
    response = client.models.generate_content(model=MODEL, contents=full_prompt)
    answer = response.text
except Exception as e:
    st.error("เรียก Gemini API ไม่สำเร็จ")
    st.code(repr(e))
    st.stop()

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
