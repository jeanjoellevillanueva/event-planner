"""
Settings package.

Import from development or production based on DJANGO_ENV environment variable.
"""

import os

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
