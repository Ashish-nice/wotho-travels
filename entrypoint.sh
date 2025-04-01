set -e

python manage.py flush --no-input
python manage.py migrate

# Create default site if it doesn't exist
python -c "
from django.contrib.sites.models import Site
Site.objects.get_or_create(
    id=1,
    defaults={'domain': 'localhost:8000', 'name': 'Wotho Travels'}
)
"

exec "$@"