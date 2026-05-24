# replai-ai

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Cloud-E97627)](https://www.trychroma.com/)
[![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-Vertex_AI-4285F4?logo=google&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Redis](https://img.shields.io/badge/Upstash_Redis-48h_TTL-DC382D?logo=redis&logoColor=white)](https://upstash.com/)

> Stateless AI-сервис платформы replAI. RAG-пайплайн на базе ChromaDB, контекстные диалоги через Vertex AI Gemini 2.0 Flash, скоринг лидов и Telegram-интеграция.

---

## ИИ-архитектура

```
POST /chat/
    │
    ├─ 1. search_knowledge_base(bot_id, message)
    │       └─ ChromaDB: top-3 chunks из коллекции bot-{bot_id}
    │
    ├─ 2. _load_history(chat_id)
    │       └─ Upstash Redis: последние 40 сообщений (TTL 48h)
    │
    ├─ 3. GenerativeModel(system_prompt + RAG-контекст)
    │       └─ Vertex AI Gemini 2.0 Flash
    │
    ├─ 4. _save_history(chat_id, chat.history)
    │       └─ Redis: обновить слайдинг-окно
    │
    └─ 5. detect_intent(message)
            └─ → {"reply": str, "is_lead": bool, "lead_summary": str | null}
```

---

## Ключевые ИИ-фичи

### RAG-архитектура (Retrieval-Augmented Generation)

Каждый бот имеет изолированную векторную коллекцию в ChromaDB. При входящем сообщении система ищет top-3 релевантных чанка из базы знаний компании и инжектирует их в системный промпт перед отправкой в LLM.

```python
# Чанкование при загрузке (размер 800 символов, перекрытие 150)
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Поиск при ответе
results = col.query(query_texts=[query], n_results=min(3, col.count()))
```

Контекст из базы знаний обёрнут в специальный блок-маркер, который системный промпт запрещает AI исполнять как инструкции — защита от Prompt Injection через загруженные документы.

### Изоляция векторных коллекций (bot-{id} prefix)

ChromaDB требует имена коллекций длиной ≥ 3 символа. Числовые `bot_id` (например, `"2"`) нарушают это ограничение. Решение: единая функция `_col_name(bot_id)` с префиксацией:

```python
def _col_name(bot_id: str) -> str:
    return f"bot-{bot_id}"   # "2" → "bot-2" (5 символов)
```

Все операции (create, query, delete) проходят через эту функцию — консистентность гарантирована.

### Скоринг лидов за один проход

`detect_intent()` анализирует сообщение пользователя и возвращает три поля, которые бэкенд записывает в `Chat`:

| Поле | Тип | Описание |
|---|---|---|
| `reply` | `str` | Ответ AI (может содержать `\|\|\|` — разбивается на несколько сообщений Telegram) |
| `is_lead` | `bool` | Клиент проявил покупательский интент |
| `lead_summary` | `str\|null` | Краткое резюме: что хочет купить, телефон, имя |

### Многосообщенческие ответы

Длинный ответ разбивается по разделителю `|||` и отправляется отдельными сообщениями Telegram с паузой — имитирует набор текста живым менеджером:

```
"Отлично, помогу! ||| Подарок для кого — мужчина или женщина?"
→ сообщение 1: "Отлично, помогу!"
→ сообщение 2: "Подарок для кого — мужчина или женщина?"
```

### Защита от Prompt Injection

Системный промпт содержит явные guardrail-инструкции против:
- `"ignore previous instructions"` / `"забудь предыдущие инструкции"`
- Попыток сменить роль (DAN, GPT, другое имя)
- Запросов раскрыть системный промпт
- Задач вне области продаж (код, стихи, математика)

---

## API

### `POST /chat/`

```http
POST /chat/
X-Internal-Key: <AI_SERVICE_INTERNAL_KEY>
Content-Type: application/json

{
  "botId": 42,
  "chatId": "telegram:123456789",
  "message": "Хочу купить что-нибудь в подарок",
  "systemPrompt": "..."  // опционально — кастомный промпт из БД
}
```

**Ответ:**
```json
{
  "reply": "Отлично, помогу подобрать! 🎁 ||| Подарок для кого — мужчина или женщина?",
  "is_lead": false,
  "lead_summary": null
}
```

### `POST /knowledge/upload`

```http
POST /knowledge/upload
X-Internal-Key: <key>
Content-Type: multipart/form-data

bot_id=42
file=<binary>
```

Поддерживаемые форматы: `.pdf`, `.docx`, `.txt`. Лимит: 5 MB (контролируется бэкендом).

### `DELETE /knowledge/{bot_id}`

Удаляет ChromaDB-коллекцию `bot-{bot_id}` целиком.

### `GET /health`

```json
{"status": "ok"}
```

---

## Локальная разработка

### Требования

- Python 3.10+
- Аккаунты: Google Cloud (Vertex AI), ChromaDB Cloud, Upstash Redis

### Установка

```bash
git clone https://github.com/ksulaimanov/replai-ai.git
cd replai-ai
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Переменные окружения (`.env`)

```env
GOOGLE_CLOUD_PROJECT_ID=your_project_id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.0-flash-001
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
CHROMA_API_KEY=your_key
CHROMA_TENANT=your_tenant
CHROMA_DATABASE=your_database
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=your_token
AI_SERVICE_INTERNAL_KEY=secret
```

Поместите `flashly-vertex.json` (Google Service Account Key) в корень `replai-ai/`.

### Запуск

```bash
uvicorn main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`

---

## Docker

```bash
docker build -t replai-ai:latest .
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  replai-ai:latest
```

Для продакшена используйте `docker-compose.yml` из корневого репозитория.

---

## Структура проекта

```
replai-ai/
├── main.py                   FastAPI app + Telegram lifespan
├── routers/
│   ├── chat.py               POST /chat/ — основной LLM-эндпоинт
│   ├── knowledge.py          POST /knowledge/upload, DELETE /knowledge/{bot_id}
│   ├── health.py             GET /health
│   └── dependencies.py       X-Internal-Key верификация
├── services/
│   ├── llm_service.py        Vertex AI GenerativeModel + история чата
│   ├── rag_service.py        ChromaDB: chunking, indexing, semantic search
│   ├── intent_service.py     Скоринг лидов (is_lead, lead_summary)
│   └── file_parser.py        Парсинг PDF / DOCX / TXT
└── bot/
    └── telegram_bot.py       aiogram 3 polling bot (фоновый lifespan-task)
```

---

## Контакты

Email: [ksulaimanov.dev@gmail.com](mailto:ksulaimanov.dev@gmail.com) · Telegram: [@ksulaimanov](https://t.me/ksulaimanov)
