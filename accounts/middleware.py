import time
from django.http import JsonResponse

class RateLimitMiddleware:
    MAX_REQUESTS = 100          # requests
    WINDOW = 60                # seconds

    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_log = {}

    def get_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def __call__(self, request):
        ip = self.get_ip(request)
        now = time.time()

        if ip not in self.requests_log:
            self.requests_log[ip] = []

        # Clean old timestamps
        self.requests_log[ip] = [
            ts for ts in self.requests_log[ip]
            if now - ts < self.WINDOW
        ]

        # Check limit
        if len(self.requests_log[ip]) >= self.MAX_REQUESTS:
            return JsonResponse(
                {"detail": "Too many requests. Please slow down."},
                status=429
            )

        # Add this request timestamp
        self.requests_log[ip].append(now)

        return self.get_response(request)
