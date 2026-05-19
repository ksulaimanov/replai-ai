from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from services.llm_service import get_ai_response
from routers.dependencies import verify_internal_key

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_internal_key)])


class ChatRequest(BaseModel):
    bot_id: str
    chat_id: str
    message: str
    system_prompt: Optional[str] = None


@router.post("/")
async def chat(req: ChatRequest):
    reply = get_ai_response(req.bot_id, req.chat_id, req.message, req.system_prompt)
    return {"reply": reply}
