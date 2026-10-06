FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar salida directa a consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace/apps/analytics

# Instalar dependencias del sistema mínimas si fueran requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar paquetes analíticos
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Comando por defecto: ejecutar la suite de pruebas
CMD ["pytest", "-v", "tests/"]