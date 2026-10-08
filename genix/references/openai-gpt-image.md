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
| `-m`, `--model` | `gpt-image-2.5-flare` | Model to use |
| `-s`, `--size` | `auto` | Output size (`auto` omits the param so the model decides) |
| `-q`, `--quality` | `auto` | Image quality (`xhigh` / `max` only on gpt-image-2.5) |
| `-f`, `--format` | `png` | Output format |
| `-b`, `--background` | `auto` | Background type (`transparent` requires png or webp) |
| `--normalize-alpha` | off | Clip near-opaque alpha (252-254) back to 255 (png/webp only) |
| `-n`, `--number` | `1` | Number of images to generate (1-10) |
| `-o`, `--output` | `generated_image.png` | Output file path |

## Supported Models

| Model | Positioning | Notes |
| ----- | ----------- | ----- |
| `gpt-image-2.5-flare` | **Default.** Fastest model for high-quality everyday generation | OpenAI's "default choice for most applications": higher quality than `gpt-image-2` at roughly half the latency, same token rates. The small model of the 2.5 pair, optimized for speed |
| `gpt-image-2.5-sunburst` | Most capable model for generation and editing | For workflows where editing precision and subject preservation matter most. The base model of the 2.5 pair, optimized for quality; slower than flare |
| `gpt-image-2` | Previous generation | Still supported, not deprecated. Text rendering, multilingual, neutral color fidelity, custom sizes up to 4K. Transparent background is preview-only here |
| `gpt-image-1.5` | Deprecated | Shutdown 2026-12-01; OpenAI's replacement is `gpt-image-2`. Last model with configurable `input_fidelity` |
| `gpt-image-1` | Deprecated | Shutdown 2026-10-23; replacement `gpt-image-2` |
| `gpt-image-1-mini` | Deprecated | Shutdown 2026-12-01; replacement `gpt-image-2` |

Both 2.5 models were released on 2026-09-08 (snapshot suffix `-2026-09-08`). The script accepts the aliases only, which track OpenAI's latest snapshot. It prints a warning when a deprecated model is used.

For compatible API gateways that require a provider prefix, the script also accepts `openai/gpt-image-2.5-flare` and `openai/gpt-image-2.5-sunburst`. These variants use the same size and quality validation as their unprefixed counterparts, including `xhigh` / `max`. The full model name is sent to the API unchanged; configure `OPENAI_API_BASE` and `OPENAI_API_KEY` for a gateway that supports it.

**Note**: If the user does not specify a model, use `gpt-image-2.5-flare` as default.

### Choosing between Flare and Sunburst

- **Flare** when speed matters: drafts, social and creator content, many variations (`-n`), thumbnails, high-volume runs. It already beats `gpt-image-2` on quality, so it is the no-regret upgrade from the previous default.
- **Sunburst** when the result has to be right: production campaign creative, polished product imagery, precise multi-turn edits, complex multi-reference composites, fine print detail.
- **Migrating a `gpt-image-2` workflow**: if the current output already meets the bar, try Flare first and confirm that quality holds while latency drops. If `gpt-image-2` falls short on a complex use case, try Sunburst first; once it passes, run Flare with the same prompt and inputs and only switch if quality stays acceptable.
- The same `quality` label does not mean the same image quality or response time across models. Compare with the quality held constant, then tune.

## Supported Sizes

### gpt-image-1.x

- `1024x1024` - Square (default)
- `1536x1024` - Landscape
- `1024x1536` - Portrait
- `auto` - Let the model decide

### gpt-image-2 and gpt-image-2.5

`gpt-image-2`, `gpt-image-2.5-flare` and `gpt-image-2.5-sunburst` share the same rules. Accepts `auto` (default) or any custom `WIDTHxHEIGHT` that satisfies all of:

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
- `max` - Highest tier (gpt-image-2.5 only; slowest, most tokens)
- `xhigh` - One tier above high (gpt-image-2.5 only)
- `high` - High quality
- `medium` - Medium quality
- `low` - Low quality

`xhigh` and `max` exist only on `gpt-image-2.5-flare` / `gpt-image-2.5-sunburst` (including their `openai/` variants); the script rejects them on every other model.

**Note**: If the user does not specify quality, use `auto` as default.

### Tuning order

