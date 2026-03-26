from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    question: str
    doc_id: Optional[str] = None


class SourceItem(BaseModel):
    doc_id: str | None = None
    page: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]