#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Build script ejecutándose..."

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones de base de datos
echo "Ejecutando migraciones de base de datos..."
flask db upgrade

# Opcional: Ejecutar el comando de seed aquí (¡con cuidado!)
# Si tu comando seed-db está diseñado para ser seguro de ejecutar múltiples veces 
# (es decir, no crea duplicados o errores si los datos ya existen), puedes añadirlo.
# Si no, es mejor ejecutarlo manualmente después del primer despliegue.
# echo "Ejecutando seed de base de datos..."
# flask seed-db 

echo "Build script finalizado."