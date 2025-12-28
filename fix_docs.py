"""
Script para actualizar APP_ENV en el servidor y ocultar documentación
"""

import paramiko
import sys

# Configuración
SSH_HOST = "72.62.129.33"
SSH_USER = "root"
SSH_PASSWORD = "P-0arKMI6m?4fXQViwnU"
DEPLOY_PATH = "/root/apps/rag_stocism"
SERVICE_NAME = "mentor-estoico"


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


def fix_docs():
    """Actualizar APP_ENV y reiniciar servicio"""
    print("="*70)
    print("ACTUALIZANDO CONFIGURACION")
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

        # 1. Verificar valor actual de APP_ENV
        print("Verificando configuracion actual...")
        success, output = execute_ssh(client, f"grep APP_ENV {DEPLOY_PATH}/.env || echo 'NO_EXISTE'")

        # 2. Actualizar APP_ENV a production
        print("\nActualizando APP_ENV a production...")
        execute_ssh(client, f"sed -i 's/^APP_ENV=.*/APP_ENV=production/' {DEPLOY_PATH}/.env")

        # 3. Verificar el cambio
        print("\nVerificando cambio...")
        execute_ssh(client, f"grep APP_ENV {DEPLOY_PATH}/.env")

        # 4. Reiniciar servicio
        print("\nReiniciando servicio...")
        execute_ssh(client, f"sudo systemctl restart {SERVICE_NAME}")

        # Esperar un momento
        import time
        time.sleep(2)

        # 5. Verificar estado
        print("\nVerificando estado del servicio...")
        execute_ssh(client, f"sudo systemctl status {SERVICE_NAME} --no-pager -l | head -15")

        print("\n" + "="*70)
        print("OK CONFIGURACION ACTUALIZADA")
        print("="*70)

        print(f"\nVerifica que la documentacion este oculta:")
        print(f"   http://{SSH_HOST}:8001/docs (deberia dar 404)")
        print(f"   http://{SSH_HOST}:8001/redoc (deberia dar 404)")
        print(f"   http://{SSH_HOST}:8001/health (deberia funcionar)")

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
        success = fix_docs()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperacion cancelada")
        sys.exit(1)
