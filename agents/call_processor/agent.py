"""
Call Processor Agent — Фиксатор звонков
=======================================
Транскрибирует запись звонка, извлекает детали заказа (аренда лодки)
и создаёт событие в Google Calendar.

Стек:
  - OpenAI Whisper  — транскрибация аудио
  - Claude          — извлечение структурированных данных из текста
  - Google Calendar — создание события
"""

import os
import json
import anthropic
from openai import OpenAI
from datetime import datetime, timedelta
from pathlib import Path


# ── Клиенты ───────────────────────────────────────────────────────────────────
anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ── Системный промпт для извлечения заказа ───────────────────────────────────
EXTRACTION_PROMPT = """Ты — ассистент менеджера компании по аренде лодок и водным прогулкам.

Тебе дана транскрипция телефонного разговора с клиентом.
Извлеки детали заказа и верни их СТРОГО в формате JSON.

Поля для извлечения:
- date: дата в формате YYYY-MM-DD (если "завтра" — вычисли от сегодня)
- time_start: время начала HH:MM (24ч формат)
- time_end: время окончания HH:MM (24ч формат)
- boat_name: название лодки/судна
- guests: количество гостей (число)
- services: список дополнительных услуг (бокалы, фуршет, музыка и т.д.)
- payment: способ оплаты
- client_name: имя клиента (если упомянуто, иначе null)
- client_phone: телефон клиента (если упомянуто, иначе null)
- notes: любые важные примечания
- is_order: true если это подтверждённый заказ, false если просто консультация

Сегодняшняя дата: {today}

Верни ТОЛЬКО JSON, без пояснений. Пример:
{{
  "date": "2026-06-08",
  "time_start": "15:00",
  "time_end": "19:00",
  "boat_name": "Рапсодия",
  "guests": 4,
  "services": ["бокалы", "фуршет от Гранд Фуршет"],
  "payment": "картой на месте",
  "client_name": null,
  "client_phone": null,
  "notes": "",
  "is_order": true
}}"""


def transcribe_audio(audio_path: str) -> str:
    """Транскрибировать аудиофайл через OpenAI Whisper."""
    print(f"🎙️  Транскрибирую: {audio_path}")
    with open(audio_path, "rb") as audio_file:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ru",
        )
    print(f"✅ Транскрипция готова ({len(transcript.text)} символов)")
    return transcript.text


def extract_order(transcript: str) -> dict:
    """Извлечь детали заказа из транскрипции с помощью Claude."""
    print("🤖 Анализирую разговор...")
    today = datetime.now().strftime("%Y-%m-%d")

    response = anthropic_client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT.format(today=today)}\n\nТранскрипция:\n{transcript}",
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Убрать markdown-блоки если есть
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    order = json.loads(raw)
    print(f"✅ Заказ извлечён: {order.get('boat_name')} на {order.get('date')}")
    return order


def create_calendar_event(order: dict, calendar_id: str = "primary") -> str:
    """Создать событие в Google Calendar."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    import pickle

    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None
    token_path = Path(__file__).parent / "token.pickle"
    creds_path = Path(__file__).parent / "credentials.json"

    if token_path.exists():
        with open(token_path, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)

    service = build("calendar", "v3", credentials=creds)

    # Сформировать название события
    title_parts = []
    if order.get("boat_name"):
        title_parts.append(f"🚢 {order['boat_name']}")
    if order.get("guests"):
        title_parts.append(f"{order['guests']} чел.")
    title = " | ".join(title_parts) if title_parts else "Аренда лодки"

    # Сформировать описание
    desc_lines = []
    if order.get("client_name"):
        desc_lines.append(f"👤 Клиент: {order['client_name']}")
    if order.get("client_phone"):
        desc_lines.append(f"📞 Тел: {order['client_phone']}")
    if order.get("guests"):
        desc_lines.append(f"👥 Гостей: {order['guests']}")
    if order.get("services"):
        desc_lines.append(f"✨ Услуги: {', '.join(order['services'])}")
    if order.get("payment"):
        desc_lines.append(f"💳 Оплата: {order['payment']}")
    if order.get("notes"):
        desc_lines.append(f"📝 Примечания: {order['notes']}")

    description = "\n".join(desc_lines)

    # Создать событие
    date = order["date"]
    start_dt = f"{date}T{order['time_start']}:00"
    end_dt = f"{date}T{order['time_end']}:00"

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt, "timeZone": "Europe/Moscow"},
        "end": {"dateTime": end_dt, "timeZone": "Europe/Moscow"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},
            ],
        },
    }

    created = service.events().insert(calendarId=calendar_id, body=event).execute()
    event_url = created.get("htmlLink")
    print(f"✅ Событие создано: {event_url}")
    return event_url


def process_call(audio_path: str, auto_confirm: bool = False) -> dict:
    """
    Полный цикл обработки звонка.

    Args:
        audio_path: Путь к аудиофайлу
        auto_confirm: Создать событие без подтверждения

    Returns:
        Словарь с деталями заказа и ссылкой на событие
    """
    # 1. Транскрибация
    transcript = transcribe_audio(audio_path)

    # 2. Извлечение заказа
    order = extract_order(transcript)
    order["transcript"] = transcript

    if not order.get("is_order"):
        print("ℹ️  Это консультация, заказ не обнаружен.")
        return order

    # 3. Показать менеджеру
    print("\n" + "="*50)
    print("📋 ДЕТАЛИ ЗАКАЗА:")
    print(f"  Лодка:   {order.get('boat_name', '—')}")
    print(f"  Дата:    {order.get('date', '—')}")
    print(f"  Время:   {order.get('time_start', '—')} – {order.get('time_end', '—')}")
    print(f"  Гостей:  {order.get('guests', '—')}")
    print(f"  Услуги:  {', '.join(order.get('services', []))}")
    print(f"  Оплата:  {order.get('payment', '—')}")
    print("="*50)

    # 4. Подтверждение
    if not auto_confirm:
        confirm = input("\nДобавить в Google Calendar? (y/n): ").strip().lower()
        if confirm != "y":
            print("Отменено.")
            return order

    # 5. Создание события
    event_url = create_calendar_event(order)
    order["calendar_event_url"] = event_url
    return order


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Call Processor Agent")
    parser.add_argument("audio", help="Путь к аудиофайлу (.mp3, .wav, .m4a, .ogg)")
    parser.add_argument("--auto", action="store_true", help="Создать событие без подтверждения")
    args = parser.parse_args()

    result = process_call(args.audio, auto_confirm=args.auto)
    print(f"\n✅ Готово! {result.get('calendar_event_url', '')}")
