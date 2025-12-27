from minio import Minio
from minio.error import S3Error
from pathlib import Path
import io

from core.enviroment import env


class MinIOClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializa conexión con MinIO"""
        self.client = Minio(
            endpoint=env.MINIO_ENDPOINT,
            access_key=env.MINIO_ACCESS_KEY,
            secret_key=env.MINIO_SECRET_KEY,
            secure=env.MINIO_SECURE
        )
        self.bucket_name = env.MINIO_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Crea el bucket si no existe"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✓ Bucket '{self.bucket_name}' creado en MinIO")
            else:
                print(f"✓ Bucket '{self.bucket_name}' ya existe")
        except S3Error as e:
            raise RuntimeError(f"Error verificando/creando bucket: {e}")

    def upload_file(self, file_path: str, object_name: str) -> str:
        """
        Sube un archivo a MinIO
        
        Args:
            file_path: Ruta local del archivo
            object_name: Nombre del objeto en MinIO (ej: 'pdfs/libro.pdf')
        
        Returns:
            object_name: Ruta del objeto en MinIO
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=str(path),
                content_type=self._get_content_type(path)
            )
            
            print(f"✓ Archivo subido a MinIO: {object_name}")
            return object_name

        except S3Error as e:
            raise RuntimeError(f"Error subiendo a MinIO: {e}")

    def upload_file_object(self, file_data: bytes, object_name: str, content_type: str = "application/pdf") -> str:
        """
        Sube un archivo desde memoria (bytes) a MinIO
        
        Args:
            file_data: Contenido del archivo en bytes
            object_name: Nombre del objeto en MinIO
            content_type: Tipo MIME del archivo
        
        Returns:
            object_name: Ruta del objeto en MinIO
        """
        try:
            file_stream = io.BytesIO(file_data)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_stream,
                length=len(file_data),
                content_type=content_type
            )
            
            print(f"✓ Archivo subido a MinIO: {object_name}")
            return object_name

        except S3Error as e:
            raise RuntimeError(f"Error subiendo a MinIO: {e}")

    def download_file(self, object_name: str, file_path: str) -> str:
        """
        Descarga un archivo de MinIO
        
        Args:
            object_name: Nombre del objeto en MinIO
            file_path: Ruta local donde guardar el archivo
        
        Returns:
            file_path: Ruta del archivo descargado
        """
        try:
            self.client.fget_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            
            print(f"✓ Archivo descargado de MinIO: {object_name}")
            return file_path

        except S3Error as e:
            raise RuntimeError(f"Error descargando de MinIO: {e}")

    def get_file_url(self, object_name: str, expires_days: int = 7) -> str:
        """
        Genera una URL temporal para acceder al archivo
        
        Args:
            object_name: Nombre del objeto en MinIO
            expires_days: Días de validez de la URL
        
        Returns:
            URL temporal
        """
        try:
            from datetime import timedelta
            
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(days=expires_days)
            )
            return url

        except S3Error as e:
            raise RuntimeError(f"Error generando URL: {e}")

    def delete_file(self, object_name: str) -> bool:
        """
        Elimina un archivo de MinIO
        
        Args:
            object_name: Nombre del objeto en MinIO
        
        Returns:
            True si se eliminó correctamente
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            print(f"✓ Archivo eliminado de MinIO: {object_name}")
            return True

        except S3Error as e:
            raise RuntimeError(f"Error eliminando de MinIO: {e}")

    def list_files(self, prefix: str = "") -> list:
        """
        Lista archivos en MinIO
        
        Args:
            prefix: Prefijo para filtrar (ej: 'pdfs/')
        
        Returns:
            Lista de nombres de objetos
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]

        except S3Error as e:
            raise RuntimeError(f"Error listando archivos: {e}")

    def _get_content_type(self, path: Path) -> str:
        """Determina el content type basado en la extensión"""
        extension = path.suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        return content_types.get(extension, 'application/octet-stream')


# Singleton global
minio_client = MinIOClient()