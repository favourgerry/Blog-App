from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
import os

def run_auto_setup():
    try:
        # Run migrations automatically
        call_command('makemigrations', interactive=False)
        call_command('migrate', interactive=False)

        # Auto-create superuser
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"✅ Superuser '{username}' created successfully.")
        else:
            print(f"ℹ️ Superuser '{username}' already exists.")
    except OperationalError:
        print("⚠️ Database not ready yet.")
