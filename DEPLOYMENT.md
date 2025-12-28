# 🚀 Guía de Deployment - Mentor Estoico Digital

Esta guía explica cómo desplegar el proyecto FastAPI en un servidor remoto usando el script de deployment automatizado.

## 📋 Pre-requisitos

### En tu máquina local:
1. Python 3.8+ instalado
2. Biblioteca Paramiko:
   ```bash
   pip install paramiko
   ```

### En el servidor remoto:
1. Sistema operativo: Ubuntu 20.04+ (o Debian)
2. Acceso SSH con llave privada (.pem o id_rsa)
3. Usuario con permisos sudo
4. Puertos abiertos:
   - 8000 (FastAPI)
   - 80 (NGINX - opcional)
   - 443 (HTTPS - opcional)

### Servicios requeridos en el servidor:
- MySQL 8.0+
- MinIO (almacenamiento S3-compatible)
- ChromaDB (base de datos vectorial)

## ⚙️ Configuración del Script

### 1. Editar `deploy.py`

Abre el archivo `deploy.py` y modifica la clase `DeployConfig`:

```python
class DeployConfig:
    # 🔧 Configuración del servidor SSH
    SSH_HOST = "52.45.123.456"  # IP o dominio de tu servidor
    SSH_PORT = 22
    SSH_USER = "ubuntu"  # Usuario SSH
    SSH_KEY_PATH = "/ruta/a/tu/llave.pem"  # Ruta a tu llave SSH

    # 🔧 Configuración del proyecto
    GITHUB_REPO = "https://github.com/CarlosMaroRuiz/rag_stocism.git"
    BRANCH = "main"

    # 🔧 Variables de entorno
    ENV_VARS = {
        "DEEPSEEK_API_KEY": "sk-abc123...",
        "JWT_SECRET": "tu-secret-jwt-muy-seguro",
        "MYSQL_HOST": "localhost",
        "MYSQL_USER": "mentor_user",
        "MYSQL_PASSWORD": "password_seguro",
        "MYSQL_DATABASE": "mentor_estoico",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin123",
        # ... más variables
    }
```

### 2. Permisos de la llave SSH

```bash
chmod 400 /ruta/a/tu/llave.pem
```

## 🚀 Ejecutar Deployment

### Deployment automático completo:

```bash
python deploy.py
```

El script realizará automáticamente:
1. ✅ Instalación de dependencias del sistema
2. ✅ Clonado del repositorio desde GitHub
3. ✅ Configuración del entorno virtual de Python
4. ✅ Instalación de dependencias Python
5. ✅ Creación del archivo `.env`
6. ✅ Configuración del servicio systemd
7. ✅ Inicio del servicio como demonio
8. ✅ (Opcional) Configuración de NGINX reverse proxy

## 📊 Gestión del Servicio

Una vez desplegado, puedes gestionar el servicio con systemd:

### Ver estado del servicio:
```bash
sudo systemctl status mentor-estoico
```

### Ver logs en tiempo real:
```bash
sudo journalctl -u mentor-estoico -f
```

### Ver logs de archivo:
```bash
tail -f /var/log/mentor-estoico.log
tail -f /var/log/mentor-estoico.error.log
```

### Reiniciar el servicio:
```bash
sudo systemctl restart mentor-estoico
```

### Detener el servicio:
```bash
sudo systemctl stop mentor-estoico
```

### Iniciar el servicio:
```bash
sudo systemctl start mentor-estoico
```

### Deshabilitar inicio automático:
```bash
sudo systemctl disable mentor-estoico
```

## 🔄 Actualizar el Código

Para actualizar el código desplegado sin rehacer todo el deployment:

```bash
# Conectarse al servidor
ssh -i /ruta/a/tu/llave.pem ubuntu@tu-servidor.com

# Navegar al directorio del proyecto
cd /home/ubuntu/apps/rag_stocism

# Pull de los cambios
git pull origin main

# Reinstalar dependencias si es necesario
/home/ubuntu/apps/rag_stocism/venv/bin/pip install -r requirements.txt

# Reiniciar el servicio
sudo systemctl restart mentor-estoico
```

## 🌐 Configuración de NGINX (Reverse Proxy)

Si configuraste NGINX durante el deployment, el servicio estará accesible en el puerto 80:

```nginx
# Archivo: /etc/nginx/sites-available/mentor-estoico

server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Soporte para SSE/Streaming
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### Configurar HTTPS con Let's Encrypt:

```bash
# Instalar Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com

# Renovación automática (ya configurada por certbot)
sudo certbot renew --dry-run
```

## 🔧 Troubleshooting

### El servicio no inicia:

1. **Verificar logs:**
   ```bash
   sudo journalctl -u mentor-estoico -n 50 --no-pager
   ```

2. **Verificar configuración de systemd:**
   ```bash
   sudo systemctl cat mentor-estoico
   ```

3. **Probar ejecución manual:**
   ```bash
   cd /home/ubuntu/apps/rag_stocism
   source venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### Errores de conexión a MySQL:

```bash
# Verificar que MySQL esté corriendo
sudo systemctl status mysql

# Probar conexión
mysql -u mentor_user -p -h localhost mentor_estoico
```

### Errores de MinIO:

```bash
# Verificar que MinIO esté corriendo
sudo systemctl status minio

# Probar acceso a la consola
curl http://localhost:9000/minio/health/live
```

### Puerto 8000 ya en uso:

```bash
# Encontrar proceso usando el puerto
sudo lsof -i :8000

# Matar proceso
sudo kill -9 <PID>
```

## 📁 Estructura de Archivos en el Servidor

```
/home/ubuntu/apps/rag_stocism/
├── .env                    # Variables de entorno
├── .git/                   # Repositorio git
├── venv/                   # Entorno virtual Python
├── main.py                 # Aplicación FastAPI
├── requirements.txt        # Dependencias Python
├── core/                   # Módulos core
├── routes/                 # Rutas de la API
├── schemas/                # Schemas Pydantic
└── ...

/etc/systemd/system/
└── mentor-estoico.service  # Archivo de servicio systemd

/var/log/
├── mentor-estoico.log      # Logs de la aplicación
└── mentor-estoico.error.log # Logs de errores
```

## 🔐 Seguridad

### Recomendaciones:

1. **Firewall (UFW):**
   ```bash
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

2. **Cambiar puerto SSH por defecto:**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Port 2222
   sudo systemctl restart sshd
   ```

3. **Deshabilitar autenticación por contraseña:**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # PasswordAuthentication no
   sudo systemctl restart sshd
   ```

4. **Mantener sistema actualizado:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

## 📞 Soporte

Para problemas o dudas:
- Revisar logs del servicio
- Verificar configuración de variables de entorno
- Comprobar conectividad con MySQL, MinIO y ChromaDB

## 📝 Notas

- El servicio se reinicia automáticamente si falla
- Los logs se rotan automáticamente por systemd
- El servicio inicia automáticamente al reiniciar el servidor
- Se ejecutan 4 workers de Uvicorn para mejor rendimiento
