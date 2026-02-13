# Usar una imagen ligera de Python oficial
FROM python:3.9-slim

# Evitar que Python escriba archivos .pyc y permitir logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Instalar dependencias del sistema necesarias para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Crear carpeta de trabajo
WORKDIR /app

# Copiar PRIMERO los requisitos para aprovechar la caché de Docker si no cambian
COPY requirements.txt .

# Instalar las librerías OBLIGATORIAMENTE
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# 2. Instalar los navegadores de Playwright y sus dependencias de SO
RUN playwright install --with-deps chromium

# Copiar el resto del código (main.py, carpetas, etc.)
COPY . .

# Comando para iniciar la aplicación en el puerto que Google espera (8080)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]