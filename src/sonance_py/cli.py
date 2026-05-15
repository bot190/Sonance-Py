"""Typer CLI for Sonance DSP status and group control."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any

import typer

from .amplifier import SonanceDSP
from .models import OnOff, OutputGroup

app = typer.Typer(help="Control and inspect Sonance DSP amplifiers.")
group_app = typer.Typer(help="Group status and controls.")
app.add_typer(group_app, name="group")


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


@group_app.command("status")
def group_status_command(ctx: typer.Context, group: OutputGroup) -> None:
    """Show status for one output group."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            current_state = amp.output_group_states[group]
            typer.echo(f"group: {current_state.group}")
            typer.echo(f"source_1: {current_state.source_1}")
            typer.echo(f"source_2: {current_state.source_2}")
            typer.echo(f"source_mode: {current_state.source_mode}")
            typer.echo(f"volume: {current_state.volume}")
            typer.echo(f"turn_on_volume: {current_state.turn_on_volume}")
            typer.echo(f"maximum_volume: {current_state.maximum_volume}")
            typer.echo(f"gain_offset: {current_state.gain_offset}")
            typer.echo(f"muted: {current_state.muted}")

    asyncio.run(_run())


@group_app.command("mute")
def group_mute_command(ctx: typer.Context, group: OutputGroup) -> None:
    """Mute an output group."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            updated = await amp.output_group_states[group].set_muted(OnOff.ON)
            typer.echo(
                f"group {group} muted={updated.output_group_states[group].muted}"
            )

    asyncio.run(_run())


@group_app.command("unmute")
def group_unmute_command(ctx: typer.Context, group: OutputGroup) -> None:
    """Unmute an output group."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            updated = await amp.output_group_states[group].set_muted(OnOff.OFF)
            typer.echo(
                f"group {group} muted={updated.output_group_states[group].muted}"
            )

    asyncio.run(_run())


@group_app.command("volume")
def group_volume_command(ctx: typer.Context, group: OutputGroup, value: int) -> None:
    """Set output-group volume in dB."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            updated = await amp.output_group_states[group].set_volume(value)
            typer.echo(
                f"group {group} volume={updated.output_group_states[group].volume}"
            )

    asyncio.run(_run())
