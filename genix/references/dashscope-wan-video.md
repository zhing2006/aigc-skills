# DashScope Wan 3.0 Video

Video generation using Alibaba Bailian (DashScope) **Wan 3.0** — an all-in-one
reference model that covers text-to-video, first/last-frame video, multi-modal
reference video, and uniquely **document-to-video** and **webpage-to-video** in a
single model. Output is up to **30 seconds** at a fixed **30fps**. The native API
is asynchronous (create task → poll → download), handled automatically by the
script.

## Contents

- [Commands](#commands)
- [Supported Models](#supported-models)
- [Input Group Exclusivity](#input-group-exclusivity)
- [Media Input Limits](#media-input-limits)
- [Prompt Best Practices](#prompt-best-practices)
- [Examples](#examples)
- [Environment Variables](#environment-variables)

| Mode | Trigger | Notes |
| ---- | ------- | ----- |
| Text-to-Video | prompt only | `ratio` defaults to `adaptive` |
| First Frame | `--first-frame` | the image is used strictly as frame 1 |
| Last Frame | `--last-frame` | the image is used strictly as the final frame |
| First + Last Frame | `--first-frame` + `--last-frame` | transition between two stills |
| Reference (all-in-one) | `--ref-image` / `--ref-video` / `--ref-audio` | refer to them as `图1`, `视频1`, `音频1` in the prompt |
| Document-to-Video | `--file` | pptx / pdf / docx / xlsx / md …, ≤50 pages |
| Webpage-to-Video | `--link` | any public page needing no login |

## Commands

### generate (default)

Create a video generation task and wait for the result. The `generate` keyword
can be omitted.

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py generate "prompt" [options]
{python} {skill_dir}/scripts/dashscope-wan-video.py "prompt" [options]
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Conditional | Required unless at least one media input is given. In reference mode, refer to assets as `图1` / `视频1` / `音频1` |

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--first-frame` | None | First frame image path/URL (strictly frame 1) |
| `--last-frame` | None | Last frame image path/URL (strictly the final frame) |
| `--ref-image` | None | Reference image path/URL (repeatable, up to 10) → `图1`, `图2`, … |
| `--ref-video` | None | Reference video **URL** (repeatable, up to 5; each 1-15s, 15s combined) → `视频1`, … |
| `--ref-audio` | None | Reference audio **URL** (repeatable, up to 5; each 1-15s, 15s combined) → `音频1`, … |
| `--file` | None | Document **URL** → Document-to-Video. Mutually exclusive with `--link` |
| `--link` | None | Public webpage **URL** → Webpage-to-Video. Mutually exclusive with `--file` |
| `-m`, `--model` | `wan3.0-video` | Model ID (`wan3.0-video` / `wan3.0-video-prime`) |
| `--prime` | false | Shorthand for `-m wan3.0-video-prime` (high-speed variant) |
| `-r`, `--resolution` | `1080P` | Video resolution (`480P`, `720P`, `1080P`; lowercase accepted) |
| `-a`, `--ratio` | `adaptive` | Aspect ratio (`adaptive`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`) |
| `-d`, `--duration` | `5` | Duration in seconds (2-30), or `-1` for auto duration |
| `--no-audio` | false | Generate a silent video (audio is on by default, same price) |
| `--no-prompt-extend` | false | Disable LLM prompt rewriting (on by default) |
| `--watermark` | false | Add an AI-generated watermark (off by default) |
| `--seed` | None | Random seed `0-2147483647` for reproducibility |
| `-o`, `--output` | `generated_video.mp4` | Output file path |

### get

Query a single video generation task by ID. Task IDs and result URLs are valid for **24 hours**.

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py get <task_id>
```

## Supported Models

| Model | Description |
| ----- | ----------- |
| `wan3.0-video` | Standard version (default) |
| `wan3.0-video-prime` | High-speed version — matches the standard model's capabilities with significantly faster end-to-end generation |

Both models support every mode and every parameter. Use `--prime` (or
`-m wan3.0-video-prime`) when turnaround time matters more than anything else.

## Input Group Exclusivity

Wan 3.0 splits media inputs into two groups that **cannot be mixed in one request**:

| Group | Types |
| ----- | ----- |
| Frame group | `--first-frame`, `--last-frame` |
| Reference group | `--ref-image`, `--ref-video`, `--ref-audio`, `--file`, `--link` |

Additionally `--file` and `--link` are mutually exclusive — at most one document
**or** one webpage per request. The script rejects invalid combinations before
sending anything.

## Parameter Applicability

Every parameter applies to every mode. `ratio` defaults to `adaptive`, which lets
the model infer the aspect ratio from the input media and the prompt's intent —
prefer leaving it on `adaptive` when you supply frames or reference video.

| Parameter | Notes |
| --------- | ----- |
| `resolution` | `480P` / `720P` / `1080P` (default) |
| `ratio` | `adaptive` (default) / `16:9` / `4:3` / `1:1` / `3:4` / `9:16` |
| `duration` | `2`-`30` seconds (default `5`), or `-1` for auto duration |
| `audio` | On by default; `--no-audio` drops the audio track. **Same price either way** |
| `prompt_extend` | On by default; noticeably improves short prompts at the cost of latency |
| `watermark` | Off by default (the opposite of HappyHorse) |
| `seed` | `0`-`2147483647` |

## Supported Resolutions

`480P`, `720P`, `1080P` (default). Lowercase (`480p` / `720p` / `1080p`) is accepted and normalized.

## Supported Aspect Ratios

`adaptive` (default), `16:9`, `4:3`, `1:1`, `3:4`, `9:16`

## Supported Durations

`2` to `30` seconds (integer), default `5`. Output frame rate is always **30fps**.

- `-1` enables **auto duration**: the model picks a length from the prompt, the
  content and the supplied media.
- With reference video input, the API caps **input video total + output duration
  at 30 seconds**. The script cannot check this locally (it never decodes media),
  so an over-budget request fails server-side.

## Media Input Limits

**Only images can be inlined.** Local image paths are auto-encoded to base64 data
URIs; public URLs and OSS temporary URLs (`oss://dashscope-instant/...`) are
passed through. Video, audio and document inputs **must already be a URL** — the
script rejects local paths with an explicit message rather than failing at the API.

| Input | Count | Limits |
| ----- | ----- | ------ |
| `first_frame` / `last_frame` | ≤1 each | JPEG/JPG/PNG (no alpha)/BMP/WEBP, each side 240-8000px, aspect ≤8:1, ≤20MB |
| `reference_image` | ≤10 | same image limits as above |
| `reference_video` | ≤5 | mp4/mov, each 1-15s and **15s combined**, each side 240-4096px, aspect ≤8:1, ≤100MB per file. **URL only** |
| `reference_audio` | ≤5 | wav/mp3, each 1-15s and **15s combined**, ≤15MB. **URL only** |
| `file` | ≤1 | docx/doc/xlsx/xls/pptx/ppt/pdf/txt/key/pages/numbers/md, ≤100MB, ≤50 pages. **URL only** |
| `link` | ≤1 | a public webpage (news, blog, article) needing no login. **URL only** |

## Prompt Best Practices

Prefer the first-party
[Wan 3.0 API reference](https://help.aliyun.com/zh/model-studio/wan-video-api-reference)
examples over generic prompt collections.

### Prompt Length & Language

- Max: 20000 characters (each Chinese character or letter counts as one); excess is auto-truncated
- Chinese and English are both supported

### Referring to reference assets — use Chinese ordinals

This is the single biggest difference from HappyHorse. Wan 3.0 expects **Chinese
ordinals**, not `[Image 1]`:

| Asset | Reference in prompt |
| ----- | ------------------- |
| `--ref-image` (1st, 2nd, …) | `图1`, `图2`, … |
| `--ref-video` (1st, 2nd, …) | `视频1`, `视频2`, … |
| `--ref-audio` (1st, 2nd, …) | `音频1`, `音频2`, … |

Numbering follows the flag order on the command line, and **each type is counted
separately** — the first `--ref-video` is `视频1` even when three `--ref-image`
flags came before it. Identify what inside each asset you mean; do not just write
"用图1".

```text
图1中的女主角走进视频1的巷道，脚步节奏跟随音频1的鼓点。
```

### Mode-specific patterns

#### Text-to-Video

```text
Subject + specific action + environment/lighting + camera + visual style
```

Prefer `黄昏时暖金色侧光从左侧打入` over `光线很好`. Sequence multiple actions
chronologically. With `-d` up to 30 seconds you can write a genuine multi-shot
sequence — describe each shot in order and mark the cuts.

#### First / Last Frame

The frame images already fix the subject, style, composition and aspect ratio.
Spend the prompt on motion, camera behavior, environmental change, and what must
stay consistent. For First + Last Frame, describe the **path between** the two
stills rather than redescribing either one.

```text
从首帧的冬季庭院自然过渡到尾帧的夏日庭院：积雪逐渐消融，枝头抽芽开花，
光线由清冷转为温暖。固定机位，过渡连续无跳变。
```

#### Reference (all-in-one)

Assign every asset one clear job and state the relationships between them.

```text
图1中的人物拿起图2中的产品，在图3的场景里缓慢走向镜头；
镜头运动参考视频1的节奏，背景音乐使用音频1。
```

#### Document-to-Video

The model reads the document and builds the video from it, so the prompt is a
**creative brief**, not a content description: name the style, palette, pacing,
shot progression, on-screen graphics and ending. Let the document supply the
facts and the parameters.

```text
一支高端智能眼镜产品广告，整体风格极简、未来感，光影克制，画面以黑色、
银灰色、冰蓝色为主色调。开场产品从纯黑背景中浮现，超近距离掠过镜片与转轴细节，
随后模特佩戴展示，结尾推进到品牌 logo 与 slogan。极简电子配乐，节奏干净有力。
```

#### Webpage-to-Video

Same idea as document mode. Say what the video is *for* (explainer, news recap,
social teaser), the tone, and how long each beat should run. Keep `-d -1` in mind
when you do not know how much material the page holds.

### Cross-mode rules

1. Use specific, observable actions rather than abstract adjectives.
2. Sequence actions in event order and keep transitions physically connected.
3. Keep camera instructions purposeful; use a cut when camera behavior changes.
4. For reference inputs, assign each asset one clear responsibility.
5. Leave `prompt_extend` on for short prompts; disable it with
   `--no-prompt-extend` when you have written a long, precise prompt and want it
   respected verbatim.
6. Fix `--seed` when repeatability matters, but do not promise identical output —
   and pair it with `--no-prompt-extend`, because prompt rewriting is applied
   before generation and only the *original* prompt comes back in `orig_prompt`,
   so a rewritten prompt is never observable or reproducible.
7. Do not append an unsupported universal negative-prompt list.

### Camera and shots

Camera: 推/拉镜头 (dolly), 左/右摇 (pan), 上仰/下俯 (tilt), 跟镜头 (tracking),
升/降镜头 (crane), 环绕运镜 (orbit), 固定机位 (static), 航拍 (aerial).
Shots: 特写 / 近景 / 中景 / 全景 / 远景 / 大远景.

Use quality and style words only when they add information. Resolution is
controlled by `--resolution`; do not claim `4K` when Wan 3.0 output tops out at
1080P.

```text
细节丰富，画面稳定，色彩自然，电影质感，运动流畅
```

## Examples

### Text-to-Video

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py "清晨的老书店，店主推开木门，尘埃在斜射的光束中浮动。一位年轻女子走进来，店主指向角落的一本书。固定机位中景转缓慢推镜，暖色调，电影质感。" -a 16:9 -d 10 -o bookshop.mp4
```

### First Frame

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py "首帧中的猫先压低前腿蓄力，随后沿草地向画面右侧自然奔跑，尾巴随步伐摆动。低机位平稳跟拍，保持猫的花纹与场景风格一致。" -i cat_first_frame.png -d 5 -o cat_run.mp4
```

### First + Last Frame Transition

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py "从首帧的冬季庭院自然过渡到尾帧的夏日庭院：积雪逐渐消融，枝头抽芽开花，光线由清冷转为温暖。固定机位，过渡连续无跳变。" -i winter.png --last-frame summer.png -d 6 -o seasons.mp4
```

### Reference (image + video + audio)

Refer to each asset with Chinese ordinals, numbered per type in flag order:

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py "图1中身着红色旗袍的女性走进图2的雨夜巷道，镜头运动参考视频1的跟拍节奏，脚步与音频1的鼓点同步。最后推近至面部特写。" --ref-image girl.jpg --ref-image alley.jpg --ref-video "https://example.com/camera_ref.mp4" --ref-audio "https://example.com/drums.mp3" -a 9:16 -d 12 -o qipao.mp4
```

### Document-to-Video (PPT / PDF)

The document must be a public URL or an OSS temporary URL:

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py "一支高端智能眼镜产品广告，极简未来感，黑色/银灰/冰蓝主色调。开场产品从纯黑背景浮现，超近距离掠过镜片与转轴细节，随后模特佩戴展示，结尾推进到品牌 logo 与 slogan。极简电子配乐。" --file "https://example.com/glass.pptx" -r 720P -a 16:9 -d 10 -o glasses_ad.mp4
```

### Webpage-to-Video

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py "把这篇文章做成一条社交平台科普短片：开场一句钩子，中段三个要点各配一组画面，结尾一句总结。明快节奏，竖屏，字幕简洁。" --link "https://example.com/article/ai-basics" -a 9:16 -d -1 -o explainer.mp4
```

### Auto Duration + High-Speed Model

`-d -1` lets the model choose the length; `--prime` trades nothing but time:

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py "微距镜头，露珠从花瓣滑落，慢动作，浅景深" --prime -d -1 -r 720P --no-audio --seed 42 -o dewdrop.mp4
```

### Get Task

```bash
{python} {skill_dir}/scripts/dashscope-wan-video.py get 0385dc79-5ff8-4d82-bcb6-xxxxxx
```

## Environment Variables

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `DASHSCOPE_API_KEY` | Yes | API key for Alibaba Bailian (DashScope) |
| `DASHSCOPE_WORKSPACE_ID` | No | Business-space ID. When set (and no explicit base URL is given), the Beijing business-space host `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com` is built automatically. The shared default host serves Wan 3.0 too, so this is only needed to target a business space |
| `DASHSCOPE_VIDEO_BASE_URL` | No | Native async API host (default: `https://dashscope.aliyuncs.com`). May contain a `{WorkspaceId}` placeholder, substituted from `DASHSCOPE_WORKSPACE_ID` — e.g. `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com` for Singapore |

Set in `.genix.env` file.

**Note**: The model, endpoint URL, and API Key must all belong to the **same region** — cross-region calls fail. The shared `https://dashscope.aliyuncs.com` host (the default) serves Wan 3.0, so no extra configuration is normally needed. If a request is rejected for an unknown model or missing permission, set `DASHSCOPE_WORKSPACE_ID` to your business-space ID and retry.

