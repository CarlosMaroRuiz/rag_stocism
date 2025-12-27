import json
from typing import Dict, Any
from fastapi import HTTPException

from core.llm import llm_pipe
from schemas.recommendation_schema import (
    GenerateRecommendationsResponse,
    Recommendation,
    StoicQuizRequest
)


class RecommendationController:

    def _parse_db_quiz_to_request(self, db_quiz: Dict[str, Any]) -> StoicQuizRequest:
        """
        Convierte un dict de BD a StoicQuizRequest.
        Los datos ya vienen normalizados por get_quizz_user_by_id().
        """
        # Los campos ya vienen parseados como listas por _normalize_quiz()
        return StoicQuizRequest(
            age_range=db_quiz["age_range"],
            gender=db_quiz.get("gender"),
            country=db_quiz.get("country"),
            religious_belief=db_quiz.get("religious_belief"),
            spiritual_practice_level=db_quiz["spiritual_practice_level"],
            spiritual_practice_frequency=db_quiz["spiritual_practice_frequency"],
            stoic_level=db_quiz.get("stoic_level") or "principiante",  # Default si es None o vacío
            stoic_paths=db_quiz.get("stoic_paths") or [],
            daily_challenges=db_quiz.get("daily_challenges") or [],
            num_recommendations=5
        )

    async def generate_recommendations(
        self,
        user_quiz: StoicQuizRequest | Dict[str, Any]  # Acepta ambos formatos
    ) -> GenerateRecommendationsResponse:
        try:
            # 0️⃣ Si viene de BD (dict), convertir a StoicQuizRequest
            if isinstance(user_quiz, dict):
                user_quiz = self._parse_db_quiz_to_request(user_quiz)

            # 1️⃣ Construir perfil semántico desde el cuestionario estoico
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
                "num_recommendations": user_quiz.num_recommendations
            }

            # 2️⃣ Llamar al LLM RAG con vectores estoicos
            raw_response = llm_pipe.generate_recommendations(
                user_profile=user_profile,
                k=5  # Recuperar 5 chunks de textos estoicos
            )

            # 3️⃣ Limpiar markdown del LLM
            print(f"🔍 DEBUG - Raw LLM Response (primeros 300 chars):\n{raw_response[:300]}\n")

            clean_json = raw_response.strip()

            # Remover bloques de código markdown si existen
            if "```" in clean_json:
                # Buscar el contenido entre ``` y ```
                parts = clean_json.split("```")
                if len(parts) >= 3:
                    # Tomar la segunda parte (el contenido del bloque)
                    clean_json = parts[1]
                    # Remover el lenguaje (json, etc.) si existe
                    if clean_json.startswith("json"):
                        clean_json = clean_json[4:]
                    elif clean_json.startswith("JSON"):
                        clean_json = clean_json[4:]
                elif len(parts) == 2:
                    # Caso: solo hay un bloque de código (ej: "texto ```json...")
                    clean_json = parts[1]
                    if clean_json.startswith("json"):
                        clean_json = clean_json[4:]
                    elif clean_json.startswith("JSON"):
                        clean_json = clean_json[4:]

            clean_json = clean_json.strip()

            print(f"✅ DEBUG - JSON limpio (primeros 300 chars):\n{clean_json[:300]}\n")

            # Verificar que no esté vacío
            if not clean_json:
                raise ValueError(
                    f"La respuesta del LLM está vacía después de limpiar markdown.\n"
                    f"Raw response: {raw_response[:500]}"
                )

            # Intentar encontrar JSON si está embebido en texto
            if not clean_json.startswith("{"):
                # Buscar el primer { y tomar desde ahí
                json_start = clean_json.find("{")
                if json_start != -1:
                    clean_json = clean_json[json_start:]
                    print(f"⚠️  DEBUG - JSON encontrado en posición {json_start}")
                else:
                    raise ValueError(
                        f"No se encontró JSON válido en la respuesta.\n"
                        f"Cleaned response: {clean_json[:500]}"
                    )

            data = json.loads(clean_json)

            recommendations = [
                Recommendation(**rec)
                for rec in data["recommendations"]
            ]

            # 4️⃣ Resumen del perfil estoico
            stoic_paths_str = ', '.join([path.value for path in user_quiz.stoic_paths])
            profile_summary = (
                f"Usuario {user_quiz.age_range.value} | "
                f"{user_quiz.spiritual_practice_level.value} | "
                f"Nivel estoico: {user_quiz.stoic_level.value} | "
                f"Caminos: {stoic_paths_str}"
            )

            return GenerateRecommendationsResponse(
                user_profile_summary=profile_summary,
                topic="estoicismo",
                recommendations=recommendations
            )

        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {str(e)}")
            print(f"❌ Problematic JSON (primeros 500 chars): {clean_json[:500] if 'clean_json' in locals() else 'N/A'}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Error al parsear respuesta del LLM",
                    "json_error": str(e),
                    "raw_preview": raw_response[:300] if 'raw_response' in locals() else "N/A",
                    "suggestion": "El LLM no retornó JSON válido. Revisa el prompt o el modelo."
                }
            )
        except ValueError as e:
            print(f"❌ ValueError: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Error en formato de respuesta",
                    "details": str(e),
                    "suggestion": "La respuesta del LLM no contiene JSON válido"
                }
            )
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Error generando recomendaciones: {str(e)}"
            )


recommendation_controller = RecommendationController()
