from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup
import re
import time
import random

def buscar_productos(query, limite=10):
    url = f"https://www.sigmaelectronica.net/?s={query}&post_type=product"
    
    print(f"--- PLAYWRIGHT: Iniciando búsqueda para '{query}' ---")
    
    # Iniciamos Playwright
    with sync_playwright() as p:
        # Lanzamos navegador. 
        # En GCP/Docker es CRÍTICO usar los args '--no-sandbox'
        browser = p.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-setuid-sandbox'] 
        )
        
        # Contexto persistente (simula un perfil de usuario)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        # --- APLICAR STEALTH ---
        # Esto elimina variables como 'navigator.webdriver' que delatan al bot
        stealth_sync(page)

        try:
            print(f"--- PLAYWRIGHT: Navegando a {url} ---")
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Pequeña espera aleatoria para parecer humano
            time.sleep(random.uniform(2, 4))
            
            # Esperamos a que aparezca al menos un producto O el mensaje de 'no encontrado'
            # Esto da tiempo a que JS se ejecute y pase el challenge si es ligero.
            try:
                page.wait_for_selector('.product, .woocommerce-info', timeout=15000)
            except Exception:
                print("--- PLAYWRIGHT: Timeout esperando selector. Posible bloqueo fuerte o carga lenta.")

            # Extraemos el HTML renderizado (ya procesado por el navegador)
            contenido_html = page.content()
            
            # --- DEBUG: Ver si seguimos bloqueados ---
            if "recaptcha" in contenido_html.lower() or "challenge" in contenido_html.lower():
                print("--- ALERTA: El HTML aún contiene rastros de ReCAPTCHA/Challenge ---")

            # --- PARSING (Tu lógica original con BS4) ---
            soup = BeautifulSoup(contenido_html, 'html.parser')
            items = soup.select('.product, .type-product')
            print(f"--- PLAYWRIGHT: Items encontrados en el DOM: {len(items)} ---")
            
            productos = []
            
            for item in items:
                try:
                    tag_titulo = item.select_one('.woocommerce-loop-product__title, .product-title, h2, h3')
                    tag_link = item.select_one('a.woocommerce-LoopProduct-link, a')
                    
                    if not tag_titulo or not tag_link: continue

                    nombre = tag_titulo.get_text(strip=True)
                    url_producto = tag_link['href']

                    # Precio
                    tag_precio = item.select_one('.price')
                    precio = "Consultar"
                    if tag_precio:
                        texto_precio = tag_precio.get_text(" ", strip=True)
                        match = re.findall(r'[\$][\s\d,.]+', texto_precio)
                        precio = match[-1] if match else texto_precio

                    # Imagen
                    tag_img = item.select_one('img')
                    imagen = "https://via.placeholder.com/150?text=Sigma"
                    if tag_img:
                        src = tag_img.get('src') or tag_img.get('data-src')
                        if src: imagen = src

                    # Stock (Lógica Regex)
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
                    
                    if len(productos) >= limite: break

                except Exception:
                    continue

            browser.close()
            return productos

        except Exception as e:
            print(f"Error crítico Playwright: {e}")
            browser.close()
            return []

if __name__ == "__main__":
    # Prueba local
    res = buscar_productos("arduino", limite=5)
    for p in res:
        print(f"[{p['stock']}] {p['nombre']} - {p['precio']}")