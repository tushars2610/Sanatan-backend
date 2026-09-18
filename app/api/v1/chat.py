import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.dependencies import get_db
from app.db.models.models import User, Conversation, Message, Persona
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
    SourceCitation,
)
from app.services.chat_service import ChatService
from app.services.persona_service import PersonaService

router = APIRouter(prefix="/sakha", tags=["Sakha Chat"])


@router.post("/chat", response_model=ChatMessageResponse)
async def chat_with_sakha(
    body: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to Sakha.

    - `user_id` is **required** — the backend loads the user's full persona
      (identity, deity, vedic profile, AI insights) from the database using it,
      so every reply is deeply personalised.
    - `session_id` is optional — pass it from a previous response to continue
      the same conversation. Omit it to start a fresh one.

    Every reply is RAG-grounded: the top-5 most relevant Bhagavad Gita passages
    are retrieved from Milvus and injected into the LLM context before generation.
    """
    # ── 1. Resolve user ───────────────────────────────────────────────────────
    u_res = await db.execute(select(User).where(User.id == body.user_id))
    user = u_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{body.user_id}' not found. Please register first.",
        )

    # ── 2. Resolve session_id ─────────────────────────────────────────────────
    session_id = body.session_id or str(uuid.uuid4())

    # ── 3. Resolve or create conversation ────────────────────────────────────
    conv: Conversation | None = None

    if body.session_id:
        # Resume existing conversation for this user+session
        res = await db.execute(
            select(Conversation).where(
                Conversation.session_id == body.session_id,
                Conversation.user_id == user.id,
            ).order_by(Conversation.updated_at.desc()).limit(1)
        )
        conv = res.scalar_one_or_none()

    if conv is None:
        title = body.content[:50] + "…" if len(body.content) > 50 else body.content
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=user.id,
            session_id=session_id,
            title=title,
        )
        db.add(conv)
        await db.flush()
    else:
        session_id = conv.session_id  # keep the existing one

    # ── 4. Load persona ───────────────────────────────────────────────────────
    # Priority: stored canonical_json → live-build from profile/astro data
    p_res = await db.execute(select(Persona).where(Persona.user_id == user.id))
    persona_row = p_res.scalar_one_or_none()

    if persona_row and persona_row.canonical_json:
        persona_json = persona_row.canonical_json
    else:
        # Build a fresh persona from the user's raw profile and astro data
        persona_json = await PersonaService.build_canonical_persona_async(user)

    # ── 5. Retrieve recent message history ────────────────────────────────────
    recent_msgs = []
    m_res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    for m in reversed(m_res.scalars().all()):
        recent_msgs.append({"role": m.role, "content": m.content})

    # ── 6. Generate RAG-grounded response ─────────────────────────────────────
    reply_text, cited_ids = await ChatService.generate_response(
        user_message=body.content,
        persona_json=persona_json,
        recent_messages=recent_msgs,
    )

    # ── 7. Build source citations ─────────────────────────────────────────────
    sources: List[SourceCitation] = []
    if cited_ids:
        rows = await db.execute(
            text("""
                SELECT p.id, s.name, p.verse_number, p.translation
                FROM passages p
                JOIN sources s ON p.source_id = s.id
                WHERE p.id = ANY(CAST(:ids AS uuid[]))
            """),
            {"ids": cited_ids},
        )
        for row in rows.fetchall():
            sources.append(
                SourceCitation(
                    passage_id=str(row[0]),
                    source=row[1],
                    reference=row[2] or "",
                    translation=row[3],
                )
            )

    # ── 8. Persist messages ───────────────────────────────────────────────────
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="user",
        content=body.content,
    )
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="assistant",
        content=reply_text,
        cited_passage_ids=cited_ids if cited_ids else None,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    conv.updated_at = datetime.utcnow()

    await db.commit()

    return ChatMessageResponse(
        conversation_id=conv.id,
        session_id=session_id,
        user_message=body.content,
        sakha_reply=reply_text,
        sources=sources,
    )


@router.get("/conversations/{user_id}", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all spiritual dialogue conversations for a given user."""
    res = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = res.scalars().all()
    return [
        ConversationResponse(
            id=c.id,
            session_id=c.session_id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=0,
        )
        for c in convs
    ]
