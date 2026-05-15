"""Public dataclass models for Sonance DSP library APIs."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class OnOff(StrEnum):
    """On/off values used throughout the API."""

    ON = "on"
    OFF = "off"


class AutoOnMethod(StrEnum):
    """Auto-on method values returned by general settings."""

    TRIGGER = "trigger"
    TRIGGER_GREEN = "trigger_green"
    IP = "ip"
    IR = "ir"
    AUDIO = "audio"
    CONSOLE = "console"


class OutputGroup(StrEnum):
    """Output group identifiers."""

    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"


class StereoMode(StrEnum):
    """Stereo or mono output mode."""

    STEREO = "stereo"
    MONO = "mono"


class SourceMode(StrEnum):
    """Source mixing mode."""

    MUTE = "mute"
    OFF = "off"
    MIX = "mix"


class CrossoverFilterType(StrEnum):
    """Crossover filter type values."""

    BW_6DB = "bw-6db"
    BW_12DB = "bw-12db"
    BW_18DB = "bw-18db"
    BW_24DB = "bw-24db"


class Limiter(StrEnum):
    """Limiter values returned by EQ settings."""

    OFF = "off"
    MINUS_3DB = "-3db"
    MINUS_6DB = "-6db"
    MINUS_12DB = "-12db"


@dataclass(frozen=True, slots=True)
class PresetItem:
    """Named preset option returned by the amplifier."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class GeneralSettings:
    """General settings state returned by the amplifier."""

    ip_address: str
    ip_subnet_mask: str
    dhcp_switch: OnOff
    flash_power_switch: OnOff
    power: OnOff
    standby_mode: OnOff
    auto_on_method: AutoOnMethod
    auto_on_delay: str
    amplifier_name: str
    dealer_name: str
    amplifier_model: str
    installer_name: str
    customer_name: str
    installition_date: str
    firmware_version: str
    serial_number: str


@dataclass(frozen=True, slots=True)
class BasicStatus:
    """Basic amplifier status fields for quick health/state checks."""

    power: OnOff
    firmware_version: str
    amplifier_name: str
    serial_number: str


@dataclass(frozen=True, slots=True)
class OutputGroupItem:
    """Output group option returned by the input/output settings endpoint."""

    name: str
    value: OutputGroup


@dataclass(frozen=True, slots=True)
class BridgeModeItem:
    """Bridge mode option returned by the input/output settings endpoint."""

    name: str
    value: OnOff


@dataclass(frozen=True, slots=True)
class OutputChannel:
    """Physical amplifier output channel configuration."""

    index: int
    number: int
    side: Literal["left", "right"]
    pair_index: int
    name: str
    title: str
    stereo_mode: StereoMode
    dsp_preset: int
    output_group: OutputGroup


@dataclass(frozen=True, slots=True)
class OutputGroupState:
    """Runtime state controlled through an output group."""

    group: OutputGroup
    source_1: int
    source_2: int
    source_mode: SourceMode
    volume: str
    turn_on_volume: str
    maximum_volume: str
    gain_offset: str
    muted: OnOff


@dataclass(frozen=True, slots=True)
class Output:
    """Logical controllable amplifier output."""

    index: int
    number: int
    channels: tuple[OutputChannel, ...]
    output_group: OutputGroup
    group_state: OutputGroupState
    stereo_mode: StereoMode


