import logging
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from starlette import status

from src.database import AsyncSessionLocal, get_db_session
from src.pipeline.pipeline import process_document
from src.schemas.jira.jira_schemas import JiraTaskRequest
from src.schemas.jira.request_schemas import AcceptResultRequest
from src.services.jira_service import JiraService, get_jira_service

processing_router = APIRouter(
    prefix="/file",
    tags=["File Processing"],
    responses={404: {"description": "Not found"}},
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@processing_router.post("/process")
async def process_file(file: UploadFile = File(...), db: AsyncSessionLocal = Depends(get_db_session)):
    """Endpoint to process a file."""
    try:
        pipeline = await process_document(file)

        if "error" in pipeline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=pipeline["error"]
            )

        summary = pipeline.get("summary", "")
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось создать резюме для данного документа."
            )

        return {
            "success": True,
            "model": pipeline.get("model", "yandex-gpt"),
            "document_name": file.filename,
            "summary": summary,
        }

    except Exception as e:
        return HTTPException(
            status_code=500,
            detail=str(e)
        )


@processing_router.post("/reject")
async def reject_file():
    """Endpoint to reject a file."""
    return {"message": "File rejection endpoint is under construction."}


@processing_router.post("/accept")
async def accept_file(
    request: AcceptResultRequest,
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
        logger.info(f"Jira result: {jira_result}")

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
            "message": "Результат принят и задачи созданы в Jira",
            "result_id": request.result_id,
            "jira_result": jira_result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании задач: {str(e)}"
        )
