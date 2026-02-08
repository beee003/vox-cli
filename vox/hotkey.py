"""Global hotkey listener for push-to-talk functionality."""

from __future__ import annotations

import logging
import sys
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class HotkeyError(Exception):
    pass


class PushToTalk:
    """Thread-safe push-to-talk hotkey listener.

    Hold the trigger key to activate, release to deactivate.
    Calls on_start when key is pressed and on_stop when released.
    """

    def __init__(
        self,
        trigger_key: str = "alt_r",
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
    ) -> None:
        self._trigger_key_name = trigger_key
        self._on_start = on_start or (lambda: None)
        self._on_stop = on_stop or (lambda: None)
        self._active = False
        self._lock = threading.Lock()
        self._listener = None
        self._trigger_key = None

    def _resolve_key(self):
        """Resolve the string key name to a pynput Key object."""
        from pynput.keyboard import Key

        # Build key map dynamically — some keys don't exist on all platforms
        key_names = [
            "alt_r", "alt_l", "alt", "ctrl_r", "ctrl_l", "ctrl",
            "shift_r", "shift_l", "shift", "cmd", "cmd_r",
            "f1", "f2", "f3", "f4", "f5", "f6",
            "f7", "f8", "f9", "f10", "f11", "f12",
            "scroll_lock", "pause", "insert",
        ]
        key_map = {}
        for name in key_names:
            try:
                key_map[name] = getattr(Key, name)
            except AttributeError:
                pass

        if self._trigger_key_name in key_map:
            return key_map[self._trigger_key_name]

        raise HotkeyError(
            f"Unknown key {self._trigger_key_name!r}. "
            f"Valid keys: {', '.join(sorted(key_map))}"
        )

    def _on_press(self, key) -> None:
        """Handle key press events."""
        if key == self._trigger_key:
            with self._lock:
                if not self._active:
                    self._active = True
                    logger.debug("Push-to-talk activated")
                    try:
                        self._on_start()
                    except Exception:
                        logger.exception("Error in on_start callback")

    def _on_release(self, key) -> None:
        """Handle key release events."""
        if key == self._trigger_key:
            with self._lock:
                if self._active:
                    self._active = False
                    logger.debug("Push-to-talk deactivated")
                    try:
                        self._on_stop()
                    except Exception:
                        logger.exception("Error in on_stop callback")

    def start(self) -> None:
        """Start listening for the hotkey."""
        from pynput.keyboard import Listener

        self._trigger_key = self._resolve_key()

        if sys.platform == "darwin":
            logger.info(
                "macOS detected — ensure Terminal/app has Accessibility permission "
                "(System Settings > Privacy & Security > Accessibility)"
            )

        try:
            self._listener = Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
            self._listener.start()
            logger.info("Hotkey listener started (trigger: %s)", self._trigger_key_name)
        except Exception as e:
            raise HotkeyError(f"Failed to start hotkey listener: {e}") from e

    def stop(self) -> None:
        """Stop listening for the hotkey."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
            logger.info("Hotkey listener stopped")

    @property
    def is_active(self) -> bool:
        """Whether the push-to-talk key is currently held."""
        with self._lock:
            return self._active
