#!/bin/bash
set -e
echo "==> Running migrations..."
python manage.py migrate --noinput
echo "==> Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@growthpath.com', 'admin123')
    print('Superuser created.')
else:
    u = User.objects.get(username='admin')
    u.set_password('admin123')
    u.save()
    print('Superuser password updated.')
"
echo "==> Collecting static files..."
python manage.py collectstatic --noinput
echo "==> Starting gunicorn..."
exec gunicorn growthpath.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --timeout 120 \
  --log-level info
