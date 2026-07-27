# Volcengine Voice Clone

Clone voices from audio samples and manage voice instances using Volcengine Voice Clone 2.0.

## Usage

```bash
# Train a cloned voice from an audio sample
{python} {skill_dir}/scripts/volcengine-voice-clone.py train <audio_file> -s <speaker_id> [options]

# Query the training status of a voice
{python} {skill_dir}/scripts/volcengine-voice-clone.py status <speaker_id> [options]

# Upgrade a V1 cloned voice to V3 (usable across products)
{python} {skill_dir}/scripts/volcengine-voice-clone.py upgrade <speaker_id>

# List purchased voices and their states (management API)
{python} {skill_dir}/scripts/volcengine-voice-clone.py list [options]

# Purchase voice clone resource packs (PAID)
{python} {skill_dir}/scripts/volcengine-voice-clone.py order [options]

# Renew voice instances (PAID)
{python} {skill_dir}/scripts/volcengine-voice-clone.py renew <speaker_id...> [options]
```

## Train Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `audio_file` | Yes | Audio sample (WAV/MP3/OGG/M4A/AAC/PCM, <10MB) |
| `-s`, `--speaker-id` | Yes | Purchased speaker ID (`S_xxx`), or custom ID with `--custom` |

## Train Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--custom` | Off | Treat the ID as a custom (postpaid) speaker ID |
| `-t`, `--text` | None | Reference transcript (training fails on large mismatch, error 45001109) |
| `-l`, `--language` | `cn` | Sample language: cn/en/ja/es/id/pt/de/fr/ko/th/vi/ru/fil/ms/ar/mx/pt-br |
| `--demo-text` | None | Demo text for the preview audio (4-300 chars; longer = slower training) |
| `--denoise` | Off | Enable denoising (recommended for noisy samples only) |
| `--no-volume-normalization` | Off | Keep the sample's volume (higher similarity) |

## Status Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--custom` | Off | Treat the ID as a custom (postpaid) speaker ID |
| `--download-demo` | Off | Download the demo audio if available |
| `-o`, `--output` | `<speaker_id>_demo.mp3` | Demo audio output path |

## List Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--speaker-ids` | All | Filter by specific speaker IDs |
| `--state` | All | Filter: Unknown/Training/Success/Active/Expired/Reclaimed |
| `-p`, `--page` | `1` | Page number (1-based) |
| `-n`, `--page-size` | `10` | Items per page (1-100) |

## Order / Renew Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--quantity` (order) | `1` | Number of voices to purchase |
| `--times` | `1` | Duration in months |

## Audio Requirements

| Item | Requirement |
| ---- | ----------- |
| Format | WAV, MP3, OGG, M4A, AAC, PCM (PCM: 24kHz mono only) |
| Duration | 10-15 seconds recommended (longer audio is truncated) |
| File size | < 10 MB |
| Content | Single speaker, low noise, clear speech, steady emotion |
| Language | Must match `-l` language; cover both for zh/en mixed reading |

## Voice Status

| Status | Name | Meaning |
| ------ | ---- | ------- |
| 0 | NotFound | Speaker ID not trained yet |
| 1 | Training | Training in progress |
| 2 | Success | Ready for TTS synthesis |
| 3 | Failed | Training failed (see message) |
| 4 | Active | Activated (ready for TTS, no more training) |

Demo audio URLs are valid for **1 hour** — the script downloads them immediately.

## Billing Note

- `order` and `renew` are **paid operations** billed to your Volcengine account (auto-paid from balance/coupons). Use `list` first to check existing resources.
- For custom (postpaid) speaker IDs, the **first synthesis call activates the voice and bills the slot fee** — confirm the demo audio before synthesizing.

## Synthesis

After status reaches 2 (Success) or 4 (Active), synthesize with the cloned voice:

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "你好，世界" -v S_abc12345
```

Cloned voices default to `seed-tts-2.0-standard` (lower latency). Voice instructions (`-I`) and CoT voice tags (`--cot-tags`) only work on `seed-tts-2.0-expressive`, which the TTS script selects automatically when either is used:

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "引航者……你为什么说这些话……" -v S_abc12345 -I "用最悲伤的语气演绎下面这句话："
```

`--tone-fidelity` makes the model stay closer to the training sample's timbre and style (same-language text only).

## Environment Variables

| Variable | Used by | Description |
| -------- | ------- | ----------- |
| `VOLCENGINE_TTS_API_KEY` | train/status/upgrade | Speech API Key from the console |
| `VOLCENGINE_TTS_BASE` | train/status/upgrade | Optional, defaults to `https://openspeech.bytedance.com` |
| `VOLCENGINE_TTS_APPID` | list/order/renew | Speech service App ID |
| `VOLCENGINE_ACCESS_KEY` | list/order/renew | Volcengine account Access Key |
| `VOLCENGINE_SECRET_KEY` | list/order/renew | Volcengine account Secret Key |

## Examples

### Clone a Chinese Voice

```bash
{python} {skill_dir}/scripts/volcengine-voice-clone.py train sample.wav -s S_abc12345 -l cn -t "今天天气真不错，我们一起出去走走吧。"
```

### Clone with Denoising and a Demo Preview

```bash
{python} {skill_dir}/scripts/volcengine-voice-clone.py train noisy_sample.mp3 -s S_abc12345 --denoise --demo-text "大家好，这是我的克隆音色。"
```

### Check Training Status and Download the Demo

```bash
{python} {skill_dir}/scripts/volcengine-voice-clone.py status S_abc12345 --download-demo
```

### Upgrade a V1 Voice

```bash
{python} {skill_dir}/scripts/volcengine-voice-clone.py upgrade S_abc12345
```

### List All Trained Voices

```bash
{python} {skill_dir}/scripts/volcengine-voice-clone.py list --state Success
```

### Purchase and Renew (PAID)

```bash
{python} {skill_dir}/scripts/volcengine-voice-clone.py order --quantity 1 --times 12
{python} {skill_dir}/scripts/volcengine-voice-clone.py renew S_abc12345 --times 6
```
