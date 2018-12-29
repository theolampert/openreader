from urllib.parse import urlparse

from starlette.config import Config

config = Config('.env')

REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379')
PORT = config('PORT', cast=int, default=8000)
DEBUG = config('DEBUG', cast=bool, default=False)

redis_url = urlparse(REDIS_URL)
