from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.base import SuccessResponse
from app.schemas.records import (
    RecordCreateRequest,
    RecordCreateResponse,
    RecordDetailResponse,
    RecordGenerateRequest,
    RecordListQuery,
    RecordListResponse,
    RecordUpdateRequest,
    RecordUpdateResponse,
    TodayRecordResponse,
)
from app.services.records import (
    create_record,
    delete_record,
    generate_record_stream,
    get_record,
    get_today_record,
    list_records,
    update_record,
)

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


@router.get("", response_model=RecordListResponse, summary="기록 목록 조회")
async def list_records_route(
    query: Annotated[RecordListQuery, Query()],
    user: User = Depends(get_current_user)
):
    return await list_records(user, query)


@router.get("/today", response_model=TodayRecordResponse, summary="오늘 기록 확인")
async def get_today_record_route(
    user: User = Depends(get_current_user)
):
    return await get_today_record(user)


@router.get("/{record_id}", response_model=RecordDetailResponse, summary="기록 상세 조회")
async def get_record_route(
    record_id: str,
    user: User = Depends(get_current_user)
):
    return await get_record(user, record_id)


@router.put("/{record_id}", response_model=RecordUpdateResponse, summary="기록 수정")
async def update_record_route(
    record_id: str,
    payload: RecordUpdateRequest,
    user: User = Depends(get_current_user)
):
    return await update_record(user, record_id, payload)


@router.delete("/{record_id}", response_model=SuccessResponse, summary="기록 삭제")
async def delete_record_route(
    record_id: str,
    user: User = Depends(get_current_user)
):
    return await delete_record(user, record_id)
