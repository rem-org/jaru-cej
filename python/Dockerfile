# Imagen base de Python
FROM python:3.11-slim

# Instalar Node.js (versión 16.x) y NPM
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar Prisma localmente dentro del proyecto
WORKDIR /app
COPY package.json ./
RUN npm install prisma@4.15.0

# Copiar los archivos de Prisma y el archivo .env
COPY prisma/ /app/prisma/
COPY app/.env /app/.env

# Instalar las dependencias de la aplicación Python
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación Python, incluyendo main.py
COPY app/ /app/

# Generar Prisma Client para Python
RUN npx prisma generate --schema=/app/prisma/schema.prisma

# Ejecutar el archivo principal de Python
CMD ["python", "main.py"]
