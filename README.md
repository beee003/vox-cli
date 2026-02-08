# vox

Voice comments for your terminal. Push-to-talk for Claude Code, Cursor, and any CLI.

## Install

```bash
pip install vox-cli
```

## Quick Start

```bash
# One-shot: speak and get text
vox say

# Push-to-talk daemon (hold Right Alt to record)
vox listen

# List audio devices
vox devices
```

## Features

- **Local-first** — runs Whisper locally, no cloud API calls
- **Code-aware cleaning** — fixes capitalization of `API`, `JSON`, `None`, etc.
- **Voice casing** — say "snake case my variable name" → `my_variable_name`
- **Multiple outputs** — clipboard (default), stdout, or simulated paste
- **Push-to-talk** — configurable hotkey, silence detection auto-stops

## Options

```
vox listen --model small      # tiny|base|small|medium
vox listen --output stdout    # clipboard|stdout|paste
vox listen --key f5           # any modifier or function key
vox say --duration 15         # max recording seconds
vox --verbose listen          # debug logging
```

## Requirements

- Python 3.10+
- A microphone
- macOS: grant Terminal Accessibility permission for hotkey support

## License

MIT
