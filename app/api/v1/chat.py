from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user
from app.db.models.models import User, Conversation, Message, Persona
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ConversationResponse
from app.services.chat_service import ChatService
from app.services.persona_service import PersonaService

router = APIRouter(prefix="/sakha", tags=["Sakha Chat"])


@router.post("/chat", response_model=ChatMessageResponse)
async def chat_with_sakha(
    body: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to Sakha spiritual companion. Injects user Persona JSON and Vedic context
    while upholding non-judgmental, warm spiritual guardrails.
    """
    # 1. Resolve or create conversation
    conv = None
    if body.conversation_id:
        c_res = await db.execute(
            select(Conversation).where(Conversation.id == body.conversation_id, Conversation.user_id == user.id)
        )
        conv = c_res.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        title = body.content[:40] + "..." if len(body.content) > 40 else body.content
        conv = Conversation(user_id=user.id, title=title)
        db.add(conv)
        await db.flush()

    # 2. Retrieve persona JSON
    p_res = await db.execute(select(Persona).where(Persona.user_id == user.id))
    persona_row = p_res.scalar_one_or_none()
    persona_json = persona_row.canonical_json if persona_row else await PersonaService.build_canonical_persona_async(user)

    # 3. Retrieve recent message history explicitly
    recent_msgs = []
    if body.conversation_id:
        m_res = await db.execute(
            select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).limit(6)
        )
        for m in reversed(m_res.scalars().all()):
            recent_msgs.append({"role": m.role, "content": m.content})

    # 4. Generate response
    reply_text = await ChatService.generate_response(body.content, persona_json, recent_msgs)

    # 5. Persist user and assistant messages
    user_msg = Message(conversation_id=conv.id, role="user", content=body.content)
    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=reply_text)
    db.add(user_msg)
    db.add(assistant_msg)
    conv.updated_at = datetime.utcnow()

    await db.commit()

    return ChatMessageResponse(
        conversation_id=conv.id,
        user_message=body.content,
        sakha_reply=reply_text,
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all spiritual dialogue conversations for the authenticated user."""
    res = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = res.scalars().all()
    output = []
    for c in convs:
        output.append(
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=0,
            )
        )
    return output
