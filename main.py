import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import electronilab
import vistronica

# Inicialización de la aplicación FastAPI
app = FastAPI()

# Configuración de carpetas para los archivos HTML
templates = Jinja2Templates(directory="templates")

# Modelo de datos para recibir mensajes desde el frontend
class ChatRequest(BaseModel):
    message: str
    
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Sirve el archivo index.html ubicado en la carpeta 'templates'.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat(data: ChatRequest):
    query = data.message
    
    # 1. Ejecutar búsquedas
    try:
        # Buscamos hasta 10 para tener variedad en la lista
        productos_vistronica = vistronica.buscar_productos(query, limite=10)
    except:
        productos_vistronica = []

    try:
        productos_electronilab = electronilab.buscar_productos(query, limite=10)
    except:
        productos_electronilab = []

    # 2. Construir respuesta agrupada por Tienda
    # Ya no mezclamos las listas, las mantenemos separadas
    resultados_agrupados = {
        "Vistronica": productos_vistronica,
        "Electronilab": productos_electronilab
    }

    # 3. Mensaje resumen
    count_v = len(productos_vistronica)
    count_e = len(productos_electronilab)
    
    if count_v + count_e > 0:
        reply = f"Resultados para '{query}': {count_v} en Vistronica y {count_e} en Electronilab."
    else:
        reply = f"No encontré nada relacionado con '{query}' en las tiendas."

    return {
        "reply": reply,
        "results": resultados_agrupados # Objeto { "Tienda A": [...], "Tienda B": [...] }
    }

if __name__ == '__main__':
    import uvicorn
    # Configuración del puerto para ejecución local o despliegue
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host='0.0.0.0', port=port)