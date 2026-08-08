import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status

from app.models.pattern import Pattern
from app.models.record import Record
from app.models.user import User
from app.schemas.pattern import (
    HeatmapDay,
    HeatmapResponse,
    PatternItem,
    PatternListResponse,
)

logger = logging.getLogger(__name__)

WEEKDAY_NAMES = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def _resolve_range(period: str) -> tuple[str, str]:
    """period로부터 (start, end) 날짜 문자열을 계산한다."""
    today = datetime.now().date()

    if period == "1year":
        start = today - timedelta(days=364)
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    if period.isdigit() and len(period) == 4:
        return f"{period}-01-01", f"{period}-12-31"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="지원하지 않는 기간이에요."
    )


def _most_frequent_day(dates: list[datetime]) -> Optional[str]:
    if not dates:
        return None
    weekday, _ = Counter(d.weekday() for d in dates).most_common(1)[0]
    return WEEKDAY_NAMES[weekday]


def _most_active_month(dates: list[datetime]) -> Optional[str]:
    if not dates:
        return None
    month, _ = Counter(d.month for d in dates).most_common(1)[0]
    return f"{month}월"


async def get_heatmap(user: User, period: str) -> HeatmapResponse:
    start_str, end_str = _resolve_range(period)

    records = await Record.find(
        Record.user_id == user.id,
        {"date": {"$gte": start_str, "$lte": end_str}},
    ).sort(-Record.date).to_list()

    record_dates = [datetime.strptime(record.date, "%Y-%m-%d") for record in records]

    return HeatmapResponse(
        period=period,
        totalRecords=len(records),
        mostFrequentDay=_most_frequent_day(record_dates),
        mostActiveMonth=_most_active_month(record_dates),
        days=[HeatmapDay(date=record.date, recordId=str(record.id)) for record in records],
    )


async def get_patterns(user: User) -> PatternListResponse:
    patterns = await Pattern.find(Pattern.user_id == user.id).sort(-Pattern.created_at).to_list()

    return PatternListResponse(
        patterns=[
            PatternItem(
                id=str(pattern.id),
                description=pattern.description,
                evidenceRecordIds=[str(record_id) for record_id in pattern.evidence_record_ids],
                status=pattern.status,
                userModifiedDescription=pattern.user_modified_description,
            )
            for pattern in patterns
        ]
    )
