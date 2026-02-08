"""Speech-to-text module wrapping faster-whisper for local transcription."""

import logging
from typing import Dict

import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

_models: Dict[str, WhisperModel] = {}

VALID_MODEL_SIZES = ("tiny", "base", "small", "medium")


def _detect_device() -> tuple[str, str]:
    """Detect available device and return (device, compute_type)."""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda", "float16"
    except ImportError:
        pass
    return "cpu", "int8"


def get_model(model_size: str) -> WhisperModel:
    """Load and cache a WhisperModel by size.

    On the first call for a given model_size, this downloads (if needed)
    and loads the model. Subsequent calls return the cached instance.

    Args:
        model_size: One of "tiny", "base", "small", "medium".

    Returns:
        The loaded WhisperModel instance.
    """
    if model_size not in VALID_MODEL_SIZES:
        raise ValueError(
            f"Invalid model_size {model_size!r}. "
            f"Must be one of {VALID_MODEL_SIZES}"
        )

    if model_size not in _models:
        device, compute_type = _detect_device()
        logger.info(
            "Loading whisper model %r on %s (compute_type=%s)",
            model_size,
            device,
            compute_type,
        )
        _models[model_size] = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )

    return _models[model_size]


def transcribe(audio: np.ndarray, model_size: str = "base") -> str:
    """Transcribe a float32 16kHz audio array to text.

    Args:
        audio: Float32 numpy array of audio samples at 16 kHz.
        model_size: Whisper model size -- "tiny", "base", "small", or "medium".

    Returns:
        The transcribed text as a single string.
    """
    model = get_model(model_size)
    segments, _ = model.transcribe(audio, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments).strip()
