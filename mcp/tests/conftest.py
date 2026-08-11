"""Pytest configuration.

Sets service environment variables before any application module is imported
so ``Settings()`` is constructed from a known state rather than from whatever
the developer happens to have exported. CI sets these in the workflow; this is
the local fallback.
"""

import os

os.environ.setdefault("MCP_HOST", "127.0.0.1")
os.environ.setdefault("MCP_PORT", "8001")
