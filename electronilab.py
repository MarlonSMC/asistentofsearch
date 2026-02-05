import requests
import json

# URL exacta que me diste (sin los parámetros, esos van aparte)
URL = "https://search.electronilab.co/multi_search"

# LA LLAVE CORREGIDA (Copiada de tu URL textual)
API_KEY = "oFhX57bSNkk5sutcWAFaQP1uTHFW12lV"

def buscar_productos(query: str, limite: int = 5):
    # 1. Parámetros de URL (La llave va aquí, tal como en tu navegador)
    params = {
        "x-typesense-api-key": API_KEY
    }

    # 2. Payload para Multi-Search (El "paquete" de búsqueda)
    payload = {
        "searches": [
            {
                "collection": "product",
                "q": query,
                "query_by": "sku, post_content, post_title",
                "sort_by": "_text_match:desc,stock_qt:desc,total_sales:desc",
                "per_page": limite,
                "page": 1
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Origin": "https://electronilab.co",
        "Referer": "https://electronilab.co/"
    }

    try:
        # Petición POST enviando la llave en la URL (?x-typesense...) y los datos en JSON
        response = requests.post(URL, params=params, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Typesense devuelve: { results: [ { hits: [...] } ] }
            if "results" in data and len(data["results"]) > 0:
                hits = data["results"][0].get("hits", [])
                
                resultados_limpios = []
                for hit in hits:
                    doc = hit.get("document", {})
                    
                    # Extraemos los datos usando las llaves que vimos en tus capturas
                    resultados_limpios.append({
                        "nombre": doc.get("post_title"),
                        "precio": doc.get("price"),       # Ojo: a veces es 'regular_price'
                        "stock": doc.get("stock_qt"),
                        "url": doc.get("permalink"),
                        "imagen": doc.get("image_url"),   # Si existe
                        "tienda": "Electronilab"
                    })
                return resultados_limpios
            else:
                return []
        else:
            print(f"Error Electronilab {response.status_code}: {response.text}")
            return []

    except Exception as e:
        print(f"Error crítico en Electronilab: {e}")
        return []

# --- Bloque de Prueba ---
if __name__ == "__main__":
    resultados = buscar_productos("arduino")
    
    if results := resultados: # (Walrus operator, Python 3.8+)
        print(f"¡ÉXITO! Encontrados: {len(results)}")
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
    else:
        print("No se encontraron resultados (o falló la conexión).")