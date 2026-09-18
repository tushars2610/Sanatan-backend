from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    user_id: str = Field(
        ...,
        description="The UUID of the authenticated user. Used to load their persona for a personalised reply.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Client session token. Pass the value returned from a previous response to continue the conversation. Omit to start a new one.",
    )
    content: str = Field(..., min_length=1, description="Message to Sakha companion")
    language: Optional[str] = Field(default="hi", description="Preferred response language")


class SourceCitation(BaseModel):
    passage_id: str
    source: str          # "Bhagavad Gita"
    reference: str       # "2.47"
    translation: str


class ChatMessageResponse(BaseModel):
    conversation_id: str
    session_id: str
    user_message: str
    sakha_reply: str
    sources: List[SourceCitation] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationResponse(BaseModel):
    id: str
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
