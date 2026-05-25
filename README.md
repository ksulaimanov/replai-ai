# replai-ai

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Cloud-E97627)](https://www.trychroma.com/)
[![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-Vertex_AI-4285F4?logo=google&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Redis](https://img.shields.io/badge/Upstash_Redis-48h_TTL-DC382D?logo=redis&logoColor=white)](https://upstash.com/)

> Stateless AI service of the replAI platform. RAG pipeline powered by ChromaDB, context-aware conversations via Vertex AI Gemini 2.0 Flash, lead scoring, and Telegram integration.

---

## AI Architecture

```
POST /chat/
    │
    ├─ 1. ChromaDB Collection Query: search_knowledge_base(bot_id, message)
    │       └─ top-3 chunks from collection bot-{bot_id}
    │
    ├─ 2. _load_history(chat_id)
    │       └─ Upstash Redis: last 40 messages (TTL 48h)
    │
    ├─ 3. Context-Aware LLM Inference: GenerativeModel(system_prompt + RAG context)
    │       └─ Vertex AI Gemini 2.0 Flash
    │
    ├─ 4. _save_history(chat_id, chat.history)
    │       └─ Redis: update sliding window
    │
    └─ 5. detect_intent(message)
            └─ → {"reply": str, "is_lead": bool, "lead_summary": str | null}
```

---

## Key AI Features

### RAG Architecture (Retrieval-Augmented Generation)

Each bot maintains an isolated vector collection in ChromaDB. On every incoming message the system performs a ChromaDB Collection Query to retrieve the top-3 most relevant chunks from the company's Knowledge Base (KB) and injects them into the system prompt before forwarding to the LLM — this is Context-Aware LLM Inference.

```python
# Document Chunking at upload time (chunk size 800 chars, overlap 150)
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# ChromaDB Collection Query at inference time
results = col.query(query_texts=[query], n_results=min(3, col.count()))
```

The Knowledge Base context is wrapped in a dedicated marker block. The system prompt explicitly instructs the AI not to execute it as instructions — protection against Prompt Injection via uploaded documents.

### Vector Collection Isolation — Dynamic Multi-Tenant Vector Space Partitioning

Dynamic multi-tenant vector space partitioning using `bot-{id}` prefixing to comply with ChromaDB character constraints: ChromaDB requires collection names to be at least 3 characters long. Numeric `bot_id` values (e.g., `"2"`) violate this constraint. The solution: a single `_col_name(bot_id)` function with consistent prefixing:

```python
def _col_name(bot_id: str) -> str:
    return f"bot-{bot_id}"   # "2" → "bot-2" (5 characters)
```

All operations (create, query, delete) route through this function — namespace consistency is guaranteed across the entire multi-tenant vector space.

### Single-Pass Lead Scoring

`detect_intent()` analyses the user's message and returns three fields that the backend writes to `Chat`:

| Field | Type | Description |
|---|---|---|
| `reply` | `str` | AI response (may contain `\|\|\|` — split into multiple Telegram messages) |
| `is_lead` | `bool` | Customer has expressed purchase intent |
| `lead_summary` | `str\|null` | Brief summary: what they want to buy, phone number, name |

### Multi-Message Responses

A long reply is split on the `|||` delimiter and sent as separate Telegram messages with a pause — simulating a live sales manager typing in real time:

```
"Great, I can help! ||| Who is the gift for — a man or a woman?"
→ message 1: "Great, I can help!"
→ message 2: "Who is the gift for — a man or a woman?"
```

### Prompt Injection Protection

The system prompt contains explicit guardrail instructions against:
- `"ignore previous instructions"` and equivalent phrases
- Role-switching attempts (DAN, GPT, alternate persona names)
- Requests to reveal the system prompt
- Off-topic tasks outside the sales domain (code generation, poetry, mathematics)

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
  "message": "I want to buy something as a gift",
  "systemPrompt": "..."  // optional — custom prompt from the database
}
```

**Response:**
```json
{
  "reply": "Great, I can help you find something! 🎁 ||| Who is the gift for — a man or a woman?",
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

Supported formats: `.pdf`, `.docx`, `.txt`. Limit: 5 MB (enforced by the backend).

### `DELETE /knowledge/{bot_id}`

Deletes the ChromaDB collection `bot-{bot_id}` in its entirety.

### `GET /health`

```json
{"status": "ok"}
```

---

## Local Development

### Prerequisites

- Python 3.10+
- Accounts: Google Cloud (Vertex AI), ChromaDB Cloud, Upstash Redis

### Installation

```bash
git clone https://github.com/ksulaimanov/replai-ai.git
cd replai-ai
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Environment Variables (`.env`)

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

Place `flashly-vertex.json` (Google Service Account Key) in the root of `replai-ai/`.

### Run

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

For production use the `docker-compose.yml` from the root repository.

---

## Project Structure

```
replai-ai/
├── main.py                   FastAPI app + Telegram lifespan
├── routers/
│   ├── chat.py               POST /chat/ — primary LLM endpoint
│   ├── knowledge.py          POST /knowledge/upload, DELETE /knowledge/{bot_id}
│   ├── health.py             GET /health
│   └── dependencies.py       X-Internal-Key verification
├── services/
│   ├── llm_service.py        Vertex AI GenerativeModel + chat history management
│   ├── rag_service.py        ChromaDB: Document Chunking, Gemini Vector Embeddings, semantic search
│   ├── intent_service.py     Lead scoring (is_lead, lead_summary)
│   └── file_parser.py        PDF / DOCX / TXT parsing
└── bot/
    └── telegram_bot.py       aiogram 3 polling bot (background lifespan task)
```

---

## Contact

Email: [ksulaimanov.dev@gmail.com](mailto:ksulaimanov.dev@gmail.com) · Telegram: [@ksulaimanov](https://t.me/ksulaimanov)
