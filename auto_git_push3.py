import os
import subprocess
import schedule
import time
from datetime import datetime

# --- Configuración y Constantes ---
COUNT_FILE = "git_commit_count.txt"

# ESTÁNDAR: Usaremos 'main' como la rama moderna por defecto.
# El script ahora forzará a que tu rama local se llame así para evitar errores.
BRANCH_NAME = "main"

GITHUB_USER_BASE_URL = "https://github.com/ariascsdocs/"

# --------------------------------------------------------------------------

def get_current_commit_count():
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def update_commit_count(count):
    with open(COUNT_FILE, 'w') as f:
        f.write(str(count))

def run_git_command(command_parts):
    try:
        # Se usa encoding='utf-8' para manejar tildes y caracteres especiales
        result = subprocess.run(
            command_parts,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8' 
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar: {' '.join(command_parts)}")
        print(f"   Detalle: {e.stderr.strip()}")
        return None
    except Exception as e:
        print(f"🛑 Error inesperado: {e}")
        return None

def check_and_initialize_repo(repo_path):
    repo_name = os.path.basename(repo_path)
    full_remote_url = f"{GITHUB_USER_BASE_URL}{repo_name}.git"
    
    # 1. Inicializar si no existe .git
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        print("⚙️ Inicializando repositorio Git...")
        run_git_command(["git", "init"])
        
    # 2. Configurar remoto
    remotes_output = run_git_command(["git", "remote", "-v"])
    
    if not remotes_output or full_remote_url not in remotes_output:
        print(f"\n⚙️ Configurando remoto a: {full_remote_url}")
        if remotes_output and "origin" in remotes_output:
            run_git_command(["git", "remote", "remove", "origin"])
        run_git_command(["git", "remote", "add", "origin", full_remote_url])

def auto_push_changes():
    current_count = get_current_commit_count()
    new_count = current_count + 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Actualización: {new_count} - {timestamp}"
    
    print(f"\n--- 🔄 Ejecutando Tarea de Git ({timestamp}) ---")

    # 1. Add
    print("1. Añadiendo cambios...")
    run_git_command(["git", "add", "."])
    
    # 2. Commit
    print("2. Realizando commit...")
    try:
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # Si no hay cambios, salimos
        if "nothing to commit" in commit_result.stdout:
            print("✅ No hay cambios nuevos. Esperando al siguiente ciclo.")
            return

    except Exception as e:
        print(f"🛑 Error en commit: {e}")
        return

    # --- CORRECCIÓN CLAVE: Estandarización de Rama ---
    # Esto renombra la rama actual (sea master u otra) a 'main'
    # para asegurar que coincida con BRANCH_NAME.
    print(f"   -> Asegurando que la rama se llame '{BRANCH_NAME}'...")
    run_git_command(["git", "branch", "-M", BRANCH_NAME])
    # -------------------------------------------------

    # 3. Push
    print(f"3. Subiendo a GitHub ({BRANCH_NAME})...")
    push_result = run_git_command(["git", "push", "-u", "origin", BRANCH_NAME])
    
    if push_result is not None:
        print("🎉 ¡Push exitoso!")
        update_commit_count(new_count)
    else:
        print("⚠️ Push fallido.")

def main():
    repo_path = os.path.abspath(os.path.dirname(__file__))
    os.chdir(repo_path)
    repo_name = os.path.basename(repo_path)
    
    print("===============================================")
    print("🚀 Auto Git Push - CORREGIDO")
    print(f"Repo: {repo_name} | Rama objetivo: {BRANCH_NAME}")
    print("===============================================")

    check_and_initialize_repo(repo_path)
    
    # Ejecución inmediata
    auto_push_changes()
    
    # Programación cada 25 min
    print("\n⏳ Script en espera. Próxima ejecución en 25 minutos.")
    schedule.every(25).minutes.do(auto_push_changes)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()