from typing import List, Dict
from pathlib import Path
import uuid

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from core.enviroment import env

class LlmPipe:
    def __init__(self):
        # Embeddings locales
        self.embeddings = HuggingFaceEmbeddings(
            model_name=env.EMBEDDING_MODEL,
        )

        # Vector store para textos estoicos
        self.collection_name = "stoic_texts"
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            connection=env.RAG_DB_CONN,
            collection_name=self.collection_name,
            use_jsonb=True,
        )

        # LLM OpenAI
        self.llm = ChatOpenAI(
            model=env.OPENAI_MODEL,
            temperature=0.8,  # Aumentada para mayor creatividad y variedad
            api_key=env.OPENAI_API_KEY,
        )

    def ingest_pdf(
        self, 
        file_path: str, 
        document_id: str | None = None,
        minio_path: str | None = None
    ) -> dict:
        """Ingesta un PDF: chunking + embeddings + store"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró: {file_path}")

        doc_id = document_id or str(uuid.uuid4())
        minio_path = minio_path or f"pdfs/{path.name}"

        loader = PyPDFLoader(str(path))
        pages: List[Document] = loader.load()

        full_text = "\n\n".join([page.page_content for page in pages])

        # Optimizado para textos filosóficos estoicos
        # - Chunks más grandes para preservar argumentos completos
        # - Mayor overlap para mantener contexto filosófico
        # - Separadores priorizando estructura de párrafos y oraciones
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=300,
            separators=[
                "\n\n\n",  # Secciones grandes
                "\n\n",    # Párrafos (prioridad alta para textos filosóficos)
                "\n",      # Líneas
                ". ",      # Oraciones completas
                "; ",      # Cláusulas
                ", ",      # Frases
                " ",       # Palabras
                ""         # Caracteres
            ],
        )
        chunks = splitter.split_text(full_text)

        documents = []
        for idx, chunk_text in enumerate(chunks):
            doc = Document(
                page_content=chunk_text,
                metadata={
                    "document_id": doc_id,
                    "file_name": path.name,
                    "minio_path": minio_path,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                }
            )
            documents.append(doc)

        self.vector_store.add_documents(documents)

        return {
            "document_id": doc_id,
            "file_name": path.name,
            "total_chunks": len(chunks),
            "minio_path": minio_path,
        }

    def generate_single_exercise(
        self,
        user_profile: Dict,
        exercise_number: int,
        total_exercises: int,
        context_text: str,
        source_file: str,
        focus_offset: int = 0
    ) -> str:
        """
        Genera UN solo ejercicio estoico práctico para streaming en tiempo real.

        Args:
            user_profile: Perfil del usuario
            exercise_number: Número de este ejercicio (1-based)
            total_exercises: Total de ejercicios a generar
            context_text: Contexto de textos estoicos
            source_file: Nombre del archivo fuente
            focus_offset: Offset para variar el focus_area y evitar repeticiones

        Returns:
            JSON con un solo ejercicio
        """
        prompt = self._build_single_exercise_prompt(
            user_profile=user_profile,
            exercise_number=exercise_number,
            total_exercises=total_exercises,
            context=context_text,
            source_file=source_file,
            focus_offset=focus_offset
        )

        resp = self.llm.invoke(prompt)
        return resp.content

    def get_stoic_context(self, user_profile: Dict, k: int = 5) -> tuple[str, str]:
        """
        Obtiene el contexto de textos estoicos una sola vez para todas las recomendaciones.

        Returns:
            Tuple de (context_text, source_file)
        """
        search_query = self._build_search_query(user_profile)

        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(search_query)

        if not docs:
            return ("", "principios fundamentales del estoicismo")

        context_text = "\n\n".join([d.page_content for d in docs])
        source_file = docs[0].metadata.get("file_name", "textos estoicos")

        # Limpiar el nombre del archivo: eliminar UUID de MinIO si existe
        # Formato: "uuid_nombre.pdf" -> "nombre.pdf"
        import re
        source_file = re.sub(r'^[a-f0-9\-]{36}_', '', source_file)

        return (context_text, source_file)

    def _build_search_query(self, profile: Dict) -> str:
        """Construye query optimizada para búsqueda en textos estoicos"""
        parts = ["estoicismo filosofía"]  # Base para textos estoicos

        # Agregar caminos estoicos de interés
        if profile.get("stoic_paths"):
            paths = profile["stoic_paths"]
            # Convertir enums a valores si es necesario
            path_values = [p.value if hasattr(p, 'value') else str(p) for p in paths]
            parts.extend(path_values)

        # Agregar desafíos/prácticas del usuario
        if profile.get("daily_challenges"):
            challenges = profile["daily_challenges"]
            challenge_values = [c.value if hasattr(c, 'value') else str(c) for c in challenges]
            parts.extend(challenge_values)

        # Nivel de conocimiento estoico
        if profile.get("stoic_level"):
            level = profile["stoic_level"]
            level_value = level.value if hasattr(level, 'value') else str(level)
            parts.append(level_value)

        return " ".join(parts)

    def _build_single_exercise_prompt(
        self,
        user_profile: Dict,
        exercise_number: int,
        total_exercises: int,
        context: str,
        source_file: str,
        focus_offset: int = 0
    ) -> str:
        """Construye el prompt para generar UN solo ejercicio estoico práctico (streaming)"""

        # Extraer valores de enums si es necesario
        def get_value(item):
            return item.value if hasattr(item, 'value') else str(item)

        age_range = get_value(user_profile.get('age_range', 'adulto'))
        practice_level = get_value(user_profile.get('practice_level', 'principiante'))
        practice_freq = get_value(user_profile.get('practice_frequency', 'ocasionalmente'))
        stoic_level = get_value(user_profile.get('stoic_level', 'principiante'))

        # Procesar listas
        stoic_paths = user_profile.get('stoic_paths', [])
        paths_str = ', '.join([get_value(p) for p in stoic_paths]) if stoic_paths else 'No especificados'

        daily_challenges = user_profile.get('daily_challenges', [])
        challenges_str = ', '.join([get_value(c) for c in daily_challenges]) if daily_challenges else 'No especificados'

        belief = user_profile.get('belief', 'No especificada')
        country = user_profile.get('country', '')

        profile_summary = f"""
