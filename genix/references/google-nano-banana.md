# Google Nano Banana Image Generation

Text-to-Image and Image-to-Image generation using Google's Nano Banana models.

## Usage

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text prompt for image generation |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--images` | None | Input image file paths (max 14) |
| `-m`, `--model` | `gemini-3.1-flash-image` | Model to use |
| `-a`, `--aspect-ratio` | `1:1` | Output aspect ratio |
| `-r`, `--resolution` | `1K` | Output resolution |
| `-s`, `--search` | false | Enable Image Search grounding (**Nano Banana 2 only**) |
| `-o`, `--output` | `generated_image.png` | Output file path |

## Supported Models

| Model | Code Name | Speed | Cost (1K) | Notes |
| ----- | --------- | ----- | --------- | ----- |
| `gemini-3.1-flash-image` | Nano Banana 2 | Fast (Flash) | ~$0.045 | **Default** (GA). Image Search grounding, extra aspect ratios; `gemini-3.1-flash-image-preview` kept as legacy alias |
| `gemini-3-pro-image-preview` | Nano Banana Pro | Slower (Pro) | ~$0.134 | Studio-quality, original model |

**Note**: If the user does not specify model, use `gemini-3.1-flash-image` (Nano Banana 2) as default.

## Supported Aspect Ratios

**All models**: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

**Nano Banana 2 only** (`gemini-3.1-flash-image-preview`): `4:1`, `1:4`, `8:1`, `1:8`

**Important**: Do NOT use Nano Banana 2-only aspect ratios (`4:1`, `1:4`, `8:1`, `1:8`) with the Pro model — the API will return an error.

**Note**: If the user does not specify aspect ratio, use `1:1` as default.

## Supported Resolutions

`1K` (1024px), `2K` (2048px), `4K` (4096px)

**Note**: If the user does not specify resolution, use `1K` as default.

## Image Search Grounding (Nano Banana 2 Only)

Image Search grounding enables the model to retrieve real photos from Google Image Search as visual references during generation. This produces more accurate results for real-world subjects.

**When to use** (`-s` flag):
- Real landmarks and architecture (e.g., Eiffel Tower, Sydney Opera House)
- Specific products, brands, or logos
- Known animals, plants, or natural formations
- Famous artworks or cultural references

**When NOT to use**:
- Pure fantasy or fictional scenes
- Abstract art or creative compositions
- Style transfers where accuracy to reality is not needed

**Important**: Do NOT use `--search` with the Pro model (`gemini-3-pro-image-preview`) — it is only supported on Nano Banana 2.

## Prompt Best Practices

### Prompt Structure

Use this formula for best results:

```txt
[Subject + Adjectives] doing [Action] in [Location/Context]. [Composition/Camera Angle]. [Lighting/Atmosphere]. [Style/Media].
```

### Key Principles

1. **Use Natural Language**: Write full sentences as if briefing a human artist, not keyword lists
   - ❌ `"Cool car, neon, city, night, 8k"`
   - ✅ `"A cinematic shot of a futuristic sports car speeding through a rainy Tokyo street at night"`

2. **Be Specific**: Define subjects, settings, lighting, and mood explicitly
   - Include materiality: "matte finish", "soft velvet", "brushed metal"
   - Specify camera: "85mm portrait lens", "wide-angle 24mm", "overhead shot"

3. **Avoid Keyword Spam**: Skip repetitive tags like "4k, trending on artstation, masterpiece" - the model understands descriptive language

4. **Precise Text Rendering**: For text in images, be explicit
   - ✅ `"Write 'HELLO WORLD' in bold red serif font on the sign"`

5. **Provide Context**: Explain purpose or audience for better artistic decisions
   - `"For a Brazilian high-end gourmet cookbook"` → informs professional plating

### Lighting Tips

| Mood | Lighting Description |
| ---- | -------------------- |
| Intimate | "Candlelit", "warm ambient glow" |
| Dramatic | "Harsh rim lighting", "single spotlight from above" |
| Professional | "Three-point studio lighting", "soft diffused light" |
| Cinematic | "Golden hour", "neon-lit noir atmosphere" |

### Style Modifiers

| Category | Examples |
| -------- | -------- |
| Photography | "Raw photo", "film grain", "DSLR quality" |
| Digital Art | "Concept art", "matte painting", "3D render" |
| Traditional | "Oil painting", "watercolor", "charcoal sketch" |
| Stylized | "Anime style", "Pixar-inspired", "comic book art" |

### Reference Images (Image-to-Image)

- Upload 3-5 images for best character/brand consistency
- State explicitly: "Keep facial features exactly as in the reference image"
- Describe changes while maintaining identity

## Examples

### Cinematic Portrait

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "A weathered astronaut removing her helmet on Mars, dust particles floating in golden hour sunlight. Close-up portrait shot with 85mm lens. Dramatic rim lighting from the setting sun. Photorealistic with subtle film grain." -a 3:4 -r 2K -o astronaut.png
```

### Product Photography

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "A sleek matte black wireless earbuds case on white marble surface. Overhead product shot with soft diffused studio lighting. Clean minimal aesthetic for e-commerce listing." -a 1:1 -r 2K -o earbuds.png
```

### Landscape Scene

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "Ancient Japanese temple nestled in misty mountains during cherry blossom season. Wide-angle establishing shot. Soft morning light filtering through fog. Traditional ink wash painting style with subtle color accents." -a 16:9 -r 4K -o temple.png
```

### Character with Text

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "A friendly robot barista with glowing blue eyes holding a coffee cup. The cup has 'HELLO HUMAN' written in white sans-serif font. Warm cafe lighting. Pixar-inspired 3D render style." -a 4:5 -r 2K -o robot_barista.png
```

### Style Transfer with Reference

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "Transform this photo into Studio Ghibli anime style. Keep the composition and subject exactly the same. Soft watercolor textures with vibrant but gentle colors." -i photo.jpg -a 16:9 -r 2K -o ghibli_style.png
```

### Character Consistency

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "The character from the reference images now sitting in a cozy library reading a book. Keep facial features exactly as shown. Warm afternoon sunlight through window. Photorealistic style." -i ref1.png ref2.png ref3.png -a 3:2 -r 2K -o character_library.png
```

### Image Search Grounding (Nano Banana 2)

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "The Sydney Opera House at golden hour with dramatic cloud formations above. Wide-angle architectural photography with warm rim lighting." -s -a 16:9 -r 4K -o sydney_opera.png
```

### Ultra-Wide Panorama (Nano Banana 2)

```bash
{python} {skill_dir}/scripts/google-nano-banana.py "A sweeping mountain panorama at dawn, mist rolling through valleys, snow-capped peaks catching first light. Landscape photography with rich natural colors." -a 8:1 -r 4K -o mountain_panorama.png
```

## Environment Variables

Requires `GOOGLE_CLOUD_API_KEY` to be set in `.env` file.
