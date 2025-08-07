class MeetingService:
    """Для поддержания слоистой архитектуры приложения, сервис MeetingService."""

    def __init__(self, meeting_repository):
        self.meeting_repository = meeting_repository

    def create_meeting(self, meeting_data):
        return self.meeting_repository.create_meeting(meeting_data)

    def get_meeting(self, meeting_id):
        return self.meeting_repository.get_meeting(meeting_id)

    def update_meeting(self, meeting_id, meeting_data):
        return self.meeting_repository.update_meeting(meeting_id, meeting_data)

    def delete_meeting(self, meeting_id):
        return self.meeting_repository.delete_meeting(meeting_id)

    def list_meetings(self):
        return self.meeting_repository.list_meetings()

    def get_all_meetings(self):
        """Получить все встречи."""
        return self.meeting_repository.get_all_meetings()
