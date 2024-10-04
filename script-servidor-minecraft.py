import os
import subprocess
import time

def limpiar_consola():
    """Limpia la consola automáticamente."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_message(message):
    """Muestra un mensaje, espera 3 segundos y limpia la consola."""
    print(message)
    time.sleep(3)
    limpiar_consola()

def run_command(command):
    """Ejecuta un comando del sistema y maneja errores."""
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if process.returncode != 0:
            raise Exception(error.decode())
        return output.decode()
    except Exception as e:
        print(f"Error al ejecutar el comando: {command}\n{str(e)}")
        return None

def install_packages():
    """Instala paquetes esenciales para el servidor."""
    display_message("Instalando paquetes esenciales...")
    run_command("sudo apt update && sudo apt install -y curl wget tar default-jre")
    limpiar_consola()

def install_pterodactyl():
    """Instalación de Pterodactyl Panel."""
    display_message("Instalando Pterodactyl Panel...")
    run_command("bash <(curl -s https://pterodactyl-installer.se)")
    limpiar_consola()

def configure_security():
    """Configurar medidas de seguridad para mitigar ataques y escaneos."""
    display_message("Configurando medidas de seguridad...")
    
    # Configurar firewall para puertos esenciales
    run_command("sudo ufw allow 22/tcp")  # SSH
    run_command("sudo ufw allow 8080/tcp")  # Pterodactyl
    run_command("sudo ufw allow 25565/tcp")  # Minecraft
    run_command("sudo ufw default deny incoming")  # Denegar todo lo entrante por defecto
    run_command("sudo ufw default allow outgoing")  # Permitir todo lo saliente
    run_command("sudo ufw enable")  # Activar UFW (firewall)
    
    # Instalar y configurar Fail2Ban para proteger contra ataques de fuerza bruta
    run_command("sudo apt install -y fail2ban")
    run_command("sudo systemctl enable fail2ban")
    
    # Crear configuración personalizada para SSH y Minecraft
    fail2ban_config = """
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 600

[minecraft]
enabled = true
port = 25565
filter = minecraft
logpath = /var/log/minecraft.log
maxretry = 3
bantime = 3600
    """
    with open("/etc/fail2ban/jail.local", "w") as f:
        f.write(fail2ban_config)
    
    # Deshabilitar acceso root por SSH
    ssh_config = "/etc/ssh/sshd_config"
    run_command(f"sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' {ssh_config}")
    
    # Reiniciar SSH para aplicar cambios
    run_command("sudo systemctl restart ssh")

    # Habilitar autenticación con clave SSH
    run_command(f"sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' {ssh_config}")
    run_command("sudo systemctl restart ssh")

    # Habilitar actualizaciones automáticas
    run_command("sudo apt install -y unattended-upgrades")
    auto_update_config = """
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
    """
    with open("/etc/apt/apt.conf.d/20auto-upgrades", "w") as f:
        f.write(auto_update_config)

    display_message("Seguridad configurada correctamente.")
    limpiar_consola()

def choose_minecraft_server_type(api_token, node_id):
    """Permitir al usuario elegir el tipo de servidor de Minecraft y configurar el servidor en Pterodactyl."""
    server_name = input("Introduce el nombre del servidor de Minecraft: ")
    
    print("Elige el tipo de servidor de Minecraft:")
    print("1. Vanilla")
    print("2. Forge")
    print("3. Mohist")
    print("4. Spigot")

    choice = input("Introduce el número de tu elección (1/2/3/4): ")
    
    ram_allocation = input("¿Cuánta memoria RAM deseas asignar al servidor en MB (ejemplo: 2048)? ")

    # Crear el servidor en Pterodactyl
    create_pterodactyl_server(server_name, ram_allocation, choice, api_token, node_id)
    limpiar_consola()

def create_pterodactyl_server(server_name, ram_allocation, server_type, api_token, node_id):
    """Crea un servidor en Pterodactyl."""
    display_message("Creando el servidor en Pterodactyl...")
    
    api_url = "http://localhost:8080/api/application/servers"

    server_jar = {
        "1": "minecraft_server.jar",  # Vanilla
        "2": "forge-installer.jar",    # Forge
        "3": "mohist_server.jar",       # Mohist
        "4": "spigot_server.jar"        # Spigot
    }

    # Datos del servidor a crear
    data = {
        "name": server_name,
        "user": "1",  # ID del usuario
        "node": node_id,
        "allocation": "1",  # Asignación a un puerto disponible
        "nest": "1",  # ID del nido de Minecraft
        "egg": "1",  # ID del huevo de Minecraft
        "docker_image": "quay.io/pterodactyl/core:java:latest",
        "start_on_completion": True,
        "limits": {
            "memory": int(ram_allocation),
            "swap": 0,
            "disk": 1024,
            "io": 500,
            "cpu": 100
        },
        "feature_limits": {
            "databases": 1,
            "allocations": 1
        },
        "environment": {
            "JAVA_VERSION": "17",
            "SERVER_JAR": server_jar[server_type]  # Selección de jar según el tipo de servidor
        }
    }

    response = run_command(f"curl -X POST {api_url} -H 'Authorization: {api_token}' -H 'Content-Type: application/json' -d '{data}'")
    
    if response:
        display_message("Servidor creado en Pterodactyl correctamente.")
    else:
        display_message("Error al crear el servidor en Pterodactyl.")
    limpiar_consola()

def main():
    """Función principal para ejecutar el script."""
    install_packages()
    install_pterodactyl()
    configure_security()
    
    # Solicitar datos de Pterodactyl
    api_token = input("Introduce tu token de API de Pterodactyl: ")
    node_id = input("Introduce el ID del nodo donde deseas crear el servidor: ")
    
    choose_minecraft_server_type(api_token, node_id)

if __name__ == "__main__":
    main()