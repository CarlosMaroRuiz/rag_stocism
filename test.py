"""
Script de prueba para el sistema de recomendaciones estoicas.

Uso:
    python test.py              # Prueba directa del controller
    python test.py --sse        # Prueba del endpoint SSE (requiere servidor corriendo)
"""
import asyncio
import json
import sys
from controllers.recommendation_controller import recommendation_controller
from shared.utils.quizz_user import get_quizz_user_by_id


async def test_recommendations():
    print("=" * 80)
    print("🧘 TEST: Sistema de Recomendaciones Estoicas")
    print("=" * 80)

    # Usuario de prueba (el mismo del default en la ruta)
    user_id = "7e41ec3e-344a-42d4-8aba-f75196098e10"

    print(f"\n1️⃣ Obteniendo quiz del usuario: {user_id}")
    user_quiz = get_quizz_user_by_id(user_id)

    if not user_quiz:
        print(f"❌ ERROR: No se encontró el quiz para el usuario {user_id}")
        print("💡 Asegúrate de que el usuario existe en la base de datos")
        return

    print(f"✅ Quiz obtenido exitosamente:")
    print(json.dumps(user_quiz, indent=2, ensure_ascii=False))

    print(f"\n2️⃣ Generando recomendaciones estoicas...")
    try:
        response = await recommendation_controller.generate_recommendations(user_quiz)

        print(f"\n✅ Recomendaciones generadas exitosamente!")
        print(f"📊 Perfil: {response.user_profile_summary}")
        print(f"📚 Tema: {response.topic}")
        print(f"🎯 Número de recomendaciones: {len(response.recommendations)}")

        print("\n" + "=" * 80)
        print("📖 RECOMENDACIONES ESTOICAS:")
        print("=" * 80)

        for idx, rec in enumerate(response.recommendations, 1):
            print(f"\n{'─' * 80}")
            print(f"📌 Recomendación {idx}: {rec.title}")
            print(f"   Dificultad: {rec.difficulty}")
            print(f"{'─' * 80}")
            print(f"\n{rec.content}\n")
            print(f"💬 Fuente: {rec.source_reference}")
            print(f"{'─' * 80}")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR al generar recomendaciones:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")

        if hasattr(e, 'detail'):
            print(f"\n📋 Detalles del error:")
            print(json.dumps(e.detail, indent=2, ensure_ascii=False))

        import traceback
        print(f"\n🔍 Traceback completo:")
        traceback.print_exc()


def test_sse_endpoint():
    """Prueba el endpoint SSE (requiere que el servidor esté corriendo)"""
    import requests

    print("=" * 80)
    print("🌊 TEST: Endpoint SSE (Server-Sent Events)")
    print("=" * 80)

    user_id = "7e41ec3e-344a-42d4-8aba-f75196098e10"
    url = f"http://localhost:8000/generate/recommendations/stream?user_id={user_id}"

    print(f"\n📡 Conectando a: {url}\n")

    try:
        # Hacer request con stream=True para SSE
        response = requests.get(url, stream=True, timeout=120)

        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}")
            print(response.text)
            return

        print("✅ Conexión SSE establecida. Escuchando eventos...\n")
        print("=" * 80)

        # Procesar eventos SSE
        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.startswith('event:'):
                    event_type = line.split(':', 1)[1].strip()
                    print(f"\n🔔 Evento: {event_type}")

                elif line.startswith('data:'):
                    data = line.split(':', 1)[1].strip()
                    try:
                        parsed_data = json.loads(data)
                        print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print(data)

        print("\n" + "=" * 80)
        print("✅ Stream completado")
        print("=" * 80)

    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("💡 Asegúrate de que el servidor esté corriendo: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if "--sse" in sys.argv:
        print("\n🌊 Probando endpoint SSE...\n")
        test_sse_endpoint()
    else:
        print("\n🚀 Iniciando test directo del controller...\n")
        asyncio.run(test_recommendations())
