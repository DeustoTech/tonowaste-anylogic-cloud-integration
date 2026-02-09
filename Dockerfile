FROM python:3.9-slim

WORKDIR /app

# Copiar dependencias primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto por defecto de FastAPI
EXPOSE 8000

# Comando para arrancar el servicio
CMD ["uvicorn", "scripts.service_anylogic:app", "--host", "0.0.0.0", "--port", "8000"]