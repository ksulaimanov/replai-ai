from fastapi import APIRouter
from pydantic import BaseModel
from services.llm_service import get_ai_response

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    bot_id: str
    chat_id: str
    message: str


@router.post("/")
async def chat(req: ChatRequest):
    reply = get_ai_response(req.bot_id, req.chat_id, req.message)
    return {"reply": reply}
