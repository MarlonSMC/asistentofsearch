import requests
from bs4 import BeautifulSoup
import json

# CORRECCIÓN CLAVE: La URL correcta detectada por tu diagnóstico
SEARCH_URL = "https://www.zamux.co/search"

def buscar_productos(query: str, limite: int = 10):
    """
    Wrapper para Zamux usando la ruta correcta /search.
    """
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    resultados = []

    try:
        response = requests.get(SEARCH_URL, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selector de productos (mantenemos el que funcionó en debug_layout)
            items = soup.select('.product-block')

            for item in items[:limite]:
                try:
                    # 1. NOMBRE y URL
                    # Buscamos el anchor con la clase específica
                    tag_anchor = item.select_one('.product-block__anchor')
                    
                    if tag_anchor:
                        # Extraemos título limpio del atributo 'title' ("Ir a ARDUINO...")
                        raw_title = tag_anchor.get('title', '')
                        nombre = raw_title.replace('Ir a ', '').strip()
                        url_rel = tag_anchor.get('href')
                    else:
                        # Fallback
                        tag_backup = item.select_one('h3 a, h4 a, .name a')
                        if not tag_backup: continue
                        nombre = tag_backup.get_text(strip=True)
                        url_rel = tag_backup.get('href')

                    # URL Absoluta
                    url_final = f"https://www.zamux.co{url_rel}" if not url_rel.startswith('http') else url_rel

                    # 2. IMAGEN
                    # Prioridad: <source srcset> (imágenes optimizadas) -> <img>
                    imagen = "https://via.placeholder.com/150"
                    
                    tag_source = item.select_one('.product-block__picture source')
                    tag_img = item.select_one('.product-block__picture img')
                    
                    src = None
                    if tag_source:
                        src = tag_source.get('srcset')
                    elif tag_img:
                        src = tag_img.get('src')
                    
                    if src:
                        # Limpiar query params (?v=...)
                        src = src.split('?')[0]
                        # Limpiar saltos de línea o espacios
                        src = src.strip().split(' ')[0] 
                        imagen = "https:" + src if src.startswith('//') else src

                    # 3. PRECIO
                    tag_precio = item.select_one('.product-block__price, .product-block__price-current, .price')
                    precio = tag_precio.get_text(strip=True) if tag_precio else "Ver Precio"

                    # 4. STOCK
                    # Inferencia por texto "Agotado" en el bloque
                    stock = "Disponible"
                    texto_completo = item.get_text().lower()
                    if "agotado" in texto_completo or "sin stock" in texto_completo:
                        stock = "Agotado"

                    resultados.append({
                        "nombre": nombre,
                        "precio": precio,
                        "stock": stock,
                        "url": url_final,
                        "imagen": imagen,
                        "tienda": "Zamux"
                    })

                except Exception as e:
                    continue

    except Exception as e:
        print(f"Error conectando con Zamux: {e}")

    return resultados

# --- Bloque de Prueba ---
if __name__ == "__main__":
    print("Probando búsqueda REAL en Zamux...")
    # Prueba con algo específico para verificar que el filtro funcione
    resultados = buscar_productos("arduino") 
    
    if results := resultados:
        print(f"¡ÉXITO! Encontrados: {len(results)}")
        # Imprimimos el primero para verificar que sea un Arduino y no un Pegante
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
    else:
        print("No se encontraron resultados.")