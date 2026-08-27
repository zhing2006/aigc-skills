# OpenAI GPT Image

Text-to-Image and Image-to-Image generation using OpenAI's GPT Image models.

## Contents

- [Usage](#usage)
- [Supported Models](#supported-models)
- [Model-Specific Notes](#model-specific-notes)
- [Prompt Best Practices](#prompt-best-practices)
- [Examples](#examples)
- [Environment Variables](#environment-variables)

## Usage

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text prompt for image generation (max 32000 characters) |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--images` | None | Input image file paths for editing (max 16) |
| `-m`, `--model` | `gpt-image-2` | Model to use |
| `-s`, `--size` | `auto` | Output size (`auto` omits the param so the model decides) |
| `-q`, `--quality` | `auto` | Image quality |
| `-f`, `--format` | `png` | Output format |
| `-b`, `--background` | `auto` | Background type (`transparent` requires png or webp) |
| `--normalize-alpha` | off | Clip near-opaque alpha (252-254) back to 255 (png/webp only) |
| `-n`, `--number` | `1` | Number of images to generate (1-10) |
| `-o`, `--output` | `generated_image.png` | Output file path |

## Supported Models

- `gpt-image-2` - Next-generation, default (recommended: improved text rendering, multilingual, neutral color fidelity, custom sizes up to 4K, ~2x faster)
- `gpt-image-1.5` - Previous flagship
- `gpt-image-1` - Standard
- `gpt-image-1-mini` - Lightweight

**Note**: If the user does not specify a model, use `gpt-image-2` as default.

## Supported Sizes

### gpt-image-1.x

- `1024x1024` - Square (default)
- `1536x1024` - Landscape
- `1024x1536` - Portrait
- `auto` - Let the model decide

### gpt-image-2

Accepts `auto` (default) or any custom `WIDTHxHEIGHT` that satisfies all of:

| Constraint | Value |
| ---------- | ----- |
| Edge multiple | Both width and height divisible by `16` |
| Aspect ratio | Between `1:3` and `3:1` (inclusive) |
| Long edge | At most `3840px` |
| Total pixels | Between `655,360` and `8,294,400` |

Common choices: `1024x1024` (square), `1536x1024` / `2048x1152` (landscape), `1024x1536` (portrait), `2048x2048`, `3840x2160` (4K).

Anything above `3,686,400` pixels (the 2560x1440 threshold) is marked experimental by OpenAI — the script prints a warning but still submits the request. Generation is slower and more likely to fail at those sizes.

The script omits `size` from the API call when it's `auto`, so the default just works. With `auto`, bias the aspect ratio via the prompt (e.g. `"portrait composition"`, `"wide landscape"`).

## Supported Quality

- `auto` - Automatically select best quality (default)
- `high` - High quality
- `medium` - Medium quality
- `low` - Low quality

**Note**: If the user does not specify quality, use `auto` as default.

## Supported Formats

- `png` - PNG format (default, supports transparency)
- `jpeg` - JPEG format
- `webp` - WebP format (supports transparency)

## Supported Backgrounds

- `auto` - Model decides (default)
- `transparent` - Transparent background (requires png or webp)
- `opaque` - Solid background

`background=transparent` works on `gpt-image-2` since 2026-08-20 (preview), on both text-to-image and image edit, at no extra cost. `gpt-image-1.5` and `gpt-image-1` support it too. The alpha channel is built into generation rather than cut out afterwards, so it holds up better on glass, smoke, and fine strands of hair than a background-removal tool would.

### Prompting for transparency

**Do not mention the background in the prompt.** The `background` parameter handles it; describing a backdrop ("on a white surface", "studio background") fights the parameter and the model may paint one anyway. Describe only the subject, then add framing cues like `"sticker die-cut style"` or `"isolated product shot"` if you want tight cropping.

### Known preview defects

Two issues are widely reported during the preview (community-reported, not officially acknowledged — OpenAI may fix them at any time):

1. **Opaque regions are not fully opaque.** Alpha in solid areas comes back as 252-254 (usually 253) instead of 255, so a very dark or very light backdrop bleeds through when the asset is composited. `--normalize-alpha` fixes this by clipping alpha ≥ 250 up to 255. It is a no-op when the image already contains a 255 pixel or is semi-transparent throughout, so it never flattens intentional soft edges.
2. **Grey halo at the edges.** The RGB layer under the cutout carries a grey border slightly wider than the alpha mask. This is *not* fixed by `--normalize-alpha`. If it shows up, either re-run with a prompt that puts a deliberate outline on the subject, or erode the alpha mask by 1-2px in an image editor.

**Workflow requirement**: before running the script with `-b transparent`, tell the user about both defects and ask whether to add `--normalize-alpha`. Do not enable it silently.

### Transparency in edit mode

Passing an RGBA image to `-i` and asking the model to preserve the see-through areas does not work — edit output is a hard cutout, and the input's alpha is not carried over. Generate transparent assets from scratch instead of editing an existing transparent PNG.

### Output path must carry alpha

The output extension is used verbatim, so `-b transparent -o sticker.jpg` is rejected. Use a `.png` or `.webp` path. A mismatch between `--format` and the output extension (e.g. `-f webp -o out.png`) only prints a warning — the bytes written match `--format`, not the filename.

## Model-Specific Notes

| Aspect | gpt-image-2 | gpt-image-1.5 |
| ------ | ----------- | ------------- |
| Default in this skill | Yes | No |
| Recommended `--size` | `auto`, or any `WxH` meeting the constraints | `1024x1024` or pick from fixed set |
| Size flexibility | Any 16-multiple size within ratio/pixel limits | 3 fixed sizes + auto |
| Max resolution | `3840x2160` (above 2560x1440 experimental) | 1536 long edge |
| Response shape | b64_json or url (auto-handled) | b64_json |
| `background=transparent` | Supported (preview; png/webp) | Supported |
| `input_fidelity` | Disabled (always high) | Configurable |
| Strengths | Text rendering, multilingual, neutral colors, reasoning, custom sizes | Mature, stable transparency |

## Prompt Best Practices

### Prompt Structure

Use layered structure for best results:

```txt
Scene: [environment/background]
Subject: [main focus with specific details]
Details: [materials, textures, colors]
Constraints: [what to preserve, what to change]
```

Or use this formula:

```txt
A [medium] of [subject] in [environment], [specific visual characteristics]. [Lighting description]. [Composition/camera]. [Style reference].
```

### Key Principles

1. **Be Specific, Not Generic**: Concrete details beat buzzwords
   - ❌ `"A beautiful landscape, 8K ultra-HD, masterpiece"`
   - ✅ `"A misty mountain valley at dawn with golden light filtering through pine trees, reflecting off a still lake. Wide-angle landscape photography."`

2. **Use Layered Structure**: Organize as Scene → Subject → Details → Constraints
   - Use line breaks or labels to reduce confusion
   - Limit to 3-5 key elements per prompt

3. **Prioritize Lighting**: Be specific about light direction and quality
   - ✅ `"Rim lighting from behind creating a golden halo effect"`
   - ❌ `"Good lighting"`

4. **Use Camera/Composition Terms**: These guide realism better than quality buzzwords
   - `"Shot with 35mm lens, shallow depth of field"`
   - `"Bird's eye view", "eye-level perspective", "close-up macro shot"`

5. **Iterate Instead of Overloading**: Generate base image, then refine
   - `"Make the lighting warmer, keep the subject unchanged"`
   - `"Preserve the car's geometry, change only the texture"`

### Text Rendering Tips

- Use quotes or CAPS for text: `"'Welcome to 2025' in bold sans-serif font"`
- Specify placement and size: `"Centered at the bottom, white text on black, 72pt"`
- Spell tricky names character-by-character: `"O-P-E-N-A-I"`
- Test simple phrases before complex layouts

### Identity Preservation (for edits)

- Explicitly state what to keep: `"Keep face, pose, and lighting identical"`
- Describe interactions clearly: `"Preserve the car's geometry, change only the texture"`
- Restate invariants on every iteration to prevent drift

### Lighting Tips

| Mood | Lighting Description |
| ---- | -------------------- |
| Warm | "Golden hour sunlight", "warm ambient glow" |
| Cool | "Blue hour twilight", "cool overcast light" |
| Dramatic | "Rim lighting from behind", "harsh directional spotlight", "chiaroscuro" |
| Soft | "Diffused overcast light", "soft box lighting eliminating harsh shadows" |
| Studio | "Three-point lighting setup", "professional studio strobes" |

### Style Modifiers

| Category | Examples |
| -------- | -------- |
| Photography | "Professional studio photography", "35mm film", "macro shot", "85mm portrait lens" |
| Digital Art | "Concept art", "matte painting", "3D render", "digital illustration" |
| Traditional | "Oil painting", "watercolor wash", "charcoal sketch", "ink drawing" |
| Commercial | "E-commerce product shot", "editorial photography", "advertising campaign" |
| Stylized | "Anime style", "Pixar aesthetic", "comic book art", "vintage poster" |

### Reference Images (Image-to-Image)

- Provide up to 16 reference images
- Describe what elements to use from each image
- Be explicit about what to preserve vs modify
- Use action words: "edit", "add", "transform" (not "combine" or "merge")

## Examples

> All examples below use the default `gpt-image-2`. Sizes must be 16-multiples within the ratio and pixel limits documented above; omit `-s` to let the model choose.

### Photorealistic Portrait

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A high-resolution photograph of a young woman with freckles, standing in a sunlit wheat field during golden hour. She has windswept auburn hair, wearing a vintage floral dress. Soft warm lighting with lens flare, shallow depth of field, 85mm portrait lens aesthetic." -s 1024x1536 -q high -o portrait.png
```

### Product Photography

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A sleek wireless headphone on a minimalist white surface. Professional product photography with soft diffused lighting, subtle reflections, clean background. Commercial e-commerce style." -q high -o headphones.png
```

### Landscape Scene

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A majestic mountain range at sunrise with mist rolling through the valleys. Vibrant orange and pink sky reflected in a still alpine lake. Wide-angle composition, landscape orientation, National Geographic photography style." -s 1536x1024 -q high -o mountain.png
```

### 4K Landscape

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A vast desert canyon at dusk, layered sandstone walls in ochre and violet, a thin river catching the last light at the canyon floor. Ultra-wide vista, high dynamic range, large-format landscape photography." -s 3840x2160 -q high -o canyon_4k.png
```

### Illustration with Transparent Background

The `-b transparent` parameter handles the background — note that the prompt says nothing about a backdrop.

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A cute cartoon robot mascot waving hello, simple flat design illustration, clean bold outlines, vibrant teal and orange palette, sticker die-cut style." -s 1024x1024 -b transparent -f png -o robot_sticker.png
```

With the preview alpha defect worked around (ask the user before adding this flag):

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A cute cartoon robot mascot waving hello, simple flat design illustration, clean bold outlines, vibrant teal and orange palette, sticker die-cut style." -s 1024x1024 -b transparent -f png --normalize-alpha -o robot_sticker.png
```

### Transparent Product Cutout for Compositing

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A matte black stainless steel travel mug with a brushed metal lid, three-quarter view, soft studio key light from upper left with a gentle falloff down the body, crisp specular highlight along the left edge." -s 1536x1024 -q high -b transparent -f png --normalize-alpha -o mug_cutout.png
```

### Icon Design

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A modern app icon for a music streaming service. Minimalist design with a stylized sound wave, gradient from purple to blue, rounded corners, flat design style." -s 1024x1024 -q high -o music_icon.png
```

### Image Editing with References

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "Edit this photo by adding a dramatic sunset sky with orange and purple clouds. Keep the foreground subject exactly as shown." -i original_photo.jpg -s 1536x1024 -o sunset_edit.png
```

### Multiple Image Generation

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A variety of colorful tropical cocktails in different glass shapes, each with unique garnishes, overhead view, summer party aesthetic." -s 1024x1024 -n 4 -o cocktails.png
```

## Environment Variables

Requires the following to be set in `.env` file:

- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_API_BASE` (optional) - Custom API base URL
