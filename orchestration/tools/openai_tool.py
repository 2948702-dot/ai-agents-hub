"""ChatGPT (OpenAI) — инструмент для Claude-оркестратора."""

import os
from openai import OpenAI

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def query_chatgpt(prompt: str, system: str = "You are a helpful assistant.", model: str = "gpt-4o") -> str:
    """
    Отправить запрос к ChatGPT и вернуть текстовый ответ.

    Args:
        prompt: Пользовательский запрос
        system: Системный промпт
        model: Модель OpenAI (по умолчанию gpt-4o)

    Returns:
        Текстовый ответ ChatGPT
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
    )
    return response.choices[0].message.content
