# caption.py
# Caption generator for TripMate Thailand AI travel posts
from __future__ import annotations

import argparse
import json
import os
import re
import time
import warnings

from dotenv import load_dotenv

try:
    import google.genai as genai
    USE_NEW_SDK = True
except ModuleNotFoundError:
    warnings.filterwarnings("ignore", category=FutureWarning)
    import google.generativeai as genai
    USE_NEW_SDK = False

MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "models/gemini-2.5-flash-lite")
FALLBACK_MODEL_NAME = os.getenv("GOOGLE_FALLBACK_MODEL_NAME", "")
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("หา GOOGLE_API_KEY ในไฟล์ .env ไม่เจอ")
    return api_key


def build_prompt(trip_name: str, budget: str) -> str:
    return (
        "You are a creative Thai travel caption writer for TripMate Thailand AI.\n"
        f"Create 3 caption variants for this travel idea: '{trip_name}' with estimated budget {budget} THB.\n"
        "Write in Thai with a friendly tone.\n"
        "Styles: cute, minimal, gen-z.\n"
        "Mention that the budget is an estimate if needed.\n"
        "Return valid JSON only with keys: cute, minimal, gen-z."
    )


def should_retry(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(t in text for t in ["503", "unavailable", "429", "rate_limit", "rate limit", "timeout"])


def format_api_error(exc: Exception) -> str:
    text = str(exc)
    if "PERMISSION_DENIED" in text or "denied access" in text.lower():
        return "โปรเจกต์ถูกปฏิเสธการเข้าถึง Gemini API โปรดตรวจ API key และสิทธิ์โปรเจกต์"
    if "UNAUTHENTICATED" in text or "invalid_api_key" in text.lower():
        return "API key ไม่ถูกต้องหรือยังไม่ได้ตั้งค่า GOOGLE_API_KEY"
    if "429" in text or "quota" in text.lower() or "RESOURCE_EXHAUSTED" in text:
        return "โควตา Gemini API หมดหรือเรียกถี่เกินไป โปรดลองใหม่ภายหลัง"
    return "โปรดตรวจ API key, model name และสิทธิ์ Gemini API"


def normalize_caption_key(key: str) -> str:
    normalized = key.strip().lower().replace("_", "-").replace(" ", "-")
    if normalized == "genz":
        normalized = "gen-z"
    return normalized


def parse_captions(response_text: str) -> dict[str, str]:
    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = response_text.strip("`").replace("json", "", 1).strip()
    if response_text.startswith("{"):
        try:
            parsed_json = json.loads(response_text)
            parsed = {normalize_caption_key(k): str(v).strip() for k, v in parsed_json.items()}
            return {
                "cute": parsed.get("cute", ""),
                "minimal": parsed.get("minimal", ""),
                "gen-z": parsed.get("gen-z", ""),
            }
        except json.JSONDecodeError:
            pass

    parsed = {"cute": "", "minimal": "", "gen-z": ""}
    for line in response_text.splitlines():
        match = re.match(r"^(cute|minimal|gen[- ]?z)\s*[:\-]\s*(.+)$", line.strip(), re.I)
        if match:
            parsed[normalize_caption_key(match.group(1))] = match.group(2).strip().strip('"')
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


def generate_captions(trip_name: str, budget: str) -> dict[str, str]:
    api_key = load_api_key()
    prompt = build_prompt(trip_name, budget)
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
                    time.sleep(RETRY_DELAY_SECONDS * (2 ** (attempt - 1)))
                    continue
                break
        if response_text:
            break

    if not response_text:
        raise RuntimeError(f"เรียก API ไม่ได้: {format_api_error(last_exception or Exception('unknown'))}")

    captions = parse_captions(response_text)
    if not all(captions.values()):
        raise RuntimeError("ผลลัพธ์จาก API ไม่ครบ ต้องมี cute, minimal, gen-z\nRaw response: " + response_text)
    return captions


def main() -> None:
    parser = argparse.ArgumentParser(description="สร้าง 3 แคปชั่นสำหรับโปรโมตทริปท่องเที่ยว")
    parser.add_argument("trip_name", help="ชื่อทริปหรือสถานที่ เช่น ทริปบางแสน 1 วัน")
    parser.add_argument("budget", help="งบประมาณโดยประมาณ")
    args = parser.parse_args()

    captions = generate_captions(args.trip_name, args.budget)
    print(json.dumps(captions, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
