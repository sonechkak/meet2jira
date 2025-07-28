import logging
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from starlette import status

from src.database import AsyncSessionLocal, get_db_session
from src.pipeline.pipeline import process_document
from src.schemas.jira.jira_schemas import JiraTaskRequest
from src.schemas.processing.processing_schemas import (
    ProcessingResponseSchema,
    AcceptResultRequestSchema,
    RejectProcessingResponseSchema,
    RejectProcessingRequestSchema,
)
from src.services.jira_service import JiraService, get_jira_service


processing_router = APIRouter(
    prefix="/file",
    tags=["File Processing"],
    responses={404: {"description": "Not found"}},
)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@processing_router.post("/process", response_model=ProcessingResponseSchema)
async def process_file(
        file: UploadFile = File(...),
        db: AsyncSessionLocal = Depends(get_db_session)
):
    """Endpoint to process a file."""
    try:
        summary = await process_document(file)

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        return ProcessingResponseSchema(
            success=True,
            model="yandex-gpt",
            document_name=file.filename,
            summary=summary,
            error=False
        )

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@processing_router.post("/reject")
async def reject_processing(
        request: RejectProcessingRequestSchema,
):
    """Endpoint to reject a file."""

    return RejectProcessingResponseSchema(
        success=True,
        message="Файл отклонен, обратная связь учтена"
    )


@processing_router.post("/accept")
async def accept_file(
    request: AcceptResultRequestSchema,
    jira_service: JiraService = Depends(get_jira_service)
):
    """Cоздание задач в Jira."""
    try:
        jira_request = JiraTaskRequest(
            tasks_text=request.tasks_text,
            project_key=request.project_key,
            epic_key=request.epic_key
        )

        jira_result = await jira_service.process_tasks_to_jira(jira_request)
        logger.debug(f"Jira result: {jira_result}")

        if not jira_result.success and not jira_result.created_tasks:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Не удалось создать задачи в Jira",
                    "errors": jira_result.errors
                }
            )

        return {
            "success": True,
            "message": "Результат принят и задачи созданы в Jira!",
            "jira_result": {
                "success": jira_result.success,
                "created_tasks": [
                    {
                        "key": task["key"],
                        "url": task["url"],
                        "title": task["title"]
                    } for task in jira_result.created_tasks
                ],
                "errors": jira_result.errors
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании задач: {str(e)}"
        )
