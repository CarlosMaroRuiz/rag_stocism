from fastapi import APIRouter
from controllers.recommendation_controller import recommendation_controller
from schemas.recommendation_schema import (
    UserProfileRequest,
    GenerateRecommendationsResponse
)

router = APIRouter(prefix="/generate", tags=["Recommendations"])

@router.post("/recommendations", response_model=GenerateRecommendationsResponse)
async def generate_recommendations(request: UserProfileRequest):
    """
    Genera recomendaciones personalizadas basadas en:
    - El perfil del usuario (nivel, situación, objetivos)
    - Contenido del libro subido (RAG)
    
    Ejemplo de request:
    {
        "name": "Carlos",
        "topic": "estoicismo",
        "knowledge_level": "principiante",
        "current_situation": "Estoy estresado por el trabajo y necesito paz mental",
        "goals": "Aprender a manejar la ansiedad y vivir más tranquilo",
        "interests": ["meditación", "control emocional"],
        "num_recommendations": 5
    }
    """
    return await recommendation_controller.generate_recommendations(request)