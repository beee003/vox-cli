"""Tests for vox.hotkey — push-to-talk hotkey listener."""

from unittest.mock import MagicMock, patch

import pytest

from vox.hotkey import HotkeyError, PushToTalk


class TestPushToTalk:
    def test_init_defaults(self):
        ptt = PushToTalk()
        assert ptt._trigger_key_name == "alt_r"
        assert ptt.is_active is False

    def test_init_custom_key(self):
        ptt = PushToTalk(trigger_key="f5")
        assert ptt._trigger_key_name == "f5"

    def test_invalid_key_raises(self):
        ptt = PushToTalk(trigger_key="nonexistent_key_xyz")
        with pytest.raises(HotkeyError, match="Unknown key"):
            ptt._resolve_key()

    @patch("vox.hotkey.Listener", create=True)
    def test_on_press_activates(self, _mock_listener):
        callback_called = []
        ptt = PushToTalk(
            trigger_key="alt_r",
            on_start=lambda: callback_called.append("start"),
        )
        # Manually resolve key and simulate press
        with patch("vox.hotkey.Key", create=True) as mock_key:
            mock_key.alt_r = "ALT_R_KEY"
            ptt._trigger_key = "ALT_R_KEY"
            ptt._on_press("ALT_R_KEY")

        assert ptt.is_active is True
        assert callback_called == ["start"]

    @patch("vox.hotkey.Listener", create=True)
    def test_on_release_deactivates(self, _mock_listener):
        callback_called = []
        ptt = PushToTalk(
            trigger_key="alt_r",
            on_stop=lambda: callback_called.append("stop"),
        )
        ptt._trigger_key = "ALT_R_KEY"
        # Activate first
        ptt._active = True
        ptt._on_release("ALT_R_KEY")

        assert ptt.is_active is False
        assert callback_called == ["stop"]

    def test_press_wrong_key_ignored(self):
        ptt = PushToTalk()
        ptt._trigger_key = "ALT_R_KEY"
        ptt._on_press("OTHER_KEY")
        assert ptt.is_active is False

    def test_double_press_only_fires_once(self):
        count = []
        ptt = PushToTalk(on_start=lambda: count.append(1))
        ptt._trigger_key = "KEY"
        ptt._on_press("KEY")
        ptt._on_press("KEY")  # Should not fire again
        assert len(count) == 1

    def test_double_release_only_fires_once(self):
        count = []
        ptt = PushToTalk(on_stop=lambda: count.append(1))
        ptt._trigger_key = "KEY"
        ptt._active = True
        ptt._on_release("KEY")
        ptt._on_release("KEY")
        assert len(count) == 1

    def test_stop_without_start(self):
        ptt = PushToTalk()
        ptt.stop()  # Should not raise
