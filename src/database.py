"""
Supabase client singleton.

Usage:
    from src.database import get_client, get_admin_client, get_direct_connection

- get_client(jwt)            — Supabase client authenticated as the user (RLS enforced).
- get_admin_client()         — Supabase service-role client (BYPASSES RLS).
                               Use ONLY in migration scripts and admin-only tooling.
                               NEVER call from API route handlers or Celery workers.
- get_direct_connection()    — Raw psycopg2 connection via DATABASE_URL.
                               ONLY for queries that Supabase-py cannot express
                               (pgvector cosine similarity search). Caller MUST add
                               WHERE user_id = %s to every query manually.
"""

import logging

import psycopg2
import psycopg2.extras
from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from src.config import settings

logger = logging.getLogger(__name__)


def get_client(user_jwt: str) -> Client:
    """Return a Supabase client scoped to the authenticated user.

    The client uses the user's access token for Authorization so all queries are
    subject to RLS policies. We intentionally avoid ``auth.set_session()`` here:
    Supabase-py requires both access+refresh tokens for that flow, while API and
    worker code usually receives only the bearer access token.

    Args:
        user_jwt: The bearer token issued to the user by Supabase Auth.

    Returns:
        An authenticated Supabase Client.
    """
    if not user_jwt.strip():
        raise ValueError("user_jwt must be non-empty")

    options = SyncClientOptions(
        headers={"Authorization": f"Bearer {user_jwt}"},
        auto_refresh_token=False,
        persist_session=False,
    )
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY, options=options)
    return client


_STATEMENT_TIMEOUT_MS = 10_000  # 10 seconds max for any vector search query


def get_direct_connection() -> psycopg2.extensions.connection:
    """Return a raw psycopg2 connection via DATABASE_URL.

    Use ONLY for queries that the Supabase PostgREST client cannot express —
    specifically pgvector cosine similarity search (<=> operator).

    IMPORTANT: This connection bypasses RLS. Every query MUST include an
    explicit ``WHERE user_id = %s`` clause using a user_id from a validated JWT.
    Never pass user-supplied strings directly into query parameters — only
    validated user_id values from the auth dependency.

    The caller is responsible for closing the connection (use a try/finally or
    a context manager).

    Returns:
        An open psycopg2 connection with RealDictCursor as default cursor factory.
    """
    conn = psycopg2.connect(
        settings.DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
        options=f"-c statement_timeout={_STATEMENT_TIMEOUT_MS}",
    )
    return conn


def get_admin_client() -> Client:
    """Return a Supabase client using the service role key.

    WARNING: This client BYPASSES Row Level Security entirely.
    Permitted uses:
    - Database migration scripts
    - CI test harness setup/teardown
    - Scheduled maintenance jobs run outside the request lifecycle

    FORBIDDEN uses:
    - FastAPI route handlers
    - Celery worker task bodies
    - Any code path reachable by user input

    Returns:
        A service-role Supabase Client.
    """
    logger.warning(
        "Admin (service-role) Supabase client created — RLS is bypassed. "
        "Ensure this is only called from migration or admin scripts."
    )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
