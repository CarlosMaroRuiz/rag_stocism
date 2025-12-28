"""
Script para actualizar el código en el servidor sin deployment completo
Ejecuta git pull y reinicia el servicio
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
    print(f"⚙️  Ejecutando: {command[:80]}...")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()

    if output:
        print(f"   {output}")
    if error and exit_status != 0:
        print(f"   ❌ Error: {error}")
        return False

    return True


def update_server():
    """Actualizar código en el servidor"""
    print("="*70)
    print("🔄 ACTUALIZACIÓN DEL SERVIDOR")
    print("="*70)

    print(f"\n🔌 Conectando a {SSH_USER}@{SSH_HOST}...")

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

        print("✅ Conexión SSH establecida\n")

        # 1. Git pull
        print("📥 Actualizando código desde GitHub...")
        if not execute_ssh(client, f"cd {DEPLOY_PATH} && git fetch origin"):
            return False

        if not execute_ssh(client, f"cd {DEPLOY_PATH} && git reset --hard origin/main"):
            return False

        if not execute_ssh(client, f"cd {DEPLOY_PATH} && git pull origin main"):
            return False

        print("\n✅ Código actualizado")

        # 2. Reinstalar dependencias (solo si requirements.txt cambió)
        print("\n📦 Verificando dependencias...")
        execute_ssh(client, f"{DEPLOY_PATH}/venv/bin/pip install -r {DEPLOY_PATH}/requirements.txt --quiet")

        # 3. Reiniciar servicio
        print("\n🔄 Reiniciando servicio...")
        if not execute_ssh(client, f"sudo systemctl restart {SERVICE_NAME}"):
            return False

        # Esperar un momento
        import time
        time.sleep(2)

        # 4. Verificar estado
        print("\n📊 Verificando estado del servicio...")
        execute_ssh(client, f"sudo systemctl status {SERVICE_NAME} --no-pager -l | head -20")

        print("\n" + "="*70)
        print("✅ ACTUALIZACIÓN COMPLETADA")
        print("="*70)

        print(f"\n🔗 API actualizada en: http://{SSH_HOST}:8001")
        print(f"🔗 Health check: http://{SSH_HOST}:8001/health")

        print("\n📝 Para ver logs en tiempo real:")
        print(f"   sudo journalctl -u {SERVICE_NAME} -f")

        client.close()
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    try:
        success = update_server()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Actualización cancelada")
        sys.exit(1)
