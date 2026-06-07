"""Antigravity — инструмент для бизнес-логики и данных проекта."""

import os
import requests

ANTIGRAVITY_API_URL = os.environ.get("ANTIGRAVITY_API_URL", "https://api.antigravity.ai/v1")


def call_antigravity(module: str, action: str, payload: dict | None = None) -> str:
    """
    Вызвать модуль Antigravity.

    Args:
        module: Имя модуля (например, "analytics", "crm", "content")
        action: Действие / метод (например, "get_report", "create_lead")
        payload: Данные для передачи

    Returns:
        Ответ от Antigravity API
    """
    api_key = os.environ.get("ANTIGRAVITY_API_KEY")
    if not api_key:
        return "[Antigravity] API ключ не задан. Установите ANTIGRAVITY_API_KEY в .env"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "module": module,
        "action": action,
        "data": payload or {},
    }

    try:
        response = requests.post(
            f"{ANTIGRAVITY_API_URL}/execute",
            json=body,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return f"[Antigravity] Ошибка: {e}"
