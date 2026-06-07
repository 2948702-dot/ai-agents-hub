"""Base44 — инструмент для деплоя веб-приложений из Claude-оркестратора."""

import os
import requests

BASE44_API_URL = "https://api.base44.com/v1"


def deploy_to_base44(spec: str, app_id: str | None = None) -> str:
    """
    Создать или обновить приложение в Base44.

    Args:
        spec: Описание приложения / компонента (естественный язык или код)
        app_id: ID существующего приложения (если обновление)

    Returns:
        URL задеплоенного приложения или статус операции
    """
    api_key = os.environ.get("BASE44_API_KEY")
    if not api_key:
        return "[Base44] API ключ не задан. Установите BASE44_API_KEY в .env"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {"spec": spec}
    if app_id:
        payload["app_id"] = app_id

    try:
        endpoint = f"{BASE44_API_URL}/apps"
        method = "put" if app_id else "post"
        response = getattr(requests, method)(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return f"[Base44] Приложение задеплоено: {data.get('url', data)}"
    except requests.RequestException as e:
        return f"[Base44] Ошибка: {e}"
