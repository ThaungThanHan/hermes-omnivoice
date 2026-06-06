# Hermes OmniVoice TTS Plugin

Powered by [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) from Xiaomi. 🎙️

OmniVoice is an impressive local multilingual zero-shot TTS model with broad language support, voice cloning, voice design, fine-grained speech controls, and fast inference.

`hermes-omnivoice` brings OmniVoice into [Hermes Agent](https://github.com/NousResearch/hermes-agent) as a community TTS plugin.

Once enabled, the plugin registers a Hermes TTS provider named:

```text
omnivoice
```

Hermes' existing text_to_speech flow can synthesize speech through OmniVoice.

## What can it do?

- 🌍 **Multilingual TTS** - generate speech in 600+ languages supported by OmniVoice.
- 🎭 **Voice design** — describe the voice you want, such as gender, pitch, age, accent, or speaking style.
- 🧬 **Voice cloning** — use any reference audio to create a similar voice.
- 🛠️ **Advanced controls** — configure speed, diffusion steps, guidance scale, duration, and more.
- 🧩 **Hermes-native** — works as a Hermes TTS provider without modifying Hermes core.
- 💻 **Local inference** — run speech generation locally with OmniVoice.

## Use cases

- Personalized, custom voices for Hermes agents
- Voice cloning to tune the voice as you desire
- Marketing and product-demo voiceovers
- Video narration for tutorials, reels, and explainers
- Multilingual content creation
- Creative voice experiments

## Install

You can let your Hermes agent install the hermes-omnivoice plugin by itself. Just give it the installation commands or the repository link.

Install the plugin and OmniVoice runtime in the same Python environment that runs Hermes:

```bash
pip install "hermes-omnivoice[omnivoice] @ git+https://github.com/ThaungThanHan/hermes-omnivoice.git"
hermes plugins enable omnivoice
hermes config set tts.provider omnivoice
```

If you only want to install the lightweight plugin package without OmniVoice:

```bash
pip install "hermes-omnivoice @ git+https://github.com/ThaungThanHan/hermes-omnivoice.git"
```

## Basic config

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

After changing config, restart Hermes.

## Voice modes

OmniVoice supports three main voice modes through this plugin.

### 1. Auto voice

Let OmniVoice pick the voice automatically:

```yaml
tts:
  provider: omnivoice
  omnivoice:
    voice: auto
```

Good for quick testing.

### 2. Voice design

Describe the voice you want:

```yaml
tts:
  provider: omnivoice
  omnivoice:
    voice: "female, low pitch, british accent"
```

You can also pass a voice-design instruction at call time:

```text
instruct:female, low pitch, british accent
```

Example ideas:

```text
male, young adult, high pitch
female, whisper
older male, deep voice
female, british accent
```

### 3. Voice cloning

Use a short reference audio file:

```yaml
tts:
  provider: omnivoice
  omnivoice:
    ref_audio: /absolute/path/to/reference.wav
    ref_text: "Transcript of the reference audio"
```

Hermes can also pass reference audio at call time:

```text
ref:/absolute/path/to/reference.wav
```

or simply pass an existing local audio-file path as the voice value.

For best results, use a clean reference clip with one speaker, low background noise, and an accurate transcript.

## Runtime voice values

When Hermes passes a `voice` value, the provider handles it like this:

| Voice value | Behavior |
| --- | --- |
| `auto` | Automatic voice selection |
| `default` | Automatic voice selection |
| `random` | Automatic voice selection |
| `instruct:female, british accent` | Voice-design instruction |
| `ref:/path/to/reference.wav` | Reference audio for voice cloning |
| `/path/to/reference.wav` | Reference audio if the file exists |
| Any other non-empty string | OmniVoice `instruct` value |

## Configuration

The provider reads `tts.omnivoice` from `~/.hermes/config.yaml`.

Environment variables override config values.

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

Generation controls also support:

```text
t_shift
denoise
postprocess_output
layer_penalty_factor
position_temperature
class_temperature
```

## Multilingual example

Set a language in your Hermes config:

```yaml
tts:
  provider: omnivoice
  omnivoice:
    language: th
```

Then ask Hermes to speak:

```text
Use text_to_speech to say: สวัสดีครับ นี่คือเสียงจาก OmniVoice
```

You can also test Chinese, English, Burmese, Japanese, Korean, and other languages supported by OmniVoice.

## Audio format

OmniVoice generates waveform audio.

This plugin can write these formats directly through `soundfile`:

```text
wav
flac
ogg
```

If Hermes requests `mp3`, the plugin uses `ffmpeg` when available. If `ffmpeg` is not available, it writes a `.wav` file and returns that path.

Install ffmpeg for MP3 output and Telegram voice-bubble conversion:

```bash
brew install ffmpeg
# or
sudo apt install ffmpeg
```

## Command-provider fallback

If you prefer Hermes' config-driven command provider instead of the Python plugin, you can use the included wrapper command:

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

The Python plugin is recommended for normal use because it can keep the model loaded during the Hermes session.

## Quick test

Create a text file:

```bash
echo "Hello from Hermes OmniVoice." > test.txt
```

Run:

```bash
omnivoice-hermes-tts \
  --text-file test.txt \
  --output test.wav \
  --voice auto \
  --format wav
```

Then play the generated file:

```bash
open test.wav
```

On Linux:

```bash
ffplay test.wav
```

## Notes

- First generation may take longer because the model needs to download and load.
- GPU is recommended for faster inference.
- CPU may work, but can be slow.
- Voice cloning quality depends heavily on the reference audio quality.
- Voice design behavior depends on OmniVoice model capabilities.

## Safety

OmniVoice supports voice cloning.

Only clone voices you have the right to use. Do not use this plugin to impersonate people, deceive others, bypass verification, or create misleading content.

You are responsible for following the OmniVoice model license and local laws.

## Contributing

Issues, ideas, bug reports, and pull requests are welcome.

Useful contribution ideas:

- More tested config examples
- Better Hermes setup docs
- Voice-design presets
- Language examples
- Tests for provider behavior
- Troubleshooting notes for CUDA, CPU, macOS, and Linux

If you try this plugin, feedback is warmly welcome.
