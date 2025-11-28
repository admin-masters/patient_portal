import time
from django.http import HttpResponseTooManyRequests
from django.core.cache import caches

class SimpleRateLimitMiddleware:
    """
    Very simple leaky-bucket: 60 req/min per IP on /hooks/*.
    Use local memory cache or configure 'default' to Redis in prod.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache = caches["default"]
        self.limit = 60
        self.window = 60

    def __call__(self, request):
        if request.path.startswith("/hooks/"):
            ip = request.META.get("REMOTE_ADDR", "unknown")
            key = f"rl:{ip}"
            cnt = self.cache.get(key, 0)
            if cnt >= self.limit:
                return HttpResponseTooManyRequests("Rate limit")
            if cnt == 0:
                self.cache.set(key, 1, timeout=self.window)
            else:
                self.cache.incr(key)
        return self.get_response(request)
