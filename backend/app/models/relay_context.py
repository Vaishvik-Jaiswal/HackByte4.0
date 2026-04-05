"""Briefings from earlier mail (e.g. manager): topic trigger + what to tell the other party."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base


class RelayContext(Base):
    """
    When someone emails instructions like "Client will contact you about X — tell them Y",
    we store (topic, relay_instruction) for later replies about the same topic.
    """

    __tablename__ = "relay_contexts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    source_email_id = Column(
        Integer, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, index=True
    )

    topic = Column(Text, nullable=False)
    relay_instruction = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="active")  # active | archived

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
