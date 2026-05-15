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
        self.assertEqual(len(self.amp.outputs), 4)
        self.assertEqual(self.amp.outputs[0].channel_indexes, (0, 1))
        self.assertEqual(self.amp.outputs[3].channel_indexes, (6, 7))
        self.assertTrue(
            all(request["action"] == "read" for request in self.amp.requests)
        )

    async def test_write_in_out_refreshes_cached_state(self) -> None:
        await self.amp.write_in_out("stereo-or-mono", 0, StereoMode.MONO)

        self.assertIs(self.amp.in_out_settings.stereo_or_mono[0], StereoMode.MONO)
        self.assertEqual(len(self.amp.outputs), 4)

    async def test_output_write_methods_update_the_amplifier_state(self) -> None:
        output = self.amp.outputs[0]

        await output.set_dsp_preset(2)
        await output.set_source_1(2)
        await output.set_source_mode(SourceMode.MIX)

        self.assertEqual(output.dsp_preset, 2)
        self.assertEqual(output.source_1, 2)
        self.assertIs(output.source_mode, SourceMode.MIX)
        self.assertEqual(
            self.amp.requests[-4:],
            [
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
                    "name": "dsp-preset",
                    "index": 1,
                    "value": 2,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "source-1",
                    "index": 0,
                    "value": 2,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "mode-source",
                    "index": 0,
                    "value": SourceMode.MIX,
                },
            ],
        )

    async def test_output_runtime_write_methods_update_group_state(self) -> None:
        output = self.amp.outputs[0]

        await output.set_source_1(2)
        await output.set_source_2(3)
        await output.set_source_mode(SourceMode.MIX)
        await output.set_volume(-45)
        await output.set_turn_on_volume(-45)
        await output.set_maximum_volume(12)
        await output.set_volume(12)
        await output.set_turn_on_volume(12)
        await output.set_muted(True)

        self.assertEqual(output.source_1, 2)
        self.assertEqual(output.source_2, 3)
        self.assertIs(output.source_mode, SourceMode.MIX)
        self.assertEqual(output.maximum_volume, "12")
        self.assertEqual(output.volume, "12")
        self.assertEqual(output.turn_on_volume, "12")
        self.assertIs(output.muted, OnOff.ON)

    async def test_output_mute_writes_first_channel_index(self) -> None:
        output = self.amp.outputs[1]

        await output.set_muted(OnOff.OFF)

        self.assertIs(output.muted, OnOff.OFF)
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

    async def test_output_volume_writes_first_channel_index(self) -> None:
        output = self.amp.outputs[1]

        await output.set_volume(-50)

        self.assertEqual(output.volume, "-50")
        self.assertEqual(
            self.amp.requests[-1],
            {
                "page": "in-out-settings",
                "action": "write",
                "name": "output-volume",
                "index": 2,
                "value": -50,
            },
        )

    async def test_output_rejects_non_integer_volume_values(self) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(TypeError, "Volume must be an integer"):
            await output.set_volume(-50.0)  # type: ignore[arg-type]

        with self.assertRaisesRegex(TypeError, "Volume must be an integer"):
            await output.set_volume("-50")  # type: ignore[arg-type]

    async def test_output_rejects_invalid_maximum_volume(self) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(
            ValueError, "Maximum volume must be between -70 and 12"
        ):
            await output.set_maximum_volume(13)

        with self.assertRaisesRegex(
            ValueError, "Maximum volume must be between -70 and 12"
        ):
            await output.set_maximum_volume(-71)

    async def test_output_rejects_volume_above_current_maximum(self) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(
            ValueError,
            "Volume must be between -70 and the current maximum volume -20",
        ):
            await output.set_volume(-19)

    async def test_output_rejects_volume_below_minimum(self) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(
            ValueError,
            "Volume must be between -70 and the current maximum volume -20",
        ):
            await output.set_volume(-71)

    async def test_output_rejects_turn_on_volume_above_current_maximum(
        self,
    ) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(
            ValueError,
            "Turn-on volume must be between -70 and the current maximum volume -20",
        ):
            await output.set_turn_on_volume(-19)

    async def test_output_rejects_turn_on_volume_below_minimum(self) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(
            ValueError,
            "Turn-on volume must be between -70 and the current maximum volume -20",
        ):
            await output.set_turn_on_volume(-71)

    async def test_output_sets_source_by_name(self) -> None:
        output = self.amp.outputs[0]

        self.assertEqual(
            output.source_names(),
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
        await output.set_source_by_name("Input 2R")

        self.assertEqual(output.source_1, 3)
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

    async def test_output_rejects_unknown_source_name(self) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(ValueError, "Unknown source name 'Missing'"):
            await output.set_source_by_name("Missing")

    async def test_split_copies_group_settings_before_channel_assignment(self) -> None:
        output = self.amp.outputs[0]

        await output.set_stereo_mode(StereoMode.MONO)

        self.assertEqual(len(self.amp.outputs), 5)
        self.assertEqual(self.amp.outputs[4].channel_indexes, (1,))
        self.assertIs(self.amp.outputs[4].output_group, OutputGroup.E)
        self.assertIs(self.amp.outputs[0].stereo_mode, StereoMode.MONO)
        self.assertIs(self.amp.outputs[4].stereo_mode, StereoMode.MONO)
        self.assertEqual(self.amp.outputs[4].source_1, self.amp.outputs[0].source_1)
        self.assertEqual(self.amp.outputs[4].source_2, self.amp.outputs[0].source_2)
        self.assertEqual(self.amp.outputs[4].volume, self.amp.outputs[0].volume)
        self.assertEqual(
            self.amp.requests[-11:],
            [
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "source-1",
                    "index": 1,
                    "value": 0,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "source-2",
                    "index": 1,
                    "value": 0,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "mode-source",
                    "index": 1,
                    "value": SourceMode.OFF,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "maximum-volume",
                    "index": 1,
                    "value": "-20",
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "output-volume",
                    "index": 1,
                    "value": "-60",
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "turn-on-volume",
                    "index": 1,
                    "value": "-83",
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "gain-offset",
                    "index": 1,
                    "value": "0",
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "mute-volume",
                    "index": 1,
                    "value": OnOff.OFF,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "output-group",
                    "index": 1,
                    "value": OutputGroup.E,
                },
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
                    "name": "stereo-or-mono",
                    "index": 1,
                    "value": StereoMode.MONO,
                },
            ],
        )

    async def test_join_adjacent_mono_outputs_forms_stereo_pair(self) -> None:
        await self.amp.outputs[0].set_stereo_mode(StereoMode.MONO)
        target = self.amp.outputs[0]
        member = self.amp.outputs[4]

        await target.join([member])

        self.assertEqual(len(self.amp.outputs), 4)
        self.assertEqual(self.amp.outputs[0].channel_indexes, (0, 1))
        self.assertIs(self.amp.outputs[0].output_group, OutputGroup.A)
        self.assertIs(self.amp.outputs[0].stereo_mode, StereoMode.STEREO)
        self.assertEqual(
            self.amp.requests[-3:],
            [
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "stereo-or-mono",
                    "index": 0,
                    "value": StereoMode.STEREO,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "stereo-or-mono",
                    "index": 1,
                    "value": StereoMode.STEREO,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "output-group",
                    "index": 1,
                    "value": OutputGroup.A,
                },
            ],
        )

    async def test_join_separate_outputs_copies_target_input_settings(self) -> None:
        target = self.amp.outputs[0]
        member = self.amp.outputs[1]
        member_volume = member.volume
        member_muted = member.muted
        await target.set_source_1(2)
        await target.set_source_2(3)
        await target.set_source_mode(SourceMode.MIX)

        await target.join([member])

        self.assertEqual(member.volume, member_volume)
        self.assertIs(member.muted, member_muted)
        updated_member = self.amp.outputs[1]
        self.assertEqual(updated_member.source_1, 2)
        self.assertEqual(updated_member.source_2, 3)
        self.assertIs(updated_member.source_mode, SourceMode.MIX)
        self.assertEqual(
            self.amp.requests[-3:],
            [
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "source-1",
                    "index": 2,
                    "value": 2,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "source-2",
                    "index": 2,
                    "value": 3,
                },
                {
                    "page": "in-out-settings",
                    "action": "write",
                    "name": "mode-source",
                    "index": 2,
                    "value": SourceMode.MIX,
                },
            ],
        )

    async def test_join_rejects_self_join(self) -> None:
        output = self.amp.outputs[0]

        with self.assertRaisesRegex(ValueError, "Cannot join an output to itself"):
            await output.join([output])

    async def test_stale_output_reference_is_rejected(self) -> None:
        output = self.amp.outputs[0]
        await output.set_stereo_mode(StereoMode.MONO)

        with self.assertRaisesRegex(ValueError, "stale"):
            output.number


if __name__ == "__main__":
    unittest.main()
