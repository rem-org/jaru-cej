#!/bin/sh

# Activar el entorno virtual
. /app/venv/bin/activate

# Esperar a que la base de datos esté disponible
until nc -z -v -w30 jaru-api-mysql-1 3306
do
  echo "Esperando a la base de datos..."
  sleep 5
done

# Ejecutar Prisma db push para sincronizar la base de datos
npx prisma db push --schema=/app/prisma/schema.prisma

# Iniciar la aplicación Python
python main.py