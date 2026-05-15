"""Typer commands for Sonance DSP logical outputs."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer

from .amplifier import SonanceDSP, SonanceOutput
from .models import OnOff, SourceMode, StereoMode

output_app = typer.Typer(help="Output status and controls.")
SOURCE_VALUE_HELP = (
    "Source value: 1-4 for stereo outputs, or 1L/1R-4L/4R for mono outputs."
)
CliSourceValue = Annotated[str, typer.Argument(help=SOURCE_VALUE_HELP)]


def _hostname_from_context(ctx: typer.Context) -> str:
    hostname = getattr(ctx.obj, "hostname", None)
    if not isinstance(hostname, str):
        msg = "CLI context is not configured"
        raise typer.BadParameter(msg)
    return hostname


def _find_output_by_number(amp: SonanceDSP, number: int) -> SonanceOutput:
    for output in amp.outputs:
        if output.number == number:
            return output
    msg = f"No output {number}; available outputs: 1-{len(amp.outputs)}"
    raise typer.BadParameter(msg)


def _print_output(output: SonanceOutput) -> None:
    typer.echo(
        f"output {output.number}: "
        f"channels={output.channel_indexes} "
        f"stereo_mode={output.stereo_mode} "
        f"group={output.output_group}"
    )


def _format_source_value(source_id: int, output: SonanceOutput) -> str:
    if output.stereo_mode is StereoMode.STEREO:
        return str((source_id // 2) + 1)
    side = "L" if source_id % 2 == 0 else "R"
    return f"{(source_id // 2) + 1}{side}"


def _parse_source_value(value: str, output: SonanceOutput) -> int:
    normalized = value.strip().upper()
    if output.stereo_mode is StereoMode.STEREO:
        try:
            source_number = int(normalized)
        except ValueError as err:
            msg = "Stereo output source must be a number from 1 to 4"
            raise typer.BadParameter(msg) from err
        if not 1 <= source_number <= 4:
            msg = "Stereo output source must be a number from 1 to 4"
            raise typer.BadParameter(msg)
        return (source_number - 1) * 2

    if len(normalized) != 2 or normalized[0] not in "1234" or normalized[1] not in "LR":
        msg = "Mono output source must be one of 1L, 1R, 2L, 2R, 3L, 3R, 4L, 4R"
        raise typer.BadParameter(msg)
    source_number = int(normalized[0])
    side_offset = 0 if normalized[1] == "L" else 1
    return ((source_number - 1) * 2) + side_offset


def _print_output_sources(output: SonanceOutput) -> None:
    typer.echo(
        f"output {output.number} "
        f"source_1={_format_source_value(output.source_1, output)} "
        f"source_2={_format_source_value(output.source_2, output)}"
    )


@output_app.command("status")
def output_status_command(ctx: typer.Context, output_number: int) -> None:
    """Show status for one logical output."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            current_state = output.group_state
            typer.echo(f"output: {output.number}")
            typer.echo(f"channels: {output.channel_indexes}")
            typer.echo(f"stereo_mode: {output.stereo_mode}")
            typer.echo(f"group: {output.output_group}")
            typer.echo(
                f"source_1: {_format_source_value(current_state.source_1, output)}"
            )
            typer.echo(
                f"source_2: {_format_source_value(current_state.source_2, output)}"
            )
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
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            for output in amp.outputs:
                _print_output(output)

    asyncio.run(_run())


@output_app.command("mute")
def output_mute_command(ctx: typer.Context, output_number: int) -> None:
    """Mute a logical output."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_muted(OnOff.ON)
            typer.echo(f"output {output.number} muted={output.muted}")

    asyncio.run(_run())


@output_app.command("unmute")
def output_unmute_command(ctx: typer.Context, output_number: int) -> None:
    """Unmute a logical output."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
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
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_volume(value)
            typer.echo(f"output {output.number} volume={output.volume}")

    asyncio.run(_run())


@output_app.command("source")
def output_source_command(
    ctx: typer.Context,
    output_number: int,
    value: CliSourceValue,
) -> None:
    """Set the primary input source."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_source_1(_parse_source_value(value, output))
            typer.echo(
                f"output {output.number} "
                f"source_1={_format_source_value(output.source_1, output)}"
            )

    asyncio.run(_run())


@output_app.command("source-2")
def output_source_2_command(
    ctx: typer.Context,
    output_number: int,
    value: CliSourceValue,
) -> None:
    """Set the secondary input source."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_source_2(_parse_source_value(value, output))
            typer.echo(
                f"output {output.number} "
                f"source_2={_format_source_value(output.source_2, output)}"
            )

    asyncio.run(_run())


@output_app.command("sources")
def output_sources_command(
    ctx: typer.Context,
    output_number: int,
    source_1: CliSourceValue,
    source_2: CliSourceValue,
) -> None:
    """Set both input sources."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_source_1(_parse_source_value(source_1, output))
            await output.set_source_2(_parse_source_value(source_2, output))
            _print_output_sources(output)

    asyncio.run(_run())


@output_app.command("source-mode")
def output_source_mode_command(
    ctx: typer.Context,
    output_number: int,
    value: SourceMode,
) -> None:
    """Set source mixing mode."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_source_mode(value)
            typer.echo(f"output {output.number} source_mode={output.source_mode}")

    asyncio.run(_run())


@output_app.command("turn-on-volume")
def output_turn_on_volume_command(
    ctx: typer.Context,
    output_number: int,
    value: int,
) -> None:
    """Set logical output turn-on volume in dB."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_turn_on_volume(value)
            typer.echo(f"output {output.number} turn_on_volume={output.turn_on_volume}")

    asyncio.run(_run())


@output_app.command("maximum-volume")
def output_maximum_volume_command(
    ctx: typer.Context,
    output_number: int,
    value: int,
) -> None:
    """Set logical output maximum volume in dB."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_maximum_volume(value)
            typer.echo(f"output {output.number} maximum_volume={output.maximum_volume}")

    asyncio.run(_run())


@output_app.command("gain-offset")
def output_gain_offset_command(
    ctx: typer.Context,
    output_number: int,
    value: str,
) -> None:
    """Set logical output gain offset."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_gain_offset(value)
            typer.echo(f"output {output.number} gain_offset={output.gain_offset}")

    asyncio.run(_run())


@output_app.command("join")
def output_join_command(
    ctx: typer.Context,
    target_output_number: int,
    member_output_numbers: list[int],
) -> None:
    """Join one or more logical outputs to a target output."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            target = _find_output_by_number(amp, target_output_number)
            members = [
                _find_output_by_number(amp, member_number)
                for member_number in member_output_numbers
            ]
            await target.join(members)
            for output in amp.outputs:
                _print_output(output)

    asyncio.run(_run())


@output_app.command("split")
def output_split_command(ctx: typer.Context, output_number: int) -> None:
    """Split a stereo logical output into separate mono outputs."""

    async def _run() -> None:
        async with SonanceDSP(_hostname_from_context(ctx)) as amp:
            await amp.read_in_out()
            output = _find_output_by_number(amp, output_number)
            await output.set_stereo_mode(StereoMode.MONO)
            for updated_output in amp.outputs:
                _print_output(updated_output)

    asyncio.run(_run())
