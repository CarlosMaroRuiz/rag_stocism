import os
from dotenv import load_dotenv

load_dotenv()

class Environment:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        try:
            # Database
            self.RAG_DB_CONN: str = os.environ["RAG_DB_CONN"]
            
            # LLM
            self.DEEPSEEK_API_KEY: str = os.environ["DEEPSEEK_API_KEY"]
            self.EMBEDDING_MODEL: str = os.environ["EMBEDDING_MODEL"]
            
            # MinIO
            self.MINIO_ENDPOINT: str = os.environ["MINIO_ENDPOINT"]
            self.MINIO_ACCESS_KEY: str = os.environ["MINIO_ACCESS_KEY"]
            self.MINIO_SECRET_KEY: str = os.environ["MINIO_SECRET_KEY"]
            self.MINIO_BUCKET: str = os.environ["MINIO_BUCKET"]
            self.MINIO_SECURE: bool = os.environ.get("MINIO_SECURE", "False").lower() == "true"
            
        except KeyError as e:
            raise RuntimeError(
                f"Falta la variable de entorno requerida: {e.args[0]}"
            )

env = Environment()