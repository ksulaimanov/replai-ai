import os
import json
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
from upstash_redis import Redis
from services.rag_service import search_knowledge_base

load_dotenv()

_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "woven-edge-496806-f2")
_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
_MODEL_NAME = os.getenv("VERTEX_AI_MODEL", "gemini-2.0-flash-001")

_SA_KEY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "flashly-vertex.json")
_credentials = Credentials.from_service_account_file(
    _SA_KEY_PATH,
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

vertexai.init(project=_PROJECT, location=_LOCATION, credentials=_credentials)

_redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

_HISTORY_TTL = 172800  # 48 часов
_MAX_HISTORY = 40

_SYSTEM_PROMPT = """Ты — живой менеджер по продажам. Твоё имя — Алина.

Правила поведения:
- Никогда не признавайся, что ты AI или бот. Ты живой человек.
- Пиши коротко, по-человечески, дружелюбно.
- Задавай уточняющие вопросы: для кого, какой бюджет, какой размер, какие предпочтения.
- Не выдавай всё сразу — веди диалог, как настоящий менеджер.
- Когда клиент готов купить — попроси контакт: номер телефона или имя для оформления.
- Язык общения: русский.

Когда делить ответ на несколько сообщений через |||:
- Когда сначала даёшь информацию, а потом задаёшь вопрос
- Когда перечисляешь несколько отдельных мыслей или вариантов
- Когда первое сообщение — реакция (понял, окей, отлично), а второе — уточнение
- Максимум 3 части

Когда НЕ делить (один ответ):
- Короткий ответ на простой вопрос
- Одна мысль без продолжения
- Ответ в 1-2 предложения

Примеры:

Клиент: Хочу купить что-нибудь в подарок
Ты: Отлично, помогу подобрать! 🎁 ||| Подарок для кого — мужчина или женщина? И примерный бюджет есть?

Клиент: Сколько стоит доставка?
Ты: Доставка бесплатная при заказе от 5000 рублей, иначе 300 рублей.

Клиент: Хочу купить, как оформить?
Ты: Супер, оформим прямо сейчас! ||| Скажите ваше имя и номер телефона — свяжусь в течение пары минут 😊"""


def _load_history(chat_id: str) -> list[Content]:
    raw = _redis.get(f"history:{chat_id}")
    if not raw:
        return []
    data = json.loads(raw) if isinstance(raw, str) else raw
    return [
        Content(role=d["role"], parts=[Part.from_text(p["text"]) for p in d["parts"]])
        for d in data
    ]


def _save_history(chat_id: str, history: list[Content]) -> None:
    data = [
        {"role": c.role, "parts": [{"text": p.text} for p in c.parts]}
        for c in history[-_MAX_HISTORY:]
    ]
    _redis.set(f"history:{chat_id}", json.dumps(data, ensure_ascii=False), ex=_HISTORY_TTL)


def get_ai_response(bot_id: int, chat_id: str, message: str, system_prompt: str | None = None) -> str:
    context = search_knowledge_base(str(bot_id), message)

    system = system_prompt.strip() if system_prompt and system_prompt.strip() else _SYSTEM_PROMPT
    if context:
        system += f"\n\nИнформация о продуктах/услугах компании (используй это):\n{context}"

    model = GenerativeModel(_MODEL_NAME, system_instruction=[system])

    history = _load_history(chat_id)
    chat = model.start_chat(history=history)
    response = chat.send_message(message)
    reply = response.text

    _save_history(chat_id, list(chat.history))

    return reply
