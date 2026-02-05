import requests
from bs4 import BeautifulSoup

def diagnostico_estructura():
    url = "https://www.zamux.co/search/products"
    params = {"q": "arduino"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"--- Descargando {url} ---")
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Estado HTTP: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Búsqueda amplia de candidatos
        # Buscamos cualquier cosa que parezca un producto
        posibles_productos = soup.select('.product-block, .product-item, .item, .col-sm-4, .col-6')
        
        print(f"Elementos candidatos encontrados: {len(posibles_productos)}")
        
        if len(posibles_productos) > 0:
            # Tomamos el primer candidato para inspeccionarlo
            ejemplo = posibles_productos[0]
            print("\n--- HTML DEL PRIMER ELEMENTO ENCONTRADO ---")
            print(ejemplo.prettify()[:1000]) # Solo los primeros 1000 caracteres
            print("\n--- FIN DEL HTML ---")
            
            # Intentamos extraer el título a ver si falla
            titulo = ejemplo.select_one('h3, h4, .name, .caption a')
            print(f"Intento de título: {titulo.get_text(strip=True) if titulo else 'No encontrado'}")
        else:
            print("\nNo encontré contenedores estándar. Listando clases de los primeros 10 DIVs:")
            for div in soup.find_all('div')[:15]:
                clases = div.get('class')
                if clases:
                    print(f"Div class: {clases}")

    except Exception as e:
        print(f"Error grave: {e}")

if __name__ == "__main__":
    diagnostico_estructura()