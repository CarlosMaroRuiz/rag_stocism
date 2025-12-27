from fastapi import UploadFile, HTTPException
from pathlib import Path
import uuid
import shutil
import traceback
import logging

from core.llm import llm_pipe
from core.files import minio_client
from schemas.document_schema import UploadDocumentResponse

logger = logging.getLogger(__name__)


class DocumentController:
    UPLOAD_DIR = Path("uploads")

    def __init__(self):
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    async def upload_document(self, file: UploadFile) -> UploadDocumentResponse:
        """
        Flujo completo:
        1. Guardar PDF temporalmente
        2. Subir a MinIO
        3. Procesar con LlmPipe (chunking + embeddings)
        4. Limpiar archivo temporal
        """
        
        # Validar tipo de archivo
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, 
                detail="Solo se permiten archivos PDF"
            )

        # Generar nombres únicos
        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}_{file.filename}"
        temp_file_path = self.UPLOAD_DIR / safe_filename
        minio_object_name = f"pdfs/{safe_filename}"

        try:
            # 1. Guardar temporalmente
            with temp_file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"✓ Archivo guardado temporalmente: {temp_file_path}")

            # 2. Subir a MinIO
            minio_client.upload_file(
                file_path=str(temp_file_path),
                object_name=minio_object_name
            )
            print(f"✓ Archivo subido a MinIO: {minio_object_name}")

            # 3. Procesar con LlmPipe
            print(f"🔄 Procesando documento con LlmPipe...")
            result = llm_pipe.ingest_pdf(
                file_path=str(temp_file_path),
                document_id=doc_id,
                minio_path=minio_object_name
            )
            print(f"✓ Documento procesado correctamente")

            return UploadDocumentResponse(**result)

        except Exception as e:
            # Log completo del error
            error_msg = traceback.format_exc()
            logger.error(f"Error en upload_document: {error_msg}")
            print(f"❌ ERROR: {error_msg}")
            
            # Si falla, intentar limpiar MinIO
            try:
                minio_client.delete_file(minio_object_name)
                print(f"✓ Archivo eliminado de MinIO: {minio_object_name}")
            except Exception as cleanup_error:
                logger.error(f"Error al limpiar MinIO: {cleanup_error}")
            
            raise HTTPException(
                status_code=500, 
                detail=f"Error al procesar documento: {str(e)}"
            )
        
        finally:
            # 4. Limpiar archivo temporal
            if temp_file_path.exists():
                temp_file_path.unlink()
                print(f"✓ Archivo temporal eliminado")


document_controller = DocumentController()