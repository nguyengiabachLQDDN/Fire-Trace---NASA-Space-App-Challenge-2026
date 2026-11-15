"""Vercel ASGI entrypoint for FireTrace."""
from __future__ import annotations

from urllib.parse import parse_qsl, unquote, urlencode

from app.api import app


class _VercelRewritePathMiddleware:
    """Restore original request path when Vercel rewrites traffic to /api/index.py."""

    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            qs = scope.get("query_string", b"").decode("latin-1")
            if "__vpath=" in qs:
                pairs = parse_qsl(qs, keep_blank_values=True)
                vpath = None
                kept = []
                for key, value in pairs:
                    if key == "__vpath" and vpath is None:
                        vpath = value
                    else:
                        kept.append((key, value))
                if vpath is not None:
                    clean_path = "/" + unquote(vpath).lstrip("/")
                    scope = dict(scope)
                    scope["path"] = clean_path
                    scope["raw_path"] = clean_path.encode("utf-8")
                    scope["query_string"] = urlencode(kept).encode("latin-1")
        await self.inner_app(scope, receive, send)


if not any(m.cls is _VercelRewritePathMiddleware for m in app.user_middleware):
    app.add_middleware(_VercelRewritePathMiddleware)

__all__ = ["app"]
