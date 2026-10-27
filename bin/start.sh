#!/usr/bin/env bash
# Start no Render. O plano free não tem pre-deploy nem shell, então as migrations e a criação
# do admin rodam aqui, a cada subida (as duas são idempotentes).
set -o errexit -o nounset -o pipefail

.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py ensure_admin
exec .venv/bin/gunicorn config.wsgi \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 2 \
  --timeout 60 \
  --access-logfile -
