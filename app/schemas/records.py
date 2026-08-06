from pydantic import BaseModel


class RecordGenerateRequest(BaseModel):
    input: str
