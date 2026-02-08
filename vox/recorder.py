from __future__ import annotations

import queue
from typing import Optional

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
BLOCK_SIZE = 1024


class RecorderError(Exception):
    pass


def get_input_devices() -> list[dict]:
    devices = sd.query_devices()
    result = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            result.append({
                "index": i,
                "name": dev["name"],
                "channels": dev["max_input_channels"],
                "default_samplerate": dev["default_samplerate"],
            })
    return result


def _rms_to_db(rms: float) -> float:
    if rms <= 0:
        return -120.0
    return 20.0 * np.log10(rms)


def _ensure_mic_available(device: Optional[int] = None) -> None:
    try:
        info = sd.query_devices(device, kind="input")
        if info["max_input_channels"] < 1:
            raise RecorderError(f"Device '{info['name']}' has no input channels")
    except sd.PortAudioError as e:
        raise RecorderError(f"Cannot access audio device: {e}") from e
    except Exception as e:
        if isinstance(e, RecorderError):
            raise
        raise RecorderError(f"No suitable input device found: {e}") from e


def record_until_silence(
    threshold_db: float = -40,
    silence_duration: float = 1.5,
    max_duration: float = 30,
    device: Optional[int] = None,
) -> np.ndarray:
    _ensure_mic_available(device)

    audio_queue: queue.Queue[np.ndarray] = queue.Queue()

    def callback(indata: np.ndarray, frames: int, time_info: object, status: sd.CallbackFlags) -> None:
        audio_queue.put(indata.copy())

    chunks: list[np.ndarray] = []
    silent_samples = 0
    silent_samples_needed = int(silence_duration * SAMPLE_RATE)
    max_samples = int(max_duration * SAMPLE_RATE)
    total_samples = 0

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCK_SIZE,
            device=device,
            callback=callback,
        ):
            while True:
                try:
                    chunk = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                chunks.append(chunk)
                total_samples += len(chunk)

                rms = float(np.sqrt(np.mean(chunk ** 2)))
                db = _rms_to_db(rms)

                if db < threshold_db:
                    silent_samples += len(chunk)
                else:
                    silent_samples = 0

                if silent_samples >= silent_samples_needed and total_samples > silent_samples_needed:
                    break

                if total_samples >= max_samples:
                    break

    except sd.PortAudioError as e:
        raise RecorderError(f"Audio recording failed: {e}") from e

    if not chunks:
        return np.array([], dtype=np.float32)

    audio = np.concatenate(chunks).flatten()
    return _normalize(audio)


def record_for_duration(
    duration_seconds: float,
    device: Optional[int] = None,
) -> np.ndarray:
    _ensure_mic_available(device)

    num_frames = int(duration_seconds * SAMPLE_RATE)

    try:
        recording = sd.rec(
            frames=num_frames,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            device=device,
        )
        sd.wait()
    except sd.PortAudioError as e:
        raise RecorderError(f"Audio recording failed: {e}") from e

    audio = recording.flatten()
    return _normalize(audio)


def _normalize(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio)))
    if peak > 0:
        audio = audio / peak
    return audio.astype(np.float32)
