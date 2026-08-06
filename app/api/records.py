from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.records import RecordGenerateRequest
from app.services.records import generate_record_stream

router = APIRouter()


@router.post("/generate", summary="AI 기록 생성 (SSE)")
async def generate_record_route(
    payload: RecordGenerateRequest,
    _: User = Depends(get_current_user)
):
    event_stream = await generate_record_stream(payload.input)
    return StreamingResponse(
        event_stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
