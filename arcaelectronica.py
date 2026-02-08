import requests
from bs4 import BeautifulSoup
import re

def buscar_productos(query, limite=10):
    # URL de búsqueda estándar de Shopify
    url = f"https://www.arcaelectronica.com/search?q={query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # print(f"--- Buscando en Arca: {url} ---")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        productos = []

        # Seleccionamos las tarjetas de producto de los resultados de búsqueda
        # Basado en tu debug: class="grid-item search-result ..."
        items = soup.select('.search-result')

        for item in items:
            try:
                # 1. ENLACE Y URL
                tag_link = item.select_one('a.product-grid-item')
                if not tag_link: continue # Si no es un producto válido, saltar

                url_relativa = tag_link['href']
                if not url_relativa.startswith('http'):
                    url_final = "https://www.arcaelectronica.com" + url_relativa
                else:
                    url_final = url_relativa

                # 2. IMAGEN
                # Shopify suele poner la imagen dentro de un div .product-grid-image
                tag_img = tag_link.select_one('.product-grid-image img, img')
                imagen = "https://via.placeholder.com/150?text=Arca"
                
                if tag_img:
                    src = tag_img.get('src')
                    # Shopify a veces usa data-src o pone // al principio
                    if not src and tag_img.get('data-src'):
                        src = tag_img.get('data-src')
                    
                    if src:
                        if src.startswith('//'):
                            imagen = "https:" + src
                        elif src.startswith('http'):
                            imagen = src
                        else:
                            imagen = "https://www.arcaelectronica.com" + src

                # 3. TÍTULO
                # En este tema, el título suele ser un párrafo <p> dentro del enlace
                tag_titulo = tag_link.select_one('p, .h6, .product-title')
                if tag_titulo:
                    nombre = tag_titulo.get_text(strip=True)
                else:
                    # Fallback: buscar texto que no sea precio
                    nombre = "Producto sin nombre"
                    # A veces es el atributo title de la imagen
                    if tag_img and tag_img.get('alt'):
                        nombre = tag_img.get('alt')

                # 4. PRECIO
                # Buscamos cualquier cosa que parezca precio
                precio = "Consultar"
                # Selectores comunes de precio en Shopify
                tag_precio = item.select_one('.price, .money, .product-item--price')
                
                if tag_precio:
                    precio = tag_precio.get_text(strip=True)
                else:
                    # Si no hay etiqueta, buscamos texto con signo $ usando Regex
                    texto_completo = item.get_text()
                    match_precio = re.search(r'\$[\d,.]+', texto_completo)
                    if match_precio:
                        precio = match_precio.group(0)

                # 5. STOCK
                # Shopify suele poner una etiqueta 'badge' o clase 'sold-out'
                stock = "Disponible"
                if "agotado" in item.get_text().lower() or "sold out" in item.get_text().lower():
                    stock = "Agotado"
                
                # Buscar badges específicos
                badge = item.select_one('.badge--sold-out, .product-price__sold-out')
                if badge:
                    stock = "Agotado"

                # Guardar producto
                productos.append({
                    "nombre": nombre,
                    "precio": precio,
                    "url": url_final,
                    "imagen": imagen,
                    "tienda": "Arca Electrónica",
                    "stock": stock
                })
                
                if len(productos) >= limite:
                    break
            
            except Exception as e:
                continue

        return productos

    except Exception as e:
        print(f"Error en Arca: {e}")
        return []

# --- Bloque de Prueba ---
if __name__ == "__main__":
    print("Probando Arca Electrónica...")
    res = buscar_productos("arduino", limite=5)
    print(f"Encontrados: {len(res)}")
    if res:
        for p in res:
            estado = "🔴" if p['stock'] == 'Agotado' else "🟢"
            print(f"{estado} {p['nombre']} - {p['precio']}")