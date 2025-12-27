from typing import List, Dict
from pathlib import Path
import uuid

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_deepseek import ChatDeepSeek

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

        # LLM DeepSeek
        self.llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.3,
            api_key=env.DEEPSEEK_API_KEY,
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

    def generate_recommendations(
        self, 
        user_profile: Dict,
        k: int = 5
    ) -> str:
        """
        Genera recomendaciones personalizadas basadas en:
        - El perfil del usuario
        - Contenido del libro (RAG)
        """
        
        search_query = self._build_search_query(user_profile)
        
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(search_query)

        if not docs:
            return self._generate_without_context(user_profile)

        context_text = "\n\n".join([d.page_content for d in docs])
        source_file = docs[0].metadata.get("file_name", "libro desconocido")

        prompt = self._build_recommendation_prompt(
            user_profile=user_profile,
            context=context_text,
            source_file=source_file
        )

        resp = self.llm.invoke(prompt)
        return resp.content

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

    def _build_recommendation_prompt(
        self,
        user_profile: Dict,
        context: str,
        source_file: str
    ) -> str:
        """Construye el prompt especializado en filosofía estoica"""

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

        num_recommendations = user_profile.get('num_recommendations', 5)

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
Como maestro estoico, genera {num_recommendations} enseñanzas PERSONALIZADAS basadas en los textos clásicos y el perfil del discípulo.

Cada enseñanza debe:
1. Estar fundamentada en el TEXTO ESTOICO proporcionado
2. Ser relevante a los caminos estoicos de interés del discípulo ({paths_str})
3. Abordar sus desafíos/prácticas específicas ({challenges_str})
4. Adaptarse a su nivel de conocimiento estoico ({stoic_level})
5. Incluir ejercicios prácticos estoicos concretos
6. Citar directamente a los maestros estoicos cuando sea posible

Enfoque pedagógico:
- Para nivel "principiante": Explica conceptos básicos con ejemplos cotidianos modernos
- Para nivel "intermedio": Profundiza en las virtudes cardinales y su aplicación
- Para nivel "avanzado": Enfócate en paradojas estoicas y prácticas avanzadas
- Para nivel "maestro": Analiza matices filosóficos y conexiones profundas

FORMATO DE RESPUESTA (JSON):
{{
  "recommendations": [
    {{
      "title": "Título de la enseñanza estoica",
      "content": "Explicación filosófica detallada conectando el texto clásico con la vida moderna del discípulo. Incluye un ejercicio práctico estoico específico (ej: meditación matutina, examen vespertino, visualización negativa).",
      "source_reference": "Cita textual del maestro estoico (Marco Aurelio, Epicteto o Séneca) del texto proporcionado",
      "difficulty": "fácil|intermedio|difícil"
    }}
  ]
}}

TONO Y ESTILO:
- Usa lenguaje filosófico pero accesible, al estilo de los estoicos clásicos
- Sé directo y sin rodeos, como Epicteto
- Conecta la sabiduría antigua con desafíos modernos ({challenges_str})
- Usa metáforas naturales (río, piedra, árbol) cuando sea apropiado
- Termina cada enseñanza con una práctica concreta aplicable HOY

IMPORTANTE:
- RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL
- Cada "content" debe tener mínimo 150 palabras para ser sustancial
- Las citas en "source_reference" deben ser del texto estoico proporcionado
"""
        return prompt

    def _generate_without_context(self, user_profile: Dict) -> str:
        """Fallback con enseñanzas estoicas generales (sin RAG)"""

        def get_value(item):
            return item.value if hasattr(item, 'value') else str(item)

        stoic_level = get_value(user_profile.get('stoic_level', 'principiante'))
        stoic_paths = user_profile.get('stoic_paths', [])
        paths_str = ', '.join([get_value(p) for p in stoic_paths]) if stoic_paths else 'las virtudes cardinales'

        num_recs = user_profile.get('num_recommendations', 5)

        prompt = f"""Eres un maestro estoico. No se encontró contenido específico en los textos, pero genera {num_recs} enseñanzas estoicas FUNDAMENTALES.

Nivel del discípulo: {stoic_level}
Caminos de interés: {paths_str}

Genera enseñanzas basadas en los PRINCIPIOS CLÁSICOS del estoicismo:
1. Dicotomía del Control (Epicteto)
2. Las Cuatro Virtudes Cardinales
3. Amor Fati (Marco Aurelio)
4. Memento Mori
5. Premeditatio Malorum

Cada enseñanza debe incluir:
- Explicación del principio estoico
- Ejercicio práctico concreto
- Referencia al maestro estoico que lo enseñó

Formato JSON:
{{
  "recommendations": [
    {{
      "title": "Título del principio estoico",
      "content": "Explicación detallada (mínimo 150 palabras) con ejercicio práctico aplicable hoy",
      "source_reference": "Principio fundamental del estoicismo (Marco Aurelio/Epicteto/Séneca)",
      "difficulty": "fácil|intermedio|difícil"
    }}
  ]
}}

IMPORTANTE: RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL
"""
        resp = self.llm.invoke(prompt)
        return resp.content


# Singleton global
llm_pipe = LlmPipe()