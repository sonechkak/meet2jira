from fastapi import APIRouter, File

meeting_router = APIRouter(
    prefix="/meeting",
    tags=["Meeting Management"],
)

@meeting_router.get("/info")
async def get_meeting_info():
    """Endpoint to get meeting information."""
    return {"message": "Meeting information retrieved successfully."}


@meeting_router.get("/list")
async def list_meetings():
    """Endpoint to list meetings."""
    return {"message": "List of meetings retrieved successfully.", "meeting": []}

