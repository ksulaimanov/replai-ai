from fastapi import APIRouter, Depends, File, Form, UploadFile
from services.file_parser import parse_file
from services.rag_service import add_to_knowledge_base, delete_knowledge_base
from routers.dependencies import verify_internal_key

router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(verify_internal_key)],
)


@router.post("/upload")
async def upload(bot_id: str = Form(...), file: UploadFile = File(...)):
    content = await file.read()
    text = parse_file(content, file.filename)
    add_to_knowledge_base(bot_id, text)
    return {"status": "ok", "bot_id": bot_id, "file": file.filename}


@router.delete("/{bot_id}")
async def delete(bot_id: str):
    delete_knowledge_base(bot_id)
    return {"status": "ok"}
