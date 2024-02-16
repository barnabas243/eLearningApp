"""
WSGI config for eLearningApp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eLearningApp.settings')

# Replace the default Django WSGI application with Gunicorn
from django.core.wsgi import get_wsgi_application
from django.conf import settings

# Define the WSGI application callable for Gunicorn
def get_django_application():
    # Load the Django application
    django_application = get_wsgi_application()
    return django_application

# Use Gunicorn's recommended settings
def run_gunicorn():
    bind = '0.0.0.0:8000'  # Bind to all network interfaces on port 8000
    workers = 3  # Use 3 Gunicorn worker processes
    timeout = 30  # Set a timeout of 30 seconds

    # Run Gunicorn with the specified settings
    from gunicorn.app.base import BaseApplication

    class DjangoApplication(BaseApplication):
        def __init__(self, application, options=None):
            self.options = options or {}
            self.application = application
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key, value)

        def load(self):
            return self.application

    options = {
        'bind': bind,
        'workers': workers,
        'timeout': timeout,
    }

    DjangoApplication(get_django_application(), options).run()

# Run Gunicorn
if __name__ == '__main__':
    run_gunicorn()
