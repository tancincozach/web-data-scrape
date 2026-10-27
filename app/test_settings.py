import os

# Set this before importing production settings, which require a secret key.
if not os.environ.get("DJANGO_SECRET_KEY"):
    os.environ["DJANGO_SECRET_KEY"] = "test-only-secret-key"

from .settings import *  # noqa: E402,F401,F403
from .settings import REST_FRAMEWORK  # noqa: E402

SECRET_KEY = "test-only-secret-key"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "web-data-scrape-tests",
    }
}

# Keep the real hasher in tests so credential verification exercises the
# production code path rather than a weaker test-only hasher.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]

# Keep normal tests below the production rate limit.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {"scrape": "1000/min"},
}
