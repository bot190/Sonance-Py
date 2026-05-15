# Sonance Py

Sonance Py is an async Python library for controlling Sonance DSP amplifiers,
including the DSP8-130 and related models that expose the same unauthenticated
HTTP interface.

The project is intended to support a future Home Assistant integration and a
Typer-based CLI for local development, testing, and troubleshooting.

## Current Status

This project is in early development. The initial client implements the basic
HTTP API shape discovered from the amplifier web UI:

- General settings read/write operations
- Input/output settings read/write operations
- EQ preset read/write/action operations
- Shared async HTTP session support

The CLI is not implemented yet.

## HTTP API

The amplifier web UI calls an unauthenticated endpoint at:

```text
/Web/Handler.php
```

The API uses query parameters for reads and writes, and returns JSON state
objects. The documented API shape is available in:

```text
Docs/http-api.md
```

## Basic Usage

```python
import asyncio

from sonance_py import SonanceDSP


async def main() -> None:
    async with SonanceDSP("192.168.1.50") as amp:
        general = await amp.read_general()
        print(general["amplifier-model"])


asyncio.run(main())
```

## Development

This project uses UV for dependency management and packaging.

Install dependencies:

```shell
uv sync
```

Run Ruff:

```shell
uv run ruff check .
uv run ruff format . --check
```

Build the package:

```shell
uv build
```

## Notes

- The device endpoint is unauthenticated HTTP.
- API indexes are zero-based because that is how the web UI addresses arrays.
- The project targets Python 3.14 and newer.
- Behavior still needs validation against real amplifier hardware and firmware
  versions.
