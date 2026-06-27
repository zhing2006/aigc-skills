# DashScope HappyHorse Text-to-Video

Text-to-Video generation using Alibaba Bailian (DashScope) **HappyHorse**. The model
turns a text prompt into physically realistic, smoothly-moving video. The native API is
asynchronous (create task → poll → download), handled automatically by the script.

## Commands

### generate (default)

Create a video generation task and wait for the result. This is the default command —
the `generate` keyword can be omitted.

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py generate "prompt" [options]
{python} {skill_dir}/scripts/dashscope-happyhorse.py "prompt" [options]
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text prompt describing the video to generate |

#### Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-m`, `--model` | `happyhorse-1.1-t2v` | Model to use |
| `-r`, `--resolution` | `1080P` | Video resolution (`720P`, `1080P`; lowercase accepted) |
| `-a`, `--ratio` | `16:9` | Aspect ratio |
| `-d`, `--duration` | `5` | Duration in seconds (3-15) |
| `--no-watermark` | false | Disable the "Happy Horse" watermark (API adds it by default) |
| `--seed` | None | Random seed `0-2147483647` for reproducibility |
| `-o`, `--output` | `generated_video.mp4` | Output file path |

### get

Query a single video generation task by ID. Task IDs and result URLs are valid for **24 hours**.

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py get <task_id>
```

#### Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `task_id` | Yes | The task ID to query |

## Supported Models

| Model | Model ID | Description |
| ----- | -------- | ----------- |
| HappyHorse 1.1 | `happyhorse-1.1-t2v` | Latest, highest quality (default) |
| HappyHorse 1.0 | `happyhorse-1.0-t2v` | Previous generation |

**Note**: If the user does not specify a model, use `happyhorse-1.1-t2v` as default.

## Supported Resolutions

`720P`, `1080P` (default)

Lowercase (`720p` / `1080p`) is accepted and normalized automatically.

## Supported Aspect Ratios

| Ratio | Description |
| ----- | ----------- |
| `16:9` | Landscape (widescreen, default) |
| `9:16` | Portrait (mobile/vertical) |
| `1:1` | Square |
| `4:3` | Classic TV |
| `3:4` | Portrait (classic) |
| `4:5` | Portrait (social) |
| `5:4` | Landscape (near-square) |
| `9:21` | Tall ultra-wide |
| `21:9` | Ultra-wide (cinematic) |

## Supported Durations

`3` to `15` seconds (integer). Default: `5`. Longer durations cost more.

## Watermark

By default the API burns a **"Happy Horse"** watermark into the bottom-right corner.
Pass `--no-watermark` to generate a clean video.

## Prompt Best Practices

HappyHorse is tuned for **physical realism and smooth, continuous motion**. Prompts that
describe believable physics and clear, singular motion produce the best results.

### Core Formula

```
Subject + Scene/Atmosphere + Action/Motion + Camera Movement + Style/Lighting
```

### Prompt Length

- Max: 2500 Chinese characters or 5000 non-Chinese characters (excess is auto-truncated)
- **Language**: any language is supported
- Keep it focused — over-long prompts scatter the model's attention; describe one clear scene

### Key Principles

1. **One video = one subject + one core action** — avoid juggling multiple independent actions
2. **Lean into physics** — "wind ripples the water surface", "snow crunches underfoot",
   "fabric sways with the breeze"; HappyHorse simulates physical motion well
3. **Prefer slow, smooth, continuous motion** — 缓慢、柔和、连续、自然、流畅
4. **Be specific, not vague** — "warm golden light from the left at dusk" beats "nice lighting"
5. **Avoid excessive speed** — "rapid", "lightning fast" tend to produce chaos and artifacts

### Camera Movements (运镜)

| Movement | Chinese | Description |
| -------- | ------- | ----------- |
| Dolly in / out | 推镜头 / 拉镜头 | Camera moves closer / farther |
| Pan left / right | 左摇 / 右摇 | Camera rotates horizontally |
| Tilt up / down | 上仰 / 下俯 | Camera rotates vertically |
| Tracking shot | 跟镜头 | Camera follows a moving subject |
| Crane up / down | 升镜头 / 降镜头 | Camera rises or descends |
| Orbit | 环绕运镜 | Camera orbits around subject |
| Static tripod | 固定机位 | Locks camera, prevents drift |
| Aerial / Drone | 航拍 | Bird's-eye perspective |

### Shot Types (景别)

`特写` (extreme close-up) · `近景` (close-up) · `中景` (medium) · `全景` (full) ·
`远景` (wide) · `大远景` (extreme wide)

### Lighting & Style (光影/风格)

| Category | Keywords |
| -------- | -------- |
| Cinematic | "cinematic, film grain, 35mm film" |
| Photorealistic | "photorealistic, hyper-detailed, 8K, ultra HD" |
| Golden hour | "golden hour, warm tones, soft light" |
| Dramatic | "strong rim light, silhouette, high contrast" |
| Documentary | "documentary-style, natural lighting" |

### Quality Enhancement Keywords

```
高清画质, 细节丰富, 画面稳定, 色彩自然, 电影质感, 运动流畅
```

Or in English:

```
4K, ultra HD, rich details, sharp clarity, cinematic texture, stable picture, smooth motion
```

## Examples

### Basic Text-to-Video

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "一座由硬纸板和瓶盖搭建的微型城市，在夜晚焕发出生机。一列硬纸板火车缓缓驶过，小灯点缀其间，照亮前路。" -o mini_city.mp4
```

### Cinematic with Camera Movement

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "中景，一位穿着白色连衣裙的女孩站在樱花树下，微风吹过，花瓣缓缓飘落，柔和的自然光，缓慢推镜头，电影质感，浅景深" -a 16:9 -d 8 -r 1080P -o sakura.mp4
```

### Vertical Clip, Clean (no watermark)

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "航拍，海浪缓缓拍打金色沙滩，夕阳余晖洒在水面，运动流畅，画面稳定" -a 9:16 -d 6 --no-watermark -o beach.mp4
```

### Reproducible Output with Seed

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "微距镜头，露珠从花瓣滑落，慢动作，浅景深，细节丰富" --seed 42 -r 720P -o dewdrop.mp4
```

### Quick Draft at 720P

```bash
{python} {skill_dir}/scripts/dashscope-happyhorse.py "一只橘猫在窗台上伸懒腰，阳光透过窗户洒在身上" -r 720P -d 4 -o cat_draft.mp4
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
