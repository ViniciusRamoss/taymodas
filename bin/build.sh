#!/usr/bin/env bash
# Build no Render: dependências, CSS do Tailwind e arquivos estáticos.
# Roda com DJANGO_SETTINGS_MODULE=config.settings.prod (definido no render.yaml).
set -o errexit -o nounset -o pipefail

pip install --quiet --upgrade uv
uv sync --frozen --no-dev
.venv/bin/python manage.py tailwind build
.venv/bin/python manage.py collectstatic --noinput
