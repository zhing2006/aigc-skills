# DashScope Voice Clone

Clone voices from audio files using Alibaba DashScope Qwen Voice Clone API.

## Usage

```bash
# Create a cloned voice from audio file
{python} {skill_dir}/scripts/dashscope-voice-clone.py create <audio_file> -n <name> [options]

# List all cloned voices
{python} {skill_dir}/scripts/dashscope-voice-clone.py list [options]

# Delete a specific voice
{python} {skill_dir}/scripts/dashscope-voice-clone.py delete <voice_name>
```

## Create Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `audio_file` | Yes | Path to audio file (WAV/MP3/M4A) |
| `-n`, `--name` | Yes | Preferred name (max 16 chars, alphanumeric/underscore) |

## Create Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-l`, `--language` | Auto | Audio language: zh/en/de/it/pt/es/ja/ko/fr/ru |
| `-t`, `--text` | None | Transcript of the audio (for validation) |
| `--target-model` | `qwen3-tts-vc-realtime-2026-01-15` | Target TTS model |

## List Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--page-index` | `0` | Page index (0-based) |
| `--page-size` | `10` | Number of items per page |

## Audio Requirements

| Item | Requirement |
| ---- | ----------- |
| Format | WAV (16bit), MP3, M4A |
| Duration | 10-20 seconds recommended, max 60 seconds |
| File size | < 10 MB |
| Sample rate | ≥ 24 kHz |
| Channels | Mono |
| Content | Clear speech, no background music/noise |

## Examples

### Clone a Chinese Voice

```bash
{python} {skill_dir}/scripts/dashscope-voice-clone.py create voice.mp3 -n narrator -l zh
```

### Clone an English Voice with Transcript

```bash
{python} {skill_dir}/scripts/dashscope-voice-clone.py create recording.wav -n english_host -l en -t "Hello everyone, welcome to our show"
```

### List Cloned Voices

```bash
{python} {skill_dir}/scripts/dashscope-voice-clone.py list
```

### Delete a Voice

```bash
{python} {skill_dir}/scripts/dashscope-voice-clone.py delete qwen-tts-vc-narrator-voice-20250812105009984-838b
```
