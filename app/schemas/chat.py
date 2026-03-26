from pydantic import BaseModel
from typing import Optional, List

class ChatRequest(BaseModel):
    question: str
    doc_id: Optional[str] = None
    department: Optional[str] = None


class Source(BaseModel):
    doc_id: str
    page: int


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]