1. Pick the model first (see above), then tune quality. When comparing models, hold `quality` constant.
2. If the output falls short, step up one tier at a time. Once it passes, try a lower tier to see whether latency can be recovered.
3. Reserve `xhigh` / `max` for a specific unmet requirement (fine print, dense infographics, packaging text) that still fits the latency budget. A higher tier is not guaranteed to improve every prompt.
4. Billing is per output token and higher tiers use more tokens per image. Token rates for 2.5 match `gpt-image-2`, but OpenAI's `gpt-image-2` cost calculator does not estimate 2.5 consumption. The script prints `Tokens: input=..., output=...` after each call — relay it when cost matters.

## Supported Formats

- `png` - PNG format (default, supports transparency)
- `jpeg` - JPEG format
- `webp` - WebP format (supports transparency)

## Supported Backgrounds

- `auto` - Model decides (default)
- `transparent` - Transparent background (requires png or webp)
- `opaque` - Solid background

`gpt-image-2.5-flare` and `gpt-image-2.5-sunburst` support `opaque` and `transparent` as a regular feature, on both text-to-image and image edit. On `gpt-image-2`, transparent output is still a preview (since 2026-08-20). `gpt-image-1.5` and `gpt-image-1` support it too but are scheduled for shutdown. The alpha channel is built into generation rather than cut out afterwards, so it holds up better on glass, smoke, and fine strands of hair than a background-removal tool would.

### Prompting for transparency

**Do not mention the background in the prompt.** The `background` parameter handles it; describing a backdrop ("on a white surface", "studio background") fights the parameter and the model may paint one anyway. Describe only the subject, then add framing cues like `"sticker die-cut style"` or `"isolated product shot"` if you want tight cropping.

### Known preview defects (gpt-image-2)

Two issues are widely reported during the `gpt-image-2` preview (community-reported, not officially acknowledged — OpenAI may fix them at any time):

1. **Opaque regions are not fully opaque.** Alpha in solid areas comes back as 252-254 (usually 253) instead of 255, so a very dark or very light backdrop bleeds through when the asset is composited. `--normalize-alpha` fixes this by clipping alpha ≥ 250 up to 255. It is a no-op when the image already contains a 255 pixel or is semi-transparent throughout, so it never flattens intentional soft edges.
2. **Grey halo at the edges.** The RGB layer under the cutout carries a grey border slightly wider than the alpha mask. This is *not* fixed by `--normalize-alpha`. If it shows up, either re-run with a prompt that puts a deliberate outline on the subject, or erode the alpha mask by 1-2px in an image editor.

**Workflow requirement for `gpt-image-2`**: before running the script with `-m gpt-image-2 -b transparent`, tell the user about both defects and ask whether to add `--normalize-alpha`. Do not enable it silently.

**gpt-image-2.5**: OpenAI lists transparent output as a regular (non-preview) feature on both 2.5 models and early adopters report cleaner cutouts, but whether the two preview defects above are gone has not yet been confirmed in this skill. Do not add `--normalize-alpha` up front. Run the alpha check below on the first transparent result. The defect is present only when the subject should contain solid areas *and* the max alpha lands in 250-254: then clip the existing file in place (see below) instead of regenerating, tell the user the defect persists on 2.5, and add `--normalize-alpha` to further transparent runs in the same session. A max alpha below 250 is not the defect — the artwork is deliberately translucent.

### Checking the alpha channel

Whatever the model, check the delivered file rather than trusting the parameter:

- Confirm the file really has an alpha channel (`RGBA`) instead of a painted white or checkerboard backdrop.
- Inspect hair, glass, shadows, and object edges — those are where a cutout fails first.
- Read the alpha range: `{python} -c "from PIL import Image; im=Image.open('out.png'); print(im.mode, im.getchannel('A').getextrema())"`. For a subject with solid areas, expect `RGBA (0, 255)`.
- Interpret the max alpha together with what the subject is:
  - `255` — clean, nothing to do.
  - `250`-`254` on a subject that should be solid (a mug, a mascot, a logo) — the near-opaque defect. Fix the file you already have; do not regenerate, which costs tokens and changes the picture:
    `{python} -c "from PIL import Image; p='out.png'; im=Image.open(p).convert('RGBA'); im.putalpha(im.getchannel('A').point(lambda v: 255 if v >= 250 else v)); im.save(p, **({'lossless': True, 'exact': True} if p.lower().endswith('.webp') else {}))"`
    This is the same clip that `--normalize-alpha` applies at generation time.
  - Below `250`, or a subject that is translucent by design (smoke, glass, a veil, a ghost) — not a defect. `--normalize-alpha` would leave such a file untouched anyway; keep it as is.
