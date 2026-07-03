# Volcengine Voice Design

Design custom voices from a text description or a reference image using Volcengine Voice Design.

## Usage

```bash
# Design a voice from a text description (create is the default action)
{python} {skill_dir}/scripts/volcengine-voice-design.py "voice description" -s <speaker_id> -t "preview text" [options]

# Design a voice from an image
{python} {skill_dir}/scripts/volcengine-voice-design.py --image portrait.png -s <speaker_id> -t "preview text"

# Query the status of a voice
{python} {skill_dir}/scripts/volcengine-voice-design.py status <speaker_id> [options]
```

## Create Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `text_prompt` | One of the three | Voice description (max 200 chars) |
| `--image` | One of the three | Local image file as the prompt (max 10MB) |
| `--image-url` | One of the three | Downloadable image URL as the prompt |
| `-s`, `--speaker-id` | Yes | Purchased speaker ID (`S_xxx`) |
| `-t`, `--preview-text` | Yes | Demo text synthesized with the designed voice (max 300 chars) |

## Create Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-l`, `--language` | `cn` | Voice language: `cn` / `en` (preview text must match) |
| `-o`, `--output` | `<speaker_id>_demo.mp3` | Demo audio output path |

## Status Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--download-demo` | Off | Download the demo audio if available |
| `-o`, `--output` | `<speaker_id>_demo.mp3` | Demo audio output path |

## Prompt Best Practices

Describe the voice with **concrete, specific traits** across several dimensions — avoid vague words like "好听" or "普通":

| Dimension | Example keywords |
| --------- | ---------------- |
| Gender | 女性 / 男性 |
| Age | 少女感 / 青年 / 中年 / 老者 |
| Pitch | 音调低沉 / 清脆高亢 |
| Speed | 语速中等偏快 / 缓慢从容 |
| Timbre | 沙哑 / 清亮 / 磁性 / 温润 / 有力 |
| Style / role | 新闻播报腔 / 动漫少女 / 深夜电台主播 / 说书人 |

**Good prompts:**

```text
女性，语速中等偏快，语调低沉有力
中年男性，声音低沉磁性，语速缓慢，深夜电台主播风格
少女音，清脆活泼，语速偏快，动漫角色感
```

**Bad prompts:**

```text
好听的声音          # too vague
一个普通人          # no usable traits
```

## Image Prompt

- Provide `--image` (local file, base64-encoded, max 10MB) or `--image-url` (downloadable URL).
- When both an image and a text prompt are given, the **image takes priority**.
- The model infers a matching voice from the character's appearance/temperament in the image.

## Notes

1. Each speaker ID has a limited number of design attempts (`available_training_times` is printed; error 45001123 when exhausted).
2. Demo audio URLs are valid for **1 hour** — the script downloads them immediately.
3. Once status is 2 (Success) or 4 (Active), synthesize with the designed voice via `seed-icl-2.0` (auto-detected):

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "夜色渐浓，城市的灯火次第亮起。" -v S_abc12345
```

## Examples

### Design from a Text Description

```bash
{python} {skill_dir}/scripts/volcengine-voice-design.py "女性，语速中等偏快，语调低沉有力" -s S_abc12345 -t "夜色渐浓，城市的灯火次第亮起，每个人都在为自己的生活奔波。"
```

### Design from a Local Image

```bash
{python} {skill_dir}/scripts/volcengine-voice-design.py --image character.png -s S_abc12345 -t "初次见面，请多多关照。"
```

### Design an English Voice

```bash
{python} {skill_dir}/scripts/volcengine-voice-design.py "Middle-aged male, deep and calm, documentary narrator" -s S_abc12345 -t "The city lights come alive as night falls." -l en
```

### Query Status and Download the Demo

```bash
{python} {skill_dir}/scripts/volcengine-voice-design.py status S_abc12345 --download-demo
```

## Environment Variables

Requires `VOLCENGINE_TTS_API_KEY` (Volcengine speech API Key) to be set in `.env` file. `VOLCENGINE_TTS_BASE` is optional (defaults to `https://openspeech.bytedance.com`).
