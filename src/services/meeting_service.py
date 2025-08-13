class MeetingService:
    """Для поддержания слоистой архитектуры приложения, сервис MeetingService."""

    def __init__(self, meeting_repository):
        self.meeting_repository = meeting_repository

    async def create_meeting(self, meeting_data):
        return await self.meeting_repository.create_meeting(meeting_data)

    async def get_meeting(self, meeting_id):
        return await self.meeting_repository.get_meeting(meeting_id)

    async def update_meeting(self, meeting_id, meeting_data):
        return await self.meeting_repository.update_meeting(meeting_id, meeting_data)

    async def delete_meeting(self, meeting_id):
        return await self.meeting_repository.delete_meeting(meeting_id)

    async def list_meetings(self):
        return await self.meeting_repository.list()
