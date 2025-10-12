from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

BASE_DIR = Path(__file__).resolve().parent.parent.parent

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
