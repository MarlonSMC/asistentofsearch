import os
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
from google.cloud import firestore  # <--- NUEVO IMPORT
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Creamos un "sub-router" para autenticación
router = APIRouter()

# --- CONFIGURACIÓN DE GOOGLE ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Validación rápida de credenciales en consola
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("!!! ERROR CRÍTICO: Faltan credenciales de Google en .env !!!")
else:
    print(f"DEBUG: Credenciales leídas correctamente. Client ID termina en: ...{GOOGLE_CLIENT_ID[-5:]}")

# Inicializar OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- INICIALIZAR FIRESTORE ---
# Se autentica automáticamente en Cloud Run. En local requiere 'gcloud auth application-default login'
# En auth.py, cambia la línea donde creas el cliente:
try:
    # Especificamos el ID de la base de datos que creaste
    db = firestore.Client(project="project-3b15455d-b6f3-47a3-9ca", database="asistentofsearchdb")
    print("DEBUG: Cliente de Firestore inicializado en database: asistentofsearchdb")
except Exception as e:
    print(f"ERROR: No se pudo conectar a Firestore: {e}")
    db = None

# --- RUTAS DE AUTH ---

@router.get("/login")
async def login(request: Request):
    # 1. Genera la URL base (en Cloud Run esto suele salir como http:// por el proxy)
    redirect_uri = request.url_for('auth_callback')
    
    # 2. CORRECCIÓN AUTOMÁTICA HTTPS:
    # Si NO estamos en localhost, forzamos https para que Google no rechace la petición
    redirect_str = str(redirect_uri)
    if "localhost" not in redirect_str and "127.0.0.1" not in redirect_str:
        redirect_uri = redirect_str.replace("http://", "https://")
    
    print(f"DEBUG: Redirigiendo a Google con URI: {redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if user_info:
            email = user_info.get('email')
            print(f"DEBUG: Intentando autenticar usuario: {email}")

            # --- VERIFICACIÓN EN FIRESTORE ---
            if db:
                # Buscamos el documento cuyo ID sea el correo electrónico
                doc_ref = db.collection('authorized_users').document(email)
                doc = doc_ref.get()

                if doc.exists:
                    # El usuario existe en la DB
                    datos_usuario = doc.to_dict()
                    # Obtenemos el rol de la DB, si no existe, asignamos 'viewer' por defecto
                    rol_usuario = datos_usuario.get('rol', 'viewer') 
                    
                    # Guardamos en sesión
                    request.session['user'] = dict(user_info)
                    request.session['role'] = rol_usuario
                    
                    print(f"ACCESO CONCEDIDO: {email} con rol {rol_usuario}")
                    return RedirectResponse(url='/')
                else:
                    print(f"ACCESO DENEGADO: {email} no está en la colección 'usuarios_permitidos'")
                    return HTMLResponse(
                        content=f"<h1>Acceso Denegado 403</h1><p>El usuario {email} no tiene permisos registrados en la base de datos.</p>", 
                        status_code=403
                    )
            else:
                 return HTMLResponse(content="Error interno: No hay conexión a la base de datos.", status_code=500)

    except Exception as e:
        print(f"ERROR AUTH: {str(e)}")
        return HTMLResponse(content=f"Error de autenticación: {str(e)}", status_code=400)
        
    return RedirectResponse(url='/login')

@router.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    request.session.pop('role', None)
    return RedirectResponse(url='/login')

# --- DEPENDENCIAS DE SEGURIDAD (Helpers) ---

def get_current_user(request: Request):
    """Función para usar en otras rutas y verificar sesión"""
    return request.session.get('user')

def get_current_role(request: Request):
    """Función para obtener el rol del usuario actual"""
    return request.session.get('role', 'viewer')