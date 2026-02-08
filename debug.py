import requests
from bs4 import BeautifulSoup

def espiar_electrosena():
    # URL estándar de Jumpseller
    url = "https://www.electrosena.com/search/arduino"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"--- Conectando a {url} ---")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Estado HTTP: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscamos contenedores típicos de Jumpseller
            # Mactronica usaba .product-slide-entry
            # Otros usan .product-block, .item, .caption
            items = soup.select('.product-block, .product-slide-entry, .item, .caption, .product-item')
            
            print(f"Posibles productos encontrados: {len(items)}")
            
            if items:
                # Tomamos uno que tenga precio para asegurar que es un producto
                candidato = None
                for i in items:
                    if i.select_one('.price, .product-price, .amount'):
                        candidato = i
                        break
                
                if candidato:
                    print("\n--- HTML DE UN PRODUCTO ---")
                    # Imprimimos el padre del candidato para ver el contenedor completo
                    padre = candidato.find_parent('div')
                    if padre:
                        print(padre.prettify()[:1000])
                    else:
                        print(candidato.prettify()[:1000])
                else:
                    print("Encontré contenedores pero ninguno parece tener precio dentro. Imprimiendo el primero:")
                    print(items[0].prettify()[:500])

            else:
                print("⚠ No encontré clases estándar. Imprimiendo estructura general del body:")
                print(soup.select_one('#content-block, #main, body').prettify()[:500])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    espiar_electrosena()