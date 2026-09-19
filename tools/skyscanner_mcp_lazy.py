#!/usr/bin/env python3
"""Start the pinned third-party Skyscanner MCP without doing network I/O at startup.

The upstream mcp_server.py constructs SkyScanner() at module import time. That
constructor immediately contacts PerimeterX, so a blocked/slow network can kill
the MCP process before Claude finishes the MCP handshake and surfaces only
CONNECTION_CLOSED.

This shim temporarily replaces skyscanner.SkyScanner with a lazy proxy, then
executes the pinned upstream server unchanged. The real SkyScanner client is
created only when a Skyscanner tool is actually called, where the upstream
tool's existing error handling can return a structured failure instead of
taking down the MCP connection.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    source = os.environ.get("SKYSCANNER_MCP_SOURCE")
    if not source:
        raise SystemExit("SKYSCANNER_MCP_SOURCE is not set")

    source_dir = Path(source).resolve()
    vendor_dir = source_dir / "vendor" / "skyscanner"
    upstream_server = source_dir / "mcp_server.py"

    if not vendor_dir.is_dir():
        raise SystemExit(f"Skyscanner vendor submodule missing: {vendor_dir}")
    if not upstream_server.is_file():
        raise SystemExit(f"Skyscanner MCP server missing: {upstream_server}")

    sys.path.insert(0, str(vendor_dir))

    import skyscanner as skyscanner_package

    real_skyscanner = skyscanner_package.SkyScanner

    class LazySkyScanner:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._args = args
            self._kwargs = kwargs
            self._client: Any | None = None

        def _get_client(self) -> Any:
            if self._client is None:
                # Only now do we trigger the upstream PerimeterX/Skyscanner
                # network setup. If it fails, the MCP tool call catches the
                # exception and the server process remains available.
                self._client = real_skyscanner(*self._args, **self._kwargs)
            return self._client

        def __getattr__(self, name: str) -> Any:
            return getattr(self._get_client(), name)

    skyscanner_package.SkyScanner = LazySkyScanner

    # Execute the pinned upstream server as __main__. Its own mcp.run() remains
    # authoritative; this shim changes only when the network client is created.
    runpy.run_path(str(upstream_server), run_name="__main__")


if __name__ == "__main__":
    main()
