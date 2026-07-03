# Volcengine Text-to-Speech

Streaming Text-to-Speech using Volcengine Doubao Seed-TTS 2.0, with support for official voices, cloned/designed voices, voice tags, and voice instructions.

## Usage

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "text" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `text` | Yes (or `-i`) | Text to synthesize; may contain `[voice tags]` before sentences |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--input` | None | Input text file path (alternative to `text`) |
| `-v`, `--voice` | `zh_female_vv_uranus_bigtts` | Voice ID (official voice or cloned `S_xxx` voice) |
| `-m`, `--model` | Auto | Model version; cloned voices default to `seed-tts-2.0-standard` |
| `--resource-id` | Auto | Override `X-Api-Resource-Id` (`seed-tts-2.0` / `seed-icl-2.0`) |
| `-f`, `--format` | `mp3` | Output format: `mp3` / `wav` / `pcm` / `ogg_opus` |
| `-r`, `--sample-rate` | `24000` | Sample rate: 8000-48000 Hz |
| `--bit-rate` | None | MP3 bit rate in bps (64000-160000) |
| `--speed` | `0` | Speech rate: -50 (0.5x) to 100 (2.0x) |
| `--loudness` | `0` | Loudness: -50 (0.5x) to 100 (2.0x) |
| `-I`, `--instruction` | None | Voice instruction (repeatable); official voices only |
| `--ssml` | Off | Parse text as SSML markup |
| `--subtitle` | Off | Save word-level timestamps to `<output>.json` (zh/en only) |
| `--silence-duration` | None | Trailing silence in ms (0-30000) |
| `--explicit-language` | Auto | Only read the specified language (`zh-cn`/`en`/`ja`/...) |
| `--keep-markdown` | Off | Read Markdown syntax literally (stripped by default) |
| `--watermark` | Off | Add an audible AIGC watermark at the end |
| `-o`, `--output` | `tts_output.<ext>` | Output file path |

## Voice Types & Resource IDs

The script auto-detects the API resource ID from the voice ID:

| Voice ID pattern | Type | Resource ID | Model |
| ---------------- | ---- | ----------- | ----- |
| `*_uranus_bigtts` (e.g. `zh_female_vv_uranus_bigtts`) | Official Seed-TTS 2.0 voice | `seed-tts-2.0` | — |
| `S_xxxxxxxx` | Cloned / designed voice (Voice Clone 2.0) | `seed-icl-2.0` | `seed-tts-2.0-standard` |

Use `--resource-id` to override the auto-detection if needed.

## Official Voices (Seed-TTS 2.0)

| Name | Voice ID | Notes |
| ---- | -------- | ----- |
| Vivi 薇薇 | `zh_female_vv_uranus_bigtts` | Female, expressive (default) |
| 刘飞 | `zh_male_liufei_uranus_bigtts` | Male, expressive |
| 云舟 | `zh_male_m191_uranus_bigtts` | Male, narration |
| 灿灿 | `zh_female_cancan_uranus_bigtts` | Female |

The full voice list (including tag-capable voices such as 可爱女生, 调皮公主, 爽朗少年, 天才同桌) is available in the Volcengine speech console. 2.0 voices use the `*_uranus_bigtts` suffix.

## Voice Tags (语音标签)

Doubao 2.0 supports bracketed tags embedded directly in the text, placed **before a sentence**, describing facial expressions, inner thoughts / psychology, and body movements. Write them as concrete scene descriptions in natural language (Chinese works best):

| Category | Example |
| -------- | ------- |
| Emotion + action | `[怒目圆睁，冲着你大声怒吼]放肆！我是龙族的女王，岂容你来评判我！` |
| Narration mood | `[旁白，语调惊恐，强调恐怖气氛]可当他的手触碰到对方的身体时，却感觉一阵冰冷僵硬……` |
| Inner thoughts | `[心里既紧张又期待，声音发颤]那个……你今天，有空吗？` |
| Paralinguistics | `[长叹一口气，苦笑]算了，都过去了。` |

**Notes:**

1. Voice tags are an early-access feature. They are supported by **selected official 2.0 voices** (e.g. 可爱女生, 调皮公主, 爽朗少年, 天才同桌) and **all Voice Clone 2.0 voices** (`S_xxx`).
2. Tags describe *how* to speak; they are not read aloud.
3. Prefer specific scene/action descriptions over abstract adjectives: `[怒目圆睁，大声怒吼]` works better than `[生气]`.

## Voice Instructions (语音指令)

Voice instructions control the **overall** delivery — emotion, dialect, tone, speed, and pitch — and are passed via `-I/--instruction` (API `context_texts`). They can also quote preceding dialogue so the model continues the conversational mood ("引用上文").

| Purpose | Example instruction |
| ------- | ------------------- |
| Overall emotion | `用颤抖沙哑、带着崩溃与绝望的哭腔，夹杂着质问与心碎的语气说` |
| Dialect | `用四川话说` |
| Tone / style | `用asmr的语气来试试撩撩我` |
| Multi-layer emotion | `用试探性的犹豫、带点害羞又藏着温柔期待的语气说` |
| Quote context | `是……是你吗？怎么看着……好像没怎么变啊？` (the reply is synthesized in a matching mood) |

**Notes:**

1. Instructions are **not billed** and are **not read aloud**.
2. Only official Seed-TTS 2.0 voices support instructions; **cloned voices do not** (the script warns and ignores them).
3. Combine both: instructions set the global mood, voice tags refine individual sentences.

## Prompt Best Practices

1. **Be concrete**: describe the scene, action, and vocal quality (`颤抖沙哑`, `哭腔`, `悄悄话`) rather than a single abstract emotion word.
2. **Stack dimensions**: voice quality + emotion + intensity, e.g. `[#用低沉沙哑的语气、带着沧桑与绝望地说]`.
3. **Avoid duplication**: when a tag conveys a laugh/sigh, do not also write "哈哈"/"唉" in the text.
4. **Long texts**: split texts over ~300 Chinese characters and synthesize in segments; use `section_id`-free separate calls and concatenate.
5. **SSML**: only Chinese/English voices support SSML; do not mix SSML with voice tags.

## Output Format Notes

- `mp3` (default) is the safest choice for saved files.
- `pcm` is raw audio without a header; the sample rate/bit depth are what you requested.
- `wav` from the streaming API may have an imprecise header size field; prefer `mp3` or `pcm` when exact headers matter.

## Examples

### Basic Chinese TTS

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "夜色渐浓，城市的灯火次第亮起。" -o night.mp3
```

### Emotional Synthesis with Voice Tags

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "[怒目圆睁，冲着你大声怒吼]放肆！我是龙族的女王，岂容你这蝼蚁来评判我！" -o dragon_queen.mp3
```

### Overall Mood with a Voice Instruction

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "我逆转时空九十九次救你，你却次次死于同一支暗箭。" -I "用颤抖沙哑、带着崩溃与绝望的哭腔说" -o heartbroken.mp3
```

### Synthesize with a Cloned Voice

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "大家好，欢迎收听本期节目。" -v S_abc12345 -o cloned.mp3
```

### Word-Level Subtitles

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "今天天气不错。" --subtitle -o weather.mp3
```

### High-Quality WAV at 48kHz

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "专业级音频输出。" -f wav -r 48000 -o hq.wav
```

### Slow Down and Read a File

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py -i story.txt --speed -20 -o story.mp3
```

## Environment Variables

Requires `VOLCENGINE_TTS_API_KEY` (Volcengine speech API Key from the console API Key page) to be set in `.env` file. `VOLCENGINE_TTS_BASE` is optional (defaults to `https://openspeech.bytedance.com`).
