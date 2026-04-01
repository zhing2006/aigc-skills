# Volcengine Seedance 2.0 Video Generation

Text-to-Video, Image-to-Video, and Multi-modal Reference video generation using Volcengine Seedance 2.0.

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

*At least one of `prompt`, `--first-frame`, `--ref-image`, or `--ref-video` is required.

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--first-frame` | None | First frame image for image-to-video |
| `--last-frame` | None | Last frame image (requires `--first-frame`) |
| `--ref-image` | None | Reference image (repeatable, max 9) |
| `--ref-video` | None | Reference video URL (repeatable, max 3) |
| `--ref-audio` | None | Reference audio (repeatable, max 3, requires ref image/video) |
| `-m`, `--model` | `doubao-seedance-2-0-260128` | Model to use |
| `-r`, `--resolution` | `720p` | Video resolution |
| `-a`, `--ratio` | `adaptive` | Aspect ratio |
| `-d`, `--duration` | `5` | Duration in seconds (4-15 or -1 for auto) |
| `--no-audio` | false | Disable synchronized audio generation |
| `--watermark` | false | Add watermark |
| `--web-search` | false | Enable web search enhancement (text-to-video only) |
| `-o`, `--output` | `generated_video.mp4` | Output file path |

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
| `-s`, `--status` | None | Filter by status: `queued`, `running`, `succeeded`, `failed`, `cancelled` |
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
| Seedance 2.0 | `doubao-seedance-2-0-260128` | Highest quality (default) |
| Seedance 2.0 fast | `doubao-seedance-2-0-fast-260128` | Faster, lower cost |

**Note**: If the user does not specify model, use `doubao-seedance-2-0-260128` as default. For quick previews or drafts, recommend the fast model.

## Supported Resolutions

`480p`, `720p` (default)

**Tip**: Draft at 480p to iterate quickly, then re-run at 720p for final output.

## Supported Aspect Ratios

| Ratio | Description |
| ----- | ----------- |
| `16:9` | Landscape (widescreen) |
| `4:3` | Classic TV |
| `1:1` | Square |
| `3:4` | Portrait (classic) |
| `9:16` | Portrait (mobile/vertical) |
| `21:9` | Ultra-wide (cinematic) |
| `adaptive` | Auto-select based on input (default) |

## Supported Durations

`4` to `15` seconds (integer), or `-1` for model auto-select.

Default: `5` seconds. Longer durations cost more tokens.

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

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "使用图片1作为主角，全程使用视频1的第一视角构图" --ref-image character.png --ref-video scene.mp4 --ref-audio bgm.mp3 -a 16:9 -d 11 -o result.mp4
```

**Note**: First frame mode and multi-modal reference mode are mutually exclusive. Audio references require at least one image or video reference.

## Prompt Best Practices

### Core Formula

```
Subject + Scene/Atmosphere + Action/Performance + Camera Movement + Style/Lighting
```

Or equivalently:

```
Scene description → Subject action → Camera movement → Audio cue
```

### Prompt Length

- Recommended: 60-200 characters (Chinese) or 60-200 words (English)
- Too long may cause the model to ignore details
- Both Chinese and English prompts are supported

### Key Principles

1. **One video = one subject + one core action** — this is the iron rule
2. **Use slow, smooth, continuous motion** — prioritize: 缓慢、柔和、连续、自然、流畅
3. **Be specific, not vague** — "golden hour warm lighting from the left" beats "beautiful lighting"
4. **Describe physics** — "wind blowing through hair", "water splashing on rocks" leverages the model's physics simulation
5. **Use positive constraints** — Seedance does NOT support negative prompts; say what you want, not what to avoid

### Camera Movements (运镜)

