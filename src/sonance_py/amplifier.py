"""Client for the Sonance DSP amplifier HTTP API."""

import random
from collections.abc import Mapping
from typing import Any, Self

import aiohttp

from ._wire_models import WireEqSettings, WireGeneralSettings, WireInOutSettings
from .models import (
    BasicStatus,
    EqSettings,
    GeneralSettings,
    InOutSettings,
    OnOff,
    OutputChannel,
    OutputGroup,
    OutputGroupState,
    SourceMode,
    StereoMode,
    StereoOutputPair,
)

JsonObject = dict[str, Any]
MIN_VOLUME = -70
MAX_VOLUME = 12


def _parse_cached_integer_value(value: str, name: str) -> int:
    """Parse an integer setting value from cached amplifier state."""

    try:
        return int(value)
    except ValueError as err:
        msg = f"{name} must be an integer"
        raise ValueError(msg) from err


def _validate_integer_value(value: int, name: str) -> int:
    """Validate an integer volume setting before sending it to the amplifier."""

    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{name} must be an integer"
        raise TypeError(msg)
    return value


class SonanceOutputChannel:
    """Live physical output channel control."""

    __slots__ = ("_amp", "_index")

    def __init__(self, amp: SonanceDSP, index: int) -> None:
        self._amp = amp
        self._index = index

    @property
    def _state(self) -> OutputChannel:
        return self._amp.in_out_settings.output_channels[self._index]

    @property
    def index(self) -> int:
        """Zero-based output channel index."""

        return self._state.index

    @property
    def number(self) -> int:
        """User-facing output pair number."""

        return self._state.number

    @property
    def side(self) -> str:
        """Channel side within its pair."""

        return self._state.side

    @property
    def pair_index(self) -> int:
        """Zero-based adjacent output pair index."""

        return self._state.pair_index

    @property
    def name(self) -> str:
        """Output channel name."""

        return self._state.name

    @property
    def title(self) -> str:
        """Output channel title."""

        return self._state.title

    @property
    def stereo_mode(self) -> StereoMode:
        """Stereo or mono mode for this output channel."""

        return self._state.stereo_mode

    async def set_stereo_mode(self, value: StereoMode) -> InOutSettings:
        """Set the stereo or mono mode for this output channel."""

        return await self._amp.write_in_out("stereo-or-mono", self.index, value)

    @property
    def dsp_preset(self) -> int:
        """DSP preset assigned to this output channel."""

        return self._state.dsp_preset

    async def set_dsp_preset(self, value: int) -> InOutSettings:
        """Set the DSP preset assigned to this output channel."""

        return await self._amp.write_in_out("dsp-preset", self.index, value)

    @property
    def output_group(self) -> OutputGroup:
        """Output group assigned to this output channel."""

        return self._state.output_group

    async def set_output_group(self, value: OutputGroup) -> InOutSettings:
        """Set the output group assigned to this output channel."""

        return await self._amp.write_in_out("output-group", self.index, value)


