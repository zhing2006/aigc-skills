# Volcengine Text-to-Speech

Streaming Text-to-Speech using Volcengine Doubao Seed-TTS 2.0, with support for official voices, cloned/designed voices, voice instructions, dialects, and CoT voice tags.

## Usage

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "text" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `text` | Yes (or `-i`) | Text to synthesize |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--input` | None | Input text file path (alternative to `text`) |
| `-v`, `--voice` | `zh_female_vv_uranus_bigtts` | Voice ID (official voice or cloned `S_xxx` voice) |
| `-m`, `--model` | Auto | Cloned-voice model: `seed-tts-2.0-standard` / `seed-tts-2.0-expressive` |
| `--resource-id` | Auto | Override `X-Api-Resource-Id` (`seed-tts-2.0` / `seed-icl-2.0`) |
| `-f`, `--format` | `mp3` | Output format: `mp3` / `wav` / `pcm` / `ogg_opus` |
| `-r`, `--sample-rate` | `24000` | Sample rate: 8000-48000 Hz |
| `--bit-rate` | None | MP3 bit rate in bps (64000-160000) |
| `--speed` | `0` | Speech rate: -50 (0.5x) to 100 (2.0x) |
| `--loudness` | `0` | Loudness: -50 (0.5x) to 100 (2.0x) |
| `--pitch` | `0` | Pitch shift: -12 to 12 |
| `-I`, `--instruction` | None | Voice instruction (`context_texts`); only the first one takes effect |
| `--cot-tags` | Off | Parse `<cot text=...>...</cot>` voice tags (cloned expressive voices only) |
| `--dialect` | None | `sichuan` / `shaanxi` / `dongbei`; needs a dialect-capable voice |
| `--section-id` | None | Shared ID that carries context across successive calls |
| `--tone-fidelity` | Off | Restore the training prompt's timbre/style (cloned voices) |
| `--ssml` | Off | Parse text as SSML markup (2.0 models support `<phoneme>` only) |
| `--subtitle` | Off | Save word-level timestamps to `<output>.json` (zh/en, official voices only) |
| `--silence-duration` | None | Trailing silence in ms (0-30000) |
| `--explicit-language` | Auto | Only read the specified language (`zh-cn`/`en`/`ja`/...) |
| `--keep-markdown` | Off | Read Markdown syntax literally (stripped by default) |
| `--strip-emoji` | Off | Strip emoji instead of reading them out |
| `--filter-parenthesis` | Off | Skip text inside parentheses instead of reading it |
| `--latex` / `--latex-v2` | Off | Read LaTeX formulas (`--latex-v2` is stronger but slower) |
| `--watermark` | Off | Add an audible AIGC watermark at the end |
| `-o`, `--output` | `tts_output.<ext>` | Output file path |

## Voice Types, Resource IDs & Models

The script auto-detects the API resource ID from the voice ID:

| Voice ID pattern | Type | Resource ID | Model |
| ---------------- | ---- | ----------- | ----- |
| `*_uranus_bigtts` (e.g. `zh_female_vv_uranus_bigtts`) | Official Seed-TTS 2.0 voice | `seed-tts-2.0` | — |
| `ICL_uranus_*_tob` (role-play catalog voices) | Official Seed-TTS 2.0 voice | `seed-tts-2.0` | — |
| `S_xxxxxxxx` / `icl_xxx` | Cloned / designed voice (Voice Clone 2.0) | `seed-icl-2.0` | see below |

Cloned voices have two model versions (`-m`):

| Model | Latency | Voice instructions | CoT tags | Notes |
| ----- | ------- | ------------------ | -------- | ----- |
| `seed-tts-2.0-standard` | Lower | Dropped | Dropped | Default when no instruction/tag is used |
| `seed-tts-2.0-expressive` | Higher | Supported | Supported | Auto-selected with `-I` or `--cot-tags`; output varies between runs |

Use `--resource-id` to override the auto-detection if needed.

## Official Voices (Seed-TTS 2.0)

All `*_uranus_bigtts` voices support instruction following (`-I`).

| Name | Voice ID | Notes |
| ---- | -------- | ----- |
| Vivi 2.0 | `zh_female_vv_uranus_bigtts` | Default; zh/ja/id/es-mx + Sichuan/Shaanxi/Dongbei dialects |
| 小何 2.0 | `zh_female_xiaohe_uranus_bigtts` | Female, general |
| 云舟 2.0 | `zh_male_m191_uranus_bigtts` | Male, narration |
| 小天 2.0 | `zh_male_taocheng_uranus_bigtts` | Male, general |
| 刘飞 2.0 | `zh_male_liufei_uranus_bigtts` | Male, expressive |
| 知性灿灿 2.0 | `zh_female_cancan_uranus_bigtts` | Female, role-play |
| 清新女声 2.0 | `zh_female_qingxinnvsheng_uranus_bigtts` | Female, fresh |
| 爽快思思 2.0 | `zh_female_shuangkuaisisi_uranus_bigtts` | Female, brisk |
| 邻家女孩 2.0 | `zh_female_linjianvhai_uranus_bigtts` | Female, young |
| 高冷御姐 2.0 | `zh_female_gaolengyujie_uranus_bigtts` | Female, cool |
| 少年梓辛 2.0 | `zh_male_shaonianzixin_uranus_bigtts` | Male, teen |
| 儒雅青年 2.0 | `zh_male_ruyaqingnian_uranus_bigtts` | Male, refined (audiobooks) |
| 擎苍 2.0 | `zh_male_qingcang_uranus_bigtts` | Male, epic narration |
| 傲娇霸总 2.0 | `zh_male_aojiaobazong_uranus_bigtts` | Male, arrogant CEO |
| 儿童绘本 2.0 | `zh_female_xiaoxue_uranus_bigtts` | Children's storybooks |
| Tina老师 2.0 | `zh_female_yingyujiaoxue_uranus_bigtts` | Chinese + British English (teaching) |
| Tim | `en_male_tim_uranus_bigtts` | American English |
| Dacey | `en_female_dacey_uranus_bigtts` | American English |

The 2.0 catalog also contains a large role-play family with `ICL_uranus_*_tob` IDs (可爱女生, 调皮公主, 爽朗少年, 天才同桌, ...). Those are character voices **without** instruction-following support — `-I` has little or no effect on them. The full list lives in the Volcengine speech console.

## Voice Instructions (语音指令)

Voice instructions are the way to control delivery on Seed-TTS 2.0: emotion, tone, style, speed, volume, and dialect flavour. They are passed with `-I/--instruction` (API `additions.context_texts`) and correspond to the `[#...]` field in the console UI.

| Purpose | Example instruction |
| ------- | ------------------- |
| Overall emotion | `用颤抖沙哑、带着崩溃与绝望的哭腔，夹杂着质问与心碎的语气说` |
| Multi-layer emotion | `用试探性的犹豫、带点害羞又藏着温柔期待的语气说` |
| Tone / style | `用asmr的语气来试试撩撩我` |
| Argument / conflict | `你得跟我互怼！就是跟我用吵架的语气对话` |
| Speed | `你可以说慢一点吗？` |
| Volume | `你嗓门再小点。` |
| Dialect flavour | `用四川话说` |

**Notes:**

1. **Only the first instruction takes effect** — the API ignores later `-I` values.
2. Instructions are **not billed** and are **not read aloud**.
3. Supported by official Seed-TTS 2.0 voices and by cloned voices on `seed-tts-2.0-expressive` (the standard cloned model silently drops them).
4. The instruction applies to the **whole request**; there is no per-sentence instruction. Split the text and call once per delivery change (see `--section-id`).

## Quoting the Previous Turn (引用上文)

An instruction can also be the *preceding* line of dialogue instead of a directive. The model reads the context and continues its mood — useful for LLM replies and conversational scenes:

```bash
# Previous line: "是……是你吗？怎么看着……好像没怎么变啊？"
{python} {skill_dir}/scripts/volcengine-text-speech.py "你头发长了…… 以前总说留不长，十年了…… 你还好吗？" \
  -I "是……是你吗？怎么看着……好像没怎么变啊？" -o reunion.mp3
```

## CoT Voice Tags (语音标签)

CoT tags are inline `<cot text=...>...</cot>` spans that steer speed and emotion **sentence by sentence**. They require `--cot-tags` (API `additions.use_tag_parser`).

```
<cot text=急促难耐>工作占据了生活的绝大部分</cot>，只有去做自己认为伟大的工作，才能获得满足感。<cot text=语速缓慢>不管生活再苦再累，都绝不放弃寻找</cot>。
```

**Notes:**

1. Tags only work with **Voice Clone 2.0 voices on `seed-tts-2.0-expressive`**. Official 2.0 voices (including `*_uranus_bigtts`) ignore them — use `-I` instructions there.
2. Keep each sentence under ~64 characters, tags included; a tag's effect is scoped to its sentence.
3. Bare bracket text such as `[怒目圆睁]` is **not** a tag — it is read aloud or dropped. Use `-I` or `--filter-parenthesis` instead.

## Dialects

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "巴适得板，走嘛一起去吃火锅。" --dialect sichuan -o sichuan.mp3
```

`--dialect` accepts `sichuan` / `shaanxi` / `dongbei` and requires a dialect-capable voice — currently Vivi 2.0 (`zh_female_vv_uranus_bigtts`). Without such a voice the parameter has no effect; an instruction like `-I "用四川话说"` is the fallback.

## Context Across Calls (section_id)

Passing the same `--section-id` (a UUID you generate) across successive calls lets the service keep the conversational context, so a long text split into segments keeps a consistent mood:

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "第一段……" --section-id 8f1c6c0e-1 -o part1.mp3
{python} {skill_dir}/scripts/volcengine-text-speech.py "第二段……" --section-id 8f1c6c0e-1 -o part2.mp3
```

Server-side history is limited (about 30 turns / 10 minutes) and works with Seed-TTS 2.0 and Voice Clone 2.0 voices.

## Prompt Best Practices

1. **Be concrete**: describe voice quality plus emotion (`颤抖沙哑`, `哭腔`, `悄悄话`) rather than one abstract word — `用怒目圆睁、大声怒吼的语气说` beats `生气`.
2. **One instruction per call**: stack the dimensions into a single sentence instead of passing several `-I` values.
3. **Avoid duplication**: when the instruction conveys a laugh or sigh, do not also write "哈哈"/"唉" in the text.
4. **Long texts**: split texts over ~300 Chinese characters, synthesize per segment with a shared `--section-id`, and concatenate.
5. **Stage directions in the text**: strip them, or use `--filter-parenthesis` so `（小声嘀咕）` is skipped instead of read aloud.
6. **SSML**: Seed-TTS 2.0 and Voice Clone 2.0 only support the `<phoneme>` tag; do not mix SSML with CoT tags.

## Output Format Notes

- `mp3` (default) is the safest choice for saved files.
- `pcm` is raw audio without a header; the sample rate/bit depth are what you requested.
- `wav` from the streaming API may have an imprecise header size field; prefer `mp3` or `pcm` when exact headers matter.

## Examples

### Basic Chinese TTS

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "夜色渐浓，城市的灯火次第亮起。" -o night.mp3
```

### Emotional Synthesis with a Voice Instruction

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "我逆转时空九十九次救你，你却次次死于同一支暗箭。" -I "用颤抖沙哑、带着崩溃与绝望的哭腔说" -o heartbroken.mp3
```

### Angry Role-Play Line

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "放肆！我是龙族的女王，岂容你这蝼蚁来评判我！" -v zh_female_gaolengyujie_uranus_bigtts -I "用怒目圆睁、冲着对方大声怒吼的语气说" -o dragon_queen.mp3
```

### Lower Pitch and Slower Delivery

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "高兄，你看这烛火，要灭了……" --pitch -4 --speed -15 -I "用低沉沙哑的语气、带着沧桑与绝望地说" -o dying_swordsman.mp3
```

### Synthesize with a Cloned Voice

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "大家好，欢迎收听本期节目。" -v S_abc12345 -o cloned.mp3
```

### Cloned Voice with CoT Tags

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py "<cot text=急促难耐>工作占据了生活的绝大部分</cot>，只有去做自己认为伟大的工作，才能获得满足感。" -v S_abc12345 --cot-tags -o cot_tags.mp3
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

### Read Formulas in a Lesson Script

```bash
{python} {skill_dir}/scripts/volcengine-text-speech.py -i lesson.md --latex-v2 -o lesson.mp3
```

## Environment Variables

Requires `VOLCENGINE_TTS_API_KEY` (Volcengine speech API Key from the console API Key page) to be set in `.env` file. `VOLCENGINE_TTS_BASE` is optional (defaults to `https://openspeech.bytedance.com`).