@dataclass(frozen=True, slots=True)
class InOutSettings:
    """Input/output settings state returned by the amplifier."""

    dsp_preset_items: list[PresetItem]
    input_names: list[str]
    input_titles: list[str]
    output_titles: list[str]
    level_trim_dbs: list[str]
    output_names: list[str]
    stereo_or_mono: list[StereoMode]
    dsp_presets: list[int]
    output_group_items: list[OutputGroupItem]
    output_groups: list[OutputGroup]
    bridge_mode_items: list[BridgeModeItem]
    bridge_modes: list[OnOff]
    sources_1: list[int]
    sources_2: list[int]
    mode_sources: list[SourceMode]
    output_volumes: list[str]
    turn_on_volumes: list[str]
    maximum_volumes: list[str]
    gain_offset: list[str]
    mute_volumes: list[OnOff]

    def _output_group_state(self, group: OutputGroup, index: int) -> OutputGroupState:
        return OutputGroupState(
            group=group,
            source_1=self.sources_1[index],
            source_2=self.sources_2[index],
            source_mode=self.mode_sources[index],
            volume=self.output_volumes[index],
            turn_on_volume=self.turn_on_volumes[index],
            maximum_volume=self.maximum_volumes[index],
            gain_offset=self.gain_offset[index],
            muted=self.mute_volumes[index],
        )

    @property
    def output_channels(self) -> tuple[OutputChannel, ...]:
        """Physical output channels derived from channel-indexed settings."""

        return tuple(
            OutputChannel(
                index=index,
                number=(index // 2) + 1,
                side="left" if index % 2 == 0 else "right",
                pair_index=index // 2,
                name=name,
                title=self.output_titles[index],
                stereo_mode=self.stereo_or_mono[index],
                dsp_preset=self.dsp_presets[index],
                output_group=self.output_groups[index],
            )
            for index, name in enumerate(self.output_names)
        )

    @property
    def output_group_states(self) -> dict[OutputGroup, OutputGroupState]:
        """Runtime output group states derived from output channel slots."""

        channel_indexes_by_group = {
            channel.output_group: channel.index
            for channel in reversed(self.output_channels)
        }
        return {
            group: self._output_group_state(
                group,
                channel_indexes_by_group.get(group, index),
            )
            for index, group in enumerate(OutputGroup)
        }

    @property
    def outputs(self) -> tuple[Output, ...]:
        """Logical controllable outputs derived from channel and group state."""

        channels = self.output_channels
        grouped_channels: dict[OutputGroup, tuple[OutputChannel, ...]] = {}
        consumed_channel_indexes: set[int] = set()

        for left, right in zip(channels[::2], channels[1::2], strict=False):
            if (
                left.stereo_mode is StereoMode.STEREO
                and right.stereo_mode is StereoMode.STEREO
                and left.output_group is right.output_group
            ):
                grouped_channels[left.output_group] = (left, right)
                consumed_channel_indexes.update({left.index, right.index})

        for channel in channels:
            if channel.index not in consumed_channel_indexes:
                grouped_channels[channel.output_group] = (channel,)

        outputs: list[Output] = []
        for group in OutputGroup:
            output_channels = grouped_channels.get(group)
            if output_channels is None:
                continue
            outputs.append(
                Output(
                    index=len(outputs),
                    number=len(outputs) + 1,
                    channels=output_channels,
                    output_group=group,
                    group_state=self._output_group_state(
                        group, output_channels[0].index
                    ),
                    stereo_mode=(
                        StereoMode.STEREO
                        if len(output_channels) == 2
                        else StereoMode.MONO
                    ),
                )
            )
        return tuple(outputs)


@dataclass(frozen=True, slots=True)
class ParametricEqBand:
    """Single parametric EQ band."""

    enable_status: OnOff
    freq: int
    q: float
    gain: float


@dataclass(frozen=True, slots=True)
class TiltBand:
    """Low or high tilt EQ band."""

    on_or_off: OnOff
    freq: int
    gain: float


@dataclass(frozen=True, slots=True)
class TiltSettings:
    """Tilt control settings."""

    low: TiltBand
    high: TiltBand


@dataclass(frozen=True, slots=True)
class CrossoverBand:
    """Low-pass or high-pass crossover settings."""

    on_or_off: OnOff
    freq: int
    filter_type: CrossoverFilterType


@dataclass(frozen=True, slots=True)
class CrossoverSettings:
    """Crossover settings."""

    low_pass: CrossoverBand
    high_pass: CrossoverBand


@dataclass(frozen=True, slots=True)
class DelaySettings:
    """Delay settings in the units returned by the amplifier."""

    seconds: float
    feet: float
    meters: float


@dataclass(frozen=True, slots=True)
class EqSettings:
    """EQ settings state returned by the amplifier."""

    output_names: list[str]
    dsp_presets: list[int]
    output_titles: list[str]
    amplifier_model: str
    input_names: list[str]
    source_select: list[int]
    output_volumes: list[str]
    mute_volumes: list[OnOff]
    eq_presets: list[PresetItem]
    current_eq_preset: str
    parametric_eq: list[ParametricEqBand]
    tilt: TiltSettings
    crossover: CrossoverSettings
    limiter_limiters: Limiter
    delay: DelaySettings
