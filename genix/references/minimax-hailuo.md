# MiniMax Hailuo (MiniMax-H3) Video Generation

Text-to-Video, Image-to-Video (first / last frame), and Multi-modal Reference
video generation using the MiniMax video generation V2 API (**Hailuo-03**).
Output is **2K with native synchronized audio**. The API is asynchronous
(create task → poll → download), handled automatically by the script.

Three modes are auto-detected from the inputs you provide:

| Mode | Trigger | Notes |
| ---- | ------- | ----- |
| Text-to-Video (t2va) | prompt only | `--ratio` is **required** and cannot be `adaptive` |
| Image-to-Video (i2va) | `--first-frame` and/or `--last-frame` | aspect ratio follows the input image |
| Multi-modal Reference (r2va) | `--ref-image` / `--ref-video` / `--ref-audio` | refer to inputs in the prompt as `参考图1`, `参考视频1`, `音色参考音频1` |

**Two rules that differ from the other video providers:**

1. A **non-empty text prompt is required in every mode**, including
   image-to-video. Requests without one are rejected with error `2013`.
2. First/last frame mode and multi-modal reference mode are **mutually
   exclusive** — they cannot be mixed in one request.

## Contents

- [Commands](#commands)
- [Supported Models](#supported-models)
- [Parameter Applicability](#parameter-applicability)
- [Generation Modes](#generation-modes)
- [Media Input Limits](#media-input-limits)
- [Prompt Best Practices](#prompt-best-practices)
- [Examples](#examples)
- [Environment Variables](#environment-variables)

## Commands

### generate (default)

Create a video generation task and wait for the result. The `generate` keyword
can be omitted.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py generate "prompt" [options]
{python} {skill_dir}/scripts/minimax-hailuo.py "prompt" [options]
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text prompt. Required in **every** mode, max 7000 characters |

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--first-frame` | None | First frame image path/URL → Image-to-Video |
| `--last-frame` | None | Last frame image path/URL (usable on its own, or paired with `--first-frame`) |
| `--ref-image` | None | Reference image path/URL (repeatable, max 9) → Multi-modal Reference |
| `--ref-video` | None | Reference video path/URL (repeatable, max 3) |
| `--ref-audio` | None | Reference audio path/URL (repeatable, max 3, requires ref image/video) |
| `-m`, `--model` | `MiniMax-H3` | Model to use (currently the only value) |
| `-r`, `--resolution` | `2K` | Video resolution (the only value the API accepts; lowercase `2k` is normalized) |
| `-a`, `--ratio` | `16:9` for t2va, `adaptive` otherwise | Aspect ratio |
| `-d`, `--duration` | `5` | Duration in seconds (integer, 4-15) |
| `--watermark` | false | Add the AIGC identification watermark |
| `-o`, `--output` | `generated_video.mp4` | Output file path |

The API's `callback_url` parameter is not exposed — the script polls the task
itself every 10 seconds (the interval the docs recommend).

### get

Query a single video generation task by ID. Only tasks from the **last 7 days**
are queryable, and result URLs expire — re-query to get a fresh one.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py get <task_id>
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | The task ID to query |

### list

List video generation tasks from the last 7 days, with optional filters.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py list [options]
```

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-s`, `--status` | None | Filter by status: `queued`, `running`, `succeeded`, `failed`, `cancelled`, `expired` |
| `-m`, `--model` | None | Filter by model name |
| `--task-ids` | None | Filter by specific task IDs (space-separated) |
| `--task-type` | None | Filter by task type (e.g. `generation`) |
| `-p`, `--page` | `1` | Page number |
| `-n`, `--page-size` | `10` | Number of tasks per page |

### delete

Cancel or delete a task. The API picks the action from the task's current state:

| Task status | Action | Note |
| ----------- | ------ | ---- |
| `queued` | cancel | Generation has not started, so there is no charge |
| `succeeded` / `failed` / `expired` | delete | Removes the task record |
| `running` / `cancelled` | — | Not allowed; returns an error |

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py delete <task_id>
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | The task ID to cancel or delete |

## Supported Models

| Model | Model ID | Description |
| ----- | -------- | ----------- |
| Hailuo-03 | `MiniMax-H3` | Unified multi-modal model: text / image / video / audio in, 2K video with audio out |

**Note**: `MiniMax-H3` is currently the only model on this API, and it is the
default — there is no need to pass `-m`.

## Supported Resolutions

`2K` only. It is a required API field with a single allowed value, so there is no
resolution trade-off to make and nothing to tune for cost.

MiniMax's older `720P` / `768P` / `1080P` models live on a separate V1 API family
that this script does not cover.

## Supported Aspect Ratios

| Ratio | Description |
| ----- | ----------- |
| `21:9` | Ultra-wide (cinematic) |
| `16:9` | Landscape (widescreen) |
| `4:3` | Classic TV |
| `1:1` | Square |
| `3:4` | Portrait (classic) |
| `9:16` | Portrait (mobile/vertical) |
| `adaptive` | Auto-select from the input media |

Rules per mode — the script applies these automatically:

| Mode | `ratio` behaviour |
| ---- | ----------------- |
| Text-to-Video | **Required, and `adaptive` is rejected.** Defaults to `16:9` when omitted |
| Image-to-Video | Always `adaptive`; the ratio comes from the input image. Any other value is ignored (the script prints a note) |
| Multi-modal Reference | Optional, defaults to `adaptive`. A concrete ratio may be set explicitly |

When `adaptive` is used, read the actual ratio the model chose from the `Ratio`
field of `get` / `list`.

## Supported Durations

`4` to `15` seconds (integer). Default: `5`. Any value in the range is allowed —
unlike some providers there is no fixed 6s/10s choice. Longer durations cost more.

## Parameter Applicability

| Parameter | t2va | i2va | r2va |
| --------- | :--: | :--: | :--: |
| `prompt` | ✅ required | ✅ required | ✅ required |
| `resolution` | ✅ (`2K`) | ✅ (`2K`) | ✅ (`2K`) |
| `ratio` | ✅ required, no `adaptive` | ❌ (follows input image) | ✅ optional |
| `duration` | ✅ | ✅ | ✅ |
| `watermark` | ✅ | ✅ | ✅ |
| `--first-frame` / `--last-frame` | ❌ | ✅ | ❌ (mutually exclusive) |
| `--ref-image` / `--ref-video` / `--ref-audio` | ❌ | ❌ (mutually exclusive) | ✅ |

## Generation Modes

### Text-to-Video

Prompt only. A concrete aspect ratio is required.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "史诗级太空歌剧院线预告：女舰长独自站在巨大观景窗前，最后一支舰队正在集结并跃迁离去，强光爆闪、舰桥震动，她被留在原地。" -a 16:9 -d 5 -o trailer.mp4
```

### Image-to-Video (First Frame)

Use an image as the first frame and describe the motion you want.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "镜头缓慢推近背景中的人物，拉面碗上的蒸汽变得更浓" -i ramen.png -d 5 -o ramen.mp4
```

### Image-to-Video (Last Frame)

A last frame can be used **on its own** — the model generates the lead-up to it.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "人物一步步走向窗边，最终停在这个画面" --last-frame ending.png -d 6 -o approach.mp4
```

### Image-to-Video (First + Last Frame)

Provide both frames to control a transition end to end.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "流畅的画面过渡，色调从冷色逐渐转为暖色" -i winter.png --last-frame summer.png -d 8 -o transition.mp4
```

### Multi-modal Reference

Combine reference images, videos, and audio. Assign each asset an explicit job in
the prompt — this is what makes the mode work well.

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "角色说话：Follow the wind, live free. Leave worries behind, enjoy the moment，音色参考音频1；人物外观参考图1；运镜与节奏参考视频1。" --ref-image character.png --ref-video motion.mp4 --ref-audio voice.mp3 -d 5 -o character_speech.mp4
```

**Note**: Reference audio cannot be submitted alone — include at least one
reference image or reference video.

## Media Input Limits

Total request body ≤ **64 MB**. Base64 inflates media by ~33%, so prefer a public
URL or an `mm_file://{file_id}` reference for anything sizeable. The script
validates format, size, and counts locally before sending anything.

All media arguments accept three forms:

- a public `http(s)://` URL
- `mm_file://{file_id}` — a file already on the MiniMax platform (uploaded, or a
  previous task's output)
- a local file path — auto-encoded to a `data:` URI

### Images (`--first-frame`, `--last-frame`, `--ref-image`)

| Item | Limit |
| ---- | ----- |
| Formats | JPG, JPEG, PNG, WEBP, HEIC, HEIF |
| Size | ≤ 30 MB each |
| Dimensions | 256-5760 px |
| Aspect ratio (w/h) | 0.4-2.5 |
| Count | first frame ≤ 1, last frame ≤ 1, reference images ≤ 9 |

### Videos (`--ref-video`, reference mode only)

| Item | Limit |
| ---- | ----- |
| Container | MP4 (`.mp4`), MOV (`.mov`) |
| Codecs | Video H.264/AVC or H.265/HEVC; audio AAC or MP3 |
| Size | ≤ 50 MB each |
| Count | ≤ 3 |
| Duration | 2-15 s each, ≤ 15 s total across all videos |
| Dimensions | 256-5760 px |
| Aspect ratio (w/h) | 0.4-2.5 |
| Frame rate | 23.976-60 fps |

### Audio (`--ref-audio`, reference mode only)

| Item | Limit |
| ---- | ----- |
| Formats | WAV, MP3 |
| Size | ≤ 15 MB each |
| Count | ≤ 3 |
| Duration | 2-15 s each, ≤ 15 s total |

Reference assets are also capped at **12 combined** (images + videos + audio).

## Prompt Best Practices

Use the first-party
[MiniMax H3 capability examples](https://platform.minimaxi.com/docs/guides/video-prompt)
and the [video generation guide](https://platform.minimaxi.com/docs/guides/video-generation)
instead of generic prompt collections. The examples page is a curated gallery
rather than a syntax reference, so the patterns below distil what those examples
consistently do.

### Prompt Length & Language

- Max **7000 characters** (counted per character); any language is supported
- Required in every mode — there is no "image only, no prompt" path

### Prompt structure

The official examples follow a stable four-part order:

```text
格式规格（比例/时长/画幅意图） + 参考素材映射 + 叙事与动作 + 情绪/风格/剪辑限定
```

For text-to-video, drop the reference-mapping part and set the ratio via `-a`
instead of describing it in words.

### Reference asset mapping (the key technique for r2va)

Number assets in the order you pass them on the command line, then give each one
**exactly one job**. This is the single highest-leverage thing in a reference
prompt:

```text
整体氛围、场景和胶片质感参考图1；人物资产参考图2；包袋资产参考图3；品牌 ending logo 参考图4
```

- `参考图N` / `参考视频N` / `音色参考音频N` — mapping the audio explicitly to
  *timbre* (`音色`) rather than just "audio" gives much more reliable voice transfer
- One responsibility per asset; put the most important reference first
- Avoid conflicting inputs (two images both claiming to define the same face)
- Prefer a handful of purposeful assets over filling every slot

### Dialogue and audio

H3 generates native synchronized audio. Introduce spoken lines with `角色说话：`
and attach the timbre reference in the same sentence:

```text
角色说话：Follow the wind, live free. Leave worries behind, enjoy the moment，音色参考音频1
```

Constrain the soundscape when you do **not** want speech:

```text
声音只用厨房环境声与手绘生物柔和的电子音、小小的叫声
```

- Keep dialogue in one language except for necessary proper nouns
- Name the ambience you want; silence is not the default

### Identity lock (consistency across a shot)

State `保持身份一致` and then list the concrete attributes that must not drift —
hairstyle, accessories, colour palette, clothing:

```text
保持身份一致：高马尾、左耳银色耳坠、深青色立领长衫、腰间悬白玉扣，全程不变。
```

### Camera Movements (运镜)

Prefer one movement per shot; cut to a new shot when the camera behaviour changes.

| Movement | Chinese | Description |
| -------- | ------- | ----------- |
| `Dolly in / Dolly out` | 推镜头 / 拉镜头 | Camera moves closer/farther; creates intimacy or reveals scale |
| `Pan left / Pan right` | 左摇 / 右摇 | Horizontal rotation, good for environmental reveals |
| `Tilt up / Tilt down` | 上仰 / 下俯 | Vertical rotation |
| `Tracking shot` | 跟镜头 | Camera follows a moving subject |
| `Crane up / Crane down` | 升镜头 / 降镜头 | Camera rises or descends; good for establishing shots |
| `Orbit` | 环绕运镜 | Camera orbits the subject |
| `Static tripod shot` | 固定机位 | Locks the camera, prevents unwanted micro-movement |
| `Handheld` | 手持拍摄 | Intentional shake for realism |
| `Aerial / Drone shot` | 航拍 | Bird's-eye perspective |
| `Pull focus / Rack focus` | 变焦对焦 | Shifts focus between foreground and background |

### Shot Types (景别)

| Shot | Chinese | Description |
| ---- | ------- | ----------- |
| `Extreme close-up` | 特写 | Intense detail (eyes, texture) |
| `Close-up` | 近景 | Face or object detail |
| `Medium shot` | 中景 | Subject from the waist up |
| `Full shot` | 全景 | Full body in frame |
| `Wide shot` | 远景 | Full scene overview |
| `Extreme wide shot` | 大远景 | Vast landscape |

The examples often set a shot-distance *policy* for the whole clip rather than
per-moment framing:

```text
人物以中近景、特写为主，突出脸、眼神与关系张力；远景只用背影、侧背或环境空镜。
```

### Lighting & Style (光影/风格)

| Category | Keywords |
| -------- | -------- |
| Cinematic | "cinematic, film grain, 35mm film, anamorphic" |
| Photorealistic | "photorealistic, detailed texture, natural color" |
| Golden hour | "golden hour, warm tones, soft light" |
| Dramatic | "strong rim light, silhouette, high contrast" |
| Neon/Cyberpunk | "neon-lit, cyberpunk, saturated colors" |
| Documentary | "documentary-style, raw footage, natural lighting" |
| Phone footage | 画面带有智能手机单手拍摄的手抖、近距离对焦的犹豫、逆光曝光波动 |
| Anime | "Japanese anime style, cel-shaded" |

Pairing a genre reference with a mood descriptor works well, e.g. aligning with
`海外 ReelShort / DramaBox 吸血鬼爱情短剧预告` style while specifying
`暗黑浪漫、危险吸引力、宿命感`.

### Storyboard prompting

Use shot order (`镜头1`, `镜头2`, …) rather than exact timestamps. Within each
shot write camera/cut → action and expression → spatial change → audio.

```text
镜头1：近景固定机位，她站在观景窗前，舰队灯光扫过侧脸。
镜头2：切至中景缓慢推近，最后一艘舰船跃迁，强光爆闪，舰桥震动。
镜头3：切至特写，她闭眼再睁开，只有低频轰鸣与金属应力声。
```

### Quality and constraints

Resolution is fixed at `2K` by the API — **do not write `4K` or `8K` in the
prompt** as a substitute for a setting. Same for the aspect ratio in
text-to-video: pass `-a`, don't describe it.

Close with only the constraints that matter, e.g. `保持无字幕`,
`不要生成 Logo`, `不要生成水印`. Do not append a universal boilerplate negative
list. Avoid vague wording, contradictory requirements, and full screenplay text.

## Examples

### Text-to-Video (cinematic trailer)

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "史诗级太空歌剧院线预告。镜头1：近景固定机位，女舰长独自站在巨大观景窗前，舰队灯光扫过侧脸。镜头2：切至中景缓慢推近，最后一支舰队集结跃迁离去，强光爆闪、舰桥震动，她被留在原地。冷蓝色调，强边缘光，电影质感，只有低频轰鸣与金属应力声，保持无字幕。" -a 21:9 -d 10 -o trailer.mp4
```

### Vertical Short Video

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "手持拍摄质感，画面带有智能手机单手拍摄的轻微手抖。少年在傍晚的天台上转身面向镜头，风吹动衣角，背后是城市霓虹逐渐亮起。暖橙与靛蓝对比，纪实感，环境声为远处车流与风声。" -a 9:16 -d 8 -o vertical.mp4
```

### Image-to-Video with Dialogue

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "固定中近景，以首帧人物外观和构图为准。她先轻轻眨眼，随后看向镜头，角色说话：'这款面霜质地轻盈，一抹就吸收。' 保持身份一致：发型、耳坠与服装全程不变，动作幅度克制，不生成字幕。" -i model.png -d 6 -o dialogue.mp4
```

### Last Frame Only

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "人物从走廊深处一步步走向窗边，脚步声在空旷空间回响，最终停在这个画面。冷色调，浅景深。" --last-frame ending.png -d 6 -o approach.mp4
```

### First + Last Frame Transition

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "流畅的季节过渡，色调从冷蓝逐渐转为暖金，镜头保持固定机位。" -i winter.png --last-frame summer.png -d 8 -o transition.mp4
```

### Multi-modal Reference (voice transfer)

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "角色说话：Follow the wind, live free. Leave worries behind, enjoy the moment，音色参考音频1。人物外观参考图1，运镜与动作节奏参考视频1，但不复用视频1中的场景。保持身份一致，中近景为主。" --ref-image character.png --ref-video motion.mp4 --ref-audio voice.mp3 -d 5 -o voice_transfer.mp4
```

### Multi-modal Reference (product ad)

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "整体氛围、场景和胶片质感参考图1；人物资产参考图2；产品资产参考图3；品牌 ending logo 参考图4。镜头1：影棚中景缓慢推近，人物右手自然拿起产品并将标签朝向镜头。镜头2：切至产品特写，标签清晰可读。镜头3：切至品牌 logo 定版。保持人物面部与产品包装一致，不生成额外字幕或水印。" --ref-image mood.png --ref-image model.png --ref-image product.png --ref-image logo.png -a 9:16 -d 12 -o product_ad.mp4
```

### Reference by Public URL

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "人物外观参考图1，动作节奏参考视频1。人物在雨后街道缓慢向前行走，镜头平稳跟随。" --ref-image https://example.com/character.png --ref-video https://example.com/motion.mp4 -d 8 -o street_walk.mp4
```

### Silent, Ambient-Only Video

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "微距镜头，露珠从花瓣滑落，慢动作，浅景深。声音只用极轻的环境风声，没有音乐、没有人声、保持无字幕。" -a 16:9 -d 5 -o dewdrop.mp4
```

### With AIGC Watermark

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py "航拍，云雾缭绕的山谷在日出时分，金色阳光穿透云层，史诗级电影质感。" -a 16:9 -d 8 --watermark -o valley.mp4
```

### Get Task

```bash
{python} {skill_dir}/scripts/minimax-hailuo.py get 424010985738629
```

### List Tasks

```bash
# List recent tasks (last 7 days)
{python} {skill_dir}/scripts/minimax-hailuo.py list

# List only succeeded tasks
{python} {skill_dir}/scripts/minimax-hailuo.py list -s succeeded

# Page 2, 20 per page
{python} {skill_dir}/scripts/minimax-hailuo.py list -p 2 -n 20

# List specific tasks by ID
{python} {skill_dir}/scripts/minimax-hailuo.py list --task-ids 424010985738629 424635601932571
```

### Cancel or Delete Task

```bash
# Cancels if queued, deletes the record if already in a terminal state
{python} {skill_dir}/scripts/minimax-hailuo.py delete 424010985738629
```

## Environment Variables

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `MINIMAX_API_KEY` | Yes | API key for MiniMax (Account Management > Interface Key) |
| `MINIMAX_API_BASE` | No | API base URL (default: `https://api.minimaxi.com`) |

Set in `.genix.env` file.