class SonanceOutputGroupState:
    """Live output group control."""

    __slots__ = ("_amp", "_group")

    def __init__(self, amp: SonanceDSP, group: OutputGroup) -> None:
        self._amp = amp
        self._group = group

    @property
    def _state(self) -> OutputGroupState:
        return self._amp.in_out_settings.output_group_states[self._group]

    @property
    def _index(self) -> int:
        return list(OutputGroup).index(self._group)

    @property
    def _mute_channel_index(self) -> int:
        for channel in self._amp.in_out_settings.output_channels:
            if channel.output_group is self._group:
                return channel.index

        msg = f"No output channel is assigned to output group {self._group}"
        raise RuntimeError(msg)

    @property
    def group(self) -> OutputGroup:
        """Output group identifier."""

        return self._group

    def source_names(self) -> tuple[str, ...]:
        """Return source names available to this output group."""

        return tuple(self._amp.in_out_settings.input_names)

    async def set_source_by_name(self, name: str) -> InOutSettings:
        """Set the primary input source by source name."""

        try:
            source_index = self._amp.in_out_settings.input_names.index(name)
        except ValueError as err:
            available_sources = ", ".join(self.source_names())
            msg = f"Unknown source name {name!r}; expected one of: {available_sources}"
            raise ValueError(msg) from err
        return await self.set_source_1(source_index)

    @property
    def source_1(self) -> int:
        """Primary input source index."""

        return self._state.source_1

    async def set_source_1(self, value: int) -> InOutSettings:
        """Set the primary input source index."""

        return await self._amp.write_in_out("source-1", self._index, value)

    @property
    def source_2(self) -> int:
        """Secondary input source index."""

        return self._state.source_2

    async def set_source_2(self, value: int) -> InOutSettings:
        """Set the secondary input source index."""

        return await self._amp.write_in_out("source-2", self._index, value)

    @property
    def source_mode(self) -> SourceMode:
        """Source mixing mode."""

        return self._state.source_mode

    async def set_source_mode(self, value: SourceMode) -> InOutSettings:
        """Set the source mixing mode."""

        return await self._amp.write_in_out("mode-source", self._index, value)

    @property
    def volume(self) -> str:
        """Output group volume."""

        return self._state.volume

    async def set_volume(self, value: int) -> InOutSettings:
        """Set the output group volume."""

        volume = _validate_integer_value(value, "Volume")
        maximum_volume = _parse_cached_integer_value(
            self.maximum_volume, "Maximum volume"
        )
        if not MIN_VOLUME <= volume <= maximum_volume:
            msg = (
                f"Volume must be between -70 and the current maximum volume "
                f"{self.maximum_volume}"
            )
            raise ValueError(msg)
        return await self._amp.write_in_out("output-volume", self._index, value)

    @property
    def turn_on_volume(self) -> str:
        """Output group turn-on volume."""

        return self._state.turn_on_volume

    async def set_turn_on_volume(self, value: int) -> InOutSettings:
        """Set the output group turn-on volume."""

        turn_on_volume = _validate_integer_value(value, "Turn-on volume")
        maximum_volume = _parse_cached_integer_value(
            self.maximum_volume, "Maximum volume"
        )
        if not MIN_VOLUME <= turn_on_volume <= maximum_volume:
            msg = (
                f"Turn-on volume must be between -70 and the current maximum volume "
                f"{self.maximum_volume}"
            )
            raise ValueError(msg)
        return await self._amp.write_in_out("turn-on-volume", self._index, value)

    @property
    def maximum_volume(self) -> str:
        """Output group maximum volume."""

        return self._state.maximum_volume

    async def set_maximum_volume(self, value: int) -> InOutSettings:
        """Set the output group maximum volume."""

        maximum_volume = _validate_integer_value(value, "Maximum volume")
        if not MIN_VOLUME <= maximum_volume <= MAX_VOLUME:
            msg = "Maximum volume must be between -70 and 12"
            raise ValueError(msg)
        return await self._amp.write_in_out("maximum-volume", self._index, value)

    @property
    def gain_offset(self) -> str:
        """Output group gain offset."""

        return self._state.gain_offset

    async def set_gain_offset(self, value: str | int | float) -> InOutSettings:
        """Set the output group gain offset."""

        return await self._amp.write_in_out("gain-offset", self._index, value)

    @property
    def muted(self) -> OnOff:
        """Output group mute state."""

        return self._state.muted

    async def set_muted(self, value: OnOff | bool) -> InOutSettings:
        """Set the output group mute state."""

        return await self._amp.write_in_out(
            "mute-volume", self._mute_channel_index, value
        )


