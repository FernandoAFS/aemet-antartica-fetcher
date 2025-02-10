"""
DB wrapper context for dependency injection
"""

from contextvars import ContextVar
from aemetAntartica.util.ctxvar import context_manager_factory


from .db_proxy import FetchPointDbProxy

"Injectable db client"
db_context_var: ContextVar[FetchPointDbProxy] = ContextVar("db_context_var")

"Safe async db client context setter"
async_db_context_var_ctx = context_manager_factory(db_context_var)