Seedance 2.0 has extremely strong recognition of camera terms. Use them to instantly elevate quality.

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
| Photorealistic | "photorealistic, hyper-detailed, 8K, ultra HD" |
| Golden hour | "golden hour, warm tones, soft light" |
| Dramatic | "strong rim light, silhouette, high contrast" |
| Neon/Cyberpunk | "neon-lit, cyberpunk, high contrast, saturated colors" |
| Documentary | "documentary-style, raw footage, natural lighting" |
| Anime | "Japanese anime style, cel-shaded" |

### Audio Prompting

Seedance 2.0 generates native synchronized audio (dialogue, SFX, music). Tips:

- **Dialogue**: Put lines in double quotes: `男人说："你好，欢迎来到这里。"`
- **Sound Effects**: Describe naturally: `脚步声踩在雪地上，咯吱作响`
- **Background Music**: Include mood cues: `背景音乐为轻快的吉他弹唱`
- **Language**: Supports 8+ languages for lip-sync (Chinese, English, Japanese, Korean, etc.)

### Timeline / Storyboard Prompting

For longer videos, describe events in chronological order:

```
0-3秒：近景，女孩站在窗前，柔和的晨光洒在脸上，微微侧头；
3-6秒：中景，她转身走向桌边，拿起咖啡杯，缓慢推镜头；
6-10秒：特写，咖啡杯中的热气袅袅升起，浅景深，暖色调。
```

### Quality Enhancement Keywords

Append to any prompt for better output:

```
高清画质, 细节丰富, 画面稳定, 色彩自然, 电影质感
```

Or in English:

```
4K, ultra HD, rich details, sharp clarity, cinematic texture, stable picture
```

### What to Avoid

| Don't | Why |
| ----- | --- |
| Complex multi-person interaction (fighting, hugging) | Causes body clipping |
| Vague words ("nice", "beautiful", "cool") | AI can't interpret these |
| Contradictory requirements ("super fast" + "extremely stable") | Conflicting instructions |
| Excessive speed ("rapid", "lightning fast") | Creates chaos and artifacts |
| Too many subjects with independent actions | Model focuses on one, ignores others |

### Reference System

When using multi-modal reference mode, use numbered references in the prompt:

```
图片1中的人物作为主角，全程使用视频1的第一视角构图，背景音乐使用音频1
```

References are numbered in the order they appear in the `--ref-image`, `--ref-video`, `--ref-audio` arguments.

## Examples

### Text-to-Video with Camera Movement

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "中景，一位穿着白色连衣裙的女孩站在樱花树下，微风吹过，花瓣缓缓飘落，柔和的自然光，缓慢推镜头，电影质感，浅景深" -a 16:9 -d 8 -o sakura.mp4
```

### Image-to-Video with Audio

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "猫咪慢慢睁开眼睛，伸了个懒腰，发出轻微的喵呜声" -i sleeping_cat.jpg -d 6 -o cat_wakeup.mp4
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
{python} {skill_dir}/scripts/volcengine-seedance.py "Crane shot ascending over a misty mountain valley at dawn, golden light breaking through clouds, epic cinematic scale, 8K quality" -a 21:9 -d 10 -o epic_valley.mp4
```

### First + Last Frame Transition

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "流畅的画面过渡，色调从冷色逐渐转为暖色" -i winter_scene.png --last-frame summer_scene.png -d 8 -o season_transition.mp4
```

### Multi-modal Reference (Product Ad)

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "图片1中的模特手持图片2中的产品，面向镜头展示，清新简约背景，近景镜头，模特说：'这款面霜质地轻盈，一抹就吸收'" --ref-image model.jpg --ref-image product.jpg -a 9:16 -d 10 -o product_ad.mp4
```

### With Web Search Enhancement

```bash
{python} {skill_dir}/scripts/volcengine-seedance.py "微距镜头拍摄一只玻璃蛙，透明腹部可见心脏跳动，热带雨林背景" --web-search -a 16:9 -d 8 -o glass_frog.mp4
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

# List tasks filtered by model, page 2
{python} {skill_dir}/scripts/volcengine-seedance.py list -m doubao-seedance-2-0-fast-260128 -p 2

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
