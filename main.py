import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

# Importamos nuestro nuevo módulo de autenticación
from auth import router as auth_router, get_current_user

# Importamos las tiendas (tus scrapers)
import arcaelectronica, electronilab, electrosena, jabots, mactronica, plugandplay, sigma, vistronica, zamux

app = FastAPI()

# 1. MIDDLEWARE DE SESIÓN (Crítico para que funcione auth.py)
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET", "clave-super-secreta-cambiar-en-prod"),
    max_age=604800 # 7 días de persistencia
)

# 2. INCLUIR RUTAS DE AUTH
app.include_router(auth_router)

templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    message: str

# --- RUTAS PRINCIPALES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    
    # Protección: Si no hay usuario, mandar al login de Google
    if not user:
        return RedirectResponse(url='/login')
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": user,
        "role": request.session.get('role')
    })

@app.post("/api/chat")
async def chat(data: ChatRequest, request: Request):
    # Protección de API: Bloquear acceso si no hay sesión
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión expirada o inválida")

    query = data.message
    
    # 1. Ejecutar búsquedas (Ahora son 3 tiendas)
    try:
        productos_vistronica = await vistronica.buscar_productos(query, limite=10)
    except:
        productos_vistronica = []

    try:
        productos_electronilab = electronilab.buscar_productos(query, limite=10)
    except:
        productos_electronilab = []

    try:
        # --- NUEVA TIENDA ---
        productos_zamux = zamux.buscar_productos(query, limite=10)
    except:
        productos_zamux = []

    try:
        productos_sigma = await sigma.buscar_productos(query, limite=10)
        print(f"Sigma: Encontrados {len(productos_sigma)} productos para '{query}'")
    except Exception as e:
        print(f"Error Sigma: {e}")
        productos_sigma = []

    try:
        productos_mactronica = mactronica.buscar_productos(query, limite=10)
        print(f"Mactronica: Encontrados {len(productos_mactronica)} productos para '{query}'")
    except Exception as e:
        print(f"Error Mactronica: {e}")
        productos_mactronica = []

    try:
        productos_arcaelectronica = arcaelectronica.buscar_productos(query, limite=10)
        print(f"Arca Electrónica: Encontrados {len(productos_arcaelectronica)} productos para '{query}'")
    except Exception as e:
        print(f"Error Arca Electrónica: {e}")
        productos_arcaelectronica = []
    
    try:
        productos_plugandplay = plugandplay.buscar_productos(query, limite=10)
        print(f"Electrónica Plug and Play: Encontrados {len(productos_plugandplay)} productos para '{query}'")
    except Exception as e:
        print(f"Error Electrónica Plug and Play: {e}")
        productos_plugandplay = []
    
    try:
        productos_electrosena = electrosena.buscar_productos(query, limite=10)
        print(f"Electrónica Plug and Play: Encontrados {len(productos_electrosena)} productos para '{query}'")
    except Exception as e:
        print(f"Error Electrónica Plug and Play: {e}")
        productos_electrosena = []
    
    try:
        productos_jabots = jabots.buscar_productos(query, limite=10)
        print(f"Ja-Bots: Encontrados {len(productos_jabots)} productos para '{query}'")
    except Exception as e:
        print(f"Error Ja-Bots: {e}")
        productos_jabots = []
        
    # Agrupar resultados
    resultados_agrupados = {
        "Vistronica": productos_vistronica,
        "Electronilab": productos_electronilab,
        "Zamux": productos_zamux,
        "Sigma": productos_sigma,
        "Mactronica": productos_mactronica,
        "Arca Electrónica": productos_arcaelectronica,
        "Electrónica Plug and Play": productos_plugandplay,
        "Electrosena": productos_electrosena,
        "Ja-Bots": productos_jabots
    }

    # 3. Mensaje resumen
    count_vistronica = len(productos_vistronica)
    count_electronilab = len(productos_electronilab)
    count_zamux = len(productos_zamux)
    count_sigma = len(productos_sigma)
    count_magtronica = len(productos_mactronica)
    count_arcaelectronica = len(productos_arcaelectronica)
    count_plugandplay = len(productos_plugandplay)
    count_electrosena = len(productos_electrosena)
    count_jabots = len(productos_jabots)
    
    total = count_vistronica + count_electronilab + count_zamux + count_sigma + count_magtronica + count_arcaelectronica + count_plugandplay + count_electrosena + count_jabots
    
    if total > 0:
        reply = f"Encontré {total} resultados: {count_vistronica} en Vistronica, {count_electronilab} en Electronilab, {count_zamux} en Zamux, {count_sigma} en Sigma, {count_magtronica} en Mactronica, {count_arcaelectronica} en Arca Electrónica, {count_plugandplay} en Electrónica Plug and Play y {count_electrosena} en Electrosena y {count_jabots} en Ja-Bots."
    else:
        reply = f"No encontré nada relacionado con '{query}' en las tiendas."

    return {
        "reply": reply,
        "results": resultados_agrupados
    }

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host='0.0.0.0', port=port)