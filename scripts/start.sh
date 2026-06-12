#!/bin/bash
# scripts/start.sh — comando de arranque de Railway para Endonautas
set -e

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
