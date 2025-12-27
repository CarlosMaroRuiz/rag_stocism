from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class KnowledgeLevel(str, Enum):
    BEGINNER = "principiante"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzado"

class UserProfileRequest(BaseModel):
    """Perfil del usuario para generar recomendaciones"""
    
    # Información básica
    name: Optional[str] = Field(None, description="Nombre del usuario")
    
    # Conocimiento
    topic: str = Field(..., description="Tema de interés (ej: estoicismo)")
    knowledge_level: KnowledgeLevel = Field(
        ..., 
        description="Nivel de conocimiento en el tema"
    )
    
    # Contexto personal
    current_situation: Optional[str] = Field(
        None, 
        description="Situación actual (ej: 'Estoy estresado por el trabajo')"
    )
    goals: Optional[str] = Field(
        None,
        description="Objetivos (ej: 'Quiero aprender a manejar la ansiedad')"
    )
    interests: Optional[List[str]] = Field(
        None,
        description="Áreas específicas de interés"
    )
    
    # Configuración de la respuesta
    num_recommendations: int = Field(
        5, 
        ge=1, 
        le=10, 
        description="Cantidad de consejos a generar"
    )
    k: int = Field(
        5, 
        ge=1, 
        le=10, 
        description="Chunks a recuperar del RAG"
    )

class Recommendation(BaseModel):
    title: str = Field(..., description="Título del consejo")
    content: str = Field(..., description="Contenido del consejo")
    source_reference: Optional[str] = Field(
        None, 
        description="Referencia al libro/documento"
    )
    difficulty: str = Field(..., description="Nivel de dificultad de aplicación")

class GenerateRecommendationsResponse(BaseModel):
    user_profile_summary: str
    topic: str
    recommendations: List[Recommendation]