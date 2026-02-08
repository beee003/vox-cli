"""CLI entry point for vox — voice comments for your terminal."""

from __future__ import annotations

import logging
import sys
import threading

import click

from vox import __version__


@click.group()
@click.version_option(__version__, prog_name="vox")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def main(verbose: bool) -> None:
    """Vox — voice comments for your terminal."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


@main.command()
@click.option(
    "--model",
    type=click.Choice(["tiny", "base", "small", "medium"]),
    default="base",
    show_default=True,
    help="Whisper model size.",
)
@click.option(
    "--output",
    "output_mode",
    type=click.Choice(["clipboard", "stdout", "paste"]),
    default="clipboard",
    show_default=True,
    help="Where to send transcribed text.",
)
@click.option(
    "--key",
    default="alt_r",
    show_default=True,
    help="Push-to-talk trigger key.",
)
@click.option("--device", type=int, default=None, help="Audio input device index.")
@click.option("--no-clean", is_flag=True, help="Skip code-aware text cleaning.")
def listen(model: str, output_mode: str, key: str, device: int | None, no_clean: bool) -> None:
    """Start push-to-talk daemon. Hold the key to record, release to transcribe."""
    from vox import cleaner, output, recorder, transcriber

    click.echo(f"Vox v{__version__} — push-to-talk active (key: {key})")
    click.echo(f"Model: {model} | Output: {output_mode} | Clean: {not no_clean}")
    click.echo("Press Ctrl+C to quit.\n")

    # Pre-load the whisper model
    click.echo("Loading Whisper model...", nl=False)
    transcriber.get_model(model)
    click.echo(" done.")

    recording_event = threading.Event()
    audio_ready = threading.Event()
    audio_data = {}

    def on_start() -> None:
        click.echo("\r Recording...", nl=False)
        recording_event.set()

    def on_stop() -> None:
        recording_event.clear()
        click.echo("\r Transcribing...", nl=False)

    def record_loop() -> None:
        while True:
            recording_event.wait()
            audio = recorder.record_until_silence(device=device)
            if len(audio) > 0:
                audio_data["audio"] = audio
                audio_ready.set()

    record_thread = threading.Thread(target=record_loop, daemon=True)
    record_thread.start()

    def process_loop() -> None:
        while True:
            audio_ready.wait()
            audio_ready.clear()
            audio = audio_data.pop("audio", None)
            if audio is None:
                continue
            text = transcriber.transcribe(audio, model_size=model)
            if text and not no_clean:
                text = cleaner.clean(text)
            if text:
                output.deliver(text, mode=output_mode)
                click.echo(f"\r >> {text}")
            else:
                click.echo("\r (no speech detected)")

    process_thread = threading.Thread(target=process_loop, daemon=True)
    process_thread.start()

    # Import and start hotkey listener
    from vox.hotkey import PushToTalk

    ptt = PushToTalk(trigger_key=key, on_start=on_start, on_stop=on_stop)

    try:
        ptt.start()
        # Block main thread until Ctrl+C
        threading.Event().wait()
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
    finally:
        ptt.stop()


@main.command()
@click.option(
    "--model",
    type=click.Choice(["tiny", "base", "small", "medium"]),
    default="base",
    show_default=True,
    help="Whisper model size.",
)
@click.option(
    "--output",
    "output_mode",
    type=click.Choice(["clipboard", "stdout", "paste"]),
    default="clipboard",
    show_default=True,
    help="Where to send transcribed text.",
)
@click.option("--device", type=int, default=None, help="Audio input device index.")
@click.option("--duration", type=float, default=10.0, show_default=True, help="Max recording seconds.")
@click.option("--no-clean", is_flag=True, help="Skip code-aware text cleaning.")
def say(model: str, output_mode: str, device: int | None, duration: float, no_clean: bool) -> None:
    """One-shot: record, transcribe, and output. Press Ctrl+C to stop early."""
    from vox import cleaner, output, recorder, transcriber

    click.echo(f"Recording for up to {duration}s (speak now, silence stops recording)...")

    try:
        audio = recorder.record_until_silence(
            max_duration=duration,
            device=device,
        )
    except KeyboardInterrupt:
        click.echo("\nRecording stopped.")
        return

    if len(audio) == 0:
        click.echo("No audio captured.")
        return

    click.echo("Transcribing...", nl=False)
    text = transcriber.transcribe(audio, model_size=model)

    if text and not no_clean:
        text = cleaner.clean(text)

    if text:
        output.deliver(text, mode=output_mode)
        click.echo(f" done.\n>> {text}")
    else:
        click.echo(" no speech detected.")


@main.command()
def devices() -> None:
    """List available audio input devices."""
    from vox import recorder

    devs = recorder.get_input_devices()
    if not devs:
        click.echo("No audio input devices found.")
        return

    click.echo("Available input devices:\n")
    for dev in devs:
        click.echo(
            f"  [{dev['index']}] {dev['name']}  "
            f"(channels: {dev['channels']}, rate: {int(dev['default_samplerate'])}Hz)"
        )
