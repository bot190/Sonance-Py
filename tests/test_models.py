"""Tests for public dataclass convenience models."""

import unittest
from dataclasses import replace
from pathlib import Path

from sonance_py import OnOff, OutputGroup, SourceMode, StereoMode
from sonance_py._wire_models import WireInOutSettings
from sonance_py.models import InOutSettings

EXAMPLE_DATA = Path(__file__).parents[1] / "Docs/example-data/in-out-settings.json"


def load_in_out_settings() -> InOutSettings:
    """Load the bundled input/output settings example."""

    return WireInOutSettings.model_validate_json(EXAMPLE_DATA.read_text()).to_model()


class TestInOutSettingsModels(unittest.TestCase):
    """Validate derived input/output settings model views."""

    def test_output_channels(self) -> None:
        settings = load_in_out_settings()

        channels = settings.output_channels

        self.assertEqual(len(channels), 8)
        self.assertEqual(channels[0].index, 0)
        self.assertEqual(channels[0].number, 1)
        self.assertEqual(channels[0].side, "left")
        self.assertEqual(channels[0].pair_index, 0)
        self.assertEqual(channels[0].name, "Output 1L")
        self.assertEqual(channels[0].title, "1 LEFT")
        self.assertIs(channels[0].stereo_mode, StereoMode.STEREO)
        self.assertEqual(channels[0].dsp_preset, 0)
        self.assertIs(channels[0].output_group, OutputGroup.A)
        self.assertEqual(channels[1].index, 1)
        self.assertEqual(channels[1].number, 1)
        self.assertEqual(channels[1].side, "right")
        self.assertEqual(channels[1].pair_index, 0)
        self.assertIs(channels[1].output_group, OutputGroup.A)
        self.assertEqual(channels[7].index, 7)
        self.assertEqual(channels[7].number, 4)
        self.assertEqual(channels[7].side, "right")
        self.assertEqual(channels[7].pair_index, 3)
        self.assertIs(channels[7].output_group, OutputGroup.D)

    def test_output_group_states(self) -> None:
        settings = load_in_out_settings()

        group_states = settings.output_group_states

        self.assertEqual(set(group_states), set(OutputGroup))
        self.assertIs(group_states[OutputGroup.A].group, OutputGroup.A)
        self.assertEqual(group_states[OutputGroup.A].source_1, 0)
        self.assertEqual(group_states[OutputGroup.A].source_2, 0)
        self.assertIs(group_states[OutputGroup.A].source_mode, SourceMode.OFF)
        self.assertEqual(group_states[OutputGroup.A].volume, "-60")
        self.assertEqual(group_states[OutputGroup.A].turn_on_volume, "-83")
        self.assertEqual(group_states[OutputGroup.A].maximum_volume, "-20")
        self.assertEqual(group_states[OutputGroup.A].gain_offset, "0")
        self.assertIs(group_states[OutputGroup.A].muted, OnOff.OFF)
        self.assertIs(group_states[OutputGroup.C].group, OutputGroup.C)
        self.assertEqual(group_states[OutputGroup.C].volume, "-70")
        self.assertIs(group_states[OutputGroup.C].muted, OnOff.ON)

    def test_outputs_derives_stereo_pairs(self) -> None:
        settings = load_in_out_settings()

        outputs = settings.outputs

        self.assertEqual(len(outputs), 4)
        self.assertEqual(outputs[0].index, 0)
        self.assertEqual(outputs[0].number, 1)
        self.assertEqual([channel.index for channel in outputs[0].channels], [0, 1])
        self.assertIs(outputs[0].output_group, OutputGroup.A)
        self.assertIs(outputs[0].stereo_mode, StereoMode.STEREO)
        self.assertEqual(outputs[3].index, 3)
        self.assertEqual(outputs[3].number, 4)
        self.assertEqual([channel.index for channel in outputs[3].channels], [6, 7])
        self.assertIs(outputs[3].output_group, OutputGroup.D)

    def test_outputs_derives_split_pair_as_fifth_output(self) -> None:
        settings = load_in_out_settings()
        settings = replace(
            settings,
            stereo_or_mono=[
                StereoMode.MONO,
                StereoMode.MONO,
                *settings.stereo_or_mono[2:],
            ],
            output_groups=[
                OutputGroup.A,
                OutputGroup.E,
                *settings.output_groups[2:],
            ],
        )

        outputs = settings.outputs

        self.assertEqual(len(outputs), 5)
        self.assertEqual(
            [(output.number, output.output_group) for output in outputs],
            [
                (1, OutputGroup.A),
                (2, OutputGroup.B),
                (3, OutputGroup.C),
                (4, OutputGroup.D),
                (5, OutputGroup.E),
            ],
        )
        self.assertEqual([channel.index for channel in outputs[0].channels], [0])
        self.assertEqual([channel.index for channel in outputs[4].channels], [1])
        self.assertIs(outputs[0].stereo_mode, StereoMode.MONO)
        self.assertIs(outputs[4].stereo_mode, StereoMode.MONO)

    def test_outputs_derives_mixed_mono_and_stereo_stably(self) -> None:
        settings = load_in_out_settings()
        settings = replace(
            settings,
            stereo_or_mono=[
                *settings.stereo_or_mono[:2],
                StereoMode.MONO,
                StereoMode.MONO,
                *settings.stereo_or_mono[4:],
            ],
            output_groups=[
                *settings.output_groups[:2],
                OutputGroup.B,
                OutputGroup.F,
                *settings.output_groups[4:],
            ],
        )

        outputs = settings.outputs

        self.assertEqual(len(outputs), 5)
        self.assertEqual(
            [
                (output.output_group, [channel.index for channel in output.channels])
                for output in outputs
            ],
            [
                (OutputGroup.A, [0, 1]),
                (OutputGroup.B, [2]),
                (OutputGroup.C, [4, 5]),
                (OutputGroup.D, [6, 7]),
                (OutputGroup.F, [3]),
            ],
        )


if __name__ == "__main__":
    unittest.main()
