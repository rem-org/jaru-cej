# Imagen base de Python
FROM python:3.11-slim

# Instalar Node.js y NPM
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar Prisma localmente en el proyecto
RUN npm install -g prisma

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos necesarios
COPY python/package.json ./
COPY python/prisma/ /app/prisma/
COPY python/app/.env /app/.env
COPY python/app/requirements.txt .
COPY python/app/ /app/
COPY python/entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -r requirements.txt

# Crear y activar el entorno virtual
#RUN python -m venv /app/venv

# Actualizar pip en el entorno virtual
#RUN /app/venv/bin/pip install --upgrade pip

# Instalar dependencias de Python en el entorno virtual
#RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt



# Generar Prisma Client
#RUN npx prisma generate --schema=/app/prisma/schema.prisma

# Generate the Prisma client
RUN prisma generate

# Command to run your Python script
CMD ["python", "main.py"]
