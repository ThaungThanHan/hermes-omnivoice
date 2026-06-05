"""Hermes Agent TTS provider backed by k2-fsa/OmniVoice."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from agent.tts_provider import TTSProvider
except Exception:  # pragma: no cover - only used outside Hermes test envs
    class TTSProvider:  # type: ignore[no-redef]
        pass


_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def _env(name: str, default: Any = None) -> Any:
    value = os.environ.get(name)
    return default if value is None or value == "" else value


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _as_float(value: Any, default: Optional[float]) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_hermes_tts_config() -> Dict[str, Any]:
    """Read ~/.hermes/config.yaml tts.omnivoice when PyYAML is available."""

    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = Path(_env("HERMES_CONFIG", Path.home() / ".hermes" / "config.yaml"))
    if not config_path.exists():
        _CONFIG_CACHE = {}
        return _CONFIG_CACHE

    try:
        import yaml  # type: ignore

        with config_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        tts = data.get("tts") or {}
        provider_cfg = tts.get("omnivoice") or {}
        _CONFIG_CACHE = provider_cfg if isinstance(provider_cfg, dict) else {}
    except Exception:
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE


def _cfg(name: str, env_name: str, default: Any = None) -> Any:
    return _env(env_name, _load_hermes_tts_config().get(name, default))


def _resolve_voice_inputs(
    voice: Optional[str],
    *,
    default_instruct: Optional[str],
    default_ref_audio: Optional[str],
    default_ref_text: Optional[str],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Map Hermes' voice string plus config into OmniVoice prompt arguments."""

    instruct = default_instruct
    ref_audio = default_ref_audio
    ref_text = default_ref_text

    if not voice:
        return instruct, ref_audio, ref_text

    raw = voice.strip()
    lowered = raw.lower()
    if lowered in {"auto", "default", "random"}:
        return None, None, None
    if lowered.startswith("instruct:"):
        return raw.split(":", 1)[1].strip() or None, None, None
    if lowered.startswith("ref:"):
        return instruct, raw.split(":", 1)[1].strip() or None, ref_text
    if Path(raw).expanduser().exists():
        return instruct, str(Path(raw).expanduser()), ref_text

    return raw, ref_audio, ref_text


@dataclass(frozen=True)
class _ModelKey:
    model_id: str
    device: str
    dtype: str
    load_asr: bool
    asr_model: str


