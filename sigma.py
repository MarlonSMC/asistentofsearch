import requests
from bs4 import BeautifulSoup
import re

def buscar_productos(query, limite=10):
    # Búsqueda directa en el buscador de WordPress/WooCommerce de Sigma
    url = f"https://www.sigmaelectronica.net/?s={query}&post_type=product"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.sigmaelectronica.net/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        productos = []

        # Sigma usa WooCommerce. Los productos suelen estar en 'li.product' o 'div.product'
        # Buscamos contenedores que tengan la clase 'type-product'
        items = soup.select('.product, .type-product')

        for item in items:
            try:
                # 1. TÍTULO Y URL
                tag_titulo = item.select_one('.woocommerce-loop-product__title, .product-title, h2, h3')
                tag_link = item.select_one('a.woocommerce-LoopProduct-link, a')
                
                if not tag_titulo or not tag_link: continue

                nombre = tag_titulo.get_text(strip=True)
                url_producto = tag_link['href']

                # 2. PRECIO
                # Buscamos el precio actual (a veces hay oferta y precio regular)
                tag_precio = item.select_one('.price')
                precio = "Consultar"
                
                if tag_precio:
                    # Si hay oferta, el precio real suele estar dentro de <ins> o al final
                    # Extraemos el texto limpio
                    texto_precio = tag_precio.get_text(" ", strip=True)
                    # Buscamos el patrón de dinero: $ 15.000 o $15,000
                    match = re.findall(r'[\$][\s\d,.]+', texto_precio)
                    if match:
                        precio = match[-1] # Tomamos el último (el de oferta si hay dos)
                    else:
                        precio = texto_precio

                # 3. IMAGEN
                tag_img = item.select_one('img')
                imagen = "https://via.placeholder.com/150?text=Sigma"
                
                if tag_img:
                    src = tag_img.get('src')
                    if not src and tag_img.get('data-src'):
                        src = tag_img.get('data-src')
                    
                    if src: imagen = src

                # 4. STOCK (NUEVO: Lectura directa)
                # Sigma suele mostrar "Hay 5 disponibles" en el listado
                stock = "Disponible"
                texto_item = item.get_text(" ", strip=True)
                
                # Buscamos patrón "Hay X disponibles"
                match_stock = re.search(r'Hay\s*(\d+)\s*disponibles', texto_item, re.IGNORECASE)
                if match_stock:
                    cantidad = match_stock.group(1)
                    stock = f"{cantidad} unid."
                elif "agotado" in texto_item.lower() or "out of stock" in texto_item.lower():
                    stock = "Agotado"

                productos.append({
                    "nombre": nombre,
                    "precio": precio,
                    "url": url_producto,
                    "imagen": imagen,
                    "tienda": "Sigma",
                    "stock": stock
                })
                
                if len(productos) >= limite:
                    break

            except Exception as e:
                continue

        return productos

    except Exception as e:
        print(f"Error en Sigma: {e}")
        return []

# --- Bloque de Prueba ---
if __name__ == "__main__":
    print("Probando Sigma (Método Directo)...")
    res = buscar_productos("arduino", limite=5)
    print(f"Encontrados: {len(res)}")
    for p in res:
        print(f"[{p['stock']}] {p['nombre']} - {p['precio']}")