PERFIL DEL PRACTICANTE:
- Rango de edad: {age_range}
- País: {country}
- Creencia actual: {belief}
- Nivel de práctica espiritual: {practice_level} (frecuencia: {practice_freq})
- Nivel de conocimiento estoico: {stoic_level}
- Caminos estoicos de interés: {paths_str}
- Desafíos/prácticas diarias: {challenges_str}
"""

        # Determinar enfoque basado en el número de ejercicio
        # Lista ampliada de áreas de enfoque estoico para máxima variedad
        focus_areas = [
            # Principios fundamentales
            "Dicotomía del Control - Distinguir lo que depende de ti",
            "Virtudes Cardinales - Sabiduría, Coraje, Justicia, Templanza",
            "Vivir según la Naturaleza - Alineación con el cosmos",
            "Amor Fati - Aceptación radical del destino",
            "Memento Mori - Consciencia de la mortalidad",

            # Prácticas de autocontrol
            "Autocontrol - Gestión de impulsos y deseos",
            "Indiferencia ante circunstancias externas - Ecuanimidad",
            "Desapego de resultados - Enfoque en el proceso",
            "Juicios y percepciones - Observación sin valoración",
            "Gestión de emociones destructivas - Ira, miedo, ansiedad",

            # Ejercicios espirituales clásicos
            "Premeditatio Malorum - Visualización negativa",
            "Examen diario - Revisión de acciones y pensamientos",
            "Meditación matutina - Preparación para el día",
            "Contemplación vespertina - Reflexión sobre virtudes",
            "Vista desde arriba - Perspectiva cósmica",

            # Virtudes específicas
            "Sabiduría práctica - Phronesis en decisiones diarias",
            "Coraje moral - Enfrentar adversidades con valor",
            "Justicia y benevolencia - Trato equitativo hacia otros",
            "Templanza y moderación - Equilibrio en placeres",
            "Fortaleza interior - Resiliencia ante dificultades",

            # Relaciones y comunidad
            "Cosmopolitismo - Ciudadano del mundo",
            "Empatía y comprensión - Ver desde perspectiva ajena",
            "Perdón y compasión - Liberación del resentimiento",
            "Servicio a la comunidad - Bien común sobre interés personal",
            "Relaciones virtuosas - Amistades basadas en virtud",

            # Desapego y aceptación
            "Desapego de posesiones - Libertad interior",
            "Aceptación de cambio e impermanencia - Heráclito",
            "Simplicidad voluntaria - Reducción de necesidades",
            "Indiferencia a la fama y reputación - Ego y vanidad",
            "Aceptación de la muerte - Tranquilidad ante lo inevitable",

            # Razón y logos
            "Razón como guía - Hegemonikon y facultad gobernante",
            "Assentimiento consciente - Control de impresiones",
            "Lógica estoica - Claridad de pensamiento",
            "Contemplación filosófica - Estudio de la naturaleza",
            "Coherencia entre pensamientos y acciones - Integridad",

            # Prácticas avanzadas
            "Atención plena estoica - Prosoche",
            "Reserva de clausura - Anticipación de obstáculos",
            "Ejercicio de roles - Padre, hijo, ciudadano",
            "Gratitud estoica - Apreciar lo presente",
            "Transformación de adversidad - Obstáculo como oportunidad",

            # Desarrollo del carácter
            "Progreso moral - Prokope",
            "Hábitos virtuosos - Construcción de carácter",
            "Eliminación de vicios - Identificación y corrección",
            "Coherencia interna - Alineación de valores",
            "Autosuficiencia - Autarquía estoica",

            # Sabiduría aplicada
            "Decisiones según naturaleza racional - Kata physin",
            "Preferibles vs indiferentes - Adiaphora",
            "Deber apropiado - Kathekonta",
            "Sabiduría en adversidad - Enseñanzas de Epicteto",
            "Acción recta - Katorthoma",

            # Perspectiva y contexto
            "Relatividad del juicio - Opiniones como construcciones",
            "Zoom out cósmico - Pequeñez en el universo",
            "Transitoriedad - Todo fluye y cambia",
            "Interconexión universal - Simpatía cósmica",
            "Ciclos naturales - Aceptación del ritmo de la vida"
        ]

        # Usar offset para variar y evitar repeticiones
        current_focus = focus_areas[(exercise_number - 1 + focus_offset) % len(focus_areas)]

        # Guía de niveles
        level_guide = """