- Keep PNG lossless; do not recompress a transparent PNG through a lossy step.

### Transparency in edit mode

Passing an RGBA image to `-i` and asking the model to preserve the see-through areas does not work — edit output is a hard cutout, and the input's alpha is not carried over. Generate transparent assets from scratch instead of editing an existing transparent PNG.

### Output path must carry alpha

The output extension is used verbatim, so `-b transparent -o sticker.jpg` is rejected. Use a `.png` or `.webp` path. A mismatch between `--format` and the output extension (e.g. `-f webp -o out.png`) only prints a warning — the bytes written match `--format`, not the filename.

## Model-Specific Notes

| Aspect | gpt-image-2.5-flare | gpt-image-2.5-sunburst | gpt-image-2 | gpt-image-1.5 |
| ------ | ------------------- | ---------------------- | ----------- | ------------- |
| Default in this skill | Yes | No | No | No |
| Status | Current | Current | Current | Deprecated, shutdown 2026-12-01 |
| Recommended `--size` | `auto`, or any `WxH` meeting the constraints | Same as flare | Same as flare | `1024x1024` or pick from fixed set |
| Size flexibility | Any 16-multiple size within ratio/pixel limits | Same | Same | 3 fixed sizes + auto |
| Max resolution | `3840x2160` (above 2560x1440 experimental) | Same | Same | 1536 long edge |
| Quality tiers | `auto`, `low`, `medium`, `high`, `xhigh`, `max` | Same | Up to `high` | Up to `high` |
| Latency | Fastest (about half of gpt-image-2) | Slowest of the family | Baseline | — |
| Response shape | b64_json or url (auto-handled) | Same | Same | b64_json |
| `background=transparent` | Supported (png/webp) | Supported (png/webp) | Preview (png/webp) | Supported |
| `input_fidelity` | Not accepted (always high) | Not accepted (always high) | Not accepted (always high) | Configurable |
| Strengths | Speed, everyday quality above gpt-image-2, volume work | Editing precision, subject preservation, fine detail | Text rendering, multilingual, neutral colors, custom sizes | Mature, stable transparency |

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

Any readable format works — a short sentence, a descriptive paragraph, a JSON-like block, an instruction list, or tags. There is no special syntax; pick whatever is easiest to maintain and iterate on.

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
   - Camera specs are cues for how the image should look, not a guarantee. When you need realism, say `"photorealistic"` explicitly and name materials, colors, and the medium.

5. **Iterate Instead of Overloading**: Generate base image, then refine
   - `"Make the lighting warmer, keep the subject unchanged"`
   - `"Preserve the car's geometry, change only the texture"`

6. **Describe People and Actions**: Say how a person is framed and what they are doing
   - Framing: `"full body visible, feet included"`, `"tight head-and-shoulders portrait"`
   - Gaze and interaction: `"looking straight into the camera"`, `"holding the mug with both hands"`

### Text Rendering Tips

- Put the exact wording in quotes: `"the sign reads 'Fresh and clean'"`; use CAPS if it should be uppercase
- Specify placement, size, and typography: `"Centered at the bottom, white bold sans-serif on black, high contrast"`
- Spell tricky names character-by-character: `"O-P-E-N-A-I"`
- Say `"render the text exactly once"` and `"no extra text"` to avoid duplicates and stray captions
- Test simple phrases before complex layouts, and check the spelling in the output before delivering it

### Edits: Separate the Change from the Constraints

- Name the single change and freeze everything else: `"Change only the label text to 'Summer Blend'. Keep the bottle geometry, lighting, layout, colors, and background unchanged."`
- List what must survive explicitly: identity, geometry, layout, lighting, labels, pose, skin tone
- One change per call. For several changes, feed the previous output back in with `-i` and make the next change
- Restate the invariants on every iteration — repeated edits can drift even when each step looked fine
- Faces and products: `"Do not change her face, facial features, skin tone, body shape, pose, or identity in any way"`
- If a region must stay pixel-identical, composite the approved edit back into the original in an image editor instead of relying on the prompt alone

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

