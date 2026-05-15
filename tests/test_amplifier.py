"""Tests for stateful SonanceDSP controls."""

import copy
import json
import unittest
from collections.abc import Mapping
from pathlib import Path

from sonance_py import OnOff, OutputGroup, SonanceDSP, SourceMode, StereoMode

GENERAL_DATA = Path(__file__).parents[1] / "Docs/example-data/general-settings.json"
IN_OUT_DATA = Path(__file__).parents[1] / "Docs/example-data/in-out-settings.json"

IN_OUT_WRITE_KEYS = {
    "dsp-preset": "dsp-presets",
    "gain-offset": "gain-offset",
    "maximum-volume": "maximum-volumes",
    "mode-source": "mode-sources",
    "mute-volume": "mute-volumes",
    "output-group": "output-groups",
    "output-volume": "output-volumes",
    "source-1": "sources-1",
    "source-2": "sources-2",
    "stereo-or-mono": "stereo-or-mono",
    "turn-on-volume": "turn-on-volumes",
}
STRING_VALUE_KEYS = {
    "gain-offset",
    "maximum-volume",
    "output-volume",
    "turn-on-volume",
}


class FakeSonanceDSP(SonanceDSP):
    """SonanceDSP with an in-memory HTTP API."""

    def __init__(self) -> None:
        super().__init__("example.local")
        self.general_data = json.loads(GENERAL_DATA.read_text())
        self.in_out_data = json.loads(IN_OUT_DATA.read_text())
        self.requests: list[dict[str, str | int | float]] = []

    async def _request(self, params: Mapping[str, str | int | float]) -> dict:
        request = dict(params)
        self.requests.append(request)
        page = request["page"]
        action = request["action"]
        if page == "general-settings":
            return copy.deepcopy(self.general_data)
        if page == "in-out-settings" and action == "read":
            return copy.deepcopy(self.in_out_data)
        if page == "in-out-settings" and action == "write":
            name = str(request["name"])
            index = int(request["index"])
            value: str | int | float = request["value"]
            if name in STRING_VALUE_KEYS:
                value = str(value)
            if name == "mute-volume":
                group = self.in_out_data["output-groups"][index]
                group_index = self.in_out_data["output-group-items"].index(
                    {"name": group.upper(), "value": group}
                )
                self.in_out_data[IN_OUT_WRITE_KEYS[name]][group_index] = value
            else:
                self.in_out_data[IN_OUT_WRITE_KEYS[name]][index] = value
            return copy.deepcopy(self.in_out_data)
        msg = f"Unexpected request: {request}"
        raise AssertionError(msg)


