# Imagen base de Python
FROM python:3.11-slim

# Instalar Node.js y NPM
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos necesarios
COPY python/package.json ./
COPY python/prisma/ /app/prisma/
COPY python/app/.env /app/.env
COPY python/app/requirements.txt .
COPY python/app/ /app/
COPY python/entrypoint.sh /entrypoint.sh

# Crear y activar el entorno virtual
RUN python -m venv /app/venv

# Actualizar pip en el entorno virtual
RUN /app/venv/bin/pip install --upgrade pip

# Instalar dependencias de Python en el entorno virtual
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Instalar Prisma localmente en el proyecto
RUN npm install prisma@4.15.0 prisma-client-py

# Instalar Prisma Client para Python en el entorno virtual
RUN /app/venv/bin/pip install prisma-client

# Generar Prisma Client
RUN npx prisma generate --schema=/app/prisma/schema.prisma

# Dar permisos de ejecución al script de entrada
RUN chmod +x /entrypoint.sh

# Establecer el entrypoint
ENTRYPOINT ["/entrypoint.sh"]
