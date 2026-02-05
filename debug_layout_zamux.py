import requests
from bs4 import BeautifulSoup

def investigar_formulario():
    url = "https://www.zamux.co/"
    print(f"--- Inspeccionando buscador en {url} ---")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos todos los formularios
        forms = soup.find_all('form')
        print(f"Formularios encontrados: {len(forms)}")
        
        found_search = False
        for i, form in enumerate(forms):
            action = form.get('action', '')
            method = form.get('method', 'get').upper()
            
            # Filtramos los que parecen de búsqueda
            if 'search' in action or 'buscar' in str(form).lower():
                found_search = True
                print(f"\n[CANDIDATO DETECTADO - Form #{i+1}]")
                print(f"   • Acción (URL): {action}")
                print(f"   • Método: {method}")
                
                # Buscamos los inputs de este formulario
                inputs = form.find_all('input')
                for inp in inputs:
                    tipo = inp.get('type', 'text')
                    nombre = inp.get('name', 'SIN NOMBRE')
                    print(f"   • Input encontrado: name='{nombre}' (type={tipo})")
                    
                print("\n   -> CONCLUSIÓN PARA ESTE FORMULARIO:")
                if action.startswith('/'):
                    print(f"      URL Final sugerida: https://www.zamux.co{action}")
                else:
                    print(f"      URL Final sugerida: {action}")
                
                # Buscamos el input de texto (probablemente la query)
                text_inputs = [i.get('name') for i in inputs if i.get('type') in ['text', 'search', 'search_query']]
                if text_inputs:
                    print(f"      Parámetro de búsqueda probable: '{text_inputs[0]}'")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    investigar_formulario()