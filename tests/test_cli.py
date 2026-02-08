"""Tests for vox.cli — CLI entry point."""

from unittest.mock import patch

from click.testing import CliRunner

from vox.cli import main


class TestCLI:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "voice comments" in result.output.lower()

    def test_listen_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["listen", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--output" in result.output
        assert "--key" in result.output

    def test_say_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["say", "--help"])
        assert result.exit_code == 0
        assert "--duration" in result.output

    def test_devices_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["devices", "--help"])
        assert result.exit_code == 0

    @patch("vox.recorder.get_input_devices")
    def test_devices_command(self, mock_devices):
        mock_devices.return_value = [
            {"index": 0, "name": "Built-in Mic", "channels": 2, "default_samplerate": 44100.0},
        ]
        runner = CliRunner()
        result = runner.invoke(main, ["devices"])
        assert result.exit_code == 0
        assert "Built-in Mic" in result.output

    @patch("vox.recorder.get_input_devices")
    def test_devices_empty(self, mock_devices):
        mock_devices.return_value = []
        runner = CliRunner()
        result = runner.invoke(main, ["devices"])
        assert result.exit_code == 0
        assert "No audio input devices found" in result.output
