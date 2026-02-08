"""Tests for the vox MCP server tool functions."""

from __future__ import annotations

import asyncio
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from vox.mcp_server import record_voice, list_microphones


@pytest.fixture()
def fake_audio():
    return np.zeros(16000, dtype=np.float32)


class TestRecordVoice:
    """Tests for the record_voice tool."""

    def test_basic_transcription(self, fake_audio):
        with (
            patch("vox.recorder.record_until_silence", return_value=fake_audio) as mock_rec,
            patch("vox.transcriber.transcribe", return_value="hello world") as mock_trans,
            patch("vox.cleaner.clean", return_value="Hello world") as mock_clean,
        ):
            result = asyncio.run(record_voice(max_duration=5, model="tiny"))

            mock_rec.assert_called_once_with(max_duration=5, device=None)
            mock_trans.assert_called_once_with(fake_audio, "tiny")
            mock_clean.assert_called_once_with("hello world")
            assert result == "Hello world"

    def test_skip_cleaning(self, fake_audio):
        with (
            patch("vox.recorder.record_until_silence", return_value=fake_audio),
            patch("vox.transcriber.transcribe", return_value="um hello world"),
            patch("vox.cleaner.clean") as mock_clean,
        ):
            result = asyncio.run(record_voice(clean_text=False))

            mock_clean.assert_not_called()
            assert result == "um hello world"

    def test_passes_device(self, fake_audio):
        with (
            patch("vox.recorder.record_until_silence", return_value=fake_audio) as mock_rec,
            patch("vox.transcriber.transcribe", return_value="test"),
            patch("vox.cleaner.clean", return_value="Test"),
        ):
            asyncio.run(record_voice(device=3))
            mock_rec.assert_called_once_with(max_duration=15, device=3)

    def test_recorder_error_propagates(self):
        with patch(
            "vox.recorder.record_until_silence",
            side_effect=RuntimeError("no mic"),
        ):
            with pytest.raises(RuntimeError, match="no mic"):
                asyncio.run(record_voice())


class TestListMicrophones:
    """Tests for the list_microphones tool."""

    def test_devices_listed(self):
        devices = [
            {"index": 0, "name": "Built-in Microphone", "channels": 1, "sample_rate": 16000},
            {"index": 2, "name": "USB Mic", "channels": 2, "sample_rate": 44100},
        ]
        with patch("vox.recorder.get_input_devices", return_value=devices):
            result = asyncio.run(list_microphones())

            assert "[0] Built-in Microphone" in result
            assert "[2] USB Mic" in result

    def test_no_devices(self):
        with patch("vox.recorder.get_input_devices", return_value=[]):
            result = asyncio.run(list_microphones())
            assert result == "No input devices found."
