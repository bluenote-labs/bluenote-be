from fastapi import APIRouter, Depends, Query, status

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.pattern import (
    HeatmapResponse,
    PatternFeedbackRequest,
    PatternFeedbackResponse,
    PatternListResponse,
)
from app.services.pattern import (
    analyze_patterns,
    get_heatmap,
    get_patterns,
    submit_pattern_feedback,
)

router = APIRouter()


@router.get("/heatmap", response_model=HeatmapResponse, summary="히트맵 조회")
async def get_heatmap_route(
    period: str = Query("1year", description="조회 기간 (1year: 최근 1년, YYYY: 해당 연도 예: 2025)"),
    user: User = Depends(get_current_user)
):
    return await get_heatmap(user, period)


@router.get("/analysis", response_model=PatternListResponse, summary="저장된 패턴 조회")
async def get_patterns_route(
    user: User = Depends(get_current_user)
):
    return await get_patterns(user)


@router.post("/analysis", response_model=PatternListResponse, status_code=status.HTTP_201_CREATED, summary="AI 패턴 분석")
async def analyze_patterns_route(
    user: User = Depends(get_current_user)
):
    return await analyze_patterns(user)


@router.put("/{pattern_id}/feedback", response_model=PatternFeedbackResponse, summary="패턴 피드백")
async def submit_pattern_feedback_route(
    pattern_id: str,
    payload: PatternFeedbackRequest,
    user: User = Depends(get_current_user)
):
    return await submit_pattern_feedback(user, pattern_id, payload)
