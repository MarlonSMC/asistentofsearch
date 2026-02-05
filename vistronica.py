import cloudscraper
import time
import json

# Configuración y Cache Global
CATALOGO_CACHE = {"data": None, "last_updated": 0}
CACHE_DURATION = 86400  # 24 horas
URL_BASE = "https://www.vistronica.com/cotizaciones/products_search_cache.json"

def get_catalogo():
    """Descarga y cachea el catálogo completo evitando bloqueos 403."""
    ahora = time.time()
    
    if CATALOGO_CACHE["data"] and (ahora - CATALOGO_CACHE["last_updated"] < CACHE_DURATION):
        return CATALOGO_CACHE["data"]

    scraper = cloudscraper.create_scraper()
    v_param = int(ahora // 86400)
    
    try:
        response = scraper.get(f"{URL_BASE}?v={v_param}", timeout=15)
        response.raise_for_status()
        data = response.json()
        
        CATALOGO_CACHE["data"] = data
        CATALOGO_CACHE["last_updated"] = ahora
        return data
    except Exception as e:
        print(f"Error crítico obteniendo catálogo de Vistronica: {e}")
        return CATALOGO_CACHE["data"] or []

def buscar_productos(query: str, limite: int = 5):
    """
    Filtra el catálogo verificando que TODAS las palabras de la búsqueda
    existan en el nombre del producto (sin importar el orden).
    """
    catalogo = get_catalogo()
    
    # 1. Separamos la búsqueda en palabras individuales ("tokens")
    # Ej: "arduino r3" -> ["arduino", "r3"]
    terminos = query.lower().strip().split()
    
    resultados = []
    for p in catalogo:
        nombre_original = p.get("name") or ""
        nombre_lower = nombre_original.lower()
        
        # 2. Lógica CORREGIDA:
        # Verificamos si CADA término está presente en el nombre
        match = True
        for termino in terminos:
            if termino not in nombre_lower:
                match = False
                break # Si falta una palabra, descartamos el producto
        
        if match:
            resultados.append({
                "nombre": nombre_original,
                "precio": p.get("price_tax_incl"),
                "stock": p.get("stock_qty"),
                "url": p.get("link"),
                "imagen": p.get("image_link_small")
            })
            
    return resultados[:limite]

# --- Bloque de Prueba ---
if __name__ == "__main__":
    resultados = buscar_productos("arduino R3")
    
    if results := resultados: # (Walrus operator, Python 3.8+)
        print(f"¡ÉXITO! Encontrados: {len(results)}")
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
    else:
        print("No se encontraron resultados (o falló la conexión).")