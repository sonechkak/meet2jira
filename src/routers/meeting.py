from fastapi import APIRouter, Depends

from src.database import AsyncSessionLocal, get_async_session
from src.repositories.meeting import MeetingRepository
from src.services.meeting_service import MeetingService

meeting_router = APIRouter(tags=["Meeting"])


@meeting_router.get("/meetings")
async def get_meetings(db: AsyncSessionLocal = Depends(get_async_session)):
    """
    Получить список встреч.
    """
    meeting_repository = MeetingRepository(db)
    meeting_service = MeetingService(meeting_repository)
    meetings = await meeting_service.list_meetings()
    return meetings
