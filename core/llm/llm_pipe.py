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

        # Vector store (parámetros correctos)
        self.collection_name = "docs_rag"
        self.vector_store = PGVector(
            embeddings=self.embeddings,        # ✅ Correcto
            connection=env.RAG_DB_CONN,        # ✅ Correcto: 'connection' no 'connection_string'
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
        """Construye query optimizada para RAG"""
        parts = [profile.get("topic", "")]
        
        if profile.get("current_situation"):
            parts.append(profile["current_situation"])
        
        if profile.get("goals"):
            parts.append(profile["goals"])
        
        if profile.get("interests"):
            parts.extend(profile["interests"])
        
        return " ".join(parts)

    def _build_recommendation_prompt(
        self, 
        user_profile: Dict, 
        context: str,
        source_file: str
    ) -> str:
        """Construye el prompt para generar recomendaciones"""
        
        profile_summary = f"""
PERFIL DEL USUARIO:
- Nombre: {user_profile.get('name', 'Usuario')}
- Tema de interés: {user_profile.get('topic')}
- Nivel de conocimiento: {user_profile.get('knowledge_level')}
- Situación actual: {user_profile.get('current_situation', 'No especificada')}
- Objetivos: {user_profile.get('goals', 'No especificados')}
- Áreas de interés: {', '.join(user_profile.get('interests', [])) if user_profile.get('interests') else 'No especificadas'}
"""

        num_recommendations = user_profile.get('num_recommendations', 5)

        prompt = f"""Eres un mentor sabio y empático especializado en {user_profile.get('topic')}.

{profile_summary}

CONTENIDO DEL LIBRO "{source_file}":
{context}

INSTRUCCIONES:
Basándote en el CONTENIDO DEL LIBRO y el PERFIL DEL USUARIO, genera {num_recommendations} recomendaciones/consejos PERSONALIZADOS que:

1. Sean relevantes a la situación y objetivos del usuario
2. Estén fundamentados en el contenido del libro
3. Sean prácticos y accionables
4. Se adapten al nivel de conocimiento del usuario ({user_profile.get('knowledge_level')})
5. Incluyan referencias al libro cuando sea apropiado

FORMATO DE RESPUESTA (JSON):
{{
  "recommendations": [
    {{
      "title": "Título breve del consejo",
      "content": "Explicación detallada del consejo, cómo aplicarlo, y por qué es relevante",
      "source_reference": "Cita o referencia del libro que respalda este consejo",
      "difficulty": "fácil|intermedio|difícil de aplicar"
    }}
  ]
}}

IMPORTANTE:
- Usa un tono cálido y motivador
- Sé específico, no genérico
- Conecta el contenido del libro con la vida del usuario
- RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL
"""
        return prompt

    def _generate_without_context(self, user_profile: Dict) -> str:
        """Fallback si no hay contexto del libro"""
        prompt = f"""No se encontró contenido relevante en la base de conocimiento sobre {user_profile.get('topic')}.

Genera {user_profile.get('num_recommendations', 5)} consejos generales para alguien con nivel {user_profile.get('knowledge_level')} en este tema.

Formato JSON:
{{
  "recommendations": [
    {{
      "title": "...",
      "content": "...",
      "source_reference": "Consejo general",
      "difficulty": "fácil|intermedio|difícil"
    }}
  ]
}}
"""
        resp = self.llm.invoke(prompt)
        return resp.content


# Singleton global
llm_pipe = LlmPipe()