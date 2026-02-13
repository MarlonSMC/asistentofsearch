import os
from dotenv import load_dotenv

def test_environment():
    print("--- INICIO DEL DIAGNÓSTICO ---")
    
    # 1. Verificar dónde estamos parados (Current Working Directory)
    cwd = os.getcwd()
    print(f"📂 Directorio de trabajo actual: {cwd}")

    # 2. Verificar si el archivo .env existe físicamente
    env_path = os.path.join(cwd, '.env')
    if os.path.exists(env_path):
        print("✅ Archivo .env ENCONTRADO.")
    else:
        print("❌ Archivo .env NO ENCONTRADO en esta ruta.")
        print("   -> Asegúrate de ejecutar este script desde la raíz del proyecto.")
        return

    # 3. Cargar las variables
    print("🔄 Cargando variables de entorno...")
    load_dotenv() 

    # 4. Intentar leer las credenciales
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    # 5. Validar resultados
    print("\n--- RESULTADOS ---")
    
    if client_id:
        print(f"✅ GOOGLE_CLIENT_ID: Leído correctamente.")
        print(f"   Valor: {client_id[:15]}... (truncado por seguridad)")
    else:
        print("❌ GOOGLE_CLIENT_ID: Es None o está vacío.")

    if client_secret:
        print(f"✅ GOOGLE_CLIENT_SECRET: Leído correctamente.")
        print(f"   Longitud: {len(client_secret)} caracteres.")
    else:
        print("❌ GOOGLE_CLIENT_SECRET: Es None o está vacío.")

    print("----------------------")

if __name__ == "__main__":
    test_environment()