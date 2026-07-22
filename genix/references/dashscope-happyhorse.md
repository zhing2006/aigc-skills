# DashScope HappyHorse Video

Video generation using Alibaba Bailian (DashScope) **HappyHorse** — physically
realistic, smoothly-moving video. Four modes are supported, auto-detected from
the inputs you provide. The native API is asynchronous (create task → poll →
download), handled automatically by the script.

## Contents

- [Commands](#commands)
- [Supported Models](#supported-models)
- [Prompt Best Practices](#prompt-best-practices)
- [Examples](#examples)
- [Environment Variables](#environment-variables)

| Mode | Trigger | Model suffix | Notes |
| ---- | ------- | ------------ | ----- |
| Text-to-Video (t2v) | prompt only | `-t2v` | supports `ratio` |
| Image-to-Video (i2v) | `--first-frame` | `-i2v` | prompt optional; aspect follows the first frame (no `ratio`) |
| Reference-to-Video (r2v) | `--ref-image` (1-9) | `-r2v` | refer to images as `[Image 1]`, `[Image 2]`, … in the prompt |
| Video Edit (video-edit) | `--video` (+ 0-5 `--ref-image`) | `-video-edit` | duration/aspect follow the source; supports `--audio-setting` |

## Commands

### generate (default)

Create a video generation task and wait for the result. The `generate` keyword
can be omitted.

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py generate "prompt" [options]
{python} {skill_dir}/scripts/dashscope-happyhorse.py "prompt" [options]
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Conditional | Required for t2v / r2v / video-edit; optional for i2v |

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--first-frame` | None | First frame image path/URL → Image-to-Video |
| `--ref-image` | None | Reference image path/URL (repeatable). 1-9 → Reference-to-Video; with `--video`, 0-5 edit references |
| `--video` | None | Source video **public URL** → Video Edit |
| `--version` | `1.1` | Model version (`1.1` / `1.0`); video-edit is always `1.0` |
| `-m`, `--model` | derived | Explicit model ID (overrides mode/version derivation) |
| `-r`, `--resolution` | `1080P` | Video resolution (`720P`, `1080P`; lowercase accepted) |
| `-a`, `--ratio` | `16:9` | Aspect ratio (t2v / r2v only; ignored otherwise) |
| `-d`, `--duration` | `5` | Duration in seconds (3-15); ignored for video-edit (follows source) |
| `--audio-setting` | None | Video-edit only: `auto` (model decides) or `origin` (keep source audio) |
| `--no-watermark` | false | Disable the "Happy Horse" watermark (API adds it by default) |
| `--seed` | None | Random seed `0-2147483647` for reproducibility |
| `-o`, `--output` | `generated_video.mp4` | Output file path |

### get

Query a single video generation task by ID. Task IDs and result URLs are valid for **24 hours**.

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py get <task_id>
```

## Supported Models

| Mode | 1.1 | 1.0 |
| ---- | --- | --- |
| Text-to-Video | `happyhorse-1.1-t2v` | `happyhorse-1.0-t2v` |
| Image-to-Video | `happyhorse-1.1-i2v` | `happyhorse-1.0-i2v` |
| Reference-to-Video | `happyhorse-1.1-r2v` | `happyhorse-1.0-r2v` |
| Video Edit | — | `happyhorse-1.0-video-edit` |

**Note**: The model is auto-derived from the detected mode and `--version` (default `1.1`).
Use `-m/--model` only to override explicitly. If no mode flag is given, the default is `happyhorse-1.1-t2v`.

## Parameter Applicability

| Parameter | t2v | i2v | r2v | video-edit |
| --------- | :-: | :-: | :-: | :--------: |
| `resolution` | ✅ | ✅ | ✅ | ✅ |
| `ratio` | ✅ | ❌ (follows first frame) | ✅ | ❌ (follows source) |
| `duration` | ✅ | ✅ | ✅ | ❌ (follows source, 3-15s) |
| `audio_setting` | ❌ | ❌ | ❌ | ✅ |
| `watermark` / `seed` | ✅ | ✅ | ✅ | ✅ |

## Supported Resolutions

`720P`, `1080P` (default). Lowercase (`720p` / `1080p`) is accepted and normalized.

## Supported Aspect Ratios (t2v / r2v)

`16:9` (default), `9:16`, `1:1`, `4:3`, `3:4`, `4:5`, `5:4`, `9:21`, `21:9`

## Supported Durations

`3` to `15` seconds (integer). Default: `5`. For video-edit, the output duration follows the
source video (the first 15s are used if the source is longer than 15s).

## Watermark

By default the API burns a **"Happy Horse"** watermark into the bottom-right corner.
Pass `--no-watermark` to generate a clean video.

## Media Input Limits

- **First frame (i2v)** / **reference image (r2v / edit)**: JPEG/JPG/PNG/WEBP, ≤20MB each.
  Local files are auto-encoded to base64; public URLs are passed through.
  - i2v first frame: exactly 1; resolution ≥300px; aspect ratio 1:2.5–2.5:1
  - r2v reference images: 1-9; short edge ≥400px (720P+ recommended)
  - video-edit reference images: 0-5
- **Source video (video-edit)**: MP4/MOV (H.264 recommended), 3-60s, ≤100MB.
  Must be a **public http(s) URL** — base64/local files are not supported.

## Prompt Best Practices

Prefer the first-party HappyHorse API examples for
[text-to-video](https://help.aliyun.com/zh/model-studio/happyhorse-text-to-video-api-reference),
[image-to-video](https://help.aliyun.com/zh/model-studio/happyhorse-image-to-video-api-reference),
[reference-to-video](https://help.aliyun.com/zh/model-studio/happyhorse-reference-to-video-api-reference),
and [video editing](https://help.aliyun.com/zh/model-studio/happyhorse-video-edit-api-reference)
over generic prompt collections. The API pages provide examples rather than a
standalone prompt guide, so use the conservative mode-specific patterns below.

### Prompt Length & Language

- Max: 2500 Chinese characters or 5000 non-Chinese characters (excess auto-truncated)
- Any language is supported

### Mode-specific patterns

#### Text-to-Video

Describe visible content with concrete nouns and verbs:

```text
Subject + specific action + environment/lighting + camera + visual style
```

Prefer `warm golden light from the left at dusk` over `nice lighting`. Sequence
multiple actions chronologically and describe physical effects only when they
matter to the shot.

#### Image-to-Video

The first frame already defines the subject, style, composition, and aspect
ratio. Spend the prompt on motion, camera behavior, environmental change, and
what must remain consistent. Do not redescribe an appearance that conflicts
with the image.

```text
首帧中的猫先压低前腿蓄力，随后沿草地向画面右侧自然奔跑，尾巴随步伐摆动，草叶被轻微带起。
低机位平稳跟拍，速度逐渐加快；保持猫的花纹、体型和场景风格与首帧一致。
```

#### Reference-to-Video

Refer to each image in exact `--ref-image` order as `[Image 1]`, `[Image 2]`,
and so on. Identify the object within each image; do not write only "use Image
1". Assign every reference a clear job and relationship.

```text
[Image 1]中的人物拿起[Image 2]中的产品，在[Image 3]中的场景里缓慢走向镜头。
```

#### Video Edit

Use a **Change + Preserve** instruction: identify the target and replacement,
then name the source properties that must remain unchanged. Iterate one major
change at a time.

```text
将视频中角色原有的上衣替换为参考图片中的条纹毛衣；毛衣跟随身体动作自然形变，
保持角色头部、身体比例、动作、背景、镜头运动、时长和音频不变。
```

### Cross-mode rules

1. Use specific, observable actions rather than abstract adjectives.
2. Sequence actions in event order and keep transitions physically connected.
3. Keep camera instructions purposeful; use a cut when camera behavior changes.
4. For reference inputs, assign each asset one clear responsibility.
5. Fix `--seed` when repeatability matters, but do not promise identical output.
6. Do not append an unsupported universal negative-prompt list.

### Camera and shots

Camera: 推/拉镜头 (dolly), 左/右摇 (pan), 上仰/下俯 (tilt), 跟镜头 (tracking),
升/降镜头 (crane), 环绕运镜 (orbit), 固定机位 (static), 航拍 (aerial).
Shots: 特写 / 近景 / 中景 / 全景 / 远景 / 大远景.

Use quality and style words only when they add information. Resolution is
controlled by `--resolution`; do not claim `4K` or `8K` when HappyHorse output
is limited to 720P/1080P.

```text
细节丰富，画面稳定，色彩自然，电影质感，运动流畅
```

## Examples

### Text-to-Video

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "一座由硬纸板和瓶盖搭建的微型城市，在夜晚焕发出生机。一列硬纸板火车缓缓驶过，小灯点缀其间，照亮前路。微距低机位平稳跟拍，定格动画质感。" -a 16:9 -d 8 -o mini_city.mp4
```

### Image-to-Video (First Frame)

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "首帧中的猫先压低前腿蓄力，随后沿草地向画面右侧自然奔跑，尾巴随步伐摆动，草叶被轻微带起。低机位平稳跟拍，保持猫的花纹、体型和场景风格与首帧一致。" -i cat_first_frame.png -d 5 -o cat_run.mp4
```

### Reference-to-Video (Multi-image)

Refer to each image with `[Image N]` matching the `--ref-image` order:

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "[Image 1]中身着红色旗袍的女性，镜头先以侧面中景勾勒旗袍剪裁，随即切换至低角度仰拍；她轻抬右手展开[Image 2]中的折扇，[Image 3]中的流苏耳坠随头部转动轻盈摆动。最后推近至面部特写，定格在她指尖轻点扇骨、眼波流转的瞬间。" --ref-image girl.jpg --ref-image fan.jpg --ref-image earrings.jpg -a 9:16 -d 8 -o qipao.mp4
```

### Video Edit (instruction + reference image)

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "将视频中角色原有的上衣替换为参考图片中的条纹毛衣；毛衣跟随身体动作自然形变，保持角色头部、身体比例、动作、背景、镜头运动、时长和音频不变。" --video "https://example.com/source.mp4" --ref-image sweater.webp -r 720P --audio-setting origin -o edited.mp4
```

### Use the 1.0 Model / Clean Output

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "微距镜头，露珠从花瓣滑落，慢动作，浅景深" --version 1.0 --no-watermark --seed 42 -r 720P -o dewdrop.mp4
```

### Get Task

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py get 0385dc79-5ff8-4d82-bcb6-xxxxxx
```

## Environment Variables

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `DASHSCOPE_API_KEY` | Yes | API key for Alibaba Bailian (DashScope) |
| `DASHSCOPE_VIDEO_BASE_URL` | No | Native async API host (default: `https://dashscope.aliyuncs.com`, i.e. Beijing). Override for other regions, e.g. `https://dashscope-intl.aliyuncs.com` (Singapore), `https://dashscope-us.aliyuncs.com` (US). |

Set in `.genix.env` file.

**Note**: The model, endpoint URL, and API Key must all belong to the **same region** — cross-region calls fail.
