import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures

def obtener_dato_exacto(url_producto, session):
    """
    Entra a la ficha técnica y busca el número exacto de stock.
    Retorna: "5", "100", "En Stock", "Agotado", etc.
    """
    try:
        response = session.get(url_producto, timeout=5)
        if response.status_code != 200:
            return "Consultar"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. BUSCAR LA ETIQUETA "Disponibilidad:"
        # En OpenCart suele estar en una lista <ul><li>Disponibilidad: <span>5</span></li></ul>
        # Buscamos cualquier elemento que contenga el texto "Disponibilidad:"
        etiqueta_disp = soup.find(string=re.compile("Disponibilidad:", re.I))
        
        if etiqueta_disp:
            padre = etiqueta_disp.parent # El <li> o <div>
            texto_completo = padre.get_text(strip=True) # Ej: "Disponibilidad: 50"
            
            # Limpiamos para dejar solo el valor
            # Quitamos "Disponibilidad:" y los dos puntos
            valor = texto_completo.split(":", 1)[1].strip()
            
            # Si el valor es "En Stock", lo dejamos así o lo cambiamos a ">1"
            if "out of stock" in valor.lower() or "agotado" in valor.lower():
                return "0"
            
            return valor # Retornará "50", "15", "En Stock", etc.

        # 2. VALIDACIÓN SECUNDARIA (Si no hay etiqueta)
        # Si no hay botón de compra, asumimos 0
        html_str = str(soup)
        if "button-cart" not in html_str and "cart.add" not in html_str:
            return "0"
            
        return "Disponible" # Si hay botón pero no dice cuánto
        
    except Exception as e:
        return "Disponible"

def buscar_productos(query, limite=10):
    url = "https://www.electronicaplugandplay.com/productos/product/search"
    params = {"search": query}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, params=params, timeout=10)
        if response.status_code != 200: return []

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.product-layout')
        
        productos_temp = []

        # --- FASE 1: Recolección Rápida ---
        for item in items:
            try:
                tag_titulo = item.select_one('h4 a')
                if not tag_titulo: continue

                nombre = tag_titulo.get_text(strip=True)
                url_producto = tag_titulo['href']

                # Precio
                tag_precio = item.select_one('.price')
                precio = "Consultar"
                if tag_precio:
                    texto_precio = tag_precio.get_text(strip=True)
                    match = re.search(r'\$[\d,.]+', texto_precio)
                    if match: precio = match.group(0)

                # Imagen
                tag_img = item.select_one('.image img')
                imagen = "https://via.placeholder.com/150?text=PnP"
                if tag_img:
                    src = tag_img.get('src')
                    if src:
                        imagen = src.replace(" ", "%20")
                        if not imagen.startswith('http'):
                            imagen = "https://www.electronicaplugandplay.com" + imagen

                productos_temp.append({
                    "nombre": nombre,
                    "precio": precio,
                    "url": url_producto,
                    "imagen": imagen,
                    "tienda": "Electrónica Plug and Play",
                    "stock": "..." # Placeholder
                })
                
                if len(productos_temp) >= limite:
                    break

            except:
                continue

        # --- FASE 2: Extracción de Cantidades en Paralelo ---
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_prod = {executor.submit(obtener_dato_exacto, p["url"], session): p for p in productos_temp}
            
            for future in concurrent.futures.as_completed(future_to_prod):
                prod = future_to_prod[future]
                try:
                    cantidad = future.result()
                    # Formateo bonito para la interfaz
                    if cantidad == "0":
                        prod["stock"] = "Agotado"
                    elif cantidad.isdigit():
                        prod["stock"] = f"{cantidad} unid."
                    else:
                        prod["stock"] = cantidad # "En Stock", "Bajo Pedido", etc.
                except:
                    prod["stock"] = "Disponible"

        return productos_temp

    except Exception as e:
        print(f"Error en Plug&Play: {e}")
        return []

if __name__ == "__main__":
    print("Probando Plug&Play (Extracción de Cantidades)...")
    res = buscar_productos("arduino", limite=5)
    print(f"Encontrados: {len(res)}")
    for p in res:
        # Imprimimos para ver si sale el número
        print(f"[{p['stock']}] {p['nombre']}")