class SonanceStereoOutputPair:
    """Live adjacent stereo output pair control."""

    __slots__ = ("_amp", "_index")

    def __init__(self, amp: SonanceDSP, index: int) -> None:
        self._amp = amp
        self._index = index

    @property
    def _state(self) -> StereoOutputPair:
        for pair in self._amp.in_out_settings.stereo_output_pairs:
            if pair.index == self._index:
                return pair
        msg = f"Stereo output pair {self._index} is not available"
        raise RuntimeError(msg)

    @property
    def index(self) -> int:
        """Zero-based stereo output pair index."""

        return self._state.index

    @property
    def number(self) -> int:
        """User-facing stereo output pair number."""

        return self._state.number

    @property
    def left(self) -> SonanceOutputChannel:
        """Left output channel in this pair."""

        return SonanceOutputChannel(self._amp, self._state.left.index)

    @property
    def right(self) -> SonanceOutputChannel:
        """Right output channel in this pair."""

        return SonanceOutputChannel(self._amp, self._state.right.index)

    @property
    def output_group(self) -> OutputGroup:
        """Shared output group for this pair."""

        return self._state.output_group

    async def set_output_group(self, value: OutputGroup) -> InOutSettings:
        """Set the shared output group for this pair."""

        state = self._state
        await self._amp.write_in_out("output-group", state.left.index, value)
        return await self._amp.write_in_out("output-group", state.right.index, value)

    @property
    def dsp_preset(self) -> int:
        """DSP preset assigned to both channels in this pair."""

        state = self._state
        if state.left.dsp_preset != state.right.dsp_preset:
            msg = f"Stereo output pair {self._index} has mixed DSP presets"
            raise RuntimeError(msg)
        return state.left.dsp_preset

    async def set_dsp_preset(self, value: int) -> InOutSettings:
        """Set the DSP preset assigned to both channels in this pair."""

        state = self._state
        await self._amp.write_in_out("dsp-preset", state.left.index, value)
        return await self._amp.write_in_out("dsp-preset", state.right.index, value)

    @property
    def stereo_mode(self) -> StereoMode:
        """Stereo or mono mode assigned to both channels in this pair."""

        state = self._state
        if state.left.stereo_mode != state.right.stereo_mode:
            msg = f"Stereo output pair {self._index} has mixed stereo modes"
            raise RuntimeError(msg)
        return state.left.stereo_mode

    async def set_stereo_mode(self, value: StereoMode) -> InOutSettings:
        """Set the stereo or mono mode assigned to both channels in this pair."""

        state = self._state
        await self._amp.write_in_out("stereo-or-mono", state.left.index, value)
        return await self._amp.write_in_out("stereo-or-mono", state.right.index, value)

    @property
    def group_state(self) -> SonanceOutputGroupState:
        """Live shared output group state for this pair."""

        return SonanceOutputGroupState(self._amp, self.output_group)

    @property
    def source_1(self) -> int:
        """Shared primary input source index."""

        return self.group_state.source_1

    def source_names(self) -> tuple[str, ...]:
        """Return source names available to this pair."""

        return self.group_state.source_names()

    async def set_source_1(self, value: int) -> InOutSettings:
        """Set the shared primary input source index."""

        return await self.group_state.set_source_1(value)

    async def set_source_by_name(self, name: str) -> InOutSettings:
        """Set the shared primary input source by source name."""

        return await self.group_state.set_source_by_name(name)

    @property
    def source_2(self) -> int:
        """Shared secondary input source index."""

        return self.group_state.source_2

    async def set_source_2(self, value: int) -> InOutSettings:
        """Set the shared secondary input source index."""

        return await self.group_state.set_source_2(value)

    @property
    def source_mode(self) -> SourceMode:
        """Shared source mixing mode."""

        return self.group_state.source_mode

    async def set_source_mode(self, value: SourceMode) -> InOutSettings:
        """Set the shared source mixing mode."""

        return await self.group_state.set_source_mode(value)

    @property
    def volume(self) -> str:
        """Shared output group volume."""

        return self.group_state.volume

    async def set_volume(self, value: int) -> InOutSettings:
        """Set the shared output group volume."""

        return await self.group_state.set_volume(value)

    @property
    def muted(self) -> OnOff:
        """Shared output group mute state."""

        return self.group_state.muted

    async def set_muted(self, value: OnOff | bool) -> InOutSettings:
        """Set the shared output group mute state."""

        return await self.group_state.set_muted(value)

    @property
    def turn_on_volume(self) -> str:
        """Shared output group turn-on volume."""

        return self.group_state.turn_on_volume

    async def set_turn_on_volume(self, value: int) -> InOutSettings:
        """Set the shared output group turn-on volume."""

        return await self.group_state.set_turn_on_volume(value)

    @property
    def maximum_volume(self) -> str:
        """Shared output group maximum volume."""

        return self.group_state.maximum_volume

    async def set_maximum_volume(self, value: int) -> InOutSettings:
        """Set the shared output group maximum volume."""

        return await self.group_state.set_maximum_volume(value)

    @property
    def gain_offset(self) -> str:
        """Shared output group gain offset."""

        return self.group_state.gain_offset

    async def set_gain_offset(self, value: str | int | float) -> InOutSettings:
        """Set the shared output group gain offset."""

        return await self.group_state.set_gain_offset(value)


