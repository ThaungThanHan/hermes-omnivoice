"""OmniVoice TTS provider registration for Hermes Agent."""

from .provider import OmniVoiceTTSProvider


def register(ctx):
    """Register the OmniVoice text-to-speech provider with Hermes."""

    ctx.register_tts_provider(OmniVoiceTTSProvider())


__all__ = ["OmniVoiceTTSProvider", "register"]
