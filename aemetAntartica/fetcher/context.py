"""
Common variables injected throught context.
"""

from contextvars import ContextVar
from aemetAntartica.util.ctxvar import context_manager_factory

import httpx


"Injectable httpx client"
async_httpx_client_var: ContextVar[httpx.AsyncClient] = ContextVar(
    "httpx_client_context"
)

"Safe async httpx client context setter"
async_httpx_client_ctx = context_manager_factory(async_httpx_client_var)

"Injectable httpx context"
api_key_var: ContextVar[str] = ContextVar("httpx_client_context")

"Safe api key context setter"
api_key_ctx = context_manager_factory(api_key_var)
