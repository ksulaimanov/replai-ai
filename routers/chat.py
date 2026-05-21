import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from services.llm_service import get_ai_response
from services.intent_service import detect_intent
from routers.dependencies import verify_internal_key

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_internal_key)])


class ChatRequest(BaseModel):
    bot_id: int = Field(..., alias="botId")
    chat_id: str = Field(..., alias="chatId")
    message: str
    system_prompt: Optional[str] = Field(None, alias="systemPrompt")

    class Config:
        populate_by_name = True


@router.post("/")
async def chat(req: ChatRequest):
    reply = await asyncio.to_thread(
        get_ai_response, req.bot_id, req.chat_id, req.message, req.system_prompt
    )
    is_lead, lead_summary = detect_intent(req.message)
    return {"reply": reply, "is_lead": is_lead, "lead_summary": lead_summary}
