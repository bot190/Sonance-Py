"""Client for the Sonance DSP amplifier HTTP API."""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping
from typing import Any, Self

import aiohttp

from ._wire_models import WireEqSettings, WireGeneralSettings, WireInOutSettings
from .models import (
    BasicStatus,
    EqSettings,
    GeneralSettings,
    InOutSettings,
    OnOff,
    Output,
    OutputGroup,
    OutputGroupState,
    SourceMode,
    StereoMode,
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


class SonanceOutput:
    """Live logical output control."""

    __slots__ = ("_amp", "_channel_indexes", "_group", "_index")

    def __init__(self, amp: SonanceDSP, index: int) -> None:
        self._amp = amp
        state = amp.in_out_settings.outputs[index]
        self._index = index
        self._group = state.output_group
        self._channel_indexes = tuple(channel.index for channel in state.channels)

    @property
    def _state(self) -> Output:
        try:
            state = self._amp.in_out_settings.outputs[self._index]
        except IndexError as err:
            msg = f"Output {self._index} is not available"
            raise ValueError(msg) from err
        channel_indexes = tuple(channel.index for channel in state.channels)
        if (
            state.output_group is not self._group
            or channel_indexes != self._channel_indexes
        ):
            msg = f"Output {self._index} is stale; refresh output references"
            raise ValueError(msg)
        return state

    @property
    def index(self) -> int:
        """Zero-based logical output index."""

        return self._state.index

    @property
    def number(self) -> int:
        """User-facing output number."""

        return self._state.number

    @property
    def channel_indexes(self) -> tuple[int, ...]:
        """Physical channel indexes controlled by this output."""

        return self._channel_indexes

    @property
    def output_group(self) -> OutputGroup:
        """Output group used for this logical output."""

        return self._state.output_group

    @property
    def stereo_mode(self) -> StereoMode:
        """Stereo or mono mode for this logical output."""

        return self._state.stereo_mode

    @property
    def group_state(self) -> OutputGroupState:
        """Runtime group state for this logical output."""

        return self._state.group_state

    def source_names(self) -> tuple[str, ...]:
        """Return source names available to this output."""

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

        return self.group_state.source_1

    async def set_source_1(self, value: int) -> InOutSettings:
        """Set the primary input source index."""

        return await self._amp._write_output_setting(self._state, "source-1", value)

    @property
    def source_2(self) -> int:
        """Secondary input source index."""

        return self.group_state.source_2

    async def set_source_2(self, value: int) -> InOutSettings:
        """Set the secondary input source index."""

        return await self._amp._write_output_setting(self._state, "source-2", value)

    @property
    def source_mode(self) -> SourceMode:
        """Source mixing mode."""

        return self.group_state.source_mode

    async def set_source_mode(self, value: SourceMode) -> InOutSettings:
        """Set the source mixing mode."""

        return await self._amp._write_output_setting(
            self._state, "mode-source", value
        )

    @property
    def volume(self) -> str:
        """Output volume."""

        return self.group_state.volume

    async def set_volume(self, value: int) -> InOutSettings:
        """Set the output volume."""

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
        return await self._amp._write_output_setting(
            self._state, "output-volume", value
        )

    @property
    def turn_on_volume(self) -> str:
        """Output turn-on volume."""

        return self.group_state.turn_on_volume

    async def set_turn_on_volume(self, value: int) -> InOutSettings:
        """Set the output turn-on volume."""

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
        return await self._amp._write_output_setting(
            self._state, "turn-on-volume", value
        )

    @property
    def maximum_volume(self) -> str:
        """Output maximum volume."""

        return self.group_state.maximum_volume

    async def set_maximum_volume(self, value: int) -> InOutSettings:
        """Set the output maximum volume."""

        maximum_volume = _validate_integer_value(value, "Maximum volume")
        if not MIN_VOLUME <= maximum_volume <= MAX_VOLUME:
            msg = "Maximum volume must be between -70 and 12"
            raise ValueError(msg)
        return await self._amp._write_output_setting(
            self._state, "maximum-volume", value
        )

    @property
    def gain_offset(self) -> str:
        """Output gain offset."""

        return self.group_state.gain_offset

    async def set_gain_offset(self, value: str | int | float) -> InOutSettings:
        """Set the output gain offset."""

        return await self._amp._write_output_setting(
            self._state, "gain-offset", value
        )

    @property
    def muted(self) -> OnOff:
        """Output mute state."""

        return self.group_state.muted

    async def set_muted(self, value: OnOff | bool) -> InOutSettings:
        """Set the output mute state."""

        return await self._amp._write_output_setting(self._state, "mute-volume", value)

    @property
    def dsp_preset(self) -> int:
        """DSP preset assigned to every channel in this output."""

        state = self._state
        dsp_presets = {channel.dsp_preset for channel in state.channels}
        if len(dsp_presets) != 1:
            msg = f"Output {self._index} has mixed DSP presets"
            raise RuntimeError(msg)
        return state.channels[0].dsp_preset

    async def set_dsp_preset(self, value: int) -> InOutSettings:
        """Set the DSP preset assigned to every channel in this output."""

        state = self._state
        for channel in state.channels[:-1]:
            await self._amp.write_in_out("dsp-preset", channel.index, value)
        return await self._amp.write_in_out(
            "dsp-preset", state.channels[-1].index, value
        )

    async def set_stereo_mode(self, value: StereoMode) -> InOutSettings:
        """Set this output's stereo or mono mode when the transition is valid."""

        state = self._state
        if value is state.stereo_mode:
            return self._amp.in_out_settings
        if value is StereoMode.STEREO:
            msg = "Use join() to form a stereo output from two mono outputs"
            raise ValueError(msg)

        if len(state.channels) != 2:
            channel = state.channels[0]
            return await self._amp.write_in_out(
                "stereo-or-mono", channel.index, StereoMode.MONO
            )

        left, right = state.channels
        split_group = self._amp._split_group_for(state.output_group)
        if split_group in {
            output.output_group for output in self._amp.in_out_settings.outputs
        }:
            msg = f"Output group {split_group} is already assigned to an output"
            raise ValueError(msg)
        await self._amp._copy_group_settings(state.output_group, split_group)
        await self._amp.write_in_out("output-group", right.index, split_group)
        await self._amp.write_in_out("stereo-or-mono", left.index, StereoMode.MONO)
        return await self._amp.write_in_out(
            "stereo-or-mono", right.index, StereoMode.MONO
        )

    async def join(self, members: Iterable[SonanceOutput]) -> InOutSettings:
        """Join member outputs to this output."""

        return await self._amp.join_outputs(self, members)


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
    def outputs(self) -> tuple[SonanceOutput, ...]:
        """Live logical output controls."""

        return tuple(
            SonanceOutput(self, output.index) for output in self.in_out_settings.outputs
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

    async def join_outputs(
        self,
        target: SonanceOutput,
        members: Iterable[SonanceOutput],
    ) -> InOutSettings:
        """Join member outputs to the target output."""

        target_state = target._state
        member_states = tuple(member._state for member in members)
        if not member_states:
            return self.in_out_settings

        seen_groups = {target_state.output_group}
        for member_state in member_states:
            if member_state.output_group in seen_groups:
                msg = "Cannot join an output to itself"
                raise ValueError(msg)
            seen_groups.add(member_state.output_group)

        if len(member_states) == 1 and self._can_form_stereo_pair(
            target_state, member_states[0]
        ):
            return await self._join_as_stereo_pair(target_state, member_states[0])

        for member_state in member_states:
            await self._copy_output_input_settings(target_state, member_state)
        return self.in_out_settings

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

    async def _join_as_stereo_pair(
        self,
        target: Output,
        member: Output,
    ) -> InOutSettings:
        target_channel = target.channels[0]
        member_channel = member.channels[0]
        left, right = sorted(
            (target_channel, member_channel), key=lambda channel: channel.index
        )

        await self.write_in_out("stereo-or-mono", left.index, StereoMode.STEREO)
        await self.write_in_out("stereo-or-mono", right.index, StereoMode.STEREO)
        if left.output_group is not target.output_group:
            await self.write_in_out("output-group", left.index, target.output_group)
        if right.output_group is not target.output_group:
            return await self.write_in_out(
                "output-group", right.index, target.output_group
            )
        return self.in_out_settings

    @staticmethod
    def _can_form_stereo_pair(target: Output, member: Output) -> bool:
        if len(target.channels) != 1 or len(member.channels) != 1:
            return False
        target_channel = target.channels[0]
        member_channel = member.channels[0]
        return (
            target_channel.pair_index == member_channel.pair_index
            and target_channel.index != member_channel.index
            and target_channel.stereo_mode is StereoMode.MONO
            and member_channel.stereo_mode is StereoMode.MONO
        )

    async def _copy_output_input_settings(
        self,
        source: Output,
        target: Output,
    ) -> None:
        source_state = source.group_state
        await self._write_output_setting(target, "source-1", source_state.source_1)
        await self._write_output_setting(target, "source-2", source_state.source_2)
        await self._write_output_setting(
            target, "mode-source", source_state.source_mode
        )

    async def _copy_group_settings(
        self,
        source_group: OutputGroup,
        target_group: OutputGroup,
    ) -> None:
        source_state = self.in_out_settings.output_group_states[source_group]
        await self._write_group_setting(target_group, "source-1", source_state.source_1)
        await self._write_group_setting(target_group, "source-2", source_state.source_2)
        await self._write_group_setting(
            target_group, "mode-source", source_state.source_mode
        )
        await self._write_group_setting(
            target_group, "maximum-volume", source_state.maximum_volume
        )
        await self._write_group_setting(
            target_group, "output-volume", source_state.volume
        )
        await self._write_group_setting(
            target_group, "turn-on-volume", source_state.turn_on_volume
        )
        await self._write_group_setting(
            target_group, "gain-offset", source_state.gain_offset
        )
        await self._write_group_setting(target_group, "mute-volume", source_state.muted)

    async def _write_group_setting(
        self,
        group: OutputGroup,
        name: str,
        value: str | int | float | bool,
    ) -> InOutSettings:
        return await self.write_in_out(name, self._group_index(group), value)

    async def _write_output_setting(
        self,
        output: Output,
        name: str,
        value: str | int | float | bool,
    ) -> InOutSettings:
        return await self.write_in_out(name, output.channels[0].index, value)

    @staticmethod
    def _group_index(group: OutputGroup) -> int:
        return list(OutputGroup).index(group)

    @classmethod
    def _split_group_for(cls, group: OutputGroup) -> OutputGroup:
        split_index = cls._group_index(group) + 4
        groups = list(OutputGroup)
        try:
            return groups[split_index]
        except IndexError as err:
            msg = f"Output group {group} cannot be split to a +4 mono group"
            raise ValueError(msg) from err

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
