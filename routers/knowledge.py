from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.rag_service import add_to_knowledge_base, delete_knowledge_base
from routers.dependencies import verify_internal_key

router = APIRouter(prefix="/knowledge", tags=["knowledge"], dependencies=[Depends(verify_internal_key)])


class UploadRequest(BaseModel):
    bot_id: str
    text: str


@router.post("/upload")
async def upload(req: UploadRequest):
    add_to_knowledge_base(req.bot_id, req.text)
    return {"status": "ok"}


@router.delete("/{bot_id}")
async def delete(bot_id: str):
    delete_knowledge_base(bot_id)
    return {"status": "ok"}
