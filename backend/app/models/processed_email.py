from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


class ProcessedEmail(Base):
    """LLM-derived fields for an inbox email, keyed by source email row."""

    __tablename__ = "processed_emails"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(
        Integer,
        ForeignKey("emails.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    thread_id = Column(String, nullable=False)
    category = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    tone = Column(String, nullable=True)
    tone_reason = Column(Text, nullable=True)
    suggested_reply = Column(Text, nullable=True)
