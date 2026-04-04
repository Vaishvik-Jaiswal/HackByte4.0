from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base
import uuid

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    thread_id = Column(String, nullable=False)
    gmail_msg_id = Column(String, unique=True, nullable=False)
    from_json = Column(JSON) # Store sender as json {"name": "...", "email": "..."}
    to_json = Column(JSON)   # Store recipients as json [{"name": "...", "email": "..."}, ...]
    subject = Column(String)
    body_text = Column(Text)
    date = Column(DateTime(timezone=True))
    is_inbox = Column(Boolean, default=True)
    is_processed = Column(Boolean, default=False, nullable=False)
