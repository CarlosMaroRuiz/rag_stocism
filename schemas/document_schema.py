from pydantic import BaseModel, Field

class UploadDocumentResponse(BaseModel):
    document_id: str
    file_name: str
    total_chunks: int
    minio_path: str
    message: str = "Documento procesado exitosamente"