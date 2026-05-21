import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, knowledge, health
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="replAi AI")

_cors_origins = [o.strip() for o in os.getenv("APP_DOMAIN", "http://replai-backend:8080").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["X-Internal-Key", "Content-Type"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(knowledge.router)
