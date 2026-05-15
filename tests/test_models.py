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

    def test_stereo_output_pairs(self) -> None:
        settings = load_in_out_settings()

        pairs = settings.stereo_output_pairs

        self.assertEqual(len(pairs), 4)
        self.assertEqual(pairs[0].index, 0)
        self.assertEqual(pairs[0].number, 1)
        self.assertEqual(pairs[0].left.index, 0)
        self.assertEqual(pairs[0].right.index, 1)
        self.assertIs(pairs[0].output_group, OutputGroup.A)
        self.assertEqual(pairs[3].index, 3)
        self.assertEqual(pairs[3].number, 4)
        self.assertEqual(pairs[3].left.index, 6)
        self.assertEqual(pairs[3].right.index, 7)
        self.assertIs(pairs[3].output_group, OutputGroup.D)

    def test_stereo_output_pairs_exclude_channels_with_different_groups(self) -> None:
        settings = load_in_out_settings()
        settings = replace(
            settings,
            output_groups=[
                OutputGroup.A,
                OutputGroup.B,
                *settings.output_groups[2:],
            ],
        )

        pairs = settings.stereo_output_pairs

        self.assertEqual(len(pairs), 3)
        self.assertNotIn(0, {pair.index for pair in pairs})


if __name__ == "__main__":
    unittest.main()
