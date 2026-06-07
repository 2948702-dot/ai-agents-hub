# Деплой на GitHub

## 1. Создать репозиторий на GitHub

```bash
# Войти в папку
cd ai-agents-hub

# Инициализировать git
git init
git add .
git commit -m "feat: initial AI agents hub setup"

# Создать репо на github.com, затем:
git remote add origin https://github.com/YOUR_USERNAME/ai-agents-hub.git
git branch -M main
git push -u origin main
```

## 2. Добавить секреты в GitHub

GitHub → Settings → Secrets and variables → Actions → New repository secret:

| Имя | Значение |
|-----|----------|
| `ANTHROPIC_API_KEY` | Ключ с console.anthropic.com |
| `OPENAI_API_KEY` | Ключ с platform.openai.com |
| `BASE44_API_KEY` | Ключ с base44.com |
| `ANTIGRAVITY_API_KEY` | Ключ Antigravity |

## 3. Запустить локально

```bash
# Установить зависимости
pip install -r requirements.txt

# Скопировать и заполнить .env
cp .env.example .env

# Запустить агента
python orchestration/orchestrator.py --task "Твоя задача здесь"

# Или через Research Agent
python agents/research_agent/agent.py "Тема для исследования"
```
