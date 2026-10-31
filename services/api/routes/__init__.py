"""API route handlers for screening runs, traces, and feedback."""

try:
    from bidscreen_api.routes.runs import router
except ImportError:
    from routes.runs import router

__all__ = ["router"]
