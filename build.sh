#!/usr/bin/env bash
# Build-скрипт для Render (и любого PaaS): ставит зависимости, собирает статику,
# применяет миграции и наполняет меню только если база пустая.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Меню-заготовка только при пустой базе — правки кафе в /admin/ не затираются.
python manage.py seed_menu --if-empty

# Суперюзер создаётся, только если задан DJANGO_SUPERUSER_PASSWORD в переменных.
if [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput || true
fi
