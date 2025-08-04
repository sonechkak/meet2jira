import datetime

from pydantic import BaseModel


class MeetingCreateSchema(BaseModel):
    title: str
    description: str
    description: str = ""
    meeting_date: datetime.datetime
    duration_minutes: int = 60
    participants: str = ""
    status: str = "scheduled"
