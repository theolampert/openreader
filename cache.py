from settings import redis_url
import redis


class Cache():
    store = {}

    def get(self, key):
        try:
            return self.store[key]
        except KeyError:
            return None

    def set(self, key, value):
        self.store[key] = value


try:
    cache = redis.Redis(
        host=redis_url.hostname,
        port=redis_url.port,
        password=redis_url.password,
        db=0
    )
    cache.client_list()
except redis.ConnectionError:
    cache = Cache()
