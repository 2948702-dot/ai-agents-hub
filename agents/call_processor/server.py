"""
FastAPI сервер для Call Processor Agent.
Base44 приложение отправляет аудио сюда → получает JSON с деталями заказа.
"""

import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agent import transcribe_audio, extract_order, create_calendar_event

app = FastAPI(title="Call Processor API", version="1.0.0")

# CORS — разрешить Base44 и localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConfirmRequest(BaseModel):
    order: dict


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process-call")
async def process_call(audio: UploadFile = File(...)):
    """
    Принять аудиофайл, транскрибировать и извлечь детали заказа.
    Возвращает JSON с деталями — менеджер подтверждает в интерфейсе.
    """
    allowed = {".mp3", ".wav", ".m4a", ".ogg", ".webm", ".mp4"}
    suffix = Path(audio.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Формат не поддерживается: {suffix}")

    # Сохранить во временный файл
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        transcript = transcribe_audio(tmp_path)
        order = extract_order(transcript)
        order["transcript"] = transcript
        return {"success": True, "order": order}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        os.unlink(tmp_path)


@app.post("/confirm-order")
async def confirm_order(req: ConfirmRequest):
    """
    Менеджер подтвердил заказ — создаём событие в Google Calendar.
    """
    try:
        event_url = create_calendar_event(req.order)
        return {"success": True, "event_url": event_url}
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
