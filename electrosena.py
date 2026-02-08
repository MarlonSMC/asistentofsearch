import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures

def obtener_stock_real(url_producto, session):
    """
    Entra a la página del producto en Electrosena para leer el stock exacto.
    Estrategia Jumpseller: Leer el atributo 'max' del input de cantidad.
    """
    try:
        response = session.get(url_producto, timeout=5)
        if response.status_code != 200:
            return "Consultar"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        html_str = str(soup).lower()
        
        # ESTRATEGIA 1: Atributo 'max' en el input de cantidad
        # Jumpseller suele poner <input type="number" name="qty" max="50" ...>
        input_qty = soup.find('input', {'name': 'qty'})
        if input_qty and input_qty.has_attr('max'):
            stock_max = input_qty['max']
            # A veces max="-1" o max="" significa infinito/sin control
            if stock_max.isdigit():
                return stock_max

        # ESTRATEGIA 2: Buscar texto explícito "X en stock"
        # Patrones comunes: "15 en stock", "Stock: 15", "Disponibles: 15"
        for patron in [r'(\d+)\s*en stock', r'stock:\s*(\d+)', r'disponibles:\s*(\d+)', r'(\d+)\s*unidades']:
            match = re.search(patron, html_str)
            if match:
                return match.group(1)

        # ESTRATEGIA 3: Verificar Agotado
        if "agotado" in html_str or "sin stock" in html_str or "no disponible" in html_str:
            return "0"
        
        # ESTRATEGIA 4: Badges específicos
        if soup.select_one('.badge-sold-out, .label-danger, .product-form-sold-out'):
            return "0"

        # Si hay botón de compra pero no dice cuánto, asumimos disponible genérico
        if soup.find('form', action=re.compile('cart/add')):
            return "Disponible" # >1 pero no sabemos cuánto
            
        return "0"
        
    except Exception:
        return "Disponible"

def buscar_productos(query, limite=10):
    url = f"https://www.electrosena.com/search/{query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=15)
        if response.status_code != 200: return []

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.product-block')
        
        productos_temp = []

        # --- FASE 1: Recolección Rápida ---
        for item in items:
            try:
                # Título y URL
                tag_titulo = item.select_one('.product-block__info a')
                if not tag_titulo: 
                    tag_titulo = item.select_one('.product-block__anchor')
                
                if not tag_titulo: continue

                nombre = tag_titulo.get_text(strip=True)
                # Fallback nombre
                if not nombre:
                    img = item.select_one('img')
                    if img and img.get('alt'): nombre = img.get('alt')
                    elif tag_titulo.get('title'): nombre = tag_titulo.get('title').replace('Ir a ', '')

                url_relativa = tag_titulo['href']
                if not url_relativa.startswith('http'):
                    url_final = "https://www.electrosena.com" + url_relativa
                else:
                    url_final = url_relativa

                # Precio
                tag_precio = item.select_one('.product-block__price, .price')
                precio = "Consultar"
                if tag_precio:
                    precio = tag_precio.get_text(strip=True)
                else:
                    match = re.search(r'\$[\d,.]+', item.get_text())
                    if match: precio = match.group(0)

                # Imagen
                tag_img = item.select_one('.product-block__image')
                imagen = "https://via.placeholder.com/150?text=Electrosena"
                if tag_img:
                    src = tag_img.get('src') or tag_img.get('data-src')
                    if src:
                        if not src.startswith('http'):
                            imagen = "https:" + src if src.startswith('//') else src
                        else:
                            imagen = src

                productos_temp.append({
                    "nombre": nombre,
                    "precio": precio,
                    "url": url_final,
                    "imagen": imagen,
                    "tienda": "Electrosena",
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
        print(f"Error en Electrosena: {e}")
        return []

if __name__ == "__main__":
    print("Probando Electrosena (Stock Exacto)...")
    res = buscar_productos("arduino", limite=5)
    print(f"Encontrados: {len(res)}")
    for p in res:
        print(f"[{p['stock']}] {p['nombre']}")