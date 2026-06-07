"""
Orchestrator — Claude как главный мозг.
Принимает задачу, планирует шаги, вызывает нужные инструменты,
возвращает финальный результат.
"""

import os
import json
import anthropic
from pathlib import Path
from orchestration.tools.openai_tool import query_chatgpt
from orchestration.tools.base44_tool import deploy_to_base44
from orchestration.tools.antigravity_tool import call_antigravity

# ── Конфигурация ──────────────────────────────────────────────────────────────
ANTHROPIC_MODEL = "claude-opus-4-6"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


# ── Определения инструментов для Claude ───────────────────────────────────────
TOOLS = [
    {
        "name": "query_chatgpt",
        "description": (
            "Отправить запрос ChatGPT (GPT-4o). Используй когда нужно "
            "второе мнение, альтернативная генерация или сравнение ответов."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Текст запроса к ChatGPT"},
                "system": {"type": "string", "description": "Системный промпт (опционально)"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "deploy_to_base44",
        "description": (
            "Создать или обновить веб-приложение / интерфейс через Base44. "
            "Используй когда результат нужно показать в браузере."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spec": {"type": "string", "description": "Описание приложения / компонента"},
                "app_id": {"type": "string", "description": "ID существующего приложения (если обновление)"},
            },
            "required": ["spec"],
        },
    },
    {
        "name": "call_antigravity",
        "description": (
            "Вызвать модуль Antigravity для бизнес-логики, работы с данными "
            "проекта или специализированных инструментов."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "module": {"type": "string", "description": "Имя модуля Antigravity"},
                "action": {"type": "string", "description": "Действие / метод"},
                "payload": {"type": "object", "description": "Данные для передачи"},
            },
            "required": ["module", "action"],
        },
    },
]


# ── Выполнение вызова инструмента ─────────────────────────────────────────────
def execute_tool(name: str, inputs: dict) -> str:
    if name == "query_chatgpt":
        return query_chatgpt(**inputs)
    elif name == "deploy_to_base44":
        return deploy_to_base44(**inputs)
    elif name == "call_antigravity":
        return call_antigravity(**inputs)
    else:
        return f"[Ошибка] Неизвестный инструмент: {name}"


# ── Главная функция оркестратора ──────────────────────────────────────────────
def run(task: str, verbose: bool = True) -> str:
    """
    Запустить агента с заданной задачей.

    Args:
        task: Описание задачи на естественном языке
        verbose: Печатать ли промежуточные шаги

    Returns:
        Финальный ответ агента
    """
    system_prompt = load_prompt("orchestrator")
    messages = [{"role": "user", "content": task}]

    if verbose:
        print(f"\n{'='*60}")
        print(f"Задача: {task}")
        print(f"{'='*60}\n")

    # Агентный цикл: Claude думает → вызывает инструменты → получает результаты
    while True:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # Добавить ответ ассистента в историю
        messages.append({"role": "assistant", "content": response.content})

        # Если Claude закончил — вернуть финальный текст
        if response.stop_reason == "end_turn":
            final = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            if verbose:
                print(f"\n✅ Финальный ответ:\n{final}")
            return final

        # Обработать вызовы инструментов
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if verbose:
                print(f"🔧 Вызов инструмента: {block.name}")
                print(f"   Аргументы: {json.dumps(block.input, ensure_ascii=False)}")

            result = execute_tool(block.name, block.input)

            if verbose:
                preview = str(result)[:200]
                print(f"   Результат: {preview}{'...' if len(str(result)) > 200 else ''}\n")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result),
            })

        messages.append({"role": "user", "content": tool_results})


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Agents Hub Orchestrator")
    parser.add_argument("--task", required=True, help="Задача для агента")
    parser.add_argument("--quiet", action="store_true", help="Без промежуточных логов")
    args = parser.parse_args()

    result = run(task=args.task, verbose=not args.quiet)
