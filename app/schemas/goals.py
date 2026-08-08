from pydantic import BaseModel


class GoalParseRequest(BaseModel):
    input: str


class GoalParseResponse(BaseModel):
    title: str
    startDate: str
    endDate: str
    aiMessage: str
