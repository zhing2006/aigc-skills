# Volcengine Seedance 2.5 / 2.0 Video Generation

Text-to-Video, Image-to-Video, Audio-to-Video, and Multi-modal Reference video
generation using Volcengine Seedance 2.5 and the Seedance 2.0 series.

## Contents

- [Commands](#commands)
- [Supported Models](#supported-models)
- [Supported Resolutions](#supported-resolutions)
- [Supported Aspect Ratios](#supported-aspect-ratios)
- [Supported Durations](#supported-durations)
- [Parameter Applicability](#parameter-applicability)
- [Media Input Limits](#media-input-limits)
- [Generation Modes](#generation-modes)
- [Prompt Best Practices](#prompt-best-practices)
- [Examples](#examples)
- [Environment Variables](#environment-variables)

## Commands

### generate (default)

Generate a video. This is the default command — the `generate` keyword can be omitted.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py generate "prompt" [options]
{python} {skill_dir}/scripts/volcengine-seedance.py "prompt" [options]
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | No* | Text prompt for video generation |

*At least one of `prompt`, `--first-frame`, `--ref-image`, `--ref-video`, or
`--ref-audio` is required.

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--first-frame` | None | First frame image for image-to-video |
| `--last-frame` | None | Last frame image (requires `--first-frame`) |
| `--ref-image` | None | Reference image (repeatable; max 30 on 2.5, 9 on 2.0) |
| `--ref-video` | None | Reference video URL (repeatable; max 10 on 2.5, 3 on 2.0) |
| `--ref-audio` | None | Reference audio (repeatable; max 10 on 2.5, 3 on 2.0). 2.5 accepts audio alone; 2.0 also needs a reference image or video |
| `-m`, `--model` | `doubao-seedance-2-5-260628` | Model to use |
| `-r`, `--resolution` | `720p` | Video resolution (`480p`, `720p`, `1080p`, `4k`) — see the per-model matrix below |
| `-a`, `--ratio` | `adaptive` | Aspect ratio. 2.5 forces `adaptive` for first-frame / first+last-frame and video edit/extend tasks |
| `-d`, `--duration` | `5` | Duration in seconds (2.5: `4`-`30`; 2.0 series: `4`-`15`; `-1` for auto) |
| `--no-audio` | false | Disable synchronized audio generation |
| `--watermark` | false | Add watermark |
| `--web-search` | false | Enable web search enhancement (text-to-video only) |
| `--return-last-frame` | false | Also save the video's last frame as `<name>_last_frame.png` (for chaining clips) |
| `--output-format` | `mp4` | Output container: `mp4` or `mov` (**Seedance 2.5 only**) |
| `--priority` | None | Queue priority `0`-`9`; higher jumps ahead of lower-priority queued tasks on the same endpoint |
| `--expires-after` | `172800` (48h) | Seconds after creation before an unfinished task is marked `expired` (`3600`-`259200`) |
| `-o`, `--output` | `generated_video.<format>` | Output file path |

### get

Query a single video generation task by ID.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py get <task_id>
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | The task ID to query |

### list

List video generation tasks with optional filters.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py list [options]
```

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-s`, `--status` | None | Filter by status: `queued`, `running`, `succeeded`, `failed`, `cancelled`, `expired` |
| `-m`, `--model` | None | Filter by model ID |
| `--task-ids` | None | Filter by specific task IDs (space-separated) |
| `-p`, `--page` | `1` | Page number |
| `-n`, `--page-size` | `10` | Number of tasks per page |

### delete

Delete a video generation task.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py delete <task_id>
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | The task ID to delete |

## Supported Models

| Model | Model ID | Description |
| ----- | -------- | ----------- |
| Seedance 2.5 | `doubao-seedance-2-5-260628` | Default. 30 s coherent single-pass output, up to 30 reference images, `mov` output, audio-only input. Max 720p |
| Seedance 2.0 | `doubao-seedance-2-0-260128` | The only model with 1080p and 4k. Max 15 s |
| Seedance 2.0 fast | `doubao-seedance-2-0-fast-260128` | Faster, lower cost, max 720p / 15 s |
| Seedance 2.0 mini | `doubao-seedance-2-0-mini-260615` | Cheapest/fastest, max 720p / 15 s |

**Note**: If the user does not specify a model, use `doubao-seedance-2-5-260628`.
Switch to `doubao-seedance-2-0-260128` when the user needs 1080p or 4k, and to the
fast or mini model for quick previews and drafts.

## Supported Resolutions

`480p`, `720p` (default), `1080p`, `4k`

Resolution support depends on the model:

| Model | 480p | 720p | 1080p | 4k |
| ----- | :--: | :--: | :---: | :-: |
| `doubao-seedance-2-5-260628` | ✅ | ✅ | ❌ | ❌ |
| `doubao-seedance-2-0-260128` (full) | ✅ | ✅ | ✅ | ✅ |
| `doubao-seedance-2-0-fast-260128` | ✅ | ✅ | ❌ | ❌ |
| `doubao-seedance-2-0-mini-260615` | ✅ | ✅ | ❌ | ❌ |

**Notes**:
- Seedance 2.5 tops out at `720p`. `1080p` and `4k` require `doubao-seedance-2-0-260128`.
- The script validates resolution against the chosen model and errors early if unsupported.
- `4k` output uses 10-bit H.265 encoding (HDR-ready). Some players may not support it — use VLC, MPV, or QuickTime Player if playback fails.

**Tip**: Draft at 480p to iterate quickly, then re-run at 720p/1080p/4k for final output.

## Supported Aspect Ratios

| Ratio | Description |
| ----- | ----------- |
| `16:9` | Landscape (widescreen) |
| `4:3` | Classic TV |
| `1:1` | Square |
| `3:4` | Portrait (classic) |
| `9:16` | Portrait (mobile/vertical) |
| `21:9` | Ultra-wide (cinematic) |
| `adaptive` | Auto-select based on task and input (default) |

Not every task lets you pick the ratio:

| Task | Seedance 2.5 | Seedance 2.0 series |
| ---- | ------------ | ------------------- |
| Text-to-Video | Free choice or `adaptive` | Free choice or `adaptive` |
| Multi-modal reference (new video) | Free choice or `adaptive` | Free choice or `adaptive` |
| First frame / first+last frame | **`adaptive` only** — output follows the first frame | Free choice or `adaptive` |
| Video edit / video extend | **`adaptive` only** — output follows the source video | Free choice or `adaptive` |

The script rejects a non-`adaptive` `-a` on Seedance 2.5 first-frame tasks before
sending the request. Video edit/extend is inferred by the model from the prompt, so
that case is not caught locally — leave `-a` unset for those.

## Supported Durations

| Model | Range | `-1` behaviour |
| ----- | ----- | -------------- |
| `doubao-seedance-2-5-260628` | `4`-`30` s | Model picks a length; for a video edit it matches the source (±0.4 s) |
| `doubao-seedance-2-0-*` | `4`-`15` s | Model picks a length in range |

Default: `5` seconds. Longer durations cost more tokens.

**Seedance 2.5 video-edit tasks accept only `-d -1`** — an explicit duration errors
out server-side, and the source video must itself be 4-30 s.

The `duration` returned by `get` / `list` is `total_frames / 24` rounded down, so it
can read 1 s shorter than the actual file.

## Parameter Applicability

| Capability | Seedance 2.5 | Seedance 2.0 | 2.0 fast | 2.0 mini |
| ---------- | :----------: | :----------: | :------: | :------: |
| Max resolution | 720p | 4k | 720p | 720p |
| Duration range | 4-30 s | 4-15 s | 4-15 s | 4-15 s |
| Free choice of `-a` | Text/reference tasks only | ✅ | ✅ | ✅ |
| `--output-format mov` | ✅ | ❌ | ❌ | ❌ |
| `--priority` | ✅ | ✅ | ✅ | ✅ |
| `--expires-after` | ✅ | ✅ | ✅ | ✅ |
| `--no-audio` / synced audio | ✅ | ✅ | ✅ | ✅ |
| `--web-search` | ✅ | ✅ | ✅ | ✅ |
| Audio-only input | ✅ | ❌ | ❌ | ❌ |
| Max reference images | 30 | 9 | 9 | 9 |
| Max reference videos | 10 (≤30 s total) | 3 (≤15 s total) | 3 | 3 |
| Max reference audios | 10 (≤30 s total) | 3 (≤15 s total) | 3 | 3 |

**Not exposed by this script**: `seed`, `frames`, `camera_fixed`, `draft`, and
`service_tier` are unsupported by Seedance 2.5 and the 2.0 series (they belong to
Seedance 1.5 pro and the 1.0 models), so there are no CLI flags for them.

## Media Input Limits

Applies to every image/video/audio passed to `-i`, `--last-frame`, `--ref-image`,
`--ref-video`, `--ref-audio`. Local files are base64-encoded automatically; `http(s)://`
URLs and `asset://<ASSET_ID>` material IDs are passed through unchanged.

| Kind | Formats | Size | Other limits |
| ---- | ------- | ---- | ------------ |
| Image | `jpeg`, `png`, `webp`, `bmp`, `tiff`, `gif` | < 30 MB each | Aspect ratio 0.4-2.5; each side 300-6000 px |
| Video | `mp4`, `mov` (H.264/H.265 video, AAC/MP3 audio) | ≤ 200 MB each | 480p-4k; 24-60 fps; aspect ratio 0.4-2.5; 2.5: 2-30 s each and ≤30 s total, 2.0: 2-15 s each and ≤15 s total |
| Audio | `wav`, `mp3` | ≤ 15 MB each | 2.5: 2-30 s each and ≤30 s total, 2.0: 2-15 s each and ≤15 s total |

**Request body must stay under 64 MB.** For large files pass a public URL rather than
a local path, since local paths are inlined as base64.

**Real faces**: Seedance 2.5 and the 2.0 series reject reference images and videos
containing real human faces uploaded directly. Use one of the platform's routes
instead — output previously generated by these models on the same account within the
last 30 days, a preset virtual persona (`asset://<ASSET_ID>` from the console's
material library), or licensed footage.

## Generation Modes

### Text-to-Video

Generate video from text prompt only.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "A cat walking on the beach at golden hour" -o cat.mp4
```

### Image-to-Video (First Frame)

Use an image as the first frame, with optional text prompt to describe the desired motion.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "The cat slowly turns its head" -i cat_photo.png -o cat_turn.mp4
```

### Image-to-Video (First + Last Frame)

Provide both first and last frame images. The model generates smooth transition between them.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "Smooth camera transition" -i start.png --last-frame end.png -o transition.mp4
```

### Multi-modal Reference

Combine reference images, videos, and audio for maximum control. Use prompt to describe how references should be combined.

Seedance 2.5 accepts up to 30 images, 10 videos, and 10 audio clips per request
(2.0 series: 9 / 3 / 3). This mode also covers **video editing** and **video
extension** — the model infers which from the prompt, so word it explicitly
(see [Video editing](#video-editing)).

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "将人物A@图片1定义为主角，人物外观严格参考图片1；第一视角运镜参考视频1，但不复用其中的人物和场景；音乐节奏参考音频1。人物A在雨后街道缓慢向前行走，镜头平稳跟随，动作与音乐节拍自然同步。" --ref-image character.png --ref-video scene.mp4 --ref-audio bgm.mp3 -a 16:9 -d 11 -o result.mp4
```

**Note**: First frame mode and multi-modal reference mode are mutually exclusive.

### Audio Reference Only (Seedance 2.5)

Seedance 2.5 can drive a video from audio alone — no reference image or video needed.
The prompt is optional but strongly recommended to fix the subject and setting;
without it the model has nothing but the audio to work from.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "画面随音频1的鼓点切换：中景，霓虹灯下的雨夜街道，光斑随节拍明暗起伏，镜头平稳横移。" --ref-audio drums.mp3 -a 21:9 -d 12 -o rhythm.mp4
```

On the 2.0 series this errors out — audio there must accompany at least one reference
image or video.

## Prompt Best Practices

Use the first-party
[Volcengine Seedance prompt guide](https://www.volcengine.com/docs/82379/2222480),
the [Seedance 2.5 prompt guide](https://www.volcengine.com/docs/82379/2607689),
and [ByteDance product examples](https://seed.bytedance.com/zh/seedance2_0)
instead of generic prompt collections.

### Prompt length and language

Keep Chinese prompts under 500 characters and English prompts under 1000 words.
Past that, the model tends to latch onto the highlights and silently drop details.

All models accept Chinese and English. Beyond that:

| Model | Additional languages |
| ----- | -------------------- |
| Seedance 2.5 | Spanish, Indonesian, Portuguese, Japanese, Malay, Thai, Arabic, Vietnamese, Korean |
| Seedance 2.0 series | Spanish, Indonesian, Portuguese, Japanese |

### Choose the task first

| Task | Recommended wording |
| ---- | ------------------- |
| Text / first-frame video | `Subject + action + scene + shot/camera + audio + style/quality + constraints` |
| Multi-modal reference | `Reference image/video/audio N for one named property, then describe the new video` |
| Edit a video | `Strictly edit Video N: change X to Y; preserve A/B/C` |
| Extend a video | `Extend Video N forward/backward: next action or story beat` |

For an edit or extension, say `视频1` rather than `参考视频1`. The official
guide warns that the latter can be interpreted as a new reference-generation
task.

### Write directing instructions

Treat the prompt as a compact directing specification, not a pile of style
adjectives:

1. **Bind every subject.** With ordered references, consistently use
   `人物A@图片1`, `产品@图片2`, `视频1`, and `音频1`. Do not alternate between
   names, pronouns, and vague phrases such as "the other person".
2. **Assign one responsibility to each asset.** For example: image 1 anchors
   the face, image 2 anchors clothing, video 1 supplies movement, and audio 1
   supplies voice or rhythm. Put the most important reference first and avoid
   conflicting inputs.
3. **Storyboard in event order.** For complex video, use `镜头1`, `镜头2`,
   `镜头3`. Within each shot write the camera/cut, action and expression,
   spatial change, then audio. Prefer natural pacing; exact intervals such as
   `0-3秒` are not stable enough to use unless the user explicitly requires them.
4. **Use one camera movement per shot.** `中景缓慢推近`, `平稳横移`, or
   `固定机位` is clearer than push + pull + pan + orbit in one shot. Cut to a
   new shot when camera behavior changes.
5. **Make action observable.** Name the body part plus amplitude, speed, and
   force: `右手缓慢抬至肩部`, `快速转头`, `用力蹬地`. Describe transitions:
   `借转身惯性顺势抬手`. Express emotion through visible behavior rather than
   only `very sad` or `very angry`.
6. **Keep difficult motion achievable.** Prefer physically connected motion.
   For dense fights, chases, or montage, generate shorter clips and edit them
   together instead of overloading one prompt.
   Seedance 2.5 can hold 30 seconds in one pass, but a long take still needs a
   storyboard: 3-5 numbered shots with one clear action each beats a wall of
   simultaneous events. Beyond that, chain clips via `--return-last-frame`.
7. **Close with relevant boundaries.** State style and quality, then only the
   constraints that matter, such as `保持无字幕`, `不要生成 Logo`, or
   `不要生成水印`. Do not append a universal boilerplate negative list.

### First-frame prompting

The first frame already anchors appearance and composition. Spend the prompt on
motion, camera, environmental change, audio, and what must remain consistent.
Do not redescribe a conflicting appearance.

```text
以首帧人物外观、服装和初始构图为准。固定中近景，她先轻轻眨眼，随后缓慢抬头看向窗外，
右手将耳边一缕头发自然别到耳后，窗帘被微风轻微吹动。晨光逐渐变暖，动作幅度克制、衔接自然，
人物面部与服装全程保持一致，无台词，只有轻微风声和室内环境声。
```

### Multi-modal references

Number images, videos, and audio in their respective argument order. Define the
identity and role of every important input:

```text
将人物A@图片1定义为女剑客，将人物B@图片2定义为蒙面守卫。人物外观分别严格参考对应图片。
动作节奏参考视频1，但不复用视频1中的人物和场景；鼓点节奏参考音频1。
```

- For one person, prefer one clean face close-up plus one full-body styling
  image: `人物A的面部参考图片1，服装和体型参考图片2`.
- Avoid a multi-view contact sheet for a person; the views may be read as
  separate subjects. Clean single-person images are more reliable.
- The official guide recommends roughly 4-5 purposeful assets for a complex
  task instead of filling every input slot.
- More than four referenced people is unstable. Split large casts into groups
  or establish them in intermediate images first.
- Use reference video for exact motion, camera language, or special-effect
  behavior that is difficult to describe reliably in text.

### Video editing

Use a **Change + Preserve** instruction:

```text
严格编辑视频1：将桌上的透明香水瓶替换为图片1中的面霜罐，保持原视频的手部动作、运镜、
灯光、背景、时长和音频不变；面霜罐的大小、透视、遮挡和桌面接触阴影与原场景一致。
```

On Seedance 2.5 an edit or extension must run with `-d -1` and no explicit `-a`; the
output length and ratio track the source video. Use `--output-format mov` on both
sides of an edit chain to avoid a second generation loss.

### Camera Movements (运镜)

Seedance understands standard camera terms directly. Prefer one movement
per shot.

| Movement | Chinese | Description |
| -------- | ------- | ----------- |
| `Dolly in / Dolly out` | 推镜头 / 拉镜头 | Camera moves closer/farther, creates intimacy or reveals scale |
| `Push in / Pull back` | 推进 / 拉远 | Similar to dolly; "slow push in" works reliably |
| `Pan left / Pan right` | 左摇 / 右摇 | Camera rotates horizontally, good for environmental reveals |
| `Tilt up / Tilt down` | 上仰 / 下俯 | Camera rotates vertically |
| `Tracking shot` | 跟镜头 | Camera follows a moving subject |
| `Crane up / Crane down` | 升镜头 / 降镜头 | Camera rises or descends, good for establishing shots |
| `Orbit` | 环绕运镜 | Camera orbits around subject |
| `Static tripod shot` | 固定机位 | Locks camera, prevents unwanted micro-movements |
| `Handheld` | 手持拍摄 | Adds intentional shake for realism |
| `Aerial / Drone shot` | 航拍 | Bird's eye perspective |

### Shot Types (景别)

| Shot | Chinese | Description |
| ---- | ------- | ----------- |
| `Extreme close-up` | 特写 | Intense detail (eyes, texture) |
| `Close-up` | 近景 | Face or object detail |
| `Medium shot` | 中景 | Subject from waist up |
| `Full shot` | 全景 | Full body in frame |
| `Wide shot` | 远景 | Full scene overview |
| `Extreme wide shot` | 大远景 | Vast landscape |

### Lighting & Style (光影/风格)

| Category | Keywords |
| -------- | -------- |
| Cinematic | "cinematic, film grain, 35mm film, Hollywood blockbuster" |
| Photorealistic | "photorealistic, detailed texture, natural color" |
| Golden hour | "golden hour, warm tones, soft light" |
| Dramatic | "strong rim light, silhouette, high contrast" |
| Neon/Cyberpunk | "neon-lit, cyberpunk, high contrast, saturated colors" |
| Documentary | "documentary-style, raw footage, natural lighting" |
| Anime | "Japanese anime style, cel-shaded" |

### Audio Prompting

Seedance generates native synchronized audio (dialogue, SFX, music) unless
`--no-audio` is passed. Generated audio is always mono, regardless of how many
channels a reference audio clip has. Tips:

- **Dialogue**: Put lines in double quotes: `男人说："你好，欢迎来到这里。"`
- **Sound Effects**: Describe naturally: `脚步声踩在雪地上，咯吱作响`
- **Background Music**: Include mood cues: `背景音乐为轻快的吉他弹唱`
- **Language consistency**: Keep dialogue in one language except for necessary proper nouns
- **Voice reference**: Keep the requested delivery close to the reference audio's tone and style

### Storyboard prompting

Use shot order rather than fragile exact timestamps:

```text
镜头1：近景固定机位，女孩站在窗前，柔和晨光洒在脸上，她微微侧头。
镜头2：切至中景缓慢推近，她转身走向桌边，右手自然拿起咖啡杯。
镜头3：切至杯口特写，热气缓慢升起，浅景深，暖色调，只有轻微室内环境声。
```

### Quality and constraints

Resolution comes from `--resolution`; do not use `8K` as a substitute for the
actual output setting. Add concise visual direction only when relevant:

```text
细节丰富，画面稳定，色彩自然，电影质感，动作衔接自然
```

Avoid vague wording, contradictory requirements, redundant references, and
full screenplay text. If duplicate characters appear, restate every
subject-to-image mapping and explicitly require each named person to appear only
once; this reduces but cannot guarantee elimination of duplication.

## Examples

### Text-to-Video with Camera Movement

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "中景，一位穿着白色连衣裙的女孩站在樱花树下，微风吹过，花瓣缓缓飘落，柔和的自然光，缓慢推镜头，电影质感，浅景深" -a 16:9 -d 8 -o sakura.mp4
```

### Image-to-Video with Audio

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "以首帧猫咪外观和构图为准。固定近景，猫咪先慢慢睁开眼睛，前爪向前伸展完成一次自然的懒腰，随后轻轻抬头，发出一声短促的喵呜；保持毛色、体型和背景不变。" -i sleeping_cat.jpg -d 6 -o cat_wakeup.mp4
```

### Quick Preview with Fast Model

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "航拍，城市夜景，霓虹灯闪烁，车流如织" -m doubao-seedance-2-0-fast-260128 -r 480p -d 4 -o city_preview.mp4
```

### Silent Video

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "微距镜头，露珠从花瓣滑落，慢动作，浅景深" --no-audio -o dewdrop.mp4
```

### Ultra-wide Cinematic

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "Crane shot ascending over a misty mountain valley at dawn, golden light breaking through clouds, epic cinematic scale, detailed texture, natural color" -a 21:9 -d 10 -o epic_valley.mp4
```

### First + Last Frame Transition

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "流畅的画面过渡，色调从冷色逐渐转为暖色" -i winter_scene.png --last-frame summer_scene.png -d 8 -o season_transition.mp4
```

### Multi-modal Reference (Product Ad)

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "将人物A@图片1定义为模特，将产品@图片2定义为面霜罐，人物与产品外观严格参考对应图片。镜头1：清新简约的影棚中景缓慢推近，人物A右手自然拿起产品并将标签朝向镜头。镜头2：切至人物A近景，她保持产品位置稳定并说：'这款面霜质地轻盈，一抹就吸收。' 保持人物面部、产品包装和标签一致，不生成额外字幕或水印。" --ref-image model.jpg --ref-image product.jpg -a 9:16 -d 10 -o product_ad.mp4
```

### With Web Search Enhancement

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "微距镜头拍摄一只玻璃蛙，透明腹部可见心脏跳动，热带雨林背景" --web-search -a 16:9 -d 8 -o glass_frog.mp4
```

### 4K Output (Seedance 2.0 full model only)

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "航拍，云雾缭绕的山谷在日出时分，金色阳光穿透云层，史诗级电影质感" -m doubao-seedance-2-0-260128 -r 4k -a 16:9 -d 8 -o valley_4k.mp4
```

### 30-Second Single Take (Seedance 2.5)

Storyboard the whole thing; do not rely on one sentence to fill 30 seconds.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "镜头1：清晨的旧书店，中景固定机位，老店主推开木门，铜铃轻响。镜头2：切至书架特写缓慢横移，尘埃在斜射晨光中浮动。镜头3：切至中景，一位年轻女子推门进来，抬头环视，脚步声在木地板上回响。镜头4：切至两人近景过肩镜头，店主指向角落的一本旧书并说：'你要找的，一直在那里。' 全程暖色调，电影质感，动作衔接自然，只有环境声与轻微钢琴单音。" -d 30 -r 720p -a 16:9 -o bookstore_30s.mp4
```

### High-Fidelity mov for Editing (Seedance 2.5)

`mov` keeps higher colour precision (yuv444p + PCM audio) for grading, keying, and
compositing. Use it on both sides of an edit/extend chain. Play it with VLC, mpv,
IINA, or ffplay — many consumer players cannot.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "严格编辑视频1：将桌上的透明香水瓶替换为图片1中的面霜罐，保持原视频的手部动作、运镜、灯光、背景、时长和音频不变。" --ref-video product_shot.mov --ref-image cream_jar.png -d -1 --output-format mov -o product_edit.mov
```

### Audio-Driven Video (Seedance 2.5)

Audio alone is a valid input on 2.5 — no reference image or video required.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "画面随音频1的鼓点切换：中景，霓虹灯下的雨夜街道，光斑随节拍明暗起伏，镜头平稳横移，冷色调，赛博朋克质感。" --ref-audio drums.mp3 -a 21:9 -d 12 -o rhythm.mp4
```

### Priority and Timeout

Jump the queue for an urgent render and give up after an hour instead of the default 48 h.

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "特写，咖啡从壶口缓缓注入杯中，热气升腾，浅景深" --priority 7 --expires-after 3600 -d 5 -o pour.mp4
```

### Chaining Clips via Last Frame

Save the final frame, then feed it as the first frame of the next clip for a seamless continuation.

```bash
# Clip 1: generate and keep the last frame
{python} {skill_dir}/scripts/volcengine-seedance.py "女孩走向窗边，缓慢推镜头" --return-last-frame -d 5 -o clip1.mp4

# Clip 2: continue from clip1's last frame
{python} {skill_dir}/scripts/volcengine-seedance.py "女孩推开窗户，阳光洒入房间" -i clip1_last_frame.png -d 5 -o clip2.mp4
```

### Get Task

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py get cgt-20260401194138-w8xgn
```

### List Tasks

```bash
# List all tasks
{python} {skill_dir}/scripts/volcengine-seedance.py list

# List only succeeded tasks
{python} {skill_dir}/scripts/volcengine-seedance.py list -s succeeded

# List only expired tasks
{python} {skill_dir}/scripts/volcengine-seedance.py list -s expired

# List tasks filtered by model, page 2
{python} {skill_dir}/scripts/volcengine-seedance.py list -m doubao-seedance-2-5-260628 -p 2

# List specific tasks by ID
{python} {skill_dir}/scripts/volcengine-seedance.py list --task-ids cgt-20260401194138-w8xgn cgt-20260401200000-abc12
```

### Delete Task

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py delete cgt-20260401194138-w8xgn
```

## Environment Variables

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `VOLCENGINE_API_KEY` | Yes | API key for Volcengine |
| `VOLCENGINE_API_BASE` | No | API base URL (default: `https://ark.cn-beijing.volces.com/api/v3`) |

Set in `.genix.env` file.
