import cloudscraper
from bs4 import BeautifulSoup
import re
import sys

def buscar_productos(query, limite=10):
    url = f"https://www.sigmaelectronica.net/?s={query}&post_type=product"
    
    # Simulación de un navegador moderno para evitar bloqueos
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    print(f"--- DEBUG SIGMA: Iniciando búsqueda para '{query}' ---")
    print(f"--- DEBUG SIGMA: URL: {url} ---")

    try:
        response = scraper.get(url, timeout=20)
        
        # LOG: Estado de la respuesta
        print(f"--- DEBUG SIGMA: Status Code: {response.status_code} ---")
        
        if response.status_code != 200:
            print(f"--- DEBUG SIGMA: Error de acceso. HTML recibido (primeros 500 chars): ---")
            print(response.text[:500])
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # LOG: Verificar si el HTML contiene indicios de bloqueo (Cloudflare)
        if "cf-ray" in response.text.lower() or "checking your browser" in response.text.lower():
            print("--- DEBUG SIGMA: ¡BLOQUEO DETECTADO! Cloudflare está pidiendo verificación humana (JS Challenge).")
            return []

        productos = []

        # Intentamos identificar qué selectores están disponibles
        items = soup.select('.product, .type-product')
        print(f"--- DEBUG SIGMA: Se encontraron {len(items)} elementos con clase '.product' o '.type-product' ---")

        if len(items) == 0:
            # Si no hay items, imprimimos las clases de los primeros <div> para diagnosticar el DOM
            print("--- DEBUG SIGMA: No se hallaron productos. Estructura de clases detectada en el body: ---")
            for div in soup.find_all('div', limit=5):
                print(f"Div class: {div.get('class')}")

        for i, item in enumerate(items):
            try:
                # DEBUG SELECTORES
                tag_titulo = item.select_one('.woocommerce-loop-product__title, .product-title, h2, h3')
                tag_link = item.select_one('a.woocommerce-LoopProduct-link, a')
                
                if not tag_titulo:
                    print(f"--- DEBUG SIGMA [Item {i}]: No se encontró tag_titulo ---")
                if not tag_link:
                    print(f"--- DEBUG SIGMA [Item {i}]: No se encontró tag_link ---")
                
                if not tag_titulo or not tag_link: continue

                nombre = tag_titulo.get_text(strip=True)
                url_producto = tag_link['href']

                # 2. PRECIO
                tag_precio = item.select_one('.price')
                precio = "Consultar"
                
                if tag_precio:
                    texto_precio = tag_precio.get_text(" ", strip=True)
                    match = re.findall(r'[\$][\s\d,.]+', texto_precio)
                    precio = match[-1] if match else texto_precio
                else:
                    print(f"--- DEBUG SIGMA [Item {i}]: Precio no encontrado para {nombre} ---")

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
                    stock = f"{match_stock.group(1)} unid."
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
                print(f"--- DEBUG SIGMA: Error procesando item {i}: {e} ---")
                continue

        print(f"--- DEBUG SIGMA: Total productos extraídos: {len(productos)} ---")
        return productos

    except Exception as e:
        print(f"--- DEBUG SIGMA: ERROR CRÍTICO: {type(e).__name__} - {e} ---")
        return []

if __name__ == "__main__":
    res = buscar_productos("arduino", limite=5)
    for p in res:
        print(f"[{p['stock']}] {p['nombre']} - {p['precio']}")