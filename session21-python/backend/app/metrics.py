"""Prometheus metrics: HTTP traffic plus a couple of GearLoan business counters."""
import time

from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests handled",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Time spent handling HTTP requests",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

LOANS_CREATED = Counter("gearloan_loans_created_total", "Loans created")
LOANS_RETURNED = Counter("gearloan_loans_returned_total", "Loans returned")
ITEMS_CREATED = Counter("gearloan_items_created_total", "Items added to the inventory")


class MetricsMiddleware:
    """Plain ASGI middleware that times every request.

    The path label uses the route template (e.g. /api/items/{item_id}) instead of
    the real URL, so we don't create a new time series for every item id.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_holder = {"code": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
            await send(message)

        start = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            path = getattr(route, "path", None) or "unmatched"
            method = scope.get("method", "GET")
            HTTP_LATENCY.labels(method, path).observe(time.perf_counter() - start)
            HTTP_REQUESTS.labels(method, path, str(status_holder["code"])).inc()
