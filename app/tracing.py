from __future__ import annotations

import os
from contextlib import contextmanager
from functools import wraps
from typing import Any

try:
    from langfuse import get_client, observe, propagate_attributes

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    def get_client():
        return _NoopClient()

    @contextmanager
    def propagate_attributes(**kwargs: Any):
        yield


class _NoopObservation:
    def update(self, **_: Any) -> None:
        return None


class _NoopClient:
    def update_current_span(self, **_: Any) -> None:
        return None

    def update_current_generation(self, **_: Any) -> None:
        return None

    @contextmanager
    def start_as_current_observation(self, **_: Any):
        yield _NoopObservation()


def get_langfuse_client():
    return get_client() if tracing_enabled() else _NoopClient()


def observe_if_enabled(*args: Any, **kwargs: Any):
    """Avoid queuing unauthorized exports when local mode has no credentials."""
    def decorator(func):
        observed = observe(*args, **kwargs)(func)

        @wraps(func)
        def wrapper(*func_args: Any, **func_kwargs: Any):
            if tracing_enabled():
                return observed(*func_args, **func_kwargs)
            return func(*func_args, **func_kwargs)

        return wrapper

    return decorator


@contextmanager
def start_observation(client: Any, **kwargs: Any):
    """Open a v4 child observation, tolerating lightweight test clients."""
    start = getattr(client, "start_as_current_observation", None)
    if callable(start):
        with start(**kwargs) as observation:
            yield observation
        return

    yield _NoopObservation()


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )
