import os
import subprocess
import schedule
import time
from datetime import datetime

# --- Configuración y Constantes ---
# Nombre del archivo para almacenar el contador y asegurar la persistencia.
COUNT_FILE = "git_commit_count.txt"

# Nombre de la rama principal. (Comprueba si tu repositorio usa 'main' o 'master')
BRANCH_NAME = "master"

# URL BASE de tu GitHub. El script infiere el nombre del repositorio de la carpeta local.
# Si el nombre de tu carpeta es 'MiProyecto', la URL final será: 
# https://github.com/ariascsdocs/MiProyecto.git
GITHUB_USER_BASE_URL = "https://github.com/ariascsdocs/"

# --------------------------------------------------------------------------

def get_current_commit_count():
    """Lee el contador de commit del archivo o retorna 0 si no existe."""
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, 'r') as f:
            try:
                # Lee el valor, lo limpia y lo convierte a entero
                return int(f.read().strip())
            except ValueError:
                # Retorna 0 si el archivo existe pero tiene un valor inválido
                return 0
    return 0

def update_commit_count(count):
    """Escribe el nuevo valor del contador en el archivo."""
    with open(COUNT_FILE, 'w') as f:
        f.write(str(count))

def run_git_command(command_parts):
    """Ejecuta un comando Git y maneja los errores."""
    try:
        # Ejecuta el comando de Git. check=True lanza excepción si el comando falla.
        result = subprocess.run(
            command_parts,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8' # Asegura una correcta codificación
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar el comando Git: {' '.join(command_parts)}")
        print(f"   Salida de error: {e.stderr.strip()}")
        # Notificación específica para errores de autenticación/red
        if "push" in command_parts:
             print("💡 Sugerencia de Push Fallido: Revisa tu conexión a internet o tu **autenticación de GitHub** (Token de Acceso Personal/Credenciales).")
        return None
    except FileNotFoundError:
        print("🛑 Error: El comando 'git' no se encuentra. Asegúrate de que Git esté instalado y en tu PATH.")
        return None
    except Exception as e:
        print(f"🛑 Ocurrió un error inesperado: {e}")
        return None

def check_and_initialize_repo(repo_path):
    """
    Inicializa el repositorio si no existe y configura la URL remota.
    """
    repo_name = os.path.basename(repo_path)
    full_remote_url = f"{GITHUB_USER_BASE_URL}{repo_name}.git"
    
    # 1. Inicializar si no es un repo Git
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        print("⚙️ Inicializando repositorio Git (git init)...")
        run_git_command(["git", "init"])
        
    # 2. Configurar el remoto 'origin'
    remotes_output = run_git_command(["git", "remote", "-v"])
    
    # Si 'origin' no está en la lista de remotos O si la URL no coincide
    if not remotes_output or full_remote_url not in remotes_output:
        print("\n⚙️ Verificando y configurando el remoto 'origin'...")
        
        # Eliminar remoto existente si tiene un nombre diferente al esperado
        if remotes_output and "origin" in remotes_output:
            print("   Se encontró un remoto 'origin' diferente. Removiendo...")
            run_git_command(["git", "remote", "remove", "origin"])
        
        print(f"   Configurando remoto con URL: **{full_remote_url}**")
        run_git_command(["git", "remote", "add", "origin", full_remote_url])
        print("   Remoto 'origin' configurado.")


def auto_push_changes():
    """
    La función principal que añade, commitea e intenta subir los cambios.
    """
    current_count = get_current_commit_count()
    new_count = current_count + 1
    
    # 1. Preparar mensaje y hora
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Actualización: {new_count} - {timestamp}"
    
    print(f"\n--- 🔄 Ejecutando Tarea de Git ({timestamp}) ---")

    # 2. Agregar todos los archivos
    print("1. Añadiendo todos los cambios (git add .)...")
    run_git_command(["git", "add", "."])
    
    # 3. Commit
    print("2. Realizando commit...")
    # Usamos subprocess.run directamente aquí para verificar si hay cambios
    try:
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=False, # No lanza excepción si el commit falla (ej. no hay cambios)
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # Verifica si el commit realmente hizo algo
        if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
            print("✅ No hay cambios nuevos que commitear. Saltando el push.")
            return
            
    except Exception as e:
        print(f"🛑 Ocurrió un error en el commit: {e}")
        return None

    # 4. Push
    print(f"3. Subiendo a GitHub (git push origin {BRANCH_NAME})...")
    push_result = run_git_command(["git", "push", "origin", BRANCH_NAME])
    
    if push_result is not None:
        print("🎉 ¡Push exitoso!")
        # 5. Si el push fue exitoso, actualizamos el contador.
        update_commit_count(new_count)
    else:
        print(f"⚠️ Push fallido a la rama **{BRANCH_NAME}**. El contador NO se actualizó.")
        # El error ya fue reportado por run_git_command


def main():
    """Función principal para inicializar y programar el bucle."""
    
    # Obtener la ruta de la carpeta actual (donde está el script)
    # y cambiar el directorio de trabajo a esta ruta
    repo_path = os.path.abspath(os.path.dirname(__file__))
    os.chdir(repo_path)
    repo_name = os.path.basename(repo_path)
    
    print("===============================================")
    print("🚀 Auto Git Push Script Iniciado")
    print(f"Directorio de Repositorio Local: **{repo_path}**")
    print(f"Nombre del Repositorio Asumido: **{repo_name}**")
    print("===============================================")

    # Fase de Inicialización
    check_and_initialize_repo(repo_path)
    
    # Fase de Programación
    print("\n⏳ Programando la ejecución de 'auto_push_changes' cada **15 minutos**.")
    schedule.every(1).minutes.do(auto_push_changes)
    
    print("✅ ¡El script está cargado en la memoria y se ejecutará automáticamente!")
    print("Presiona **Ctrl+C** para detener el script.")

    # Bucle de ejecución de tareas programadas
    while True:
        schedule.run_pending()
        time.sleep(1) # Espera 1 segundo para reducir el uso de CPU

if __name__ == "__main__":
    # Asegúrate de haber instalado la librería 'schedule': pip install schedule
    main()