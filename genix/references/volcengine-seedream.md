# Volcengine Seedream Image Generation

Text-to-Image, Image-to-Image, Multi-Image Fusion, and Group (sequential) image generation using Volcengine Doubao Seedream models.

## Usage

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text prompt for image generation (Chinese and English supported) |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--images` | None | Reference image paths or URLs (max 10 for 5.0 pro, 14 for others) |
| `-m`, `--model` | `doubao-seedream-5-0-pro-260628` | Model to use |
| `-s`, `--size` | `2K` | Resolution preset (`1K`/`2K`/`3K`/`4K`, model-dependent) or `<width>x<height>` pixels |
| `-g`, `--group` | false | Enable group generation — a set of related images (**not** for 5.0 pro) |
| `-n`, `--max-images` | auto | Max images for group generation, 1-15 (implies `--group`) |
| `--optimize` | None | Prompt optimization mode: `standard` or `fast` (`fast`: 5.0 pro / 4.0 only) |
| `--web-search` | false | Enable web search tool (**5.0 lite only**) |
| `--watermark` | false | Add "AI generated" watermark |
| `-o`, `--output` | `generated_image.png` | Output file path; group images get `_1`, `_2`... suffixes |

## Supported Models

| Model | Model ID | Description |
| ----- | -------- | ----------- |
| Seedream 5.0 pro | `doubao-seedream-5-0-pro-260628` | Highest quality (default), interactive editing; single image only, max 10 reference images |
| Seedream 5.0 lite | `doubao-seedream-5-0-lite-260128` | Fast and affordable, group generation, web search, up to 4K |
| Seedream 4.5 | `doubao-seedream-4-5-251128` | Group generation, up to 4K |
| Seedream 4.0 | `doubao-seedream-4-0-250828` | Previous generation, group generation, up to 4K |

**Note**: If the user does not specify model, use `doubao-seedream-5-0-pro-260628` as default. When the user needs a set of related images (group generation) or web search, use `doubao-seedream-5-0-lite-260128` instead.

## Supported Sizes

Two ways to specify size (do not mix):

1. **Resolution preset** (recommended): pass `1K`/`2K`/`4K` etc. and describe the aspect ratio, shape, or intended use of the image in natural language inside the prompt (e.g. "16:9 横版海报"). The model decides the final dimensions.
2. **Explicit pixels**: pass `<width>x<height>` (e.g. `2048x1024`). Total pixels and aspect ratio (within [1/16, 16]) must satisfy the model's limits.

| Model | Presets | Pixel range (width x height) |
| ----- | ------- | ---------------------------- |
| Seedream 5.0 pro | `1K`, `2K` (default) | [1280x720 (921600), 4624220] |
| Seedream 5.0 lite | `2K`, `3K`, `4K` | [2560x1440 (3686400), 4096x4096 (16777216)] |
| Seedream 4.5 | `2K`, `4K` | [2560x1440 (3686400), 4096x4096 (16777216)] |
| Seedream 4.0 | `1K`, `2K`, `4K` | [1280x720 (921600), 4096x4096 (16777216)] |

**Note**: If the user does not specify size, use `2K` as default. The script validates size against the chosen model and errors early if unsupported.

## Group Generation (组图)

Generate a set of content-related images (e.g. a 4-panel story, brand poster variants, character turnarounds) in one request. Supported by **5.0 lite / 4.5 / 4.0 only** (not 5.0 pro).

- Enable with `-g`, optionally limit count with `-n` (1-15)
- The model decides the actual number of images based on the prompt, up to `max_images`
- **Reference images + generated images ≤ 15** per request
- Describe the set explicitly in the prompt, e.g. "生成一组 4 张连贯的四格漫画" or "Generate 6 poster variants of..."
- Output files are saved as `<name>_1.png`, `<name>_2.png`, ...

## Web Search (5.0 lite only)

With `--web-search`, the model decides on its own whether to search the internet (products, weather, news, etc.) to improve factual accuracy and timeliness of the generated image. Adds some latency.

**When to use**: real products or brands, current events, time-sensitive content.
**When NOT to use**: pure fantasy scenes, abstract art, style transfer.

## Prompt Best Practices

### Prompt Structure

```txt
[Subject + Details] + [Scene/Background] + [Composition/Viewpoint] + [Lighting/Atmosphere] + [Style/Medium] + [Text content if any]
```

### Key Principles

1. **Both Chinese and English work well** — Seedream has strong native Chinese understanding and excellent Chinese/English text rendering in images
2. **Keep it focused**: max ~300 Chinese characters or ~600 English words; overly long prompts scatter information and lose details
3. **Use natural language**, not keyword spam — describe like briefing a designer
4. **Be specific**: materials, camera angle, lighting direction, color palette
5. **Positive constraints only** — describe what you want, not what to avoid
6. **For text in images**, quote the exact text: `海报标题写着"春日限定"` or `The sign reads "OPEN 24H"`

### Reference Images (Image-to-Image / Multi-Image Fusion)

- Number references in input order and refer to them as 图1/图2 (or "image 1", "image 2") in the prompt:
  `将图1中的人物置于图2的场景中，保持人物面部特征不变`
- State explicitly what to keep unchanged: "保持构图不变"、"保持服装细节一致"
- For multi-image fusion, describe the role of each image (subject / background / style reference)

### Interactive Editing (5.0 pro)

Seedream 5.0 pro supports precise position-aware editing. Describe the location in the prompt using coordinates, regions, or directional language:

```txt
将图片左上角的文字改为"限时折扣"，其他区域保持不变
把画面中央的红色汽车换成白色，背景不变
```

### Style Modifiers

| Category | Examples |
| -------- | -------- |
| Photography | 写实摄影, 85mm 人像镜头, 浅景深, raw photo, film grain |
| Illustration | 扁平插画, 国风水墨, 厚涂, watercolor, concept art |
| Design | 海报设计, UI 设计图, 品牌 VI, minimalist poster |
| 3D/CG | 3D 渲染, C4D, Pixar style, clay material |

### Lighting Tips

| Mood | Lighting Description |
| ---- | -------------------- |
| Warm/intimate | 黄昏暖光, 烛光, warm ambient glow |
| Dramatic | 侧逆光, 强对比光影, single spotlight |
| Professional | 三点布光, 柔光箱, soft diffused studio lighting |
| Cinematic | 电影感色调, golden hour, neon-lit |

## Examples

### Text-to-Image (default 5.0 pro)

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "一只戴着圆框眼镜的橘猫坐在堆满旧书的木桌前，午后阳光从左侧窗户洒入，暖色调，浅景深，写实摄影风格，16:9 横版构图" -o cat_study.png
```

