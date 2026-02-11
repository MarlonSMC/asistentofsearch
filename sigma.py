import asyncio
import random
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def buscar_productos(query, limite=10):
    # Construcción de la URL
    url = f"https://www.sigmaelectronica.net/?s={query}&post_type=product"
    
    print(f"--- SIGMA (Async Stealth): Buscando '{query}' ---")
    
    try:
        async with async_playwright() as p:
            # 1. LANZAMIENTO (Con await)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 2. CONTEXTO (Con await)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='es-ES',
                timezone_id='America/Bogota'
            )
            
            page = await context.new_page()

            # 3. STEALTH MANUAL (Ahora usamos await)
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es'] });
            """)

            print(f"--- Navegando a: {url} ---")
            
            # 4. NAVEGACIÓN Y ESPERAS
            response = await page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Usamos asyncio.sleep en lugar de time.sleep para no bloquear el servidor
            await asyncio.sleep(random.uniform(2, 4))

            try:
                await page.wait_for_selector('.product, .type-product', timeout=10000)
            except Exception:
                print("--- Warning: Timeout esperando productos ---")

            # 5. OBTENER HTML
            contenido_html = await page.content()
            
            # Verificación de bloqueo
            if "cf-ray" in contenido_html.lower() and "captcha" in contenido_html.lower():
                print("--- BLOQUEO DETECTADO ---")
                await browser.close()
                return []

            # 6. PARSING (BS4 sigue siendo síncrono, es rápido)
            soup = BeautifulSoup(contenido_html, 'html.parser')
            items = soup.select('.product, .type-product')
            
            print(f"--- Items encontrados: {len(items)} ---")
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

                    # Stock
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

            await browser.close()
            return productos

    except Exception as e:
        print(f"--- ERROR CRÍTICO ASYNC: {e} ---")
        return []

# --- Bloque de Prueba Local (Solo si ejecutas el archivo directo) ---
if __name__ == "__main__":
    # asyncio.run crea el loop necesario para probar la función async
    res = asyncio.run(buscar_productos("arduino", limite=5))
    for p in res:
        print(f"[{p['stock']}] {p['nombre']} - {p['precio']}")