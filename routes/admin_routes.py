from fastapi import APIRouter, UploadFile, File
from controllers.document_controller import document_controller
from schemas.document_schema import UploadDocumentResponse

router = APIRouter(prefix="/upload-document", tags=["Admin"])

@router.post("/admin", response_model=UploadDocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Endpoint para subir y procesar PDFs (admin)"""
    return await document_controller.upload_document(file)