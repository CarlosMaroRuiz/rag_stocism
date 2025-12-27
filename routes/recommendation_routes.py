from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from controllers.recommendation_controller import recommendation_controller
from shared.utils.quizz_user import get_quizz_user_by_id
from schemas.recommendation_schema import (
    GenerateRecommendationRequest,
    GenerateRecommendationsResponse
)
import json

router = APIRouter(prefix="/generate", tags=["Recommendations"])


@router.post("/recommendations", response_model=GenerateRecommendationsResponse)
async def generate_recommendations(request: GenerateRecommendationRequest):
    """
    Genera recomendaciones estoicas personalizadas basadas en el quiz del usuario.

    El sistema:
    1. Obtiene el quiz estoico del usuario desde BD
    2. Busca contenido relevante en los textos estoicos (RAG)
    3. Genera recomendaciones personalizadas con DeepSeek
    """
    # TEMPORAL: Default user_id mientras se implementa JWT
    user_id = request.user_id or "7e41ec3e-344a-42d4-8aba-f75196098e10"

    # Obtener quiz estoico de BD
    user_quiz = get_quizz_user_by_id(user_id)

    if not user_quiz:
        raise HTTPException(
            status_code=404,
            detail=f"Quiz estoico no encontrado para usuario {user_id}"
        )

    # Generar recomendaciones (el controller parsea el dict de BD automáticamente)
    return await recommendation_controller.generate_recommendations(user_quiz)


@router.get("/recommendations/stream")
async def stream_recommendations(user_id: str | None = None):
    """
    Stream de recomendaciones estoicas usando Server-Sent Events (SSE).

    Eventos emitidos:
    - status: Estado del proceso (obteniendo quiz, generando, etc.)
    - profile: Resumen del perfil del usuario
    - recommendation: Cada recomendación individual
    - complete: Finalización del stream
    - error: En caso de error
    """
    # TEMPORAL: Default user_id mientras se implementa JWT
    user_id = user_id or "7e41ec3e-344a-42d4-8aba-f75196098e10"

    async def event_generator():
        try:
            # 1️⃣ Obtener quiz
            yield f"event: status\ndata: {json.dumps({'message': 'Obteniendo perfil estoico del usuario...'})}\n\n"

            user_quiz = get_quizz_user_by_id(user_id)
            if not user_quiz:
                yield f"event: error\ndata: {json.dumps({'error': f'Quiz no encontrado para usuario {user_id}'})}\n\n"
                return

            # 2️⃣ Generar recomendaciones
            yield f"event: status\ndata: {json.dumps({'message': 'Consultando textos estoicos y generando recomendaciones...'})}\n\n"

            response = await recommendation_controller.generate_recommendations(user_quiz)

            # 3️⃣ Enviar perfil
            yield f"event: profile\ndata: {json.dumps({'summary': response.user_profile_summary, 'topic': response.topic})}\n\n"

            # 4️⃣ Enviar cada recomendación individualmente
            for idx, rec in enumerate(response.recommendations, 1):
                rec_data = {
                    "index": idx,
                    "total": len(response.recommendations),
                    "title": rec.title,
                    "content": rec.content,
                    "source_reference": rec.source_reference,
                    "difficulty": rec.difficulty
                }
                yield f"event: recommendation\ndata: {json.dumps(rec_data, ensure_ascii=False)}\n\n"

            # 5️⃣ Finalizar
            yield f"event: complete\ndata: {json.dumps({'message': 'Recomendaciones completadas', 'total': len(response.recommendations)})}\n\n"

        except Exception as e:
            error_detail = str(e.detail) if hasattr(e, 'detail') else str(e)
            yield f"event: error\ndata: {json.dumps({'error': error_detail})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  
        }
    )