NIVELES ESTOICOS:

📗 PRINCIPIANTE:
- Ejercicios simples, cortos (1 día)
- Conceptos básicos: Dicotomía del Control, Observación de emociones
- Lenguaje claro, motivador y accesible
- Ejemplos cotidianos modernos

📘 INTERMEDIO:
- Ejercicios que requieren reflexión diaria (3-7 días)
- Aplicación en conflictos reales
- Juicios y percepciones, resiliencia emocional
- Seguimiento constante

📙 AVANZADO:
- Prácticas profundas de dominio interior (1-2 semanas)
- Desapego, virtud, responsabilidad moral
- Premeditatio malorum, Amor fati
- Alto nivel de disciplina

📕 MAESTRO:
- Integración completa del estoicismo (1 mes+)
- Transformación de carácter profunda
- Aplicación universal de principios
- Máximo nivel de exigencia
"""

        prompt = f"""Eres un maestro creativo que genera EJERCICIOS PRÁCTICOS ÚNICOS y VARIADOS basados en filosofía estoica para ayudar al usuario a desarrollar dominio del temperamento, autocontrol, virtud y claridad mental.

🎯 PRINCIPIO FUNDAMENTAL: VARIEDAD Y CREATIVIDAD
Cada ejercicio que generes debe ser COMPLETAMENTE DIFERENTE a los demás. No repitas estructuras, nombres, objetivos o enfoques similares. Sé innovador y creativo en cada ejercicio.