class TestSonanceDSPState(unittest.IsolatedAsyncioTestCase):
    """Validate cached state and live property controls."""

    async def asyncSetUp(self) -> None:
        self.amp = FakeSonanceDSP()
        await self.amp.refresh()

    async def test_refresh_populates_cached_state_and_live_controls(self) -> None:
        self.assertEqual(self.amp.general_settings.amplifier_model, "DSP8-130")
        self.assertEqual(len(self.amp.output_channels), 8)
        self.assertEqual(len(self.amp.output_group_states), 8)
        self.assertEqual(len(self.amp.stereo_output_pairs), 4)

    async def test_write_in_out_refreshes_cached_state(self) -> None:
        await self.amp.write_in_out("stereo-or-mono", 0, StereoMode.MONO)

        self.assertIs(self.amp.in_out_settings.stereo_or_mono[0], StereoMode.MONO)
        self.assertEqual(len(self.amp.stereo_output_pairs), 3)

    async def test_channel_write_methods_update_the_amplifier_state(self) -> None:
        channel = self.amp.output_channels[0]

        await channel.set_stereo_mode(StereoMode.MONO)
        await channel.set_dsp_preset(2)
        await channel.set_output_group(OutputGroup.B)

        self.assertIs(channel.stereo_mode, StereoMode.MONO)
        self.assertEqual(channel.dsp_preset, 2)
        self.assertIs(channel.output_group, OutputGroup.B)
        self.assertEqual(
            self.amp.requests[-3:],
            [
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "stereo-or-mono",
                    "index": 0,
                    "value": StereoMode.MONO,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "dsp-preset",
                    "index": 0,
                    "value": 2,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "output-group",
                    "index": 0,
                    "value": OutputGroup.B,
                },
            ],
        )

    async def test_output_group_write_methods_update_the_group_state(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        await group_state.set_source_1(2)
        await group_state.set_source_2(3)
        await group_state.set_source_mode(SourceMode.MIX)
        await group_state.set_volume(-45)
        await group_state.set_turn_on_volume(-45)
        await group_state.set_maximum_volume(12)
        await group_state.set_volume(12)
        await group_state.set_turn_on_volume(12)
        await group_state.set_muted(True)

        self.assertEqual(group_state.source_1, 2)
        self.assertEqual(group_state.source_2, 3)
        self.assertIs(group_state.source_mode, SourceMode.MIX)
        self.assertEqual(group_state.maximum_volume, "12")
        self.assertEqual(group_state.volume, "12")
        self.assertEqual(group_state.turn_on_volume, "12")
        self.assertIs(group_state.muted, OnOff.ON)

    async def test_output_group_mute_writes_channel_index_for_the_group(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.B]

        await group_state.set_muted(OnOff.OFF)

        self.assertIs(group_state.muted, OnOff.OFF)
        self.assertEqual(
            self.amp.requests[-1],
            {
                "page": "in-out-settings",
                "action": "write",
                "name": "mute-volume",
                "index": 2,
                "value": OnOff.OFF,
            },
        )

    async def test_output_group_volume_writes_group_index_integer_value(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        await group_state.set_volume(-50)

        self.assertEqual(group_state.volume, "-50")
        self.assertEqual(
            self.amp.requests[-1],
            {
                "page": "in-out-settings",
                "action": "write",
                "name": "output-volume",
                "index": 0,
                "value": -50,
            },
        )

    async def test_output_group_rejects_non_integer_volume_values(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        with self.assertRaisesRegex(TypeError, "Volume must be an integer"):
            await group_state.set_volume(-50.0)  # type: ignore[arg-type]

        with self.assertRaisesRegex(TypeError, "Volume must be an integer"):
            await group_state.set_volume("-50")  # type: ignore[arg-type]

    async def test_output_group_rejects_invalid_maximum_volume(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        with self.assertRaisesRegex(
            ValueError, "Maximum volume must be between -70 and 12"
        ):
            await group_state.set_maximum_volume(13)

        with self.assertRaisesRegex(
            ValueError, "Maximum volume must be between -70 and 12"
        ):
            await group_state.set_maximum_volume(-71)

    async def test_output_group_rejects_volume_above_current_maximum(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        with self.assertRaisesRegex(
            ValueError,
            "Volume must be between -70 and the current maximum volume -20",
        ):
            await group_state.set_volume(-19)

    async def test_output_group_rejects_volume_below_minimum(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        with self.assertRaisesRegex(
            ValueError,
            "Volume must be between -70 and the current maximum volume -20",
        ):
            await group_state.set_volume(-71)

    async def test_output_group_rejects_turn_on_volume_above_current_maximum(
        self,
    ) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        with self.assertRaisesRegex(
            ValueError,
            "Turn-on volume must be between -70 and the current maximum volume -20",
        ):
            await group_state.set_turn_on_volume(-19)

    async def test_output_group_rejects_turn_on_volume_below_minimum(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        with self.assertRaisesRegex(
            ValueError,
            "Turn-on volume must be between -70 and the current maximum volume -20",
        ):
            await group_state.set_turn_on_volume(-71)

    async def test_output_group_sets_source_by_name(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        self.assertEqual(
            group_state.source_names(),
            (
                "Input 1L",
                "Input 1R",
                "Input 2L",
                "Input 2R",
                "Input 3L",
                "Input 3R",
                "Input 4L",
                "Input 4R",
            ),
        )
        await group_state.set_source_by_name("Input 2R")

        self.assertEqual(group_state.source_1, 3)
        self.assertEqual(
            self.amp.requests[-1],
            {
                "page": "in-out-settings",
                "action": "write",
                "name": "source-1",
                "index": 0,
                "value": 3,
            },
        )

    async def test_output_group_rejects_unknown_source_name(self) -> None:
        group_state = self.amp.output_group_states[OutputGroup.A]

        with self.assertRaisesRegex(ValueError, "Unknown source name 'Missing'"):
            await group_state.set_source_by_name("Missing")

    async def test_stereo_pair_write_methods_update_both_channels(self) -> None:
        pair = self.amp.stereo_output_pairs[0]

        await pair.set_dsp_preset(3)
        await pair.set_source_1(2)
        await pair.set_source_mode(SourceMode.MIX)
        await pair.set_volume(-30)
        await pair.set_muted(OnOff.ON)

        self.assertEqual(pair.left.dsp_preset, 3)
        self.assertEqual(pair.right.dsp_preset, 3)
        self.assertEqual(pair.source_1, 2)
        self.assertIs(pair.source_mode, SourceMode.MIX)
        self.assertEqual(pair.volume, "-30")
        self.assertIs(pair.muted, OnOff.ON)

    async def test_stereo_pair_sets_source_by_name(self) -> None:
        pair = self.amp.stereo_output_pairs[0]

        self.assertEqual(pair.source_names(), pair.group_state.source_names())
        await pair.set_source_by_name("Input 3L")

        self.assertEqual(pair.source_1, 4)


if __name__ == "__main__":
    unittest.main()
