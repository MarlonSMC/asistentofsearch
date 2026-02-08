# Usamos una imagen ligera de Python basada en Linux
FROM python:3.9-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos e instalamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código fuente
COPY . .

# Cambia la última línea por esta:
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT