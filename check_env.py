"""
Script para verificar el archivo .env en el servidor
"""

import paramiko
import sys

# Configuración
SSH_HOST = "72.62.129.33"
SSH_USER = "root"
SSH_PASSWORD = "P-0arKMI6m?4fXQViwnU"
DEPLOY_PATH = "/root/apps/rag_stocism"


def check_env():
    """Verificar configuración del servidor"""
    print("="*70)
    print("DIAGNOSTICO DE CONFIGURACION")
    print("="*70)

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

        print("\nOK Conexion SSH establecida\n")

        # 1. Verificar si .env existe
        print("1. Verificando si .env existe...")
        stdin, stdout, stderr = client.exec_command(f"ls -la {DEPLOY_PATH}/.env")
        print(stdout.read().decode('utf-8'))

        # 2. Mostrar contenido completo del .env
        print("\n2. Contenido del archivo .env:")
        print("-" * 70)
        stdin, stdout, stderr = client.exec_command(f"cat {DEPLOY_PATH}/.env")
        env_content = stdout.read().decode('utf-8')
        print(env_content)
        print("-" * 70)

        # 3. Verificar específicamente APP_ENV
        print("\n3. Verificando APP_ENV:")
        stdin, stdout, stderr = client.exec_command(f"grep APP_ENV {DEPLOY_PATH}/.env")
        app_env_line = stdout.read().decode('utf-8').strip()
        print(f"   Linea encontrada: {app_env_line}")

        # 4. Verificar versión de Python en uso
        print("\n4. Version de Python del servicio:")
        stdin, stdout, stderr = client.exec_command(f"{DEPLOY_PATH}/venv/bin/python --version")
        print(f"   {stdout.read().decode('utf-8').strip()}")

        # 5. Probar importar env desde Python
        print("\n5. Probando lectura de env.APP_ENV desde Python:")
        test_cmd = f"""cd {DEPLOY_PATH} && {DEPLOY_PATH}/venv/bin/python -c "from core.enviroment import env; print('APP_ENV =', env.APP_ENV)" """
        stdin, stdout, stderr = client.exec_command(test_cmd)
        result = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()

        if result:
            print(f"   {result}")
        if error:
            print(f"   ERROR: {error}")

        client.close()

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        check_env()
    except KeyboardInterrupt:
        print("\n\nOperacion cancelada")
        sys.exit(1)
