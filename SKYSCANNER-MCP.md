# Skyscanner MCP integration

This repo uses Skyscanner as an **independent cross-check** alongside the existing
Kiwi connector. Kiwi remains the primary source; Skyscanner can win when its
fully verified, bag-inclusive total is better.

## How it is wired

Claude Code reads the project-scoped `.mcp.json` in the repo root and launches
`tools/start_skyscanner_mcp.sh`.

The launcher deliberately does **not** copy third-party Skyscanner code into this
repo. On first use it:

1. clones `shadyvb/mcp-skyscanner` into the user's cache;
2. pins it to commit `331352f41dc2bd3623680a91889c67822c3a96e6`;
3. initialises its nested `vendor/skyscanner` submodule;
4. creates an isolated Python virtual environment;
5. installs the upstream requirements; and
6. starts the MCP server over stdio through `tools/skyscanner_mcp_lazy.py`.

The local lazy-start shim is deliberate. The pinned upstream server normally
constructs its `SkyScanner()` client while the MCP process is starting. That
constructor immediately performs PerimeterX network setup; if that request is
blocked or slow, Claude sees `CONNECTION_CLOSED` before it can call any MCP
tool. The shim leaves the upstream server code pinned and unchanged, but delays
creation of the real Skyscanner client until the first `search_airports` or
`search_flights` call. A network/CAPTCHA failure can then be returned as a tool
error instead of killing the whole MCP connection.

Later launches reuse the cache while still enforcing the pinned commit.

The MCP is configured for:

- locale: `en-AU`
- currency: `AUD`
- market: `AU`

## Quick setup check

From the repository root:

```bash
bash tools/start_skyscanner_mcp.sh --check
```

Expected result:

```text
Skyscanner MCP bootstrap OK
```

This verifies the clone, nested submodule, Python dependencies, and syntax of
the local lazy-start shim. It does not perform a live fare search.

In Claude Code, `/mcp` should show a connected server named `skyscanner` with
`search_airports` and `search_flights`.

## Network access required by a cloud routine

If the routine uses restricted outbound networking, the MCP bootstrap/search
needs these hosts available:

- `github.com` — clone the pinned MCP source and nested submodule
- `pypi.org` and `files.pythonhosted.org` — install Python dependencies
- `www.skyscanner.net` — airport and flight search endpoints
- `collector-pxrf8vapwa.perimeterx.net` — upstream client's PerimeterX mobile challenge

If the bootstrap check works but live searches fail, check the last two hosts
first. A live-search failure should now appear as a Skyscanner tool error rather
than closing the MCP connection during session initialisation.

## Important limitations

This is an unofficial, experimental MCP. Its upstream README says the client is
reverse-engineered, may violate Skyscanner's terms, and is not intended for
commercial/production use. Treat it as a second research source, not as a
single point of failure.

The MCP exposes flight-search prices but no checked-baggage input. A Skyscanner
headline price must therefore **never** be treated as this project's final
all-in price until the required 20 kg+ checked bag has been verified or added.

Known upstream errors include:

- `BannedWithCaptcha` — Skyscanner/PerimeterX blocked the request
- `Timeout` — the polling search exhausted its retries
- `InvalidDate`
- `AirportNotFound`

For the daily routine: retry one failed Skyscanner search at most once, then
continue with Kiwi and the existing web checks and record the failure in Nerd
Notes. Do not burn the run on repeated MCP retries.

## Updating the pin

Do not silently track upstream `main`. To upgrade, review the upstream diff,
test the new commit, then change `UPSTREAM_COMMIT` in
`tools/start_skyscanner_mcp.sh` deliberately.
