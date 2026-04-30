# Caption generator for MilkLab cafe Instagram posts
# - Load GOOGLE_API_KEY from .env file
# - Use Gemini 2.5 Flash to generate 3 caption variants
# - Take menu name and price as input
# - Output: 3 caption styles (cute, minimal, gen-z)

from __future__ import annotations

import argparse
import json
import os
import re
import time

from dotenv import load_dotenv
import warnings

try:
    import google.genai as genai
    USE_NEW_SDK = True
except ModuleNotFoundError:
    warnings.filterwarnings(
        "ignore",
        message="All support for the `google.generativeai` package has ended.*",
        category=FutureWarning,
    )
    import google.generativeai as genai  # fallback for older environments
    USE_NEW_SDK = False

MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "models/gemini-2.5-flash")
MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "models/gemini-2.5-flash-lite")
FALLBACK_MODEL_NAME = os.getenv("GOOGLE_FALLBACK_MODEL_NAME", "")
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("หา GOOGLE_API_KEY ในไฟล์ .env ไม่เจอเลย")
    return api_key


def build_prompt(menu_name: str, price: str) -> str:
    return (
        "You are a creative caption writer for MilkLab cafe Instagram posts.\n"
        f"Create 3 caption variants for the menu item '{menu_name}' priced at {price}.\n"
        "Write the captions in Thai using a friendly, casual tone.\n"
        "Use three distinct styles: cute, minimal, and gen-z.\n"
        "Return the response as valid JSON with keys: cute, minimal, gen-z.\n"
        "Do not include any additional explanation, headers, or commentary."
    )


def format_api_error(exc: Exception) -> str:
    error_text = str(exc)
    if "PERMISSION_DENIED" in error_text or "denied access" in error_text.lower():
        return (
            "โปรเจกต์ของคุณถูกปฏิเสธการเข้าถึง Gemini API. "
            "ตรวจสอบว่า Google Cloud project ของคุณมีสิทธิ์ใช้ Gemini, "
            "ว่า API key ถูกต้อง และว่าบริการ Gemini ถูกเปิดใช้งานแล้ว."
        )
    if "UNAUTHENTICATED" in error_text or "invalid_api_key" in error_text.lower():
        return "ไม่สามารถยืนยันตัวตนได้ โปรดตรวจสอบค่า GOOGLE_API_KEY ในไฟล์ .env และสิทธิ์ API key."
    if "503" in error_text or "unavailable" in error_text.lower() or "rate_limit" in error_text.lower() or "rate limit" in error_text.lower():
        return (
            "ระบบ Gemini ช่วงนี้มีการใช้งานสูง ลองรันใหม่อีกครั้งในไม่กี่วินาที หรือใช้โมเดลสำรองด้วยตัวแปรสภาพแวดล้อม GOOGLE_FALLBACK_MODEL_NAME."
        )
    return "ลองเช็ค API key, สิทธิ์โปรเจกต์, และสิทธิ์ Gemini หน่อยสิ."


def should_retry(exc: Exception) -> bool:
    error_text = str(exc).lower()
    return any(token in error_text for token in ["503", "unavailable", "429", "rate_limit", "rate limit", "timeout"])


def normalize_caption_key(key: str) -> str:
    normalized = key.strip().lower().replace("_", "-").replace(" ", "-")
    if normalized == "genz":
        normalized = "gen-z"
    return normalized


def parse_captions(response_text: str) -> dict[str, str]:
    response_text = response_text.strip()
    if response_text.startswith("{"):
        try:
            parsed_json = json.loads(response_text)
            parsed = {
                normalize_caption_key(k): str(v).strip()
                for k, v in parsed_json.items()
            }
            return {
                "cute": parsed.get("cute", ""),
                "minimal": parsed.get("minimal", ""),
                "gen-z": parsed.get("gen-z", ""),
            }
        except json.JSONDecodeError:
            pass

    parsed = {
        "cute": "",
        "minimal": "",
        "gen-z": "",
    }

    for line in response_text.splitlines():
        line = line.strip()
        if not line or line.startswith("{") or line.startswith("}"):
            continue
        match = re.match(r'^(cute|minimal|gen[- ]?z)\s*[:\-]\s*(.+)$', line, re.IGNORECASE)
        if match:
            key = normalize_caption_key(match.group(1))
            parsed[key] = match.group(2).strip().strip('"')

    if all(parsed.values()):
        return parsed

    for label in parsed:
        pattern = label.replace("-", "[- ]?")
        regex = re.compile(rf"{pattern}.*?[:\-]\s*(.+)", re.IGNORECASE)
        match = regex.search(response_text)
        if match:
            parsed[label] = match.group(1).strip().strip('"')

    return parsed


def create_chat_response(api_key: str, model_name: str, prompt: str) -> str:
    if USE_NEW_SDK:
        client = genai.Client(api_key=api_key)
        chat = client.chats.create(model=model_name)
        response = chat.send_message(prompt)
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        chat = model.start_chat()
        response = chat.send_message(prompt)

    return response.text


def generate_captions(menu_name: str, price: str) -> dict[str, str]:
    api_key = load_api_key()
    prompt = build_prompt(menu_name, price)
    model_names = [MODEL_NAME]
    if FALLBACK_MODEL_NAME and FALLBACK_MODEL_NAME != MODEL_NAME:
        model_names.append(FALLBACK_MODEL_NAME)

    last_exception: Exception | None = None
    response_text = ""

    for model_name in model_names:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response_text = create_chat_response(api_key, model_name, prompt)
                break
            except Exception as exc:
                last_exception = exc
                if attempt < MAX_RETRIES and should_retry(exc):
                    wait = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                    time.sleep(wait)
                    continue
                break
        if response_text:
            break

    if not response_text:
        raise RuntimeError(
            "ขอโทษนะ แต่เรียก API ไม่ได้ "
            f"{format_api_error(last_exception or Exception('ไม่มีข้อความข้อผิดพลาด'))} "
            f"ข้อผิดพลาดเดิม: {last_exception}"
        )

    captions = parse_captions(response_text)
    if not all(captions.values()):
        raise RuntimeError(
            "ผลลัพธ์จาก API ไม่ครบตามที่คาดไว้: ต้องมี cute, minimal, gen-z.\n"
            f"Raw response: {response_text}"
        )

    return captions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="สร้าง 3 แบบคำบรรยายสำหรับโพสต์ Instagram ของคาเฟ่ MilkLab"
    )
    parser.add_argument("menu_name", help="ชื่อเมนู")
    parser.add_argument("price", help="ราคาเมนู")
    args = parser.parse_args()

    captions = generate_captions(args.menu_name, args.price)

    print(json.dumps(captions, indent=2, ensure_ascii=False))
        


if __name__ == "__main__":
    main()