### Explicit Pixel Size

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "极简风格的咖啡品牌横幅，米色背景，居中构图，标题写着\"SLOW MORNING\"" -s 2048x1024 -o banner.png
```

### Image-to-Image Editing

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "把画面中的天空换成粉紫色晚霞，保持其他区域不变" -i photo.jpg -o sunset_edit.png
```

### Multi-Image Fusion

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "将图1中的人物置于图2的雪山场景中，人物穿着图3的红色羽绒服，保持面部特征不变，全身照，自然光" -i person.png scene.jpg jacket.png -o fusion.png
```

### Group Generation (5.0 lite)

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "生成一组 4 张连贯的四格漫画：一只柴犬学习烘焙蛋糕，从手忙脚乱到最终成功，日系简笔画风格，画面底部配简短中文文字" -m doubao-seedream-5-0-lite-260128 -g -n 4 -o shiba_comic.png
```

### Character Turnaround (4.5)

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "基于参考图生成该角色的三视图：正面、侧面、背面，白色背景，保持服装和发型完全一致" -i character.png -m doubao-seedream-4-5-251128 -g -n 3 -o turnaround.png
```

### With Web Search (5.0 lite)

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "最新款某品牌旗舰手机的产品渲染图，悬浮在渐变蓝色背景中，展示真实外观细节" -m doubao-seedream-5-0-lite-260128 --web-search -o phone.png
```

### 4K Poster (4.0)

```bash
{python} {skill_dir}/scripts/volcengine-seedream.py "中国风新年海报，红金配色，祥云和灯笼元素，竖版 9:16，标题写着\"新春大吉\"" -m doubao-seedream-4-0-250828 -s 4K -o poster.png
```

## Environment Variables

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `VOLCENGINE_API_KEY` | Yes | API key for Volcengine |
| `VOLCENGINE_API_BASE` | No | API base URL (default: `https://ark.cn-beijing.volces.com/api/v3`) |

Set in `.genix.env` file.

**Note**: Generated image URLs from the API expire after 24 hours; the script downloads them immediately, so no action is needed.
