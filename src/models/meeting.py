from sqlalchemy import Column, DateTime, Integer, String, Text

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

    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', status='{self.status}')>"

    def __str__(self):
        return f"Meeting(id={self.id}, title='{self.title}', status='{self.status}')"
