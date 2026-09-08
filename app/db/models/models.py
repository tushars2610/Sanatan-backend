import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Boolean, Integer, Float, Date, Time, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="hi")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships with eager selectin loading for async compatibility
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    birth_profile: Mapped["BirthProfile"] = relationship("BirthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    persona: Mapped["Persona"] = relationship("Persona", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    
    # Core onboarding preferences
    current_state: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Student, Early career, Building a family, Parenting, Retired, Between chapters
    working_hours: Mapped[str | None] = mapped_column(String(100), nullable=True) # Software engineer, teacher, homemaker, etc.
    deity: Mapped[str | None] = mapped_column(String(50), nullable=True)          # Shiva, Vishnu, Devi, Ganesha, Krishna, Hanuman, Still discovering
    inner_feeling: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Peaceful, Hopeful, Restless, Searching, Heavy, Grateful, Prefer not to say
    seeking: Mapped[str | None] = mapped_column(String(50), nullable=True)        # Peace of Mind, Clarity, Strength, Healing

    # General profile fields
    primary_concern: Mapped[str | None] = mapped_column(String(100), default="work")
    faith_level: Mapped[str | None] = mapped_column(String(50), default="occasional")
    tradition: Mapped[str | None] = mapped_column(String(50), default="hindu")
    deities: Mapped[dict | list] = mapped_column(JSON, default=lambda: ["shiva", "hanuman"])
    current_practices: Mapped[dict | list] = mapped_column(JSON, default=lambda: ["prayer", "mantra"])
    daily_time_minutes: Mapped[int] = mapped_column(Integer, default=10)
    life_stage: Mapped[str | None] = mapped_column(String(50), default="professional")

    user: Mapped["User"] = relationship("User", back_populates="profile")


class BirthProfile(Base):
    __tablename__ = "birth_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    time_of_birth: Mapped[time | None] = mapped_column(Time, nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String(150), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    is_time_approximate: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="birth_profile")
    astrology_snapshot: Mapped["AstrologySnapshot"] = relationship("AstrologySnapshot", back_populates="birth_profile", uselist=False, cascade="all, delete-orphan", lazy="selectin")


class AstrologySnapshot(Base):
    __tablename__ = "astrology_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    birth_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("birth_profiles.id", ondelete="CASCADE"), unique=True)
    rashi: Mapped[dict] = mapped_column(JSON, default=dict)
    nakshatra: Mapped[dict] = mapped_column(JSON, default=dict)
    panchang_data: Mapped[dict] = mapped_column(JSON, default=dict)
    dasha_data: Mapped[dict] = mapped_column(JSON, default=dict)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    birth_profile: Mapped["BirthProfile"] = relationship("BirthProfile", back_populates="astrology_snapshot")


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    persona_version: Mapped[str] = mapped_column(String(10), default="1.0")
    completeness_level: Mapped[int] = mapped_column(Integer, default=0)
    canonical_json: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="persona")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(150), default="Spiritual Dialogue")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    content: Mapped[Text] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
