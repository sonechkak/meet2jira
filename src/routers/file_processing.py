import logging

from fastapi import APIRouter, UploadFile, File, Depends

from src.database import AsyncSessionLocal, get_db_session
from src.pipeline.pipeline import process_document
from src.schemas.jira.jira_schemas import JiraTaskRequest
from src.schemas.processing.processing_schemas import (
    AcceptResultRequestSchema,
    RejectProcessingResponseSchema,
    RejectProcessingRequestSchema,
    AcceptResultResponseSchema,
    ProcessingResponseSchema,
)
from src.services.jira_service import JiraService, get_jira_service


processing_router = APIRouter(
    prefix="/file",
    tags=["File Processing"],
    responses={404: {"description": "Not found"}},
)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@processing_router.post("/process")
async def process_file(
        file: UploadFile = File(...),
        db: AsyncSessionLocal = Depends(get_db_session)
) -> ProcessingResponseSchema:
    """Endpoint to process a file."""
    try:
        pipeline_response = await process_document(file)
        logger.info(f"Pipeline response: {pipeline_response}.")

        return pipeline_response

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return ProcessingResponseSchema(
            status="error",
            error=True,
            error_message=str(e),
            document_name=file.filename,
            summary={}
        )


@processing_router.post("/reject")
async def reject_processing(
        request: RejectProcessingRequestSchema,
) -> RejectProcessingResponseSchema:
    """Endpoint to reject a file."""

    return RejectProcessingResponseSchema(
        status="success",
        error=False
    )


@processing_router.post("/accept")
async def accept_file(
    request: AcceptResultRequestSchema,
    jira_service: JiraService = Depends(get_jira_service)
) -> AcceptResultResponseSchema:
    """Cоздание задач в Jira."""
    try:
        jira_request = JiraTaskRequest(
            tasks_text=request.tasks_text,
            project_key=request.project_key,
            epic_key=request.epic_key
        )

        jira_result = await jira_service.process_tasks_to_jira(jira_request)
        logger.info(f"Jira result: {jira_result}")

        if not jira_result.created_tasks:
            return AcceptResultResponseSchema(
                status="error",
                error=True,
                error_message="Не удалось создать задачи в Jira. Проверьте текст задач и настройки проекта.",
                result_id=request.result_id,
                tasks_text=request.tasks_text,
                project_key=request.project_key,
                epic_key=request.epic_key,
                jira_result=jira_result.dict(),
            )
        return AcceptResultResponseSchema(
            status="success",
            error=False,
            message="Результат принят и задачи созданы в Jira!",
            result_id=request.result_id,
            tasks_text=request.tasks_text,
            project_key=request.project_key,
            epic_key=request.epic_key,
            jira_result=jira_result.dict()
        )

    except Exception as e:
        logger.error(f"Error accepting file: {str(e)}")
        return AcceptResultResponseSchema(
            status="error",
            error=True,
            error_message=str(e),
            result_id=request.result_id,
            tasks_text=request.tasks_text,
            project_key=request.project_key,
            epic_key=request.epic_key,
            jira_result=jira_result.dict(),
        )
