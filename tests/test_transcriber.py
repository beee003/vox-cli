"""Tests for vox.transcriber — Whisper speech-to-text."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from vox.transcriber import VALID_MODEL_SIZES, _detect_device, transcribe


class TestDetectDevice:
    @patch.dict("sys.modules", {"torch": MagicMock(cuda=MagicMock(is_available=MagicMock(return_value=True)))})
    def test_cuda_when_available(self):
        device, compute = _detect_device()
        assert device == "cuda"
        assert compute == "float16"

    @patch.dict("sys.modules", {"torch": None})
    def test_cpu_when_no_torch(self):
        # Force ImportError by removing torch
        import sys
        saved = sys.modules.get("torch")
        sys.modules["torch"] = None
        try:
            # Need to handle the None module causing ImportError
            device, compute = _detect_device()
            assert device == "cpu"
            assert compute == "int8"
        finally:
            if saved is not None:
                sys.modules["torch"] = saved


class TestTranscribe:
    @patch("vox.transcriber.get_model")
    def test_returns_joined_text(self, mock_get_model):
        seg1 = MagicMock()
        seg1.text = " Hello "
        seg2 = MagicMock()
        seg2.text = " world "
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([seg1, seg2], None)
        mock_get_model.return_value = mock_model

        audio = np.zeros(16000, dtype=np.float32)
        result = transcribe(audio, model_size="base")

        assert result == "Hello world"
        mock_model.transcribe.assert_called_once_with(audio, beam_size=5)

    @patch("vox.transcriber.get_model")
    def test_empty_segments(self, mock_get_model):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], None)
        mock_get_model.return_value = mock_model

        audio = np.zeros(16000, dtype=np.float32)
        result = transcribe(audio)
        assert result == ""

    def test_invalid_model_size(self):
        with pytest.raises(ValueError, match="Invalid model_size"):
            transcribe(np.zeros(100, dtype=np.float32), model_size="huge")


class TestValidModelSizes:
    def test_contains_expected(self):
        assert "tiny" in VALID_MODEL_SIZES
        assert "base" in VALID_MODEL_SIZES
        assert "small" in VALID_MODEL_SIZES
        assert "medium" in VALID_MODEL_SIZES
        assert "large" not in VALID_MODEL_SIZES
