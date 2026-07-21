# DashScope Qwen Image 3.0

Text-to-Image (T2I), Image-to-Image (I2I), and image editing with Alibaba
Cloud Model Studio's `qwen-image-3.0-pro` model. The model accepts up to three
reference images and can return up to six generated images per request.

> **Access requirement:** Qwen Image 3.0 is currently invite-only. Apply for
> access in the Model Studio model marketplace before calling the API.

## Contents

- [Basic Usage](#basic-usage)
- [Parameters](#parameters)
- [Capabilities and Limits](#capabilities-and-limits)
- [Prompt Best Practices](#prompt-best-practices)
- [Examples](#examples)
- [Environment Variables](#environment-variables)

## Basic Usage

```bash
{python} {skill_dir}/scripts/dashscope-qwen-image.py "prompt" [options]
```

## Parameters

| Parameter | Required | Description |
| --------- | -------- | ----------- |
| `prompt` | Yes | Generation prompt or image editing instruction (Chinese and English supported) |
| `-i`, `--images` | No | 1-3 reference image paths, public URLs, or image data URIs |
| `-m`, `--model` | No | Model ID; currently only `qwen-image-3.0-pro` |
| `-s`, `--size` | No | Output size as `<width>x<height>`; omitted by default so the model chooses |
| `-n`, `--num-images` | No | Number of output images, 1-6 (default: 1) |
| `--no-prompt-extend` | No | Disable automatic prompt rewriting (enabled by default) |
| `--negative-prompt` | No | Describe content that should not appear |
| `--seed` | No | Random seed from 0 to 2147483647 |
| `--watermark` | No | Add the Qwen-Image watermark (off by default) |
| `-o`, `--output` | No | Output path (default: `generated_image.png`); multiple results get `_1`, `_2`, etc. |

## Capabilities and Limits

| Capability | Limit |
| ---------- | ----- |
| Text-to-Image | Prompt without `--images` |
| Image-to-Image / Edit | 1-3 reference images plus one prompt |
| Input formats | JPG/JPEG, PNG, BMP, TIFF, WEBP, GIF |
| Input file size | Up to 10MB per image |
| Recommended input dimensions | Width and height between 384 and 2048 pixels |
| Output size | Total pixels between `512x512` and `2048x2048` |
| Output count | 1-6 images |
| API output format | PNG |

Local reference images are Base64-encoded automatically. Public HTTP(S) URLs
and `data:image/...;base64,...` values are passed through unchanged.

## Prompt Best Practices

### Text-to-Image

1. Describe the subject and action first.
2. Add the scene, composition, camera angle, lighting, color palette, and style.
3. Quote exact text that must appear in the image.
4. Use `--negative-prompt` for unwanted artifacts instead of adding conflicting
   negative instructions to the main prompt.
5. Leave prompt extension enabled for short prompts. Disable it when exact
   wording and composition matter more than added detail.

### Image Editing and Multi-Image Fusion

- Refer to images in input order as `图1`, `图2`, and `图3` (or `image 1`,
  `image 2`, and `image 3`).
- State what to change and what must remain unchanged.
- For multiple references, assign each image a clear role such as subject,
  background, clothing, or visual style.
- Use precise spatial descriptions for localized edits, for example:
  `将图1左上角的招牌文字改为"今日特惠"，人物和背景保持不变`.

## Examples

### Text-to-Image with Model-Selected Size

```bash
{python} {skill_dir}/scripts/dashscope-qwen-image.py "春日城市咖啡店海报，玻璃窗外有盛开的樱花，暖色自然光，现代杂志排版，标题清晰写着'春日限定'" -o spring_poster.png
```

### Explicit Size and Multiple Variants

```bash
{python} {skill_dir}/scripts/dashscope-qwen-image.py "高端护肤品广告，白色陶瓷瓶置于水面，柔和侧光，干净留白，写实商业摄影" -s 1536x1024 -n 3 -o skincare.png
```

### Image Editing

```bash
{python} {skill_dir}/scripts/dashscope-qwen-image.py "把人物的服装换成深灰色商务西装，保持面部、发型、姿势和背景不变" -i portrait.jpg -o business_portrait.png
```

### Multi-Image Fusion

```bash
{python} {skill_dir}/scripts/dashscope-qwen-image.py "将图1中的人物放到图2的咖啡店场景中，穿着图3中的香槟色衬衫，保持人物面部特征不变，竖幅七分身人像" -i person.png cafe.jpg shirt.webp -o fusion.png
```

### Controlled Prompt and Seed

```bash
{python} {skill_dir}/scripts/dashscope-qwen-image.py "极简黑白品牌标志，居中构图，文字准确写着'GENIX'" --no-prompt-extend --negative-prompt "模糊文字，额外字符，复杂背景" --seed 42 -s 1024x1024 -o logo.png
```

## Environment Variables

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `DASHSCOPE_API_KEY` | Yes | Model Studio API key for the selected region |
| `DASHSCOPE_IMAGE_BASE_URL` | No | Native API host, API root, or full generation endpoint (default: `https://dashscope.aliyuncs.com`) |

Beijing and Singapore use separate API keys and endpoints. Do not mix them.
Alibaba Cloud recommends a workspace-specific domain:

- Beijing: `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com`
- Singapore: `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com`

Set the corresponding host as `DASHSCOPE_IMAGE_BASE_URL`. The script appends
the native multimodal generation endpoint automatically. Do not use an
OpenAI-compatible `/compatible-mode/v1` URL for this variable.

Generated image URLs expire after 24 hours. The script downloads every result
immediately, so no manual download is needed.

Official API reference:
https://help.aliyun.com/zh/model-studio/qwen-image-generation-and-editing-api-reference
