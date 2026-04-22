# OpenAI GPT Image

Text-to-Image and Image-to-Image generation using OpenAI's GPT Image models.

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
| `-s`, `--size` | `auto` | Output size (auto omits the param so routing decides) |
| `-q`, `--quality` | `auto` | Image quality |
| `-f`, `--format` | `png` | Output format |
| `-b`, `--background` | `auto` | Background type |
| `-n`, `--number` | `1` | Number of images to generate (1-10) |
| `-o`, `--output` | `generated_image.png` | Output file path |

## Supported Models

- `gpt-image-2` - Next-generation, default (recommended: improved text rendering, multilingual, neutral color fidelity, up to 4K, ~2x faster)
- `gpt-image-1.5` - Previous flagship; choose this when you need parameter-level transparent background support
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

- `auto` only (default)

gpt-image-2 uses an intelligent routing layer that chooses the size for you; explicit `WxH` values are rejected by the API. To bias the aspect ratio, describe it in the prompt instead:

- `"square composition"` / `"square 1:1"`
- `"portrait composition"` / `"vertical 9:16"`
- `"wide landscape"` / `"16:9 cinematic"`

The script omits `size` from the API call when it's `auto`, so the default just works.

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

**Note on `gpt-image-2`**: OpenAI's official docs state that `background=transparent` is not supported on `gpt-image-2`, though some proxy endpoints may still accept it. Recommended: with `gpt-image-2`, leave `-b` at `auto` and instead describe transparency in the prompt itself (e.g. "transparent background, isolated subject on alpha channel, no backdrop"). The model will decide whether to output an alpha channel. If you need a guaranteed parameter-level transparent PNG, use `gpt-image-1.5` with `-b transparent`.

## Model-Specific Notes

| Aspect | gpt-image-2 | gpt-image-1.5 |
| ------ | ----------- | ------------- |
| Default in this skill | Yes | No |
| Recommended `--size` | `auto` (only accepted value; routing decides) | `1024x1024` or pick from fixed set |
| Size flexibility | `auto` only — bias via prompt | 3 fixed sizes + auto |
| Max resolution | Routing-controlled (up to 4K) | 1536 long edge |
| Response shape | b64_json or url (auto-handled) | b64_json |
| `background=transparent` | Officially unsupported (use prompt) | Supported |
| `input_fidelity` | Disabled (always high) | Configurable |
| Strengths | Text rendering, multilingual, neutral colors, reasoning | Mature, broader parameter support |

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

> Examples that pass an explicit `-s WxH` use `-m gpt-image-1.5` because gpt-image-2 only accepts `-s auto`. For gpt-image-2, omit `-s` and describe the desired aspect ratio in the prompt (e.g. "portrait composition", "wide landscape").

### Photorealistic Portrait

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A high-resolution photograph of a young woman with freckles, standing in a sunlit wheat field during golden hour. She has windswept auburn hair, wearing a vintage floral dress. Soft warm lighting with lens flare, shallow depth of field, 85mm portrait lens aesthetic." -m gpt-image-1.5 -s 1024x1536 -q high -o portrait.png
```

### Product Photography

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A sleek wireless headphone on a minimalist white surface. Professional product photography with soft diffused lighting, subtle reflections, clean background. Commercial e-commerce style." -q high -o headphones.png
```

### Landscape Scene

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A majestic mountain range at sunrise with mist rolling through the valleys. Vibrant orange and pink sky reflected in a still alpine lake. Wide-angle composition, landscape orientation, National Geographic photography style." -m gpt-image-1.5 -s 1536x1024 -q high -o mountain.png
```

### Illustration with Transparent Background (gpt-image-2, prompt-driven)

Note: gpt-image-2 only accepts `-s auto` (the default), so don't pass `-s WxH`. Aspect ratio and transparency are both expressed in the prompt.

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A cute cartoon robot mascot waving hello, simple flat design illustration, clean lines, vibrant colors, transparent background, isolated subject on alpha channel, no backdrop, sticker format." -m gpt-image-2 -f png -o robot_sticker.png
```

### Illustration with Transparent Background (gpt-image-1.5, parameter-guaranteed)

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A cute cartoon robot mascot waving hello, simple flat design illustration style, clean lines, vibrant colors, transparent PNG sticker format." -m gpt-image-1.5 -s 1024x1024 -b transparent -f png -o robot_sticker.png
```

### Icon Design

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A modern app icon for a music streaming service. Minimalist design with a stylized sound wave, gradient from purple to blue, rounded corners, flat design style, square composition." -q high -o music_icon.png
```

### Image Editing with References

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "Edit this photo by adding a dramatic sunset sky with orange and purple clouds. Keep the foreground subject exactly as shown, wide landscape composition." -i original_photo.jpg -o sunset_edit.png
```

### Multiple Image Generation

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A variety of colorful tropical cocktails in different glass shapes, each with unique garnishes, overhead view, summer party aesthetic, square composition." -n 4 -o cocktails.png
```

## Environment Variables

Requires the following to be set in `.env` file:

- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_API_BASE` (optional) - Custom API base URL
