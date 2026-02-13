import httpx
import asyncio
import time
from unidecode import unidecode  # Ayuda a buscar "relé" escribiendo "rele"

# --- CONFIGURACIÓN Y CACHÉ ---
# Guardamos el catálogo en memoria para no descargar 5MB cada vez que buscas
CATALOGO_CACHE = {"data": None, "last_updated": 0}
CACHE_DURATION = 3600  # 1 hora de caché es suficiente
URL_BASE = "https://www.vistronica.com/cotizaciones/products_search_cache.json"

async def get_catalogo():
    """Descarga el JSON completo simulando ser un navegador real."""
    global CATALOGO_CACHE
    ahora = time.time()
    
    # 1. Verificar Caché
    if CATALOGO_CACHE["data"] and (ahora - CATALOGO_CACHE["last_updated"] < CACHE_DURATION):
        return CATALOGO_CACHE["data"]

    # 2. Configurar Headers (LA SOLUCIÓN AL ERROR 403)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.vistronica.com/",  # <--- IMPORTANTE: Dice que venimos del home
        "X-Requested-With": "XMLHttpRequest"
    }
    
    print("--- VISTRONICA: Actualizando catálogo desde servidor... ---")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL_BASE, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                CATALOGO_CACHE["data"] = data
                CATALOGO_CACHE["last_updated"] = ahora
                print(f"--- VISTRONICA: Catálogo actualizado ({len(data)} items) ---")
                return data
            else:
                print(f"--- VISTRONICA Error: Status {response.status_code} ---")
                # Si falla, intentamos devolver lo que haya en caché aunque sea viejo
                return CATALOGO_CACHE["data"] or []
                
    except Exception as e:
        print(f"--- VISTRONICA Exception: {e} ---")
        return CATALOGO_CACHE["data"] or []

async def buscar_productos(query: str, limite: int = 10):
    """
    Busca en el catálogo descargado.
    Ahora es 'async' para no bloquear tu API de FastAPI.
    """
    catalogo = await get_catalogo()
    if not catalogo:
        return []
    
    # Preparamos la búsqueda: quitamos tildes y mayúsculas
    # Ej: "Módulo Relé" -> ["modulo", "rele"]
    terminos = unidecode(query.lower()).strip().split()
    
    resultados = []
    
    for item in catalogo:
        try:
            # Vistronica a veces usa 'name' y a veces 'label'
            nombre_original = item.get("name") or item.get("label") or ""
            if not nombre_original: continue
            
            # Normalizamos el nombre del producto
            nombre_norm = unidecode(nombre_original.lower())
            
            # Lógica de coincidencia: TODAS las palabras deben estar
            match = True
            for termino in terminos:
                if termino not in nombre_norm:
                    match = False
                    break
            
            if match:
                # Corrección de URL si viene relativa
                url_prod = item.get("url") or item.get("link")
                if url_prod and not url_prod.startswith("http"):
                    url_prod = f"https://www.vistronica.com/{url_prod}"
                
                # Precio (formateo simple)
                precio = item.get("price") or item.get("price_tax_incl")
                if precio:
                    precio = f"${precio}"

                resultados.append({
                    "nombre": nombre_original,
                    "precio": precio,
                    "stock": item.get("stock_qty"), # Si está en el search cache, suele haber stock
                    "url": url_prod,
                    "imagen": item.get("image") or item.get("image_link_small"),
                    "tienda": "Vistronica"
                })
                
                if len(resultados) >= limite:
                    break

        except Exception:
            continue
            
    return resultados

# --- Bloque de Prueba Local ---
if __name__ == "__main__":
    # Al ser async, necesitamos asyncio para probarlo aquí
    print("Probando Vistronica Async...")
    try:
        res = asyncio.run(buscar_productos("arduino r3", limite=5))
        for p in res:
            print(f"[{p['stock']}] {p['nombre']} - {p['precio']}")
    except ImportError:
        print("Error: Instala 'httpx' y 'unidecode' primero.")