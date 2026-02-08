"""Tests for vox.output — text delivery module."""

from unittest.mock import MagicMock, patch

import pytest

from vox.output import OutputError, deliver, to_clipboard, to_stdout


class TestToStdout:
    def test_writes_to_stdout(self, capsys):
        to_stdout("hello world")
        captured = capsys.readouterr()
        assert captured.out == "hello world"


class TestToClipboard:
    @patch("vox.output.pyperclip.copy")
    def test_copies_text(self, mock_copy):
        to_clipboard("test text")
        mock_copy.assert_called_once_with("test text")

    @patch("vox.output.pyperclip.copy")
    def test_raises_on_clipboard_error(self, mock_copy):
        import pyperclip
        mock_copy.side_effect = pyperclip.PyperclipException("no clipboard")
        with pytest.raises(OutputError, match="Clipboard not available"):
            to_clipboard("text")


class TestDeliver:
    def test_stdout_mode(self, capsys):
        deliver("hello", mode="stdout")
        assert capsys.readouterr().out == "hello"

    @patch("vox.output.pyperclip.copy")
    def test_clipboard_mode(self, mock_copy):
        deliver("test", mode="clipboard")
        mock_copy.assert_called_once_with("test")

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Invalid output mode"):
            deliver("text", mode="email")


class TestToPaste:
    @patch("vox.output.pyperclip.copy")
    def test_copies_before_paste(self, mock_copy):
        from vox.output import to_paste
        # Will fail on paste simulation in test env, but clipboard copy should work
        try:
            to_paste("text")
        except (OutputError, Exception):
            pass
        mock_copy.assert_called_with("text")
