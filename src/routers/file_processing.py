import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from starlette import status

from src.pipeline.pipeline import process_document
from src.schemas.auth.user import UserResponseSchema


processing_router = APIRouter(
    prefix="/file",
    tags=["File Processing"],
    responses={404: {"description": "Not found"}},
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@processing_router.post("/process")
async def process_file(file: UploadFile = File(...)):
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


@processing_router.post("/reject", response_model=UserResponseSchema)
async def reject_file():
    """Endpoint to reject a file."""
    return {"message": "File rejection endpoint is under construction."}


@processing_router.post("/upload")
async def upload_file(file: bytes):
    """
    Endpoint to upload a file.
    This is a placeholder function that can be extended to handle file uploads.
    """
    # Here you would typically save the file to a server or process it
    return {"message": "File uploaded successfully.", "file_size": len(file)}


@processing_router.delete("/delete")
async def delete_file(file_id: str):
    """
    Endpoint to delete a file.
    This is a placeholder function that can be extended to handle file deletion.
    """
    # Here you would typically delete the file from the server or database
    return {"message": f"File with ID {file_id} deleted successfully."}


@processing_router.get("/download")
async def download_file(file_id: str):
    """
    Endpoint to download a file.
    This is a placeholder function that can be extended to handle file downloads.
    """
    # Here you would typically retrieve the file from the server or database
    return {"message": f"File with ID {file_id} downloaded successfully."}


@processing_router.get("/info")
async def get_file_info(file_id: str):
    """
    Endpoint to get information about a file.
    This is a placeholder function that can be extended to return file metadata.
    """
    # Here you would typically retrieve file metadata from the server or database
    return {"message": f"Information for file with ID {file_id} retrieved successfully."}


@processing_router.get("/list")
async def list_files():
    """
    Endpoint to list all files.
    This is a placeholder function that can be extended to return a list of files.
    """
    # Here you would typically retrieve a list of files from the server or database
    return {"message": "List of files retrieved successfully.", "files": []}
