import logging

from src.models.meeting import Meeting
from src.repositories.base import BaseRepository


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class MeetingRepositoryError(Exception):
    """Custom exception for MeetingRepository errors."""
    logger.debug("Ошибка в MeetingRepository.")


class MeetingRepository(BaseRepository):
    """Repository for managing meeting data in the database."""

    def __init__(self, db, model=Meeting):
        super().__init__(model=model, db=db)

    async def list(self):
        """Retrieve all meeting records from the database."""
        try:
            return await super().list()
        except Exception as e:
            logger.error(f"Error retrieving meetings: {str(e)}")
            raise MeetingRepositoryError("Failed to retrieve meetings")(e)

    async def create_meeting(self, meeting_data: dict) -> dict:
        """Create a new meeting record in the database."""
        try:
            return await self.create(obj_in=meeting_data)
        except Exception as e:
            logger.error(f"Error creating meeting: {str(e)}")
            raise MeetingRepositoryError("Failed to create meeting")(e)

    async def get_meeting(self, meeting_id: str) -> dict:
        """Retrieve a meeting by its ID."""
        try:
            return await self.get(meeting_id)
        except Exception as e:
            logger.error(f"Error retrieving meeting with ID {meeting_id}: {str(e)}")
            raise MeetingRepositoryError(f"Failed to retrieve meeting with ID {meeting_id}")(e)

    async def update_meeting(self, meeting_id: str, update_data: dict) -> dict:
        """Update an existing meeting record."""
        try:
            db_obj = await self.get(meeting_id)
            if not db_obj:
                raise ValueError(f"Meeting with ID {meeting_id} does not exist.")

            updated_obj = await self.update(db_obj=db_obj, obj_in=update_data)
            return updated_obj
        except Exception as e:
            logger.error(f"Error updating meeting: {str(e)}")
            raise MeetingRepositoryError("Failed to update meeting")(e)

    async def delete_meeting(self, meeting_id: str) -> None:
        """Delete a meeting record from the database."""
        try:
            await self.delete(meeting_id)
        except Exception as e:
            logger.error(f"Error deleting meeting: {str(e)}")
            raise MeetingRepositoryError("Failed to delete meeting")(e)