class SonanceDSP:
    """Represent a Sonance DSP amplifier exposed over its HTTP interface."""

    def __init__(
        self,
        host: str,
        *,
        port: int = 80,
        session: aiohttp.ClientSession | None = None,
        request_timeout: float = 10,
    ) -> None:
        self.host = host
        self.port = port
        self._session = session
        self._owns_session = session is None
        self._request_timeout = aiohttp.ClientTimeout(total=request_timeout)
        self._general_settings: GeneralSettings | None = None
        self._in_out_settings: InOutSettings | None = None
        self._eq_settings: EqSettings | None = None

    async def __aenter__(self) -> Self:
        await self._get_session()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.close()

    @property
    def base_url(self) -> str:
        """Base HTTP URL for the amplifier."""

        return f"http://{self.host}:{self.port}"

    async def close(self) -> None:
        """Close the owned HTTP session, if this client created one."""

        if self._owns_session and self._session is not None:
            await self._session.close()
        self._session = None

    @property
    def general_settings(self) -> GeneralSettings:
        """Latest cached general settings state."""

        if self._general_settings is None:
            msg = "General settings are unavailable; call refresh() first"
            raise RuntimeError(msg)
        return self._general_settings

    @property
    def in_out_settings(self) -> InOutSettings:
        """Latest cached input/output settings state."""

        if self._in_out_settings is None:
            msg = "Input/output settings are unavailable; call refresh() first"
            raise RuntimeError(msg)
        return self._in_out_settings

    @property
    def eq_settings(self) -> EqSettings:
        """Latest cached EQ settings state."""

        if self._eq_settings is None:
            msg = "EQ settings are unavailable; call read_eq() first"
            raise RuntimeError(msg)
        return self._eq_settings

    @property
    def output_channels(self) -> tuple[SonanceOutputChannel, ...]:
        """Live physical output channel controls."""

        return tuple(
            SonanceOutputChannel(self, channel.index)
            for channel in self.in_out_settings.output_channels
        )

    @property
    def output_group_states(self) -> dict[OutputGroup, SonanceOutputGroupState]:
        """Live output group controls."""

        return {
            group: SonanceOutputGroupState(self, group)
            for group in self.in_out_settings.output_group_states
        }

    @property
    def stereo_output_pairs(self) -> tuple[SonanceStereoOutputPair, ...]:
        """Live stereo output pair controls."""

        return tuple(
            SonanceStereoOutputPair(self, pair.index)
            for pair in self.in_out_settings.stereo_output_pairs
        )

    async def refresh(self) -> None:
        """Fetch the latest amplifier state."""

        await self.read_general()
        await self.read_in_out()

    async def read_general(self) -> GeneralSettings:
        """Read the general settings state."""

        data = await self._request(
            {
                "page": "general-settings",
                "action": "read",
            }
        )
        self._general_settings = WireGeneralSettings.model_validate(data).to_model()
        return self._general_settings

    async def read_basic_status(self) -> BasicStatus:
        """Read a compact status view containing power and device identity fields."""

        data = await self._request(
            {
                "page": "general-settings",
                "action": "read",
            }
        )
        return WireGeneralSettings.model_validate(data).to_basic_status()

    async def write_general(
        self, name: str, value: str | int | float | bool
    ) -> GeneralSettings:
        """Write a general setting and return the refreshed state."""

        data = await self._request(
            {
                "page": "general-settings",
                "action": "write",
                "name": name,
                "value": self._format_value(value),
            }
        )
        self._general_settings = WireGeneralSettings.model_validate(data).to_model()
        return self._general_settings

    async def read_in_out(self) -> InOutSettings:
        """Read the input/output settings state."""

        data = await self._request(
            {
                "page": "in-out-settings",
                "action": "read",
            }
        )
        self._in_out_settings = WireInOutSettings.model_validate(data).to_model()
        return self._in_out_settings

    async def write_in_out(
        self,
        name: str,
        index: int,
        value: str | int | float | bool,
    ) -> InOutSettings:
        """Write an indexed input/output setting and return the refreshed state."""

        data = await self._request(
            {
                "page": "in-out-settings",
                "action": "write",
                "name": name,
                "index": index,
                "value": self._format_value(value),
            }
        )
        self._in_out_settings = WireInOutSettings.model_validate(data).to_model()
        return self._in_out_settings

    async def read_eq(self, preset: int = 0) -> EqSettings:
        """Read an EQ preset state."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "read",
                "eq-preset": preset,
            }
        )
        self._eq_settings = WireEqSettings.model_validate(data).to_model()
        return self._eq_settings

    async def write_eq(
        self,
        name: str,
        value: str | int | float | bool,
        *,
        preset: int = 0,
    ) -> EqSettings:
        """Write an EQ preset-level setting and return the refreshed state."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "write",
                "eq-preset": preset,
                "name": name,
                "value": self._format_value(value),
            }
        )
        self._eq_settings = WireEqSettings.model_validate(data).to_model()
        return self._eq_settings

    async def write_eq_indexed(
        self,
        name: str,
        index: int,
        value: str | int | float | bool,
        *,
        preset: int = 0,
        extra_params: Mapping[str, str | int | float | bool] | None = None,
    ) -> EqSettings:
        """Write an indexed EQ setting and return the refreshed state."""

        params: dict[str, str | int | float] = {
            "page": "eq-settings",
            "action": "write",
            "eq-preset": preset,
            "name": name,
            "index": index,
            "value": self._format_value(value),
        }
        if extra_params:
            params.update(
                {
                    key: self._format_value(extra_value)
                    for key, extra_value in extra_params.items()
                }
            )

        data = await self._request(params)
        self._eq_settings = WireEqSettings.model_validate(data).to_model()
        return self._eq_settings

    async def write_eq_in_out(
        self,
        name: str,
        index: int,
        value: str | int | float | bool,
    ) -> EqSettings:
        """Write an in/out setting through the EQ page API."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "write",
                "name": name,
                "index": index,
                "value": self._format_value(value),
            }
        )
        self._eq_settings = WireEqSettings.model_validate(data).to_model()
        return self._eq_settings

    async def do_eq(
        self,
        name: str,
        value: str | int | float | bool,
        *,
        preset: int = 0,
    ) -> EqSettings:
        """Execute an EQ action and return the refreshed state."""

        data = await self._request(
            {
                "page": "eq-settings",
                "action": "do",
                "eq-preset": preset,
                "name": name,
                "value": self._format_value(value),
            }
        )
        self._eq_settings = WireEqSettings.model_validate(data).to_model()
        return self._eq_settings

    async def _request(self, params: Mapping[str, str | int | float]) -> JsonObject:
        session = await self._get_session()
        request_params: dict[str, str | int | float] = dict(params)
        request_params["r"] = self._cache_buster()

        async with session.get(
            f"{self.base_url}/Web/Handler.php",
            params=request_params,
        ) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)

        if not isinstance(data, dict):
            msg = f"Expected JSON object from amplifier, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._request_timeout)
        return self._session

    @staticmethod
    def _format_value(value: str | int | float | bool) -> str | int | float:
        if isinstance(value, bool):
            return "on" if value else "off"
        return value

    @staticmethod
    def _cache_buster() -> float:
        # The web UI sends Math.random(); the endpoint only needs a changing value.
        return random.random()
