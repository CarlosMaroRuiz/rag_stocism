from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from shared.utils.quizz_user import get_quizz_user_by_id
from core.middleware.jwt_middleware import require_user_role
from typing import Dict
import json
import asyncio

router = APIRouter(prefix="/generate", tags=["Exercises"])


@router.get("/exercises/stream")
async def stream_exercises(current_user: Dict = Depends(require_user_role)):
   
    # Obtener user_id del token JWT validado
    user_id = current_user["user_id"]

    async def event_generator():
        try:
            # 1️⃣ Obtener quiz
            yield f"event: status\ndata: {json.dumps({'message': 'Obteniendo perfil estoico del usuario...'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato

            user_quiz = get_quizz_user_by_id(user_id)
            if not user_quiz:
                yield f"event: error\ndata: {json.dumps({'error': f'Quiz no encontrado para usuario {user_id}'})}\n\n"
                await asyncio.sleep(0)
                return

            # 2️⃣ Parsear quiz y construir perfil
            yield f"event: status\ndata: {json.dumps({'message': 'Analizando tu perfil estoico...'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato

            # Importar aquí para evitar dependencias circulares
            from schemas.exercise_schema import StoicQuizRequest
            from core.llm import llm_pipe

            # Convertir dict de BD a StoicQuizRequest
            if isinstance(user_quiz, dict):
                user_quiz = StoicQuizRequest(
                    age_range=user_quiz["age_range"],
                    gender=user_quiz.get("gender"),
                    country=user_quiz.get("country"),
                    religious_belief=user_quiz.get("religious_belief"),
                    spiritual_practice_level=user_quiz["spiritual_practice_level"],
                    spiritual_practice_frequency=user_quiz["spiritual_practice_frequency"],
                    stoic_level=user_quiz.get("stoic_level") or "principiante",
                    stoic_paths=user_quiz.get("stoic_paths") or [],
                    daily_challenges=user_quiz.get("daily_challenges") or [],
                    num_exercises=5
                )

            # Construir perfil
            user_profile = {
                "age_range": user_quiz.age_range,
                "gender": user_quiz.gender,
                "country": user_quiz.country,
                "belief": user_quiz.religious_belief,
                "practice_level": user_quiz.spiritual_practice_level,
                "practice_frequency": user_quiz.spiritual_practice_frequency,
                "daily_challenges": user_quiz.daily_challenges,
                "stoic_paths": user_quiz.stoic_paths,
                "stoic_level": user_quiz.stoic_level,
                "num_exercises": user_quiz.num_exercises
            }


            yield f"event: status\ndata: {json.dumps({'message': 'Buscando en los textos de Marco Aurelio, Epicteto y Séneca...'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato

            context_text, source_file = llm_pipe.get_stoic_context(user_profile, k=5)

            # 4️⃣ Enviar perfil
            stoic_paths_str = ', '.join([path.value for path in user_quiz.stoic_paths])
            profile_summary = (
                f"Usuario {user_quiz.age_range.value} | "
                f"{user_quiz.spiritual_practice_level.value} | "
                f"Nivel estoico: {user_quiz.stoic_level.value} | "
                f"Caminos: {stoic_paths_str}"
            )

            yield f"event: profile\ndata: {json.dumps({'summary': profile_summary, 'topic': 'estoicismo'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato

            # 5️⃣ Generar y enviar cada ejercicio UNO POR UNO en tiempo real
            total_exercises = user_quiz.num_exercises

            for i in range(1, total_exercises + 1):
                yield f"event: status\ndata: {json.dumps({'message': f'Creando ejercicio estoico {i} de {total_exercises}...'})}\n\n"
                await asyncio.sleep(0)  # Forzar flush del mensaje de status

                # Generar un solo ejercicio
                raw_response = llm_pipe.generate_single_exercise(
                    user_profile=user_profile,
                    exercise_number=i,
                    total_exercises=total_exercises,
                    context_text=context_text,
                    source_file=source_file
                )

                # Limpiar y parsear JSON
                clean_json = raw_response.strip()

                if "```" in clean_json:
                    parts = clean_json.split("```")
                    if len(parts) >= 3:
                        clean_json = parts[1]
                    elif len(parts) == 2:
                        clean_json = parts[1]

                    if clean_json.startswith("json") or clean_json.startswith("JSON"):
                        clean_json = clean_json[4:]

                clean_json = clean_json.strip()

                if not clean_json.startswith("{"):
                    json_start = clean_json.find("{")
                    if json_start != -1:
                        clean_json = clean_json[json_start:]

                exercise_data = json.loads(clean_json)

                # Enviar ejercicio inmediatamente
                exercise_data["index"] = i
                exercise_data["total"] = total_exercises

                yield f"event: exercise\ndata: {json.dumps(exercise_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # ⚡ CRÍTICO: Forzar flush inmediato del ejercicio al cliente

            # 6️⃣ Finalizar
            yield f"event: complete\ndata: {json.dumps({'message': 'Ejercicios completados', 'total': total_exercises})}\n\n"
            await asyncio.sleep(0)  # Forzar flush final

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
