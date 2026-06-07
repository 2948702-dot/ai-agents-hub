"""
Research Agent — агент для исследования темы.
Использует Claude как основной мозг, ChatGPT как второй источник.
"""

import sys
from pathlib import Path

# Добавить корень репозитория в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.orchestrator import run


def research(topic: str) -> str:
    """
    Исследовать тему.

    Args:
        topic: Тема для исследования

    Returns:
        Структурированный отчёт
    """
    task = f"""
Исследуй следующую тему и подготовь структурированный отчёт:

ТЕМА: {topic}

Включи:
1. Краткий обзор (2-3 предложения)
2. Ключевые факты и цифры
3. Текущие тренды
4. Неочевидные инсайты

Дополнительно: получи второе мнение от ChatGPT по ключевым тезисам
и отметь, где мнения совпадают, а где расходятся.
"""
    return run(task=task, verbose=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Research Agent")
    parser.add_argument("topic", help="Тема для исследования")
    args = parser.parse_args()

    result = research(args.topic)
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("="*60)
    print(result)
