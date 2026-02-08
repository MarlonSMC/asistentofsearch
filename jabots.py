import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures

def obtener_stock_real(url_producto, session):
    """
    Entra a la página del producto en Ja-Bots para leer el stock exacto.
    Estrategia WooCommerce: Buscar la clase .stock o el input de cantidad.
    """
    try:
        response = session.get(url_producto, timeout=5)
        if response.status_code != 200:
            return "Consultar"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        html_str = str(soup).lower()
        
        # ESTRATEGIA 1: Texto explícito de stock (Clase estándar de WooCommerce)
        # <p class="stock in-stock">50 disponibles</p>
        stock_element = soup.select_one('.stock.in-stock, .stock, .availability')
        if stock_element:
            texto = stock_element.get_text(strip=True)
            # Buscamos números en el texto (ej: "50 disponibles")
            match = re.search(r'(\d+)', texto)
            if match:
                return match.group(1)
            # Si dice solo "Hay existencias" sin número
            if "hay existencias" in texto.lower() or "in stock" in texto.lower():
                # Intentamos buscar el input max como segunda opción
                pass 

        # ESTRATEGIA 2: Input de cantidad (max attribute)
        # <input type="number" ... max="15" ...>
        input_qty = soup.find('input', {'name': 'quantity'})
        if input_qty and input_qty.has_attr('max'):
            stock_max = input_qty['max']
            if stock_max and stock_max.isdigit():
                return stock_max

        # ESTRATEGIA 3: Verificar Agotado
        if "agotado" in html_str or "out of stock" in html_str:
            return "0"
        
        if soup.select_one('.outofstock, .stock.out-of-stock'):
            return "0"

        # Si hay botón de añadir al carrito, hay stock, pero no sabemos cuánto
        if soup.select_one('.single_add_to_cart_button, button[name="add-to-cart"]'):
            return "Disponible" # >1 (Indeterminado)
            
        return "0"
        
    except Exception:
        return "Disponible"

def buscar_productos(query, limite=10):
    url = f"https://ja-bots.com/?s={query}&post_type=product"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=15)
        if response.status_code != 200: return []

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('li.product, div.product')
        
        productos_temp = []

        # --- FASE 1: Recolección Rápida ---
        for item in items:
            try:
                # Título y URL
                tag_titulo = item.select_one('.woocommerce-loop-product__title, .product-title, h2, h3')
                tag_link = item.select_one('a.woocommerce-LoopProduct-link, a')
                
                if not tag_titulo or not tag_link: continue

                nombre = tag_titulo.get_text(strip=True)
                url_producto = tag_link['href']

                # Precio
                tag_precio = item.select_one('.price')
                precio = "Consultar"
                if tag_precio:
                    texto_precio = tag_precio.get_text(strip=True)
                    match = re.search(r'[\$][\s\d,.]+', texto_precio)
                    if match: precio = match.group(0)
                    else: precio = texto_precio

                # Imagen
                tag_img = item.select_one('img')
                imagen = "https://via.placeholder.com/150?text=Ja-Bots"
                if tag_img:
                    src = tag_img.get('src') or tag_img.get('data-src')
                    if src: imagen = src

                productos_temp.append({
                    "nombre": nombre,
                    "precio": precio,
                    "url": url_producto,
                    "imagen": imagen,
                    "tienda": "Ja-Bots",
                    "stock": "..." # Se llenará en Fase 2
                })
                
                if len(productos_temp) >= limite:
                    break

            except:
                continue

        # --- FASE 2: Extracción de Stock Real (Paralelo) ---
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_prod = {executor.submit(obtener_stock_real, p["url"], session): p for p in productos_temp}
            
            for future in concurrent.futures.as_completed(future_to_prod):
                prod = future_to_prod[future]
                try:
                    cantidad = future.result()
                    # Formateo
                    if cantidad.isdigit() and int(cantidad) > 0:
                        prod["stock"] = f"{cantidad} unid."
                    elif cantidad == "0":
                        prod["stock"] = "Agotado"
                    else:
                        prod["stock"] = cantidad # "Disponible"
                except:
                    prod["stock"] = "Disponible"

        return productos_temp

    except Exception as e:
        print(f"Error en Ja-Bots: {e}")
        return []

if __name__ == "__main__":
    print("Probando Ja-Bots (Stock Exacto)...")
    res = buscar_productos("arduino", limite=5)
    print(f"Encontrados: {len(res)}")
    for p in res:
        print(f"[{p['stock']}] {p['nombre']}")