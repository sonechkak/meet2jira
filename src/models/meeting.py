from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from src.database import Base


class Meeting(Base):
    """Модель встречи"""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    file_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    meeting_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    participants = Column(Text, nullable=True)
    status = Column(String(20), default="scheduled")
    jira_ticket_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', status='{self.status}')>"
