# replAi

AI-powered sales manager chatbot platform built with FastAPI and Google Vertex AI (Gemini). Supports multi-bot knowledge bases, conversation history, and Telegram integration.

## Features

- **AI Sales Manager** — persona-based assistant (Alina) that leads natural sales dialogues
- **RAG (Retrieval-Augmented Generation)** — per-bot knowledge base powered by ChromaDB
- **Multi-message responses** — splits long replies into separate messages for a human feel
- **Telegram Bot** — runs alongside the REST API via async polling
- **Conversation history** — maintains context per chat with a 40-message sliding window

## Tech Stack

- **FastAPI** — REST API
- **Google Vertex AI (Gemini 2.0 Flash)** — LLM
- **ChromaDB** — vector store for knowledge base
- **aiogram 3** — Telegram bot framework

## Project Structure

```
replAi/
├── main.py                 # FastAPI app + Telegram bot lifespan
├── bot/
│   └── telegram_bot.py     # Telegram polling bot
├── routers/
│   ├── chat.py             # POST /chat/
│   ├── knowledge.py        # POST /knowledge/upload, DELETE /knowledge/{bot_id}
│   └── health.py           # GET /health
├── services/
│   ├── llm_service.py      # Vertex AI LLM + chat history
│   ├── rag_service.py      # ChromaDB vector search
│   └── file_parser.py      # Document parser (PDF, DOCX, TXT)
└── load_knowledge.py       # Script to load knowledge base
```

## Setup

1. Clone the repository
```bash
git clone https://github.com/ksulaimanov/replai-ai.git
cd replai-ai
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create `.env` file
```env
GOOGLE_CLOUD_PROJECT_ID=your_project_id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.0-flash-001
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

4. Add Google service account key `flashly-vertex.json` to the project root

5. Run
```bash
uvicorn main:app --reload
```

## API

### Send a message
```http
POST /chat/
Content-Type: application/json

{
  "bot_id": "my_bot",
  "chat_id": "user_123",
  "message": "Хочу купить что-нибудь в подарок"
}
```

### Upload knowledge base
```http
POST /knowledge/upload
Content-Type: application/json

{
  "bot_id": "my_bot",
  "text": "Текст о продуктах и услугах..."
}
```

### Delete knowledge base
```http
DELETE /knowledge/{bot_id}
```

### Health check
```http
GET /health
```

## Telegram Bot

The bot starts automatically with the server. Responses containing `|||` are split into multiple messages with a 1-second delay between them for a natural conversation feel.
