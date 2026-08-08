from datetime import datetime


def today_str() -> str:
    """오늘 날짜를 'YYYY-MM-DD' 형식 문자열로 반환한다."""
    return datetime.now().strftime("%Y-%m-%d")
