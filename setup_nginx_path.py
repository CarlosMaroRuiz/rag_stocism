"""
Script para configurar Nginx para servir FastAPI bajo web.estoico.app/ia
"""

import paramiko
import sys

# Configuración
SSH_HOST = "72.62.129.33"
SSH_USER = "root"
SSH_PASSWORD = "P-0arKMI6m?4fXQViwnU"
DEPLOY_PATH = "/root/apps/rag_stocism"
SERVICE_NAME = "mentor-estoico"
SERVICE_PORT = 8001
LARAVEL_NGINX_SITE = "web.estoico.app"  # Nombre del archivo de configuración de Laravel


def execute_ssh(client, command):
    """Ejecutar comando SSH y mostrar resultado"""
    print(f">> Ejecutando: {command[:80]}...")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()

    if output:
        print(f"   {output}")
    if error and exit_status != 0:
        print(f"   ERROR: {error}")
        return False, output

    return True, output


def setup_nginx_location():
    """Agregar location /ia a la configuración de Nginx de Laravel"""
    print("="*70)
    print("CONFIGURANDO NGINX PARA /ia")
    print("="*70)

    print(f"\nConectando a {SSH_USER}@{SSH_HOST}...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=SSH_HOST,
            port=22,
            username=SSH_USER,
            password=SSH_PASSWORD,
            timeout=10
        )

        print("OK Conexion SSH establecida\n")

        # 1. Buscar el archivo de configuración de Nginx para web.estoico.app
        print("1. Buscando configuracion de Nginx para web.estoico.app...")

        # Buscar en sites-available
        cmd = "ls /etc/nginx/sites-available/ | grep -E 'estoico|web' || echo 'NO_ENCONTRADO'"
        success, output = execute_ssh(client, cmd)

        if "NO_ENCONTRADO" in output:
            print("   ERROR: No se encontro configuracion de web.estoico.app")
            print("   Por favor indica el nombre del archivo de configuracion")
            return False

        nginx_files = output.split('\n')
        print(f"   Archivos encontrados: {nginx_files}")

        # Usar el primero que contenga estoico o web
        nginx_config_file = None
        for f in nginx_files:
            if 'estoico' in f or 'web' in f:
                nginx_config_file = f
                break

        if not nginx_config_file:
            nginx_config_file = nginx_files[0]

        print(f"   Usando archivo: {nginx_config_file}")

        # 2. Leer la configuración actual
        print("\n2. Leyendo configuracion actual...")
        cmd = f"cat /etc/nginx/sites-available/{nginx_config_file}"
        success, config_content = execute_ssh(client, cmd)

        # 3. Verificar si ya existe la location /ia
        if "location /ia" in config_content:
            print("   La location /ia ya existe, actualizando...")

        # 4. Crear backup
        print("\n3. Creando backup de configuracion...")
        execute_ssh(client, f"sudo cp /etc/nginx/sites-available/{nginx_config_file} /etc/nginx/sites-available/{nginx_config_file}.backup")

        # 5. Agregar/actualizar location /ia
        print("\n4. Agregando location /ia para FastAPI...")

        # Bloque de configuración para agregar
        fastapi_location = f"""
    # FastAPI - Mentor Estoico (bajo /ia)
    location /ia {{
        proxy_pass http://127.0.0.1:{SERVICE_PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /ia;

        # SSE/Streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }}
"""

        # Crear script para agregar la location
        script = f"""#!/bin/bash
CONFIG_FILE="/etc/nginx/sites-available/{nginx_config_file}"

# Verificar si existe el bloque HTTPS (443)
if grep -q "listen 443" "$CONFIG_FILE"; then
    # Buscar el bloque server que escucha en 443
    # Agregar la location antes del último cierre de llaves del server block 443

    # Primero eliminar location /ia existente si existe
    sed -i '/# FastAPI - Mentor Estoico (bajo \\/ia)/,/^    \\}}/d' "$CONFIG_FILE"

    # Agregar la nueva location antes del último }} del bloque 443
    awk '
        /listen 443/ {{in_https=1}}
        in_https && /^\\}}/ && !done {{
            print "{fastapi_location.replace('$', '$$')}"
            done=1
        }}
        {{print}}
    ' "$CONFIG_FILE" > "$CONFIG_FILE.tmp"

    mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

    echo "Location /ia agregada al bloque HTTPS"
else
    echo "No se encontro bloque HTTPS en la configuracion"
    exit 1
fi
"""

        # Guardar script en el servidor
        script_path = "/tmp/add_ia_location.sh"
        cmd = f"cat > {script_path} << 'EOFSCRIPT'\n{script}\nEOFSCRIPT"
        execute_ssh(client, cmd)
        execute_ssh(client, f"chmod +x {script_path}")

        # Ejecutar script
        execute_ssh(client, f"bash {script_path}")

        # 6. Verificar configuración de Nginx
        print("\n5. Verificando configuracion de Nginx...")
        success, output = execute_ssh(client, "sudo nginx -t")

        if not success:
            print("   ERROR: Configuracion de Nginx invalida, restaurando backup...")
            execute_ssh(client, f"sudo cp /etc/nginx/sites-available/{nginx_config_file}.backup /etc/nginx/sites-available/{nginx_config_file}")
            return False

        # 7. Recargar Nginx
        print("\n6. Recargando Nginx...")
        execute_ssh(client, "sudo systemctl reload nginx")

        print("\n" + "="*70)
        print("OK CONFIGURACION COMPLETADA")
        print("="*70)

        print(f"\nTu API FastAPI ahora esta disponible en:")
        print(f"   https://web.estoico.app/ia")
        print(f"   https://web.estoico.app/ia/health")
        print(f"   https://web.estoico.app/ia/docs (si APP_ENV=dev)")

        print(f"\nLaravel sigue funcionando normal en:")
        print(f"   https://web.estoico.app/")

        client.close()
        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    try:
        success = setup_nginx_location()

        if success:
            print("\n" + "="*70)
            print("SIGUIENTE PASO: Actualizar codigo en el servidor")
            print("="*70)
            print("\nEjecuta: python update_server.py")
            print("Esto hara git pull del codigo actualizado con root_path='/ia'")

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperacion cancelada")
        sys.exit(1)
