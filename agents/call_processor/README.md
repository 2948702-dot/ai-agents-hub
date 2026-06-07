# Call Processor Agent 🎙️ → 📅

Транскрибирует звонок с клиентом, извлекает детали заказа на аренду лодки и создаёт событие в Google Calendar.

## Как работает

```
Аудио (CUBE ACR)
      ↓
Whisper (транскрибация)
      ↓
Claude (извлечение заказа)
      ↓
Менеджер подтверждает в Base44 UI
      ↓
Google Calendar (событие создано)
```

## Установка

```bash
cd agents/call_processor
pip install -r requirements.txt
```

## Настройка Google Calendar

1. Зайди на [console.cloud.google.com](https://console.cloud.google.com)
2. Создай проект → включи Google Calendar API
3. Создай OAuth 2.0 credentials → скачай `credentials.json`
4. Положи `credentials.json` в папку `agents/call_processor/`
5. При первом запуске откроется браузер для авторизации

## Запуск API сервера

```bash
python server.py
# Сервер запустится на http://localhost:8000
```

## Запуск напрямую (без UI)

```bash
python agent.py путь/к/записи.mp3
# С авто-подтверждением:
python agent.py запись.mp3 --auto
```

## API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/process-call` | Загрузить аудио, получить детали заказа |
| POST | `/confirm-order` | Подтвердить и создать событие в Calendar |
| GET | `/health` | Проверка работоспособности |

## Пример ответа /process-call

```json
{
  "success": true,
  "order": {
    "date": "2026-06-08",
    "time_start": "15:00",
    "time_end": "19:00",
    "boat_name": "Рапсодия",
    "guests": 4,
    "services": ["бокалы", "фуршет от Гранд Фуршет"],
    "payment": "картой на месте",
    "client_name": null,
    "is_order": true
  }
}
```