class OmniVoiceTTSProvider(TTSProvider):
    """Hermes TTS provider for OmniVoice."""

    _model_key: Optional[_ModelKey] = None
    _model: Any = None

    @property
    def name(self) -> str:
        return "omnivoice"

    @property
    def display_name(self) -> str:
        return "OmniVoice"

    @property
    def voice_compatible(self) -> bool:
        return True

    def is_available(self) -> bool:
        return all(
            importlib.util.find_spec(module) is not None
            for module in ("omnivoice", "torch", "soundfile")
        )

    def list_models(self):
        return [
            {
                "id": "k2-fsa/OmniVoice",
                "display": "OmniVoice",
                "languages": ["600+ languages"],
                "max_text_length": 5000,
            }
        ]

    def list_voices(self):
        return [
            {"id": "auto", "display": "Auto voice"},
            {"id": "female, british accent", "display": "Female, British accent"},
            {"id": "male, low pitch", "display": "Male, low pitch"},
            {
                "id": "instruct:female, low pitch, british accent",
                "display": "Voice design instruction",
            },
            {"id": "ref:/path/to/reference.wav", "display": "Reference audio path"},
        ]

    def get_setup_schema(self):
        return {
            "name": "OmniVoice",
            "badge": "local",
            "tag": "600+ language local zero-shot TTS and voice cloning",
            "env_vars": [],
        }

    def default_model(self) -> Optional[str]:
        return str(_cfg("model", "OMNIVOICE_MODEL", "k2-fsa/OmniVoice"))

    def default_voice(self) -> Optional[str]:
        return str(_cfg("voice", "OMNIVOICE_VOICE", "auto"))

    def _load_model(
        self,
        model_id: str,
        *,
        ref_audio: Optional[str],
        ref_text: Optional[str],
    ):
        import torch
        from omnivoice import OmniVoice

        try:
            from omnivoice.utils.common import get_best_device
        except Exception:
            get_best_device = None

        device = str(_cfg("device", "OMNIVOICE_DEVICE", "auto"))
        if device == "auto":
            device = get_best_device() if get_best_device else "cpu"

        dtype_name = str(_cfg("dtype", "OMNIVOICE_DTYPE", "float16"))
        dtype = getattr(torch, dtype_name, torch.float16)

        asr_model = str(
            _cfg("asr_model", "OMNIVOICE_ASR_MODEL", "openai/whisper-large-v3-turbo")
        )
        load_asr_default = bool(ref_audio) and not bool(ref_text)
        load_asr = _as_bool(_cfg("load_asr", "OMNIVOICE_LOAD_ASR", None), load_asr_default)

        key = _ModelKey(
            model_id=model_id,
            device=device,
            dtype=dtype_name,
            load_asr=load_asr,
            asr_model=asr_model,
        )
        if self._model is None or self._model_key != key:
            try:
                self._model = OmniVoice.from_pretrained(
                    model_id,
                    device_map=device,
                    dtype=dtype,
                    load_asr=load_asr,
                    asr_model_name=asr_model,
                )
            except TypeError:
                self._model = OmniVoice.from_pretrained(
                    model_id,
                    device_map=device,
                    dtype=dtype,
                )
            self._model_key = key
        return self._model

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        format: str = "mp3",
        **extra: Any,
    ) -> str:
        if not text or not text.strip():
            raise ValueError("No text provided for OmniVoice synthesis")

        import soundfile as sf

        model_id = model or self.default_model() or "k2-fsa/OmniVoice"
        cfg_voice = voice if voice is not None else _cfg("voice", "OMNIVOICE_VOICE", None)
        instruct, ref_audio, ref_text = _resolve_voice_inputs(
            cfg_voice,
            default_instruct=_cfg("instruct", "OMNIVOICE_INSTRUCT", None),
            default_ref_audio=_cfg("ref_audio", "OMNIVOICE_REF_AUDIO", None),
            default_ref_text=_cfg("ref_text", "OMNIVOICE_REF_TEXT", None),
        )

        ov = self._load_model(model_id, ref_audio=ref_audio, ref_text=ref_text)
        generate_kwargs: Dict[str, Any] = {
            "text": text.strip(),
            "language": _cfg("language", "OMNIVOICE_LANGUAGE", None),
            "ref_audio": str(Path(ref_audio).expanduser()) if ref_audio else None,
            "ref_text": ref_text,
            "instruct": instruct,
            "num_step": _as_int(_cfg("num_step", "OMNIVOICE_NUM_STEP", 32), 32),
            "guidance_scale": _as_float(
                _cfg("guidance_scale", "OMNIVOICE_GUIDANCE_SCALE", 2.0), 2.0
            ),
            "speed": speed
            if speed is not None
            else _as_float(_cfg("speed", "OMNIVOICE_SPEED", 1.0), 1.0),
            "duration": _as_float(_cfg("duration", "OMNIVOICE_DURATION", None), None),
            "t_shift": _as_float(_cfg("t_shift", "OMNIVOICE_T_SHIFT", 0.1), 0.1),
            "denoise": _as_bool(_cfg("denoise", "OMNIVOICE_DENOISE", True), True),
            "postprocess_output": _as_bool(
                _cfg("postprocess_output", "OMNIVOICE_POSTPROCESS_OUTPUT", True), True
            ),
            "layer_penalty_factor": _as_float(
                _cfg("layer_penalty_factor", "OMNIVOICE_LAYER_PENALTY_FACTOR", 5.0),
                5.0,
            ),
            "position_temperature": _as_float(
                _cfg("position_temperature", "OMNIVOICE_POSITION_TEMPERATURE", 5.0),
                5.0,
            ),
            "class_temperature": _as_float(
                _cfg("class_temperature", "OMNIVOICE_CLASS_TEMPERATURE", 0.0), 0.0
            ),
        }
        generate_kwargs = {k: v for k, v in generate_kwargs.items() if v is not None}

        audio = ov.generate(**generate_kwargs)
        target = Path(output_path)
        requested_format = (format or target.suffix.lstrip(".") or "wav").lower()

        if requested_format == "mp3":
            return self._write_mp3_or_wav(audio[0], ov.sampling_rate, target)

        if requested_format not in {"wav", "flac", "ogg"}:
            requested_format = "wav"
        target = target.with_suffix(f".{requested_format}")
        sf.write(str(target), audio[0], ov.sampling_rate)
        return str(target)

    def _write_mp3_or_wav(self, waveform, sampling_rate: int, target: Path) -> str:
        import soundfile as sf

        ffmpeg = os.environ.get("FFMPEG_BINARY", "ffmpeg")
        if _has_executable(ffmpeg):
            target = target.with_suffix(".mp3")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                sf.write(str(tmp_path), waveform, sampling_rate)
                subprocess.run(
                    [
                        ffmpeg,
                        "-y",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-i",
                        str(tmp_path),
                        str(target),
                    ],
                    check=True,
                )
                return str(target)
            finally:
                tmp_path.unlink(missing_ok=True)

        target = target.with_suffix(".wav")
        sf.write(str(target), waveform, sampling_rate)
        return str(target)


def _has_executable(command: str) -> bool:
    try:
        subprocess.run(
            [command, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return True
    except (OSError, ValueError):
        return False
