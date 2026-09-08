from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    conversation_id: Optional[str] = Field(default=None, description="UUID of existing conversation or null to create one")
    content: str = Field(..., min_length=1, description="Message to Sakha companion")
    language: Optional[str] = Field(default="hi", description="Preferred response language ('hi' or 'en')")


class ChatMessageResponse(BaseModel):
    conversation_id: str
    user_message: str
    sakha_reply: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
