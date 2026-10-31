"""OpenTelemetry tracing setup and helper utilities.

Exports spans to an OTLP gRPC endpoint (e.g. Jaeger or otel-collector).
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from bidscreen_common.correlation import get_correlation_id

_INITIALIZED = False


def init_tracer(service_name: str = "bidscreen", endpoint: Optional[str] = None) -> trace.Tracer:
    """Initialize OpenTelemetry tracer with BatchSpanProcessor and OTLP exporter."""
    global _INITIALIZED
    if _INITIALIZED:
        return trace.get_tracer(service_name)

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except Exception:
            # Fallback to console in development if endpoint fails
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        # Default in local testing without collector
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _INITIALIZED = True
    return trace.get_tracer(service_name)


def get_tracer(name: str = "bidscreen") -> trace.Tracer:
    """Return an OpenTelemetry Tracer instance."""
    return trace.get_tracer(name)


def traced(span_name: Optional[str] = None) -> Callable:
    """Decorator to create an OpenTelemetry span around an async or sync function."""

    def decorator(fn: Callable) -> Callable:
        name = span_name or fn.__qualname__
        tracer = get_tracer("bidscreen")

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(name) as span:
                    corr_id = get_correlation_id()
                    if corr_id:
                        span.set_attribute("correlation_id", corr_id)
                    if "run_id" in kwargs and kwargs["run_id"]:
                        span.set_attribute("run_id", str(kwargs["run_id"]))
                    return await fn(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(name) as span:
                    corr_id = get_correlation_id()
                    if corr_id:
                        span.set_attribute("correlation_id", corr_id)
                    if "run_id" in kwargs and kwargs["run_id"]:
                        span.set_attribute("run_id", str(kwargs["run_id"]))
                    return fn(*args, **kwargs)

            return sync_wrapper

    return decorator
