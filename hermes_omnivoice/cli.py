"""Command-provider wrapper for Hermes' config-driven TTS surface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .provider import OmniVoiceTTSProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnivoice-hermes-tts",
        description="Synthesize a Hermes TTS input file with OmniVoice.",
    )
    parser.add_argument("--text-file", "--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--voice", default=None)
    parser.add_argument("--speed", type=float, default=None)
    parser.add_argument("--format", default=None)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    text = Path(args.text_file).read_text(encoding="utf-8")
    output = Path(args.output)
    fmt = args.format or output.suffix.lstrip(".") or "wav"
    provider = OmniVoiceTTSProvider()
    provider.synthesize(
        text,
        str(output),
        voice=args.voice,
        model=args.model,
        speed=args.speed,
        format=fmt,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
