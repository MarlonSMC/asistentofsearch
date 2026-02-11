import cloudscraper
from bs4 import BeautifulSoup
import re

def buscar_productos(query, limite=10):
    # URL de búsqueda
    url = f"https://www.sigmaelectronica.net/?s={query}&post_type=product"
    
    # Creamos un scraper que simula ser un navegador (Chrome)
    scraper = cloudscraper.create_scraper()

    print(f"--- SIGMA (CloudScraper): Buscando '{query}' ---")

    try:
        # Usamos scraper.get en lugar de requests.get
        response = scraper.get(url, timeout=20)
        
        if response.status_code != 200:
            print(f"--- SIGMA Error: Status {response.status_code} ---")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        productos = []

        # Buscamos los productos (clases estándar de WooCommerce)
        items = soup.select('.product, .type-product')
        print(f"--- SIGMA: Encontrados {len(items)} items ---")

        for item in items:
            try:
                # 1. TÍTULO Y URL
                tag_titulo = item.select_one('.woocommerce-loop-product__title, .product-title, h2, h3')
                tag_link = item.select_one('a.woocommerce-LoopProduct-link, a')
                
                if not tag_titulo or not tag_link: continue

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
                    src = tag_img.get('src') or tag_img.get('data-src')
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

            except Exception:
                continue

        return productos

    except Exception as e:
        print(f"Error crítico en Sigma: {e}")
        return []

# --- Bloque de Prueba Local ---
if __name__ == "__main__":
    print("Probando Sigma con CloudScraper...")
    res = buscar_productos("arduino", limite=5)
    for p in res:
        print(f"[{p['stock']}] {p['nombre']}")