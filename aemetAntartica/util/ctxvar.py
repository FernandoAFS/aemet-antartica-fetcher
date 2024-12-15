from contextvars import ContextVar
from contextlib import contextmanager


def context_manager_factory[T](var: ContextVar[T]):
    "Auto generated context manager for context-var set and reset"

    @contextmanager
    def context_manager(value: T):
        token = var.set(value)
        yield
        var.reset(token)

    return context_manager
