from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.records import RecordCreateRequest, RecordCreateResponse, RecordGenerateRequest
from app.services.records import create_record, generate_record_stream

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


@router.post("", response_model=RecordCreateResponse, status_code=status.HTTP_201_CREATED, summary="기록 저장")
async def create_record_route(
    payload: RecordCreateRequest,
    user: User = Depends(get_current_user)
):
    return await create_record(user, payload)
