import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog.settings')

application = get_wsgi_application()

# --- Auto setup for migrations and superuser ---
try:
    from myblog.auto_setup import run_auto_setup
    run_auto_setup()
except Exception as e:
    print("⚠️ Auto setup skipped:", e)
