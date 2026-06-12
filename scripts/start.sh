#!/bin/bash
# scripts/start.sh — comando de arranque de Railway para Endonautas
set -e

# Configuración de persistencia para Content Studio (solo en Railway con volumen montado)
if [ -d "/app/persistent_data" ]; then
    echo "==> Railway volume detected at /app/persistent_data. Setting up symlinks..."
    mkdir -p /app/persistent_data/studio_data
    mkdir -p /app/persistent_data/contenido

    # Copiar archivos base si no existen en el volumen
    cp -rn /app/studio/data/* /app/persistent_data/studio_data/ 2>/dev/null || true
    cp -rn /app/contenido/* /app/persistent_data/contenido/ 2>/dev/null || true

    # Reemplazar carpetas con enlaces simbólicos al volumen persistente
    rm -rf /app/studio/data
    ln -s /app/persistent_data/studio_data /app/studio/data

    rm -rf /app/contenido
    ln -s /app/persistent_data/contenido /app/contenido
fi

echo "==> Running prepare_db"
python manage.py prepare_db

echo "==> Running migrations"
python manage.py migrate --fake-initial

echo "==> Running data migration"
python manage.py migrate_mirrorwork_data

echo "==> Syncing old reels/carruseles to JSON"
python manage.py sync_cgm_to_studio


echo "==> Running seeds"
python manage.py seed_wagtail
python manage.py seed_centro
python manage.py seed_missions
python manage.py seed_tests
python manage.py seed_mirror_kb
python manage.py seed_admin
python manage.py seed_packs

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Starting Content Studio Express Server (background)"
node studio/server.mjs &

echo "==> Starting Gunicorn Web Server"
exec gunicorn config.wsgi --workers 1 --timeout 300 --log-file -
