"""Code-aware text cleaning for voice-transcribed developer speech."""

from __future__ import annotations

import re

# Filler words to strip (case-insensitive)
_FILLERS = {"um", "uh", "er", "ah", "hmm", "huh", "like", "you know", "i mean", "basically", "actually", "literally"}

# Words where "like" is likely intentional (preceded by these)
_LIKE_KEEPERS = {"looks", "feels", "works", "sounds", "seems", "acts", "is", "was"}

# Python/JS/TS keywords to capitalize correctly
_CODE_KEYWORDS = {
    "none": "None", "true": "True", "false": "False",
    "def": "def", "class": "class", "import": "import",
    "return": "return", "self": "self", "async": "async",
    "await": "await", "yield": "yield", "lambda": "lambda",
    "const": "const", "let": "let", "var": "var",
    "function": "function", "null": "null", "undefined": "undefined",
}

# Tech terms to uppercase/capitalize
_TECH_TERMS = {
    "api": "API", "apis": "APIs", "json": "JSON", "rest": "REST",
    "http": "HTTP", "https": "HTTPS", "html": "HTML", "css": "CSS",
    "sql": "SQL", "url": "URL", "urls": "URLs", "cli": "CLI",
    "ssh": "SSH", "tcp": "TCP", "udp": "UDP", "dns": "DNS",
    "gpu": "GPU", "cpu": "CPU", "ram": "RAM", "ssd": "SSD",
    "oauth": "OAuth", "jwt": "JWT", "yaml": "YAML", "toml": "TOML",
    "npm": "npm", "pip": "pip", "git": "git", "docker": "Docker",
    "kubernetes": "Kubernetes", "redis": "Redis", "postgres": "Postgres",
    "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
    "numpy": "NumPy", "pandas": "pandas", "pytorch": "PyTorch",
    "tensorflow": "TensorFlow", "fastapi": "FastAPI", "flask": "Flask",
    "django": "Django", "react": "React", "nextjs": "Next.js",
    "github": "GitHub", "gitlab": "GitLab", "vscode": "VS Code",
    "openai": "OpenAI", "anthropic": "Anthropic", "claude": "Claude",
    "whisper": "Whisper",
}

# Voice casing commands
_CASING_PATTERNS = {
    "snake case": "_",
    "camel case": "camel",
    "pascal case": "pascal",
    "kebab case": "-",
    "all caps": "upper",
    "upper case": "upper",
}

# Formatting commands spoken as words
_FORMAT_COMMANDS = {
    "new line": "\n",
    "newline": "\n",
    "period": ".",
    "comma": ",",
    "colon": ":",
    "semicolon": ";",
    "open paren": "(",
    "close paren": ")",
    "open bracket": "[",
    "close bracket": "]",
    "open brace": "{",
    "close brace": "}",
    "equals": "=",
    "arrow": "->",
    "fat arrow": "=>",
    "hash": "#",
    "at sign": "@",
    "dollar sign": "$",
    "ampersand": "&",
    "pipe": "|",
    "backslash": "\\",
    "forward slash": "/",
}


def clean(text: str) -> str:
    """Apply all cleaning transformations to transcribed text."""
    if not text or not text.strip():
        return ""
    text = _strip_fillers(text)
    text = _apply_format_commands(text)
    text = _apply_casing_commands(text)
    text = _capitalize_code_keywords(text)
    text = _capitalize_tech_terms(text)
    text = _normalize_whitespace(text)
    text = _capitalize_first(text)
    return text


def _strip_fillers(text: str) -> str:
    """Remove filler words, keeping 'like' when used intentionally."""
    words = text.split()
    result = []
    for i, word in enumerate(words):
        clean_word = word.lower().strip(".,!?;:")
        # Multi-word fillers
        if i < len(words) - 1:
            pair = f"{clean_word} {words[i + 1].lower().strip('.,!?;:')}"
            if pair in _FILLERS:
                # Skip this word; next iteration will check and potentially skip the next
                continue
        # Check if previous word was part of a multi-word filler
        if i > 0:
            prev = words[i - 1].lower().strip(".,!?;:")
            pair = f"{prev} {clean_word}"
            if pair in _FILLERS:
                continue
        # Single-word fillers
        if clean_word in {"um", "uh", "er", "ah", "hmm", "huh"}:
            continue
        # Context-aware "like" removal
        if clean_word == "like":
            prev_word = words[i - 1].lower().strip(".,!?;:") if i > 0 else ""
            if prev_word not in _LIKE_KEEPERS:
                continue
        result.append(word)
    return " ".join(result)


def _apply_format_commands(text: str) -> str:
    """Replace spoken formatting commands with their symbols."""
    for command, symbol in _FORMAT_COMMANDS.items():
        pattern = re.compile(re.escape(command), re.IGNORECASE)
        text = pattern.sub(lambda _m, s=symbol: s, text)
    return text


def _apply_casing_commands(text: str) -> str:
    """Handle voice casing commands like 'snake case my variable name'."""
    for command, mode in _CASING_PATTERNS.items():
        pattern = re.compile(
            re.escape(command) + r"\s+(.+?)(?:\.|,|$)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            words_to_case = match.group(1).strip().split()
            if mode == "_":
                cased = "_".join(w.lower() for w in words_to_case)
            elif mode == "-":
                cased = "-".join(w.lower() for w in words_to_case)
            elif mode == "camel":
                cased = words_to_case[0].lower() + "".join(
                    w.capitalize() for w in words_to_case[1:]
                )
            elif mode == "pascal":
                cased = "".join(w.capitalize() for w in words_to_case)
            elif mode == "upper":
                cased = "_".join(w.upper() for w in words_to_case)
            else:
                cased = " ".join(words_to_case)
            text = text[:match.start()] + cased + text[match.end():]
    return text


def _capitalize_code_keywords(text: str) -> str:
    """Fix capitalization of code keywords."""
    # Split on single space to preserve newlines
    words = text.split(" ")
    for i, word in enumerate(words):
        stripped = word.strip(".,!?;:()[]{}\"'\n\t")
        if stripped.lower() in _CODE_KEYWORDS:
            correct = _CODE_KEYWORDS[stripped.lower()]
            words[i] = word.replace(stripped, correct, 1)
    return " ".join(words)


def _capitalize_tech_terms(text: str) -> str:
    """Fix capitalization of tech terms."""
    # Split on single space to preserve newlines
    words = text.split(" ")
    for i, word in enumerate(words):
        stripped = word.strip(".,!?;:()[]{}\"'\n\t")
        if stripped.lower() in _TECH_TERMS:
            correct = _TECH_TERMS[stripped.lower()]
            words[i] = word.replace(stripped, correct, 1)
    return " ".join(words)


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces, strip leading/trailing whitespace per line."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = re.sub(r" {2,}", " ", line).strip()
        if line:
            cleaned.append(line)
    return "\n".join(cleaned)


def _capitalize_first(text: str) -> str:
    """Capitalize first letter of the text."""
    if text:
        return text[0].upper() + text[1:]
    return text
