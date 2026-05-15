"""Typer CLI for Sonance DSP status and output control."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any

import typer

from .amplifier import SonanceDSP, SonanceOutput
from .models import OnOff

app = typer.Typer(help="Control and inspect Sonance DSP amplifiers.")
output_app = typer.Typer(help="Output status and controls.")
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


def _find_output_by_number(amp: SonanceDSP, number: int) -> SonanceOutput:
    for output in amp.outputs:
        if output.number == number:
            return output
    msg = f"No output {number}; available outputs: 1-{len(amp.outputs)}"
    raise typer.BadParameter(msg)


@app.command("status")
def status_command(ctx: typer.Context) -> None:
    """Show high-level amplifier status."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            status = await amp.read_basic_status()
        _print_dataclass(status)

    asyncio.run(_run())


@output_app.command("status")
def output_status_command(ctx: typer.Context, output_number: int) -> None:
    """Show status for one logical output."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            current_state = output.group_state
            typer.echo(f"output: {output.number}")
            typer.echo(f"channels: {output.channel_indexes}")
            typer.echo(f"stereo_mode: {output.stereo_mode}")
            typer.echo(f"group: {output.output_group}")
            typer.echo(f"source_1: {current_state.source_1}")
            typer.echo(f"source_2: {current_state.source_2}")
            typer.echo(f"source_mode: {current_state.source_mode}")
            typer.echo(f"volume: {current_state.volume}")
            typer.echo(f"turn_on_volume: {current_state.turn_on_volume}")
            typer.echo(f"maximum_volume: {current_state.maximum_volume}")
            typer.echo(f"gain_offset: {current_state.gain_offset}")
            typer.echo(f"muted: {current_state.muted}")

    asyncio.run(_run())


@output_app.command("list")
def output_list_command(ctx: typer.Context) -> None:
    """List available logical outputs."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            for output in amp.outputs:
                typer.echo(
                    f"output {output.number}: "
                    f"channels={output.channel_indexes} "
                    f"stereo_mode={output.stereo_mode} "
                    f"group={output.output_group}"
                )

    asyncio.run(_run())


@output_app.command("mute")
def output_mute_command(ctx: typer.Context, output_number: int) -> None:
    """Mute a logical output."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_muted(OnOff.ON)
            typer.echo(f"output {output.number} muted={output.muted}")

    asyncio.run(_run())


@output_app.command("unmute")
def output_unmute_command(ctx: typer.Context, output_number: int) -> None:
    """Unmute a logical output."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_muted(OnOff.OFF)
            typer.echo(f"output {output.number} muted={output.muted}")

    asyncio.run(_run())


@output_app.command("volume")
def output_volume_command(
    ctx: typer.Context,
    output_number: int,
    value: int,
) -> None:
    """Set logical output volume in dB."""

    async def _run() -> None:
        context = _get_ctx(ctx)
        async with SonanceDSP(context.hostname) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_volume(value)
            typer.echo(f"output {output.number} volume={output.volume}")

    asyncio.run(_run())
