# Skyscanner MCP integration

This repo uses Skyscanner as an **independent cross-check** alongside the existing
Kiwi connector. Kiwi remains the primary source; Skyscanner can win when its
fully verified, bag-inclusive total is better.

## How it is wired

Claude Code reads the project-scoped `.mcp.json` in the repo root and launches
`tools/start_skyscanner_mcp.sh`.

The runtime source for the MCP is copied directly into this repository at
`vendor/mcp-skyscanner/`. That is intentionally simpler and more reliable than
cloning another repository during every fresh Claude Routine session.

The vendored snapshot is pinned to:

- MCP wrapper: `shadyvb/mcp-skyscanner@331352f41dc2bd3623680a91889c67822c3a96e6`
- Skyscanner client: `irrisolto/skyscanner@cb0946b2f6107128ee7968ec4525e4f167dd4945`

The second commit is the exact submodule commit referenced by the pinned MCP
wrapper. Only the source required to run airport/flight search is copied; large
APK artefacts and examples are deliberately omitted.

The local `mcp_server.py` has one project-specific modification: the real
`SkyScanner()` client is created lazily on the first tool call instead of while
the MCP process is starting. The upstream client performs PerimeterX network
setup in its constructor, and the first live Routine test showed that eager
startup could close the MCP connection before Claude finished its handshake.

The MCP is configured for `en-AU`, `AUD`, and market `AU`.

## What still happens at runtime

The launcher creates/reuses an isolated Python virtual environment in the user
cache and installs these packages if they are missing:

- `fastmcp`
- `curl_cffi`
- `typeguard`
- `orjson`

It does **not** clone GitHub repositories or initialise git submodules.

## Quick setup check

From the repository root:

```bash
bash tools/start_skyscanner_mcp.sh --check
```

Expected result:

```text
Skyscanner MCP local copy OK
```

This checks the Python dependencies and syntax of the local MCP/client. It does
not make a live Skyscanner request.

## Network access required

For first-time Python package installation:

- `pypi.org`
- `files.pythonhosted.org`

For live Skyscanner searches:

- `www.skyscanner.net`
- `collector-pxrf8vapwa.perimeterx.net`

A live-search problem should now be returned by the Skyscanner tool instead of
closing the MCP connection during session initialisation.

## Important limitations

This remains an unofficial, experimental integration. The upstream MCP README
states that the underlying client is reverse-engineered, may violate
Skyscanner's terms, and is not intended for commercial/production use.

The MCP does not guarantee that its headline fare includes the project's
required checked 20 kg+ bag. A Skyscanner fare must therefore be verified or
adjusted to the same all-in basis as Kiwi before it can enter the table or price
log.

Known upstream errors include `BannedWithCaptcha`, `Timeout`, `InvalidDate`
and `AirportNotFound`. Retry one failed Skyscanner search at most once, then
continue with Kiwi + web and record the failure in Nerd Notes.

## Third-party licensing and provenance

The copied source remains third-party code. The MCP wrapper declares GPL-3.0
and the vendored Skyscanner client is GPL-3.0. The full GPL text is preserved
at `vendor/mcp-skyscanner/LICENSE-GPL-3.0.md`; exact source commits and the
local modification are documented in
`vendor/mcp-skyscanner/THIRD_PARTY_NOTICE.md`.

## Updating the copy

Do not silently track either upstream `main`. Review a specific upstream
commit, replace the vendored files deliberately, update the commit hashes in
`THIRD_PARTY_NOTICE.md`, and run the MCP check before merging.
