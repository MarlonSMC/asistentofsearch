import os
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from dotenv import load_dotenv


# Creamos un "sub-router" para autenticación
router = APIRouter()

# --- CONFIGURACIÓN DE GOOGLE ---
# Carga variables de entorno (asegúrate de tener .env o vars de sistema)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth()
# --- DEBUG TEMPORAL (Borrar en producción) ---
load_dotenv()
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

print(f"DEBUG: Client ID RAW: {repr(client_id)}")
if not client_id:
    print("!!! ERROR CRÍTICO: GOOGLE_CLIENT_ID está vacío o es None !!!")

print(f"DEBUG: Client Secret leído: {'OK (Oculto)' if client_secret else '!!! VACÍO !!!'}")
# ---------------------------------------------
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- LISTA BLANCA DE ACCESO ---
AUTHORIZED_USERS = {
    "marlon951215@gmail.com": "admin",
    "parsecelectronica@gmail.com": "admin",
    "invitado@ejemplo.com": "viewer"
}

# --- RUTAS DE AUTH ---

@router.get("/login")
async def login(request: Request):
    # Construye la URL de callback dinámicamente
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if user_info:
            email = user_info.get('email')
            
            # Verificación estricta de lista blanca
            if email in AUTHORIZED_USERS:
                # Guardamos usuario y rol en la cookie de sesión cifrada
                request.session['user'] = dict(user_info)
                request.session['role'] = AUTHORIZED_USERS[email]
                return RedirectResponse(url='/')
            else:
                return HTMLResponse(
                    content=f"<h1>Acceso Denegado 403</h1><p>El usuario {email} no tiene permisos.</p>", 
                    status_code=403
                )
    except Exception as e:
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