"""Pydantic models for deserializing Sonance DSP HTTP API payloads."""

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    AutoOnMethod,
    BasicStatus,
    BridgeModeItem,
    CrossoverBand,
    CrossoverFilterType,
    CrossoverSettings,
    DelaySettings,
    EqSettings,
    GeneralSettings,
    InOutSettings,
    Limiter,
    OnOff,
    OutputGroup,
    OutputGroupItem,
    ParametricEqBand,
    PresetItem,
    SourceMode,
    StereoMode,
    TiltBand,
    TiltSettings,
)


class SonanceWireModel(BaseModel):
    """Base model for wire-format API payloads."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class WirePresetItem(SonanceWireModel):
    """Named preset option returned by the amplifier."""

    name: str
    value: str

    def to_model(self) -> PresetItem:
        """Convert the wire payload to a public dataclass."""

        return PresetItem(name=self.name, value=self.value)


class WireGeneralSettings(SonanceWireModel):
    """Payload returned by the general settings read endpoint."""

    ip_address: str = Field(alias="ip-address")
    ip_subnet_mask: str = Field(alias="ip-subnet-mask")
    dhcp_switch: OnOff = Field(alias="dhcp-switch")
    flash_power_switch: OnOff = Field(alias="flash-power-switch")
    power: OnOff
    standby_mode: OnOff = Field(alias="standby-mode")
    auto_on_method: AutoOnMethod = Field(alias="auto-on-method")
    auto_on_delay: str = Field(alias="auto-on-delay")
    amplifier_name: str = Field(alias="amplifier-name")
    dealer_name: str = Field(alias="dealer-name")
    amplifier_model: str = Field(alias="amplifier-model")
    installer_name: str = Field(alias="installer-name")
    customer_name: str = Field(alias="customer-name")
    installition_date: str = Field(alias="installition-date")
    firmware_version: str = Field(alias="firmware-version")
    serial_number: str = Field(alias="serial-number")

    def to_basic_status(self) -> BasicStatus:
        """Convert the wire payload to a compact public status dataclass."""

        return BasicStatus(
            power=self.power,
            firmware_version=self.firmware_version,
            amplifier_name=self.amplifier_name,
            serial_number=self.serial_number,
        )

    def to_model(self) -> GeneralSettings:
        """Convert the wire payload to a public dataclass."""

        return GeneralSettings(
            ip_address=self.ip_address,
            ip_subnet_mask=self.ip_subnet_mask,
            dhcp_switch=self.dhcp_switch,
            flash_power_switch=self.flash_power_switch,
            power=self.power,
            standby_mode=self.standby_mode,
            auto_on_method=self.auto_on_method,
            auto_on_delay=self.auto_on_delay,
            amplifier_name=self.amplifier_name,
            dealer_name=self.dealer_name,
            amplifier_model=self.amplifier_model,
            installer_name=self.installer_name,
            customer_name=self.customer_name,
            installition_date=self.installition_date,
            firmware_version=self.firmware_version,
            serial_number=self.serial_number,
        )


class WireOutputGroupItem(SonanceWireModel):
    """Output group option returned by the input/output settings endpoint."""

    name: str
    value: OutputGroup

    def to_model(self) -> OutputGroupItem:
        """Convert the wire payload to a public dataclass."""

        return OutputGroupItem(name=self.name, value=self.value)


class WireBridgeModeItem(SonanceWireModel):
    """Bridge mode option returned by the input/output settings endpoint."""

    name: str
    value: OnOff

    def to_model(self) -> BridgeModeItem:
        """Convert the wire payload to a public dataclass."""

        return BridgeModeItem(name=self.name, value=self.value)


class WireInOutSettings(SonanceWireModel):
    """Payload returned by the input/output settings read endpoint."""

    dsp_preset_items: list[WirePresetItem] = Field(alias="dsp-preset-items")
    input_names: list[str] = Field(alias="input-names")
    input_titles: list[str] = Field(alias="input-titles")
    output_titles: list[str] = Field(alias="output-titles")
    level_trim_dbs: list[str] = Field(alias="level-trim-dBs")
    output_names: list[str] = Field(alias="output-names")
    stereo_or_mono: list[StereoMode] = Field(alias="stereo-or-mono")
    dsp_presets: list[int] = Field(alias="dsp-presets")
    output_group_items: list[WireOutputGroupItem] = Field(alias="output-group-items")
    output_groups: list[OutputGroup] = Field(alias="output-groups")
    bridge_mode_items: list[WireBridgeModeItem] = Field(alias="bridge-mode-items")
    bridge_modes: list[OnOff] = Field(alias="bridge-modes")
    sources_1: list[int] = Field(alias="sources-1")
    sources_2: list[int] = Field(alias="sources-2")
    mode_sources: list[SourceMode] = Field(alias="mode-sources")
    output_volumes: list[str] = Field(alias="output-volumes")
    turn_on_volumes: list[str] = Field(alias="turn-on-volumes")
    maximum_volumes: list[str] = Field(alias="maximum-volumes")
    gain_offset: list[str] = Field(alias="gain-offset")
    mute_volumes: list[OnOff] = Field(alias="mute-volumes")

    def to_model(self) -> InOutSettings:
        """Convert the wire payload to a public dataclass."""

        return InOutSettings(
            dsp_preset_items=[item.to_model() for item in self.dsp_preset_items],
            input_names=self.input_names,
            input_titles=self.input_titles,
            output_titles=self.output_titles,
            level_trim_dbs=self.level_trim_dbs,
            output_names=self.output_names,
            stereo_or_mono=self.stereo_or_mono,
            dsp_presets=self.dsp_presets,
            output_group_items=[item.to_model() for item in self.output_group_items],
            output_groups=self.output_groups,
            bridge_mode_items=[item.to_model() for item in self.bridge_mode_items],
            bridge_modes=self.bridge_modes,
            sources_1=self.sources_1,
            sources_2=self.sources_2,
            mode_sources=self.mode_sources,
            output_volumes=self.output_volumes,
            turn_on_volumes=self.turn_on_volumes,
            maximum_volumes=self.maximum_volumes,
            gain_offset=self.gain_offset,
            mute_volumes=self.mute_volumes,
        )


class WireParametricEqBand(SonanceWireModel):
    """Single parametric EQ band."""

    enable_status: OnOff = Field(alias="enable-status")
    freq: int
    q: float
    gain: float

    def to_model(self) -> ParametricEqBand:
        """Convert the wire payload to a public dataclass."""

        return ParametricEqBand(
            enable_status=self.enable_status,
            freq=self.freq,
            q=self.q,
            gain=self.gain,
        )


class WireTiltBand(SonanceWireModel):
    """Low or high tilt EQ band."""

    on_or_off: OnOff = Field(alias="on-or-off")
    freq: int
    gain: float

    def to_model(self) -> TiltBand:
        """Convert the wire payload to a public dataclass."""

        return TiltBand(on_or_off=self.on_or_off, freq=self.freq, gain=self.gain)


class WireTiltSettings(SonanceWireModel):
    """Tilt control settings."""

    low: WireTiltBand
    high: WireTiltBand

    def to_model(self) -> TiltSettings:
        """Convert the wire payload to a public dataclass."""

        return TiltSettings(low=self.low.to_model(), high=self.high.to_model())


class WireCrossoverBand(SonanceWireModel):
    """Low-pass or high-pass crossover settings."""

    on_or_off: OnOff = Field(alias="on-or-off")
    freq: int
    filter_type: CrossoverFilterType = Field(alias="filter-type")

    def to_model(self) -> CrossoverBand:
        """Convert the wire payload to a public dataclass."""

        return CrossoverBand(
            on_or_off=self.on_or_off,
            freq=self.freq,
            filter_type=self.filter_type,
        )


class WireCrossoverSettings(SonanceWireModel):
    """Crossover settings."""

    low_pass: WireCrossoverBand = Field(alias="low-pass")
    high_pass: WireCrossoverBand = Field(alias="high-pass")

    def to_model(self) -> CrossoverSettings:
        """Convert the wire payload to a public dataclass."""

        return CrossoverSettings(
            low_pass=self.low_pass.to_model(),
            high_pass=self.high_pass.to_model(),
        )


class WireDelaySettings(SonanceWireModel):
    """Delay settings in the units returned by the amplifier."""

    seconds: float
    feet: float
    meters: float

    def to_model(self) -> DelaySettings:
        """Convert the wire payload to a public dataclass."""

        return DelaySettings(seconds=self.seconds, feet=self.feet, meters=self.meters)


class WireEqSettings(SonanceWireModel):
    """Payload returned by the EQ settings read endpoint."""

    output_names: list[str] = Field(alias="output-names")
    dsp_presets: list[int] = Field(alias="dsp-presets")
    output_titles: list[str] = Field(alias="output-titles")
    amplifier_model: str = Field(alias="amplifier-model")
    input_names: list[str] = Field(alias="input-names")
    source_select: list[int] = Field(alias="source-select")
    output_volumes: list[str] = Field(alias="output-volumes")
    mute_volumes: list[OnOff] = Field(alias="mute-volumes")
    eq_presets: list[WirePresetItem] = Field(alias="eq-presets")
    current_eq_preset: str = Field(alias="current-eq-preset")
    parametric_eq: list[WireParametricEqBand] = Field(alias="parametric-eq")
    tilt: WireTiltSettings
    crossover: WireCrossoverSettings
    limiter_limiters: Limiter = Field(alias="limiter-limiters")
    delay: WireDelaySettings

    def to_model(self) -> EqSettings:
        """Convert the wire payload to a public dataclass."""

        return EqSettings(
            output_names=self.output_names,
            dsp_presets=self.dsp_presets,
            output_titles=self.output_titles,
            amplifier_model=self.amplifier_model,
            input_names=self.input_names,
            source_select=self.source_select,
            output_volumes=self.output_volumes,
            mute_volumes=self.mute_volumes,
            eq_presets=[item.to_model() for item in self.eq_presets],
            current_eq_preset=self.current_eq_preset,
            parametric_eq=[band.to_model() for band in self.parametric_eq],
            tilt=self.tilt.to_model(),
            crossover=self.crossover.to_model(),
            limiter_limiters=self.limiter_limiters,
            delay=self.delay.to_model(),
        )
