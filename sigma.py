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

    print(f"--- SIGMA DEBUG: Iniciando búsqueda de '{query}' ---") # DEBUG
    print(f"--- SIGMA DEBUG: URL: {url} ---") # DEBUG

    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"--- SIGMA DEBUG: Status Code: {response.status_code} ---") # DEBUG
        
        if response.status_code != 200:
            print(f"--- SIGMA DEBUG: Error en conexión. Status no es 200. ---") # DEBUG
            return []

        print(f"--- SIGMA DEBUG: Descarga exitosa. Tamaño HTML: {len(response.text)} caracteres ---") # DEBUG

        soup = BeautifulSoup(response.text, 'html.parser')
        productos = []

        # Sigma usa WooCommerce. Buscamos contenedores 'type-product'
        items = soup.select('.product, .type-product')
        print(f"--- SIGMA DEBUG: Elementos '.product' encontrados: {len(items)} ---") # DEBUG

        if len(items) == 0:
             print("--- SIGMA DEBUG: ALERTA - No se encontraron productos en el HTML. Posible cambio de estructura o bloqueo antibot. ---") # DEBUG
             # Opcional: Imprimir un pedazo del HTML para ver qué devolvieron
             # print(response.text[:500]) 

        for i, item in enumerate(items):
            try:
                # 1. TÍTULO Y URL
                tag_titulo = item.select_one('.woocommerce-loop-product__title, .product-title, h2, h3')
                tag_link = item.select_one('a.woocommerce-LoopProduct-link, a')
                
                if not tag_titulo or not tag_link: 
                    print(f"--- SIGMA DEBUG: Item {i} saltado (sin título o link) ---") # DEBUG
                    continue

                nombre = tag_titulo.get_text(strip=True)
                url_producto = tag_link['href']

                # 2. PRECIO
                tag_precio = item.select_one('.price')
                precio = "Consultar"
                
                if tag_precio:
                    texto_precio = tag_precio.get_text(" ", strip=True)
                    match = re.findall(r'[\$][\s\d,.]+', texto_precio)
                    if match:
                        precio = match[-1]
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

                # 4. STOCK
                stock = "Disponible"
                texto_item = item.get_text(" ", strip=True)
                
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
                print(f"--- SIGMA DEBUG: Error procesando item {i}: {e} ---") # DEBUG
                continue

        print(f"--- SIGMA DEBUG: Total productos procesados exitosamente: {len(productos)} ---") # DEBUG
        return productos

    except Exception as e:
        print(f"--- SIGMA DEBUG: Error CRÍTICO en Sigma: {e} ---") # DEBUG
        return []

# --- Bloque de Prueba ---
if __name__ == "__main__":
    print("Probando Sigma (Método Directo)...")
    res = buscar_productos("arduino", limite=5)
    print(f"Encontrados: {len(res)}")
    for p in res:
        print(f"[{p['stock']}] {p['nombre']} - {p['precio']}")