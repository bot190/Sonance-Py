"""Typer CLI for Sonance DSP status and output control."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any

import typer

from .amplifier import SonanceDSP
from .output_cli import output_app

app = typer.Typer(help="Control and inspect Sonance DSP amplifiers.")
app.add_typer(output_app, name="output")


class CliContext:
    """Runtime CLI configuration."""

    def __init__(self, hostname: str) -> None:
        self.hostname = hostname


@app.callback()
def main(
    ctx: typer.Context,
    hostname: str = typer.Option(
        ..., "--hostname", help="Sonance amplifier hostname or IP address."
    ),
) -> None:
    """Set connection options used by all subcommands."""

    ctx.obj = CliContext(hostname)


def _get_ctx(context: typer.Context) -> CliContext:
    if not isinstance(context.obj, CliContext):
        msg = "CLI context is not configured"
        raise typer.BadParameter(msg)
    return context.obj


def _print_dataclass(model: Any) -> None:
    payload = asdict(model)
    for key, value in payload.items():
        typer.echo(f"{key}: {value}")


@app.command("status")
def status_command(ctx: typer.Context) -> None:
    """Show high-level amplifier status."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            status = await amp.read_basic_status()
        _print_dataclass(status)

    asyncio.run(_run())


@app.command("sources")
def sources_command(ctx: typer.Context) -> None:
    """List available CLI source values and input names."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            settings = await amp.read_in_out()
        for index in range(0, len(settings.input_names), 2):
            source_number = (index // 2) + 1
            typer.echo(
                f"{source_number}: "
                f"{settings.input_names[index]} / {settings.input_names[index + 1]}"
            )
            typer.echo(f"{source_number}L: {settings.input_names[index]}")
            typer.echo(f"{source_number}R: {settings.input_names[index + 1]}")

    asyncio.run(_run())


@app.command("eqs")
def eqs_command(ctx: typer.Context) -> None:
    """List available EQ preset names."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            settings = await amp.read_eq()
        for preset in settings.eq_presets:
            typer.echo(f"{preset.value}: {preset.name}")

    asyncio.run(_run())
