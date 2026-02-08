"""Vox MCP server — exposes voice recording tools to Claude Code."""

from __future__ import annotations

import asyncio
import logging
import sys

from mcp.server.fastmcp import FastMCP

# All logging to stderr so we never corrupt the stdio JSON-RPC transport.
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("vox-mcp")

mcp = FastMCP("vox", log_level="WARNING")


@mcp.tool()
async def record_voice(
    max_duration: float = 15,
    model: str = "base",
    clean_text: bool = True,
    device: int | None = None,
) -> str:
    """Record from the microphone until silence, then transcribe.

    Args:
        max_duration: Maximum recording length in seconds (default 15).
        model: Whisper model size — tiny, base, small, or medium (default base).
        clean_text: Apply code-aware text cleaning (default True).
        device: Audio input device index. None = system default.

    Returns:
        The transcribed (and optionally cleaned) text.
    """
    from vox.recorder import record_until_silence
    from vox.transcriber import transcribe
    from vox.cleaner import clean

    logger.info("Recording (max %ss, model=%s, device=%s)…", max_duration, model, device)

    audio = await asyncio.to_thread(
        record_until_silence, max_duration=max_duration, device=device
    )

    logger.info("Transcribing…")
    text = await asyncio.to_thread(transcribe, audio, model)

    if clean_text:
        text = clean(text)

    logger.info("Result: %s", text)
    return text


@mcp.tool()
async def list_microphones() -> str:
    """List available audio input devices.

    Returns:
        A formatted list of microphone names and their device indices.
    """
    from vox.recorder import get_input_devices

    devices = await asyncio.to_thread(get_input_devices)

    if not devices:
        return "No input devices found."

    lines = [f"[{d['index']}] {d['name']} (channels={d['channels']})" for d in devices]
    return "\n".join(lines)


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
