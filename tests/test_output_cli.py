"""Tests for CLI-only output source value formatting."""

import unittest

import typer

from sonance_py import StereoMode
from sonance_py.output_cli import _format_source_value, _parse_source_value


class FakeOutput:
    """Minimal output shape needed by source CLI helpers."""

    def __init__(self, stereo_mode: StereoMode) -> None:
        self.stereo_mode = stereo_mode


class TestOutputCliSources(unittest.TestCase):
    """Validate CLI source values stay separate from internal source IDs."""

    def test_stereo_outputs_show_source_pairs_as_numbers(self) -> None:
        output = FakeOutput(StereoMode.STEREO)

        self.assertEqual(_format_source_value(0, output), "1")
        self.assertEqual(_format_source_value(1, output), "1")
        self.assertEqual(_format_source_value(6, output), "4")
        self.assertEqual(_format_source_value(7, output), "4")

    def test_stereo_outputs_accept_source_pair_numbers(self) -> None:
        output = FakeOutput(StereoMode.STEREO)

        self.assertEqual(_parse_source_value("1", output), 0)
        self.assertEqual(_parse_source_value("4", output), 6)

        with self.assertRaises(typer.BadParameter):
            _parse_source_value("1L", output)

    def test_mono_outputs_show_source_pairs_with_side_suffixes(self) -> None:
        output = FakeOutput(StereoMode.MONO)

        self.assertEqual(_format_source_value(0, output), "1L")
        self.assertEqual(_format_source_value(1, output), "1R")
        self.assertEqual(_format_source_value(6, output), "4L")
        self.assertEqual(_format_source_value(7, output), "4R")

    def test_mono_outputs_accept_source_pair_side_suffixes(self) -> None:
        output = FakeOutput(StereoMode.MONO)

        self.assertEqual(_parse_source_value("1L", output), 0)
        self.assertEqual(_parse_source_value("1r", output), 1)
        self.assertEqual(_parse_source_value("4R", output), 7)

        with self.assertRaises(typer.BadParameter):
            _parse_source_value("1", output)


if __name__ == "__main__":
    unittest.main()
