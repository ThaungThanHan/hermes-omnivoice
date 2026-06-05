from pathlib import Path

from hermes_omnivoice.provider import _as_bool, _as_float, _as_int, _resolve_voice_inputs


def test_as_bool_accepts_common_values():
    assert _as_bool("yes", False) is True
    assert _as_bool("0", True) is False
    assert _as_bool("unexpected", True) is True


def test_numeric_parsers_fall_back():
    assert _as_int("16", 32) == 16
    assert _as_int("bad", 32) == 32
    assert _as_float("1.25", 1.0) == 1.25
    assert _as_float("bad", 1.0) == 1.0


def test_resolve_voice_inputs_auto_clears_defaults():
    assert _resolve_voice_inputs(
        "auto",
        default_instruct="female",
        default_ref_audio="voice.wav",
        default_ref_text="hello",
    ) == (None, None, None)


def test_resolve_voice_inputs_no_voice_keeps_defaults():
    assert _resolve_voice_inputs(
        None,
        default_instruct="female",
        default_ref_audio="voice.wav",
        default_ref_text="hello",
    ) == ("female", "voice.wav", "hello")


def test_resolve_voice_inputs_instruct_prefix():
    assert _resolve_voice_inputs(
        "instruct:male, british accent",
        default_instruct=None,
        default_ref_audio=None,
        default_ref_text=None,
    ) == ("male, british accent", None, None)


def test_resolve_voice_inputs_ref_prefix():
    assert _resolve_voice_inputs(
        "ref:/tmp/ref.wav",
        default_instruct="soft",
        default_ref_audio=None,
        default_ref_text="sample",
    ) == ("soft", "/tmp/ref.wav", "sample")


def test_resolve_voice_inputs_existing_path(tmp_path: Path):
    ref = tmp_path / "ref.wav"
    ref.write_bytes(b"fake")
    assert _resolve_voice_inputs(
        str(ref),
        default_instruct=None,
        default_ref_audio=None,
        default_ref_text="sample",
    ) == (None, str(ref), "sample")
