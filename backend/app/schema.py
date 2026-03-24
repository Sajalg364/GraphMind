from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[list] = None

class ChatResponse(BaseModel):
    type: str
    answer: str
    sql: Optional[str] = None
    row_count: Optional[int] = None
    data: Optional[list] = None
