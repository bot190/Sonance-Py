"""Public dataclass models for Sonance DSP library APIs."""

from dataclasses import dataclass
from enum import StrEnum


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
