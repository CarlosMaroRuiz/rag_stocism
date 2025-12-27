from sqlalchemy import Column, BigInteger, Integer, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(Text, nullable=False)
    file_name = Column(Text, nullable=False)
    minio_path = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    doc_metadata = Column(JSONB)