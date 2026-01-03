from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from shared.utils.quizz_user import get_quizz_user_by_id
from shared.utils.subscription import get_user_subscription
from core.middleware.jwt_middleware import require_user_role
from core.db.exercise_repository import ExerciseRepository
from typing import Dict, Optional
import json
import asyncio

router = APIRouter(prefix="/generate", tags=["Exercises"])


@router.get("/exercises/stream")
async def stream_exercises(current_user: Dict = Depends(require_user_role)):
   
    # Obtener user_id del token JWT validado
    user_id = current_user["user_id"]
    exercise_repo = ExerciseRepository()

    async def event_generator():
        try:
            # 0️⃣ Validar suscripción activa (PRIMERO - antes del quiz)
            yield f"event: status\ndata: {json.dumps({'message': 'Verificando suscripción...'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato
            
            user_subscription = get_user_subscription(user_id)
            if not user_subscription or not user_subscription.get("has_active_subscription", False):
                yield f"event: error\ndata: {json.dumps({'error': 'No tienes una suscripción activa. Por favor, suscríbete para generar ejercicios personalizados.'})}\n\n"
                await asyncio.sleep(0)
                return

            # 1️⃣ Verificar ejercicios pendientes
            yield f"event: status\ndata: {json.dumps({'message': 'Verificando ejercicios pendientes...'})}\n\n"
            await asyncio.sleep(0)
            
            pending_count = exercise_repo.get_pending_exercises_count(user_id)
            
            if pending_count >= 5:
                # Ya tiene 5 ejercicios pendientes, devolver los existentes
                yield f"event: status\ndata: {json.dumps({'message': f'Tienes {pending_count} ejercicios pendientes. Mostrando ejercicios existentes...'})}\n\n"
                await asyncio.sleep(0)
                
                existing_exercises = exercise_repo.get_user_exercises(user_id)
                # Filtrar solo pendientes y en progreso, limitar a 5
                pending_exercises = [ex for ex in existing_exercises if ex['status'] in ('pending', 'in_progress')][:5]
                
                if pending_exercises:
                    # Enviar perfil
                    yield f"event: profile\ndata: {json.dumps({'summary': 'Ejercicios pendientes', 'topic': 'estoicismo'})}\n\n"
                    await asyncio.sleep(0)
                    
                    for idx, exercise in enumerate(pending_exercises, 1):
                        exercise_data = {
                            "id": exercise['id'],
                            "name": exercise['exercise_name'],
                            "level": exercise['exercise_level'],
                            "objective": exercise['objective'],
                            "instructions": exercise['instructions'],
                            "duration": exercise['duration'],
                            "reflection": exercise['reflection'],
                            "source": exercise.get('source'),
                            "index": idx,
                            "total": len(pending_exercises)
                        }
                        yield f"event: exercise\ndata: {json.dumps(exercise_data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0)
                    
                    yield f"event: complete\ndata: {json.dumps({'message': 'Ejercicios cargados', 'total': len(pending_exercises)})}\n\n"
                    await asyncio.sleep(0)
                    return

            # 2️⃣ Calcular cuántos ejercicios generar
            exercises_to_generate = 5 - pending_count
            
            yield f"event: status\ndata: {json.dumps({'message': f'Generando {exercises_to_generate} nuevos ejercicios...'})}\n\n"
            await asyncio.sleep(0)

            # 3️⃣ Obtener quiz
            yield f"event: status\ndata: {json.dumps({'message': 'Obteniendo perfil estoico del usuario...'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato

            user_quiz = get_quizz_user_by_id(user_id)
            if not user_quiz:
                yield f"event: error\ndata: {json.dumps({'error': f'Quiz no encontrado para usuario {user_id}. Por favor, completa el cuestionario estoico primero.'})}\n\n"
                await asyncio.sleep(0)
                return

            # 4️⃣ Parsear quiz y construir perfil
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
                    num_exercises=exercises_to_generate
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
                "num_exercises": exercises_to_generate
            }

            yield f"event: status\ndata: {json.dumps({'message': 'Buscando en los textos de Marco Aurelio, Epicteto y Séneca...'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato

            context_text, source_file = llm_pipe.get_stoic_context(user_profile, k=5)

            # 5️⃣ Enviar perfil
            stoic_paths_str = ', '.join([path.value for path in user_quiz.stoic_paths])
            profile_summary = (
                f"Usuario {user_quiz.age_range.value} | "
                f"{user_quiz.spiritual_practice_level.value} | "
                f"Nivel estoico: {user_quiz.stoic_level.value} | "
                f"Caminos: {stoic_paths_str}"
            )

            yield f"event: profile\ndata: {json.dumps({'summary': profile_summary, 'topic': 'estoicismo'})}\n\n"
            await asyncio.sleep(0)  # Forzar flush inmediato

            # Obtener offset basado en ejercicios completados para evitar repeticiones
            completed_count = exercise_repo.get_completed_exercises_count(user_id)
            focus_offset = completed_count

            # 6️⃣ Generar y enviar cada ejercicio UNO POR UNO en tiempo real
            for i in range(1, exercises_to_generate + 1):
                yield f"event: status\ndata: {json.dumps({'message': f'Creando ejercicio estoico {i} de {exercises_to_generate}...'})}\n\n"
                await asyncio.sleep(0)  # Forzar flush del mensaje de status

                # Generar un solo ejercicio
                raw_response = llm_pipe.generate_single_exercise(
                    user_profile=user_profile,
                    exercise_number=i,
                    total_exercises=exercises_to_generate,
                    context_text=context_text,
                    source_file=source_file,
                    focus_offset=focus_offset  # Pasar offset para variar
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

                # Guardar en BD
                exercise_id = exercise_repo.create_exercise(user_id, exercise_data)
                exercise_data["id"] = exercise_id

                # Enviar ejercicio inmediatamente
                exercise_data["index"] = i
                exercise_data["total"] = exercises_to_generate

                yield f"event: exercise\ndata: {json.dumps(exercise_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # ⚡ CRÍTICO: Forzar flush inmediato del ejercicio al cliente

            # 7️⃣ Finalizar
            yield f"event: complete\ndata: {json.dumps({'message': 'Ejercicios generados y guardados', 'total': exercises_to_generate})}\n\n"
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


# ==================== NUEVOS ENDPOINTS PARA GESTIÓN DE EJERCICIOS ====================

@router.post("/exercises/{exercise_id}/complete")
async def complete_exercise(
    exercise_id: str,
    current_user: Dict = Depends(require_user_role)
):
    """
    Marca un ejercicio como completado.
    Solo genera 5 nuevos ejercicios cuando se completen los 5 pendientes.
    """
    user_id = current_user["user_id"]
    exercise_repo = ExerciseRepository()
    
    # Verificar que el ejercicio existe y pertenece al usuario
    exercise = exercise_repo.get_exercise_by_id(exercise_id, user_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    if exercise['status'] == 'completed':
        raise HTTPException(status_code=400, detail="El ejercicio ya está completado")
    
    # Marcar como completado
    success = exercise_repo.mark_exercise_completed(exercise_id, user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Error al completar el ejercicio")
    
    # Verificar cuántos pendientes quedan DESPUÉS de completar
    pending_count = exercise_repo.get_pending_exercises_count(user_id)
    
    # Solo generar nuevos ejercicios si se completaron los 5 (pending_count == 0)
    new_exercises_generated = False
    if pending_count == 0:
        # Validar suscripción activa antes de generar nuevos ejercicios
        user_subscription = get_user_subscription(user_id)
        if not user_subscription or not user_subscription.get("has_active_subscription", False):
            return {
                "message": "Ejercicio completado exitosamente",
                "exercise_id": exercise_id,
                "pending_count": 0,
                "new_exercises_generated": False,
                "warning": "No se pudieron generar nuevos ejercicios porque no tienes una suscripción activa."
            }
        
        # Generar 5 nuevos ejercicios
        try:
            user_quiz = get_quizz_user_by_id(user_id)
            if user_quiz:
                from schemas.exercise_schema import StoicQuizRequest
                from core.llm import llm_pipe
                
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
                        num_exercises=5  # Generar 5 nuevos
                    )
                
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
                    "num_exercises": 5
                }
                
                # Obtener contexto RAG
                context_text, source_file = llm_pipe.get_stoic_context(user_profile, k=5)
                
                # Obtener offset basado en ejercicios completados para evitar repeticiones
                completed_count = exercise_repo.get_completed_exercises_count(user_id)
                focus_offset = completed_count
                
                # Generar los 5 ejercicios
                for i in range(1, 6):
                    raw_response = llm_pipe.generate_single_exercise(
                        user_profile=user_profile,
                        exercise_number=i,
                        total_exercises=5,
                        context_text=context_text,
                        source_file=source_file,
                        focus_offset=focus_offset  # Pasar offset para variar
                    )
                    
                    # Limpiar y parsear JSON
                    clean_json = raw_response.strip()
                    if "```" in clean_json:
                        parts = clean_json.split("```")
                        if len(parts) >= 3:
                            clean_json = parts[1]
                        if clean_json.startswith("json") or clean_json.startswith("JSON"):
                            clean_json = clean_json[4:]
                    
                    clean_json = clean_json.strip()
                    if not clean_json.startswith("{"):
                        json_start = clean_json.find("{")
                        if json_start != -1:
                            clean_json = clean_json[json_start:]
                    
                    exercise_data = json.loads(clean_json)
                    exercise_repo.create_exercise(user_id, exercise_data)
                new_exercises_generated = True
                
        except Exception as e:
            print(f"Error al generar nuevos ejercicios: {e}")
    
    return {
        "message": "Ejercicio completado exitosamente",
        "exercise_id": exercise_id,
        "pending_count": pending_count,
        "new_exercises_generated": new_exercises_generated,
        "info": "Se generaron 5 nuevos ejercicios" if new_exercises_generated else f"Quedan {pending_count} ejercicios pendientes"
    }


@router.get("/exercises")
async def get_user_exercises(
    status: Optional[str] = None,
    current_user: Dict = Depends(require_user_role)
):
    """Obtiene los ejercicios del usuario, opcionalmente filtrados por estado"""
    user_id = current_user["user_id"]
    exercise_repo = ExerciseRepository()
    
    # Validar status si se proporciona
    if status and status not in ['pending', 'in_progress', 'completed']:
        raise HTTPException(
            status_code=400, 
            detail="Status inválido. Debe ser: pending, in_progress o completed"
        )
    
    exercises = exercise_repo.get_user_exercises(user_id, status)
    
    # Formatear ejercicios para la respuesta
    formatted_exercises = []
    for ex in exercises:
        formatted_exercises.append({
            "id": ex['id'],
            "name": ex['exercise_name'],
            "level": ex['exercise_level'],
            "objective": ex['objective'],
            "instructions": ex['instructions'],
            "duration": ex['duration'],
            "reflection": ex['reflection'],
            "source": ex.get('source'),
            "status": ex['status'],
            "completed_at": str(ex['completed_at']) if ex.get('completed_at') else None,
            "created_at": str(ex['created_at']) if ex.get('created_at') else None
        })
    
    return {
        "exercises": formatted_exercises,
        "total": len(formatted_exercises),
        "pending_count": exercise_repo.get_pending_exercises_count(user_id)
    }
