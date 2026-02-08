import requests
from bs4 import BeautifulSoup

def buscar_productos(query, limite=10):
    # URL de búsqueda estilo Jumpseller
    url = f"https://www.mactronica.com.co/search/{query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # print(f"--- Buscando en Mactronica: {url} ---")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        productos = []

        items = soup.select('.product-slide-entry')

        for item in items:
            try:
                # 1. TÍTULO Y URL
                tag_titulo = item.select_one('a.title')
                if not tag_titulo: continue 

                nombre = tag_titulo.get_text(strip=True)
                url_relativa = tag_titulo['href']
                
                if not url_relativa.startswith('http'):
                    url_final = "https://www.mactronica.com.co" + url_relativa
                else:
                    url_final = url_relativa

                # 2. PRECIO
                tag_precio = item.select_one('.price .current')
                precio = "Consultar"
                if tag_precio:
                    precio = tag_precio.get_text(strip=True)

                # 3. IMAGEN
                tag_imagen = item.select_one('.product-image img')
                imagen = "https://via.placeholder.com/150?text=Mactronica"
                if tag_imagen:
                    imagen = tag_imagen.get('src')
                    if not imagen and tag_imagen.get('srcset'):
                        imagen = tag_imagen['srcset'].split(' ')[0]
                    if imagen and not imagen.startswith('http'):
                        imagen = "https:" + imagen

                # 4. DETECCIÓN DE STOCK (NUEVO)
                stock = "Disponible"
                
                # Método A: Buscar en la etiqueta .tag (donde suele salir "Agotado" o "Nuevo")
                tag_badge = item.select_one('.tag')
                if tag_badge:
                    texto_badge = tag_badge.get_text(strip=True).lower()
                    if "agotado" in texto_badge:
                        stock = "Agotado"
                
                # Método B: Buscar la palabra "Agotado" en todo el cuadro del producto (Backup)
                # Esto es útil si usan otra clase CSS para el aviso.
                if stock == "Disponible":
                    if "agotado" in item.get_text().lower():
                        stock = "Agotado"

                # Agregar a la lista
                productos.append({
                    "nombre": nombre,
                    "precio": precio,
                    "url": url_final,
                    "imagen": imagen,
                    "tienda": "Mactronica",
                    "stock": stock 
                })
                
                if len(productos) >= limite:
                    break
            
            except Exception as e:
                continue

        return productos

    except Exception as e:
        print(f"Error en Mactronica: {e}")
        return []

# --- Bloque de Prueba ---
if __name__ == "__main__":
    print("Probando Mactronica (Detector de Stock)...")
    res = buscar_productos("arduino", limite=5)
    print(f"Encontrados: {len(res)}")
    if res:
        for p in res:
            estado = "🔴 AGOTADO" if p['stock'] == 'Agotado' else "🟢 DISPONIBLE"
            print(f"{estado} | {p['nombre']} ({p['precio']})")