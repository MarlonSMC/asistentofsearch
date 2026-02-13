import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import List, Optional
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
    stores: Optional[List[str]] = None


STORE_FUNCTIONS = {
    "Vistronica": lambda q: vistronica.buscar_productos(q, limite=10),
    "Electronilab": lambda q: electronilab.buscar_productos(q, limite=10),
    "Zamux": lambda q: zamux.buscar_productos(q, limite=10),
    "Sigma": lambda q: sigma.buscar_productos(q, limite=10),
    "Mactronica": lambda q: mactronica.buscar_productos(q, limite=10),
    "Arca Electrónica": lambda q: arcaelectronica.buscar_productos(q, limite=10),
    "Electrónica Plug and Play": lambda q: plugandplay.buscar_productos(q, limite=10),
    "Electrosena": lambda q: electrosena.buscar_productos(q, limite=10),
    "Ja-Bots": lambda q: jabots.buscar_productos(q, limite=10),
}

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
    role = request.session.get('role', 'viewer')

    if role == 'viewer':
        selected_stores = list(STORE_FUNCTIONS.keys())
    else:
        selected_stores = [store for store in (data.stores or STORE_FUNCTIONS.keys()) if store in STORE_FUNCTIONS]
        if not selected_stores:
            return {
                "reply": "Debes seleccionar al menos una tienda para buscar.",
                "results": {},
                "role": role
            }

    resultados_agrupados = {}
    for store_name in selected_stores:
        try:
            productos = STORE_FUNCTIONS[store_name](query)
            if hasattr(productos, "__await__"):
                productos = await productos
            resultados_agrupados[store_name] = productos
            print(f"{store_name}: Encontrados {len(productos)} productos para '{query}'")
        except Exception as e:
            print(f"Error {store_name}: {e}")
            resultados_agrupados[store_name] = []

    if role == 'viewer':
        productos_viewer = []
        for productos in resultados_agrupados.values():
            for producto in productos:
                productos_viewer.append({
                    "nombre": producto.get("nombre", "Producto sin nombre"),
                    "precio": producto.get("precio", "No disponible"),
                    "imagen": producto.get("imagen")
                })

        total = len(productos_viewer)
        reply = (
            f"Encontré {total} resultados para tu búsqueda."
            if total > 0
            else f"No encontré nada relacionado con '{query}'."
        )

        return {
            "reply": reply,
            "results": {"Productos": productos_viewer},
            "role": role
        }

    conteos = {store: len(resultados_agrupados.get(store, [])) for store in selected_stores}
    total = sum(conteos.values())

    if total > 0:
        resumen_tiendas = ", ".join([f"{count} en {store}" for store, count in conteos.items()])
        reply = f"Encontré {total} resultados: {resumen_tiendas}."
    else:
        reply = f"No encontré nada relacionado con '{query}' en las tiendas seleccionadas."

    return {
        "reply": reply,
        "results": resultados_agrupados,
        "role": role
    }

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host='0.0.0.0', port=port)
