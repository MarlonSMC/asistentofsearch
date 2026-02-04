from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    # Este es el mensaje que verás en pantalla
    return {"status": "online", "mensaje": "Hola Mundo - Asistente de Búsqueda Activo"}