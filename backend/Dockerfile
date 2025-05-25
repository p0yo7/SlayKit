# backend/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Copiar dependencias y código
COPY . .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puerto
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
