import requests
import json
import re
import time

# URL del archivo maestro de Sigma
DB_URL = "https://www.sigmaelectronica.net/wp-content/uploads/woos_search_engine_cache/guaven_woos_data.js"
CACHE_DURATION = 86400  # 24 horas

SIGMA_CACHE = {
    "data": [], 
    "last_updated": 0
}

def actualizar_bd():
    global SIGMA_CACHE
    ahora = time.time()
    
    if SIGMA_CACHE["data"] and (ahora - SIGMA_CACHE["last_updated"] < CACHE_DURATION):
        return True

    print("--- Cargando Motor de Búsqueda Sigma ---")
    try:
        response = requests.get(DB_URL, timeout=30)
        if response.status_code != 200: return False

        content = response.text
        start = content.find('{')
        end = content.rfind('}') + 1
        data = json.loads(content[start:end])
        
        keywords_list = data.get("guaven_woos_cache_keywords", [])
        html_list = data.get("guaven_woos_cache_html", [])
        
        procesados = []
        # Las listas son paralelas: indice 0 con 0, 1 con 1...
        total = min(len(keywords_list), len(html_list))
        
        for i in range(total):
            k_str = keywords_list[i]
            h_str = html_list[i]
            
            try:
                # --- 1. EXTRACCIÓN DE DATOS ---
                # Formato típico: "SKU {{k}} ... {{o}}"> Título Descripción"
                
                # SKU (Lo que está antes de {{k}})
                sku = ""
                if '{{k}}' in k_str:
                    sku = k_str.split('{{k}}')[0].strip()

                # CONTENIDO (Lo que está después de {{o}}">)
                raw_content = ""
                if '{{o}}">' in k_str:
                    raw_content = k_str.split('{{o}}">', 1)[1].strip()
                else:
                    raw_content = k_str # Fallback

                # TÍTULO (Heurística: Primera frase hasta punto o guion)
                titulo = raw_content.split('.')[0].split('–')[0].strip()
                if len(titulo) > 80: titulo = titulo[:80]

                # PRECIO E IMAGEN
                precio = "Consultar"
                match_p = re.search(r"\{\{p\}\}([0-9.,]+)", h_str)
                if match_p: precio = "$ " + match_p.group(1)

                imagen = "https://via.placeholder.com/150?text=Sigma"
                match_img = re.search(r'\{\{d\}\}\{\{u\}\}/([^"]+?)\{\{i\}\}', h_str)
                if match_img:
                    imagen = f"https://www.sigmaelectronica.net/wp-content/uploads/{match_img.group(1)}"

                # ID (Vital para el link)
                pid = None
                match_id = re.search(r'id="prli_(\d+)"', h_str)
                if match_id: pid = match_id.group(1)

                if pid:
                    procesados.append({
                        "id": pid,
                        "sku": sku,
                        "titulo": titulo,
                        "contenido_completo": k_str.lower(), # Para búsqueda sucia
                        "titulo_lower": titulo.lower(),      # Para relevancia alta
                        "sku_lower": sku.lower(),            # Para relevancia máxima
                        "precio": precio,
                        "imagen": imagen,
                        "url": f"https://www.sigmaelectronica.net/?p={pid}",
                        "tienda": "Sigma",
                        "stock": "Disponible"
                    })
            except:
                continue

        SIGMA_CACHE["data"] = procesados
        SIGMA_CACHE["last_updated"] = ahora
        print(f"Sigma Indexado: {len(procesados)} productos.")
        return True

    except Exception as e:
        print(f"Error Sigma: {e}")
        return False

def buscar_productos(query: str, limite: int = 10):
    if not actualizar_bd():
        return []

    q_norm = query.lower().strip()
    palabras = q_norm.split()
    
    resultados_con_puntaje = []
    
    for prod in SIGMA_CACHE["data"]:
        score = 0
        
        # --- ALGORITMO DE RELEVANCIA (SCORING) ---
        
        # 1. Coincidencia EXACTA en SKU (Máxima prioridad)
        if q_norm == prod["sku_lower"]:
            score += 1000
        elif q_norm in prod["sku_lower"]:
            score += 500

        # 2. Coincidencia en TÍTULO (Alta prioridad)
        # Verificamos si TODAS las palabras están en el título
        match_titulo = True
        for p in palabras:
            if p not in prod["titulo_lower"]:
                match_titulo = False
                break
        
        if match_titulo:
            score += 100
            # Bono si empieza con la palabra buscada (Ej: "Arduino Uno" vs "Cable Arduino")
            if prod["titulo_lower"].startswith(palabras[0]):
                score += 50

        # 3. Coincidencia en DESCRIPCIÓN (Baja prioridad)
        # Solo si no hubo match en título, miramos el resto
        if score == 0:
            match_desc = True
            for p in palabras:
                if p not in prod["contenido_completo"]:
                    match_desc = False
                    break
            
            if match_desc:
                score += 10 # Puntos bajos para accesorios

        # --- FILTRO FINAL ---
        # Solo agregamos si tiene algún puntaje
        if score > 0:
            resultados_con_puntaje.append((score, prod))

    # ORDENAR POR PUNTAJE (De mayor a menor)
    # Esto pone los Arduinos reales arriba y los cables abajo
    resultados_con_puntaje.sort(key=lambda x: x[0], reverse=True)
    
    # Formatear salida
    finales = []
    for score, prod in resultados_con_puntaje[:limite]:
        finales.append({
            "nombre": prod["titulo"],
            "precio": prod["precio"],
            "stock": prod["stock"],
            "url": prod["url"],
            "imagen": prod["imagen"],
            "tienda": "Sigma"
        })

    return finales

# --- Bloque de Prueba ---
if __name__ == "__main__":
    print("Probando Sigma con Ranking...")
    # Prueba difícil: "Arduino"
    # Debería salir primero la placa, no el cable.
    res = buscar_productos("arduino")
    
    print(f"\nResultados encontrados: {len(res)}")
    for i, r in enumerate(res):
        print(f"{i+1}. {r['nombre']} ({r['precio']})")