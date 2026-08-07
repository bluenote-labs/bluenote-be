import json
import logging
import math
import re
from datetime import datetime
from typing import AsyncIterator

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.record import Record
from app.models.user import User
from app.schemas.records import (
    RecordCreateRequest,
    RecordCreateResponse,
    RecordListItem,
    RecordListQuery,
    RecordListResponse,
)
from app.services.ai import AIGenerationError, generate_json, stream_completion

logger = logging.getLogger(__name__)

TITLE_SYSTEM_PROMPT = (
    "너는 사용자의 하루 기록 입력을 보고 짧은 제목을 만드는 도우미야. "
    "10자 내외의 간결한 제목 한 줄을 만들어. "
    "사용자가 입력한 언어를 그대로 유지해. "
    '반드시 다음 JSON 형식으로만 응답해: {"title": string}'
)

BODY_SYSTEM_PROMPT = (
    "너는 사용자의 하루 기록을 정리해주는 도우미야. "
    "사용자가 입력한 내용을 바탕으로 마크다운 형식의 본문을 작성해. "
    "자연스러운 일기체 문장으로 정리해. "
    "사용자가 입력한 언어를 그대로 유지해. "
    "본문 마크다운 텍스트만 출력하고 다른 설명은 덧붙이지 마."
)


def _format_sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _extract_plain_text(node: dict) -> str:
    if not isinstance(node, dict):
        return ""

    parts = []
    if node.get("type") == "text":
        parts.append(node.get("text", ""))
    for child in node.get("content", []) or []:
        parts.append(_extract_plain_text(child))

    return " ".join(part for part in parts if part)


async def generate_record_stream(input_text: str) -> AsyncIterator[str]:
    try:
        title_result = await generate_json(TITLE_SYSTEM_PROMPT, input_text)
        title = title_result["title"]
        body_stream = await stream_completion(BODY_SYSTEM_PROMPT, input_text)
    except (AIGenerationError, KeyError, TypeError) as e:
        logger.error(f"AI 기록 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="기록 정리에 실패했어요. 다시 시도해주세요."
        )

    async def event_generator() -> AsyncIterator[str]:
        yield _format_sse({"type": "title", "content": title})
        async for delta in body_stream:
            yield _format_sse({"type": "body", "content": delta})
        yield _format_sse({"type": "done"})

    return event_generator()


async def create_record(user: User, payload: RecordCreateRequest) -> RecordCreateResponse:
    today = datetime.now().strftime("%Y-%m-%d")

    existing = await Record.find_one(Record.user_id == user.id, Record.date == today)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="오늘은 이미 기록했어요."
        )

    record = Record(
        user_id=user.id,
        date=today,
        title=payload.title,
        content=payload.content,
        plain_text=_extract_plain_text(payload.content),
        image_url=payload.imageUrl,
        goal_ids=[PydanticObjectId(goal_id) for goal_id in payload.goalIds],
    )
    await record.insert()

    return RecordCreateResponse(
        id=str(record.id),
        date=record.date,
        title=record.title,
        createdAt=record.created_at,
    )


async def list_records(user: User, query: RecordListQuery) -> RecordListResponse:
    filters = [Record.user_id == user.id]

    if query.month:
        filters.append({"date": {"$regex": f"^{re.escape(query.month)}"}})
    if query.goal_id:
        filters.append(Record.goal_ids == PydanticObjectId(query.goal_id))
    if query.keyword:
        pattern = re.escape(query.keyword)
        filters.append({
            "$or": [
                {"title": {"$regex": pattern, "$options": "i"}},
                {"plain_text": {"$regex": pattern, "$options": "i"}},
            ]
        })
    if query.has_image is True:
        filters.append({"image_url": {"$ne": None}})
    elif query.has_image is False:
        filters.append({"image_url": None})

    db_query = Record.find(*filters)
    total = await db_query.count()
    total_pages = math.ceil(total / query.limit) if total > 0 else 0

    records = await (
        db_query.sort(-Record.date)
        .skip((query.page - 1) * query.limit)
        .limit(query.limit)
        .to_list()
    )

    return RecordListResponse(
        records=[
            RecordListItem(
                id=str(record.id),
                date=record.date,
                title=record.title,
                imageUrl=record.image_url,
                goalIds=[str(goal_id) for goal_id in record.goal_ids],
                createdAt=record.created_at,
            )
            for record in records
        ],
        total=total,
        page=query.page,
        totalPages=total_pages,
        hasNext=query.page < total_pages,
    )
