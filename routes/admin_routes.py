from fastapi import APIRouter, UploadFile, File, Depends
from controllers.document_controller import document_controller
from schemas.document_schema import UploadDocumentResponse
from core.middleware.jwt_middleware import require_admin_role
from typing import Dict

router = APIRouter(prefix="/upload-document", tags=["Admin"])

@router.post("/admin", response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: Dict = Depends(require_admin_role)
):
    """
    Sube un documento PDF estoico para procesamiento RAG.

    **Requiere autenticación JWT con rol ADMIN**

    Solo los administradores pueden subir documentos al sistema.

    Args:
        file: Archivo PDF a subir
        current_user: Usuario actual (debe ser ADMIN)

    Returns:
        Respuesta con información del documento procesado

    Raises:
        403: Si el usuario no tiene rol ADMIN
    """
    return await document_controller.upload_document(file)