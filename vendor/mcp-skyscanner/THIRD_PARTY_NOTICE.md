# Third-party notice

This directory contains a vendored snapshot of third-party GPL-3.0 source used
by the Japan Flight Optimiser's Skyscanner MCP integration.

## Sources

- MCP server: https://github.com/shadyvb/mcp-skyscanner
  - commit: 331352f41dc2bd3623680a91889c67822c3a96e6
- Skyscanner client: https://github.com/irrisolto/skyscanner
  - commit: cb0946b2f6107128ee7968ec4525e4f167dd4945

The second repository is the exact submodule commit referenced by the first
repository at the pinned MCP commit.

## Files copied

The MCP server runtime files and the Skyscanner Python package required for
flight/airport search are copied. Large APK artefacts and examples are omitted
because they are not required to run this MCP.

## Local modification

`mcp_server.py` is modified so `SkyScanner()` is instantiated lazily on the
first tool call rather than during MCP process startup. This avoids performing
PerimeterX/Skyscanner network I/O before Claude completes the MCP stdio
handshake. No other intended behavioural change is made.

The original source is experimental and reverse-engineered; see
`UPSTREAM-README.md` for its disclaimer.

License: GNU GPL v3. The full text is in `LICENSE-GPL-3.0.md`.
