import json
from fastapi import HTTPException

from core.llm import llm_pipe
from schemas.recommendation_schema import (
    UserProfileRequest,
    GenerateRecommendationsResponse,
    Recommendation
)


class RecommendationController:
    async def generate_recommendations(
        self, 
        request: UserProfileRequest
    ) -> GenerateRecommendationsResponse:
        try:
            # Convertir request a dict para LlmPipe
            user_profile = {
                "name": request.name,
                "topic": request.topic,
                "knowledge_level": request.knowledge_level.value,
                "current_situation": request.current_situation,
                "goals": request.goals,
                "interests": request.interests,
                "num_recommendations": request.num_recommendations,
            }

            # Generar recomendaciones
            raw_response = llm_pipe.generate_recommendations(
                user_profile=user_profile,
                k=request.k
            )

            # Parsear JSON (limpiar markdown si existe)
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            data = json.loads(clean_json)
            
            recommendations = [
                Recommendation(**rec) 
                for rec in data["recommendations"]
            ]

            # Construir resumen del perfil
            profile_summary = f"{request.name or 'Usuario'} - {request.knowledge_level.value} en {request.topic}"
            if request.current_situation:
                profile_summary += f". Situación: {request.current_situation[:50]}..."

            return GenerateRecommendationsResponse(
                user_profile_summary=profile_summary,
                topic=request.topic,
                recommendations=recommendations
            )

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al parsear respuesta del LLM: {str(e)}\nRespuesta cruda: {raw_response[:200]}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error generando recomendaciones: {str(e)}"
            )


recommendation_controller = RecommendationController()