{level_guide}

{profile_summary}

CONTENIDO DEL LIBRO "{source_file}":
{context}

INSTRUCCIONES:
Estás generando el ejercicio #{exercise_number} de {total_exercises} para este practicante.

ENFOQUE PARA ESTE EJERCICIO: {current_focus}

⚠️ RECUERDA: Este ejercicio debe ser ÚNICO y DIFERENTE a cualquier otro que hayas generado antes. Varía el enfoque, la estructura, los ejemplos y el estilo.

El ejercicio debe:
1. Estar DIRECTAMENTE INSPIRADO en el CONTENIDO DEL LIBRO proporcionado arriba
2. Extraer ideas, principios y enseñanzas específicas del texto
3. Enfocarse en: {current_focus}
4. Ser relevante a los caminos de interés: {paths_str}
5. Abordar sus desafíos específicos: {challenges_str}
6. Adaptarse a su nivel: {stoic_level}
7. Ser aplicable a la vida cotidiana HOY
8. Incluir reflexión o autoevaluación

Enfoque por nivel:
- "principiante": Simple, 1 día, conceptos básicos, muy accesible
- "intermedio": 3-7 días, reflexión diaria, aplicación en conflictos
- "avanzado": 1-2 semanas, dominio interior profundo, desapego
- "maestro": 1 mes+, transformación de carácter, máxima exigencia

FORMATO DE RESPUESTA (JSON con UN solo ejercicio):
{{
  "name": "Nombre descriptivo del ejercicio basado en el contenido del libro",
  "level": "{stoic_level}",
  "objective": "Objetivo claro y específico conectado con las enseñanzas del texto",
  "instructions": "Instrucciones paso a paso muy claras y prácticas, inspiradas en las ideas del libro. Sé específico sobre qué hacer, cuándo hacerlo, y cómo aplicarlo en la vida diaria.",
  "duration": "Duración del ejercicio según el nivel (ej: '1 día', '3 días', '1 semana', '1 mes')",
  "reflection": "Pregunta de reflexión o autoevaluación relacionada con el ejercicio",
  "source": "INCLUYE: 1) El nombre del libro fuente '{source_file}', 2) El autor/concepto que aparece en el contenido, 3) Capítulo o sección si está disponible. Formato: 'De [libro] - [autor], [capítulo/concepto]'. Ejemplo: 'De 24 Stoic Spiritual Exercises - Epictetus, Enchiridion IV'"
}}

TONO Y ESTILO:
- Directo y práctico
- Instrucciones claras que cualquiera pueda seguir
- Conecta las enseñanzas del libro con desafíos modernos
- Motivador pero realista
- Enfoque estoico basado en el CONTENIDO REAL del libro

CRÍTICO - MUY IMPORTANTE - VARIEDAD Y CREATIVIDAD:
- RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL
- Basa el ejercicio en las IDEAS ESPECÍFICAS del contenido proporcionado
- Las instrucciones deben ser específicas y accionables
- La duración debe corresponder al nivel del usuario
- El ejercicio debe complementar los otros {total_exercises - 1} ejercicios

