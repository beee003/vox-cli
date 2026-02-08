"""Tests for vox.recorder — audio recording module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from vox.recorder import (
    RecorderError,
    _normalize,
    _rms_to_db,
    get_input_devices,
    record_for_duration,
)


class TestRmsToDb:
    def test_silence_returns_negative(self):
        assert _rms_to_db(0.0) == -120.0

    def test_full_scale(self):
        assert abs(_rms_to_db(1.0) - 0.0) < 0.01

    def test_half_scale(self):
        db = _rms_to_db(0.5)
        assert -7 < db < -5  # ~-6.02 dB

    def test_negative_returns_floor(self):
        assert _rms_to_db(-1.0) == -120.0


class TestNormalize:
    def test_normalizes_to_unit_peak(self):
        audio = np.array([0.0, 0.5, -0.25], dtype=np.float32)
        result = _normalize(audio)
        assert float(np.max(np.abs(result))) == pytest.approx(1.0)

    def test_silent_audio_unchanged(self):
        audio = np.zeros(100, dtype=np.float32)
        result = _normalize(audio)
        assert np.all(result == 0.0)

    def test_output_dtype_float32(self):
        audio = np.array([0.1, -0.2, 0.3], dtype=np.float32)
        result = _normalize(audio)
        assert result.dtype == np.float32


class TestGetInputDevices:
    @patch("vox.recorder.sd.query_devices")
    def test_filters_input_devices(self, mock_query):
        mock_query.return_value = [
            {"name": "Mic", "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 44100.0},
            {"name": "Speakers", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100.0},
            {"name": "USB Mic", "max_input_channels": 1, "max_output_channels": 0, "default_samplerate": 16000.0},
        ]
        devs = get_input_devices()
        assert len(devs) == 2
        assert devs[0]["name"] == "Mic"
        assert devs[1]["name"] == "USB Mic"

    @patch("vox.recorder.sd.query_devices")
    def test_empty_when_no_inputs(self, mock_query):
        mock_query.return_value = [
            {"name": "Speakers", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100.0},
        ]
        assert get_input_devices() == []


class TestRecordForDuration:
    @patch("vox.recorder.sd.wait")
    @patch("vox.recorder.sd.rec")
    @patch("vox.recorder._ensure_mic_available")
    def test_records_correct_frames(self, mock_ensure, mock_rec, mock_wait):
        expected_frames = int(2.0 * 16000)
        fake_audio = np.random.randn(expected_frames, 1).astype(np.float32)
        mock_rec.return_value = fake_audio

        result = record_for_duration(2.0)

        mock_rec.assert_called_once()
        call_kwargs = mock_rec.call_args
        assert call_kwargs.kwargs["frames"] == expected_frames
        assert result.dtype == np.float32

    @patch("vox.recorder._ensure_mic_available")
    def test_raises_on_portaudio_error(self, mock_ensure):
        import sounddevice as sd

        with patch("vox.recorder.sd.rec", side_effect=sd.PortAudioError("test error")):
            with pytest.raises(RecorderError, match="Audio recording failed"):
                record_for_duration(1.0)


class TestEnsureMicAvailable:
    @patch("vox.recorder.sd.query_devices")
    def test_raises_on_no_channels(self, mock_query):
        mock_query.return_value = {"name": "Bad Device", "max_input_channels": 0}
        with pytest.raises(RecorderError, match="no input channels"):
            from vox.recorder import _ensure_mic_available
            _ensure_mic_available(0)
