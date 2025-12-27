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
            # ==========================
            # PostgreSQL (RAG)
            # ==========================
            self.RAG_DB_CONN: str = os.environ["RAG_DB_CONN"]
            self.PGHOST: str = os.environ["PGHOST"]
            self.PGPORT: int = int(os.environ["PGPORT"])
            self.PGUSER: str = os.environ["PGUSER"]
            self.PGPASSWORD: str = os.environ["PGPASSWORD"]
            self.PGDATABASE: str = os.environ["PGDATABASE"]

            # ==========================
            # MySQL (Laravel)
            # ==========================
            self.MYSQL_HOST: str = os.environ["MYSQL_HOST"]
            self.MYSQL_PORT: int = int(os.environ.get("MYSQL_PORT", 3306))
            self.MYSQL_USER: str = os.environ["MYSQL_USER"]
            self.MYSQL_PASSWORD: str = os.environ["MYSQL_PASSWORD"]
            self.MYSQL_DATABASE: str = os.environ["MYSQL_DATABASE"]

            # ==========================
            # LLM / Embeddings
            # ==========================
            self.DEEPSEEK_API_KEY: str = os.environ["DEEPSEEK_API_KEY"]
            self.EMBEDDING_MODEL: str = os.environ["EMBEDDING_MODEL"]

            # ==========================
            # MinIO
            # ==========================
            self.MINIO_ENDPOINT: str = os.environ["MINIO_ENDPOINT"]
            self.MINIO_ACCESS_KEY: str = os.environ["MINIO_ACCESS_KEY"]
            self.MINIO_SECRET_KEY: str = os.environ["MINIO_SECRET_KEY"]
            self.MINIO_BUCKET: str = os.environ["MINIO_BUCKET"]
            self.MINIO_SECURE: bool = (
                os.environ.get("MINIO_SECURE", "False").lower() == "true"
            )

            # ==========================
            # App
            # ==========================
            self.APP_ENV: str = os.environ.get("APP_ENV", "dev")
            self.APP_PORT: int = int(os.environ.get("APP_PORT", 8000))

        except KeyError as e:
            raise RuntimeError(
                f"Falta la variable de entorno requerida: {e.args[0]}"
            )

env = Environment()
