import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import vertexai
from vertexai.generative_models import GenerativeModel
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

# chat_id -> list[Content]
_histories: dict[str, list] = {}


def get_ai_response(bot_id: str, chat_id: str, message: str) -> str:
    context = search_knowledge_base(bot_id, message)

    system = _SYSTEM_PROMPT
    if context:
        system += f"\n\nИнформация о продуктах/услугах компании (используй это):\n{context}"

    model = GenerativeModel(_MODEL_NAME, system_instruction=[system])

    if chat_id not in _histories:
        _histories[chat_id] = []

    chat = model.start_chat(history=_histories[chat_id])
    response = chat.send_message(message)
    reply = response.text

    _histories[chat_id] = list(chat.history)

    if len(_histories[chat_id]) > 40:
        _histories[chat_id] = _histories[chat_id][-40:]

    return reply