⚠️ VARIEDAD Y NO REPETICIÓN (CRÍTICO):
- CADA ejercicio debe ser COMPLETAMENTE ÚNICO y DIFERENTE
- NO repitas nombres, objetivos o instrucciones similares
- Varía el enfoque, el formato y la estructura de cada ejercicio
- Usa diferentes ejemplos, situaciones y contextos
- Sé CREATIVO: cada ejercicio debe tener su propia personalidad
- Si generas ejercicios similares, el usuario notará la repetición - EVÍTALO
- Busca diferentes ángulos del mismo concepto para mantener variedad
- Varía el estilo de las instrucciones (algunas más narrativas, otras más directas)
- Usa diferentes metáforas, analogías y formas de explicar

FUENTES Y REFERENCIAS:
- En el campo "source": SIEMPRE incluye el nombre del libro "{source_file}" + el autor/concepto del contenido
- FORMATO DE SOURCE: "De [nombre_libro] - [autor], [capítulo/concepto]"
- EXTRAE Y CITA a los autores que aparecen en el contenido del libro para dar VARIEDAD
- Si el texto menciona autores específicos (Marcus Aurelius, Epictetus, Seneca, u otros), ÚSALOS
- Si el texto menciona un libro específico o capítulo, inclúyelo después del autor
- Proporciona referencias DIVERSAS basadas en lo que realmente dice el contenido
- Varía las citas y referencias entre ejercicios para evitar repetición
"""
        return prompt

    def _build_exercise_batch_prompt(
        self,
        user_profile: Dict,
        context: str,
        source_file: str
    ) -> str:
        """Construye el prompt especializado en filosofía estoica (DEPRECATED - usar _build_single_exercise_prompt)"""

        # Extraer valores de enums si es necesario
        def get_value(item):
            return item.value if hasattr(item, 'value') else str(item)

        age_range = get_value(user_profile.get('age_range', 'adulto'))
        practice_level = get_value(user_profile.get('practice_level', 'principiante'))
        practice_freq = get_value(user_profile.get('practice_frequency', 'ocasionalmente'))
        stoic_level = get_value(user_profile.get('stoic_level', 'principiante'))

        # Procesar listas
        stoic_paths = user_profile.get('stoic_paths', [])
        paths_str = ', '.join([get_value(p) for p in stoic_paths]) if stoic_paths else 'No especificados'

        daily_challenges = user_profile.get('daily_challenges', [])
        challenges_str = ', '.join([get_value(c) for c in daily_challenges]) if daily_challenges else 'No especificados'

        belief = user_profile.get('belief', 'No especificada')
        country = user_profile.get('country', '')

        profile_summary = f"""
PERFIL DEL DISCÍPULO:
- Rango de edad: {age_range}
- País: {country}
- Creencia actual: {belief}
- Nivel de práctica espiritual: {practice_level} (frecuencia: {practice_freq})
- Nivel de conocimiento estoico: {stoic_level}
- Caminos estoicos de interés: {paths_str}
- Desafíos/prácticas diarias: {challenges_str}
"""

        num_exercises = user_profile.get('num_exercises', 5)

        prompt = f"""Eres un sabio filósofo estoico, seguidor de las enseñanzas de Marco Aurelio, Epicteto y Séneca.

PRINCIPIOS ESTOICOS FUNDAMENTALES:
1. Dicotomía del Control: Distinguir entre lo que está en nuestro poder (juicios, deseos, acciones) y lo que no (eventos externos, opiniones ajenas, salud)
2. Las Cuatro Virtudes Cardinales:
   - Sabiduría (Sophia): Conocimiento práctico y buen juicio
   - Coraje (Andreia): Fortaleza para enfrentar adversidades
   - Justicia (Dikaiosyne): Trato equitativo hacia otros
   - Templanza (Sophrosyne): Moderación y autocontrol
3. Vivir según la Naturaleza y la Razón
4. Amor Fati: Aceptación radical del destino
5. Memento Mori: Recordatorio de la mortalidad
6. Premeditatio Malorum: Visualización negativa para prepararse

{profile_summary}

TEXTO ESTOICO "{source_file}":
{context}

