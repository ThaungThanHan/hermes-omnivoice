# Hermes OmniVoice TTS Plugin

Hermes Agent plugin for [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice), a local multilingual zero-shot TTS model with voice cloning and voice design support.

The plugin registers a Hermes TTS provider named `omnivoice`. Once enabled, Hermes' existing `text_to_speech` tool and voice-mode delivery can synthesize through OmniVoice.

## Install

Send this github link to your hermes agent chat and let it install this plugin to use OmniVoice TTS.

Or

Install OmniVoice and this plugin in the same Python environment that runs Hermes:

```bash
pip install git+https://github.com/k2-fsa/OmniVoice.git
pip install git+https://github.com/ThaungThanHan/hermes-omnivoice.git
```

Or install as a directory plugin:

```bash
mkdir -p ~/.hermes/plugins
git clone https://github.com/ThaungThanHan/hermes-omnivoice.git ~/.hermes/plugins/omnivoice
```

Enable the plugin and select the provider:

```bash
hermes plugins enable omnivoice
```

Add this to `~/.hermes/config.yaml`:

```yaml
tts:
  provider: omnivoice
  omnivoice:
    model: k2-fsa/OmniVoice
    device: auto
    dtype: float16
    voice: auto
```

## Voice Modes

OmniVoice supports three modes through the same Hermes provider:

```yaml
# Auto voice
tts:
  provider: omnivoice
  omnivoice:
    voice: auto

# Voice design
tts:
  provider: omnivoice
  omnivoice:
    voice: "female, low pitch, british accent"

# Voice cloning
tts:
  provider: omnivoice
  omnivoice:
    ref_audio: /absolute/path/to/reference.wav
    ref_text: "Transcript of the reference audio"
```

Hermes can also pass a voice value at call time. The provider treats:

- `auto`, `default`, or `random` as automatic voice selection.
- `instruct:female, british accent` as a voice-design instruction.
- `ref:/path/to/reference.wav` or an existing local file path as reference audio.
- Any other non-empty string as an OmniVoice `instruct` value.

## Configuration

The provider reads `tts.omnivoice` from `~/.hermes/config.yaml`. Environment variables override config values.

| Config key | Environment variable | Default |
| --- | --- | --- |
| `model` | `OMNIVOICE_MODEL` | `k2-fsa/OmniVoice` |
| `device` | `OMNIVOICE_DEVICE` | `auto` |
| `dtype` | `OMNIVOICE_DTYPE` | `float16` |
| `voice` | `OMNIVOICE_VOICE` | `auto` |
| `ref_audio` | `OMNIVOICE_REF_AUDIO` | unset |
| `ref_text` | `OMNIVOICE_REF_TEXT` | unset |
| `instruct` | `OMNIVOICE_INSTRUCT` | unset |
| `language` | `OMNIVOICE_LANGUAGE` | unset |
| `num_step` | `OMNIVOICE_NUM_STEP` | `32` |
| `guidance_scale` | `OMNIVOICE_GUIDANCE_SCALE` | `2.0` |
| `speed` | `OMNIVOICE_SPEED` | Hermes speed or `1.0` |
| `duration` | `OMNIVOICE_DURATION` | unset |
| `load_asr` | `OMNIVOICE_LOAD_ASR` | enabled when `ref_text` is absent |
| `asr_model` | `OMNIVOICE_ASR_MODEL` | `openai/whisper-large-v3-turbo` |

Generation controls also support `t_shift`, `denoise`, `postprocess_output`, `layer_penalty_factor`, `position_temperature`, and `class_temperature`.

## Audio Format

OmniVoice generates waveform audio. The plugin writes `wav`, `flac`, and `ogg` directly through `soundfile`. If Hermes requests `mp3`, the plugin uses `ffmpeg` when available; otherwise it writes a `.wav` file and returns that path.

Install ffmpeg for MP3 output and Telegram voice-bubble conversion:

```bash
brew install ffmpeg
# or: sudo apt install ffmpeg
```

## Command-Provider Fallback

If you prefer Hermes' config-driven command provider instead of the Python plugin, use OmniVoice's CLI:

```yaml
tts:
  provider: omnivoice-cli
  providers:
    omnivoice-cli:
      type: command
      command: "omnivoice-hermes-tts --text-file {input_path} --output {output_path} --model k2-fsa/OmniVoice --voice {voice} --speed {speed}"
      output_format: wav
      timeout: 600
      voice_compatible: true
```

The `omnivoice-hermes-tts` wrapper is installed by this package. It reads Hermes' `{input_path}` text file and calls the same provider code used by the Python plugin.

## Safety

OmniVoice supports voice cloning. Only clone voices you have the right to use, and follow the OmniVoice model license and local laws.