- Provide up to 16 reference images; the first one is the primary image
- Assign each image a role by number and purpose: `"Image 1 is the subject. Image 2 defines the art style. Image 3 supplies the jacket. Image 4 is the background."`
- Describe what elements to use from each image
- Be explicit about what to preserve vs modify
- Use action words: "edit", "add", "transform" (not "combine" or "merge")

### Result Checklist

Before delivering, check the output against the request:

- Is required text accurate and legible? Are diagram labels and relationships correct?
- Do identities, product shapes, labels, and reference details remain intact?
- Did the edit change only what was requested?
- If transparency was required, does the file carry a real alpha channel rather than a painted background?

## Examples

> All examples below use the default `gpt-image-2.5-flare` unless `-m` is given. Sizes must be 16-multiples within the ratio and pixel limits documented above; omit `-s` to let the model choose.

### Photorealistic Portrait

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A high-resolution photograph of a young woman with freckles, standing in a sunlit wheat field during golden hour. She has windswept auburn hair, wearing a vintage floral dress. Soft warm lighting with lens flare, shallow depth of field, 85mm portrait lens aesthetic." -s 1024x1536 -q high -o portrait.png
```

### Product Photography

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A sleek wireless headphone on a minimalist white surface. Professional product photography with soft diffused lighting, subtle reflections, clean background. Commercial e-commerce style." -q high -o headphones.png
```

### Fast Draft, Then Final

Iterate on composition at `low`, then re-run the approved prompt at `high`:

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A cozy reading nook by a rain-streaked window, oversized armchair, stacked books, a steaming mug on the sill. Warm lamp light, soft focus, editorial interior photography." -q low -o nook_draft.png
{python} {skill_dir}/scripts/openai-gpt-image.py "A cozy reading nook by a rain-streaked window, oversized armchair, stacked books, a steaming mug on the sill. Warm lamp light, soft focus, editorial interior photography." -q high -o nook_final.png
```

### Provider-Prefixed Variants

When `OPENAI_API_BASE` points to a compatible gateway supporting these model names:

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A cozy reading nook, warm lamp light, editorial interior photography." -m openai/gpt-image-2.5-flare -o nook.png
{python} {skill_dir}/scripts/openai-gpt-image.py "Change only the label text to 'Summer Blend'. Keep everything else unchanged." -m openai/gpt-image-2.5-sunburst -i product.png -q max -o product_relabel.png
```

### Precision Edit with Sunburst

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "Change only the label text on the bottle to 'Summer Blend'. Keep the bottle geometry, cap, lighting, reflections, layout, and background exactly as they are. No other text." -m gpt-image-2.5-sunburst -i product.png -o product_relabel.png
```

### Maximum Detail

Only after `high` has been tried and falls short; slower and uses more tokens:

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A dense infographic titled 'How a Heat Pump Works' with five labeled stages, thin line icons, a two-column layout, and small but legible annotations. Flat vector style, white background, navy and orange palette." -m gpt-image-2.5-sunburst -s 2048x2048 -q xhigh -o heatpump_infographic.png
```

### Multi-Reference Composite with Roles

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "Image 1 is the subject; keep her face, hair, and body shape unchanged. Image 2 supplies the jacket: put it on the subject with matching folds and lighting. Image 3 is the background: place the subject in that setting at the same camera height. Do not add any other elements or text." -i person.jpg jacket.png cafe.jpg -s 1024x1536 -o composite.png
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

On `gpt-image-2`, with the preview alpha defect worked around (ask the user before adding this flag):

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A cute cartoon robot mascot waving hello, simple flat design illustration, clean bold outlines, vibrant teal and orange palette, sticker die-cut style." -m gpt-image-2 -s 1024x1024 -b transparent -f png --normalize-alpha -o robot_sticker.png
```

### Transparent Product Cutout for Compositing

```bash
{python} {skill_dir}/scripts/openai-gpt-image.py "A matte black stainless steel travel mug with a brushed metal lid, three-quarter view, soft studio key light from upper left with a gentle falloff down the body, crisp specular highlight along the left edge." -m gpt-image-2.5-sunburst -s 1536x1024 -q high -b transparent -f png -o mug_cutout.png
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

The openai SDK (3.x) verifies TLS against the operating system's trust store. Behind a corporate TLS-inspecting proxy, point `SSL_CERT_FILE` at the proxy's CA bundle if certificate errors appear.