INSTRUCCIONES:
Como maestro estoico, genera {num_exercises} ejercicios PERSONALIZADOS basados en los textos clásicos y el perfil del discípulo.

Cada ejercicio debe:
1. Estar fundamentado en el TEXTO ESTOICO proporcionado
2. Ser relevante a los caminos estoicos de interés del discípulo ({paths_str})
3. Abordar sus desafíos/prácticas específicas ({challenges_str})
4. Adaptarse a su nivel de conocimiento estoico ({stoic_level})
5. Incluir prácticas estoicas concretas
6. Citar directamente a los maestros estoicos cuando sea posible

Enfoque pedagógico:
- Para nivel "principiante": Explica conceptos básicos con ejemplos cotidianos modernos
- Para nivel "intermedio": Profundiza en las virtudes cardinales y su aplicación
- Para nivel "avanzado": Enfócate en paradojas estoicas y prácticas avanzadas
- Para nivel "maestro": Analiza matices filosóficos y conexiones profundas

FORMATO DE RESPUESTA (JSON):
{{
  "exercises": [
    {{
      "title": "Título del ejercicio estoico",
      "content": "Explicación filosófica detallada conectando el texto clásico con la vida moderna del discípulo. Incluye un ejercicio práctico estoico específico (ej: meditación matutina, examen vespertino, visualización negativa).",
      "source_reference": "Cita textual del maestro estoico (Marco Aurelio, Epicteto o Séneca) del texto proporcionado",
      "level": "principiante|intermedio|avanzado|maestro"
    }}
  ]
}}

TONO Y ESTILO:
- Usa lenguaje filosófico pero accesible, al estilo de los estoicos clásicos
- Sé directo y sin rodeos, como Epicteto
- Conecta la sabiduría antigua con desafíos modernos ({challenges_str})
- Usa metáforas naturales (río, piedra, árbol) cuando sea apropiado
- Termina cada ejercicio con una práctica concreta aplicable HOY

IMPORTANTE:
- RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL
- Cada "content" debe tener mínimo 150 palabras para ser sustancial
- Las citas en "source_reference" deben ser del texto estoico proporcionado
"""
        return prompt

    def _generate_without_context(self, user_profile: Dict) -> str:
        """Fallback con ejercicios estoicos generales (sin RAG)"""

        def get_value(item):
            return item.value if hasattr(item, 'value') else str(item)

        stoic_level = get_value(user_profile.get('stoic_level', 'principiante'))
        stoic_paths = user_profile.get('stoic_paths', [])
        paths_str = ', '.join([get_value(p) for p in stoic_paths]) if stoic_paths else 'las virtudes cardinales'

        num_exercises = user_profile.get('num_exercises', 5)

        prompt = f"""Eres un maestro estoico. No se encontró contenido específico en los textos, pero genera {num_exercises} ejercicios estoicos FUNDAMENTALES.

Nivel del discípulo: {stoic_level}
Caminos de interés: {paths_str}

Genera ejercicios basados en los PRINCIPIOS CLÁSICOS del estoicismo:
1. Dicotomía del Control (Epicteto)
2. Las Cuatro Virtudes Cardinales
3. Amor Fati (Marco Aurelio)
4. Memento Mori
5. Premeditatio Malorum

Cada ejercicio debe incluir:
- Explicación del principio estoico
- Práctica concreta
- Referencia al maestro estoico que lo enseñó

Formato JSON:
{{
  "exercises": [
    {{
      "title": "Título del principio estoico",
      "content": "Explicación detallada (mínimo 150 palabras) con ejercicio práctico aplicable hoy",
      "source_reference": "Principio fundamental del estoicismo (Marco Aurelio/Epicteto/Séneca)",
      "level": "principiante|intermedio|avanzado|maestro"
    }}
  ]
}}

IMPORTANTE: RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL
"""
        resp = self.llm.invoke(prompt)
        return resp.content


# Singleton global
llm_pipe = LlmPipe()