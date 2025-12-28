"""
Script para deshabilitar configuración antigua de Nginx (subdominio)
"""

import paramiko
import sys

# Configuración
SSH_HOST = "72.62.129.33"
SSH_USER = "root"
SSH_PASSWORD = "P-0arKMI6m?4fXQViwnU"


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
        return False

    return True


def disable_old_config():
    """Deshabilitar configuración antigua de mentor-estoico"""
    print("="*70)
    print("DESHABILITANDO CONFIGURACION ANTIGUA")
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

        # Deshabilitar el sitio mentor-estoico
        print("Deshabilitando sitio mentor-estoico...")
        execute_ssh(client, "sudo rm -f /etc/nginx/sites-enabled/mentor-estoico")

        # Verificar configuración
        print("\nVerificando configuracion de Nginx...")
        if execute_ssh(client, "sudo nginx -t"):
            print("\nRecargando Nginx...")
            execute_ssh(client, "sudo systemctl reload nginx")
            print("\nOK Configuracion antigua deshabilitada")
        else:
            print("\nERROR: Problemas con configuracion de Nginx")
            return False

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
        success = disable_old_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperacion cancelada")
        sys.exit(1)
