"""Output delivery — clipboard, stdout, or simulated paste."""

from __future__ import annotations

import logging
import sys

import pyperclip

logger = logging.getLogger(__name__)

VALID_MODES = ("clipboard", "stdout", "paste")


class OutputError(Exception):
    pass


def to_clipboard(text: str) -> None:
    """Copy text to the system clipboard."""
    try:
        pyperclip.copy(text)
        logger.info("Copied %d chars to clipboard", len(text))
    except pyperclip.PyperclipException as e:
        raise OutputError(f"Clipboard not available: {e}") from e


def to_stdout(text: str) -> None:
    """Print text to stdout."""
    sys.stdout.write(text)
    sys.stdout.flush()


def to_paste(text: str) -> None:
    """Copy to clipboard then simulate Cmd+V / Ctrl+V to paste."""
    to_clipboard(text)

    try:
        from pynput.keyboard import Controller, Key

        kb = Controller()
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with kb.pressed(modifier):
            kb.tap("v")
        logger.info("Simulated paste of %d chars", len(text))
    except Exception as e:
        raise OutputError(
            f"Paste simulation failed (text is still in clipboard): {e}"
        ) from e


def deliver(text: str, mode: str = "clipboard") -> None:
    """Deliver transcribed text using the specified output mode.

    Args:
        text: The text to deliver.
        mode: One of "clipboard", "stdout", or "paste".
    """
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid output mode {mode!r}. Must be one of {VALID_MODES}")

    dispatch = {
        "clipboard": to_clipboard,
        "stdout": to_stdout,
        "paste": to_paste,
    }
    dispatch[mode](text)
