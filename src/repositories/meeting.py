from src.models.meeting import Meeting
from src.repositories.base import BaseRepository


class MeetingRepository(BaseRepository):
    """Repository for managing meeting data in the database."""

    def __init__(self, db):
        super().__init__(Meeting, db)

    async def list(self):
        """Retrieve all meeting records from the database."""
        return await super().list()

    async def create_meeting(self, meeting_data: dict) -> dict:
        """Create a new meeting record in the database."""
        return await self.create(obj_in=meeting_data)

    async def get_meeting_by_id(self, meeting_id: str) -> dict:
        """Retrieve a meeting by its ID."""
        return await self.get(meeting_id)

    async def update_meeting(self, meeting_id: str, update_data: dict) -> dict:
        """Update an existing meeting record."""
        return await self.update(meeting_id, update_data)

    async def delete_meeting(self, meeting_id: str) -> None:
        """Delete a meeting record from the database."""
        await self.delete(meeting_id)

    async def get_all_meetings(self) -> list:
        """Retrieve all meetings."""
        return await self.list()
