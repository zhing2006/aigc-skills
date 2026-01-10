# OpenAI Sora

Text-to-Video and Image-to-Video generation using OpenAI's Sora models.

## Usage

```bash
uv run {skill_dir}/scripts/openai-sora.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text prompt for video generation |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--image` | None | Input image file path for image-to-video |
| `-m`, `--model` | `sora-2` | Model to use |
| `-d`, `--duration` | `4` | Duration in seconds |
| `-s`, `--size` | `720x1280` | Output resolution |
| `-o`, `--output` | `generated_video.mp4` | Output file path |

## Supported Models

| Model | Description |
| ----- | ----------- |
| `sora-2` | Fast iteration, good for exploration and concepting (default) |
| `sora-2-pro` | Production quality, higher fidelity, takes longer |

**Note**: If the user does not specify model, use `sora-2` as default.

## Supported Durations

`4`, `8`, `12` seconds (default: 4)

## Supported Sizes

| Size | Aspect Ratio | Description |
| ---- | ------------ | ----------- |
| `720x1280` | 9:16 | Portrait/vertical (default) |
| `1280x720` | 16:9 | Landscape/horizontal |
| `1024x1792` | 9:16 | Portrait high-res |
| `1792x1024` | 16:9 | Landscape high-res |

**Note**: If the user does not specify size, use `720x1280` as default.

## Prompt Best Practices

### Prompt Structure Formula

Use this formula for best results:

```txt
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
```

### Example

```txt
Medium shot, a tired corporate worker, rubbing his temples in exhaustion, in front of a bulky 1980s computer in a cluttered office late at night. The scene is lit by harsh fluorescent overhead lights and the green glow of the monochrome monitor. Retro aesthetic, shot as if on 1980s color film, slightly grainy.
```

### Camera Movements

| Movement | Description |
| -------- | ----------- |
| `Dolly shot` | Move camera toward/away from subject |
| `Tracking shot` | Follow subject movement |
| `Crane shot` | High ascending/descending movement |
| `Aerial view` | Bird's eye perspective |
| `Slow pan` | Horizontal camera sweep |
| `POV shot` | First-person perspective |

### Shot Types

| Shot | Description |
| ---- | ----------- |
| `Wide shot` | Full scene overview |
| `Medium shot` | Subject from waist up |
| `Close-up` | Face or detail focus |
| `Extreme close-up` | Intense detail |
| `Low angle` | Looking upward at subject |
| `Two-shot` | Multiple subjects in frame |

### Lens & Focus Techniques

| Technique | Effect |
| --------- | ------ |
| `Shallow depth of field` | Blurred background, sharp subject |
| `Wide-angle lens` | Expansive perspective |
| `Soft focus` | Dreamy, diffused effect |
| `Deep focus` | Sharp foreground to background |

### Lighting Descriptors

| Mood | Description |
| ---- | ----------- |
| Clinical | "Harsh fluorescent overhead lights" |
| Sci-fi | "Neon glow", "holographic displays" |
| Golden | "Soft morning light", "golden hour" |
| Theatrical | "Dramatic spotlight from the front" |
| Melancholic | "Cool blue tones", "overcast" |
| Energetic | "Lens flare", "vibrant colors" |

### Artistic Styles

| Category | Examples |
| -------- | -------- |
| Realistic | "Photorealistic", "shot on 8K camera" |
| Cinematic | "Cinematic", "shot on 35mm film" |
| Animation | "Japanese anime style", "Pixar-like 3D animation" |
| Art Movement | "In the style of Van Gogh", "Art Deco design" |
| Period | "Retro aesthetic", "1980s color film" |

## Examples

### Basic Text-to-Video (Portrait)

```bash
uv run {skill_dir}/scripts/openai-sora.py "A cat walking on the beach at golden hour sunset. Soft warm lighting, gentle waves in the background. Photorealistic." -o cat_beach.mp4
```

### Landscape Video

```bash
uv run {skill_dir}/scripts/openai-sora.py "Aerial drone shot slowly flying over a misty mountain range at sunrise. Cinematic, epic scale, nature documentary style." -s 1280x720 -d 8 -o mountains.mp4
```

### Image-to-Video

```bash
uv run {skill_dir}/scripts/openai-sora.py "The cat slowly turns its head and looks directly at the camera with a curious expression. Shallow depth of field." -i cat_photo.png -o cat_animated.mp4
```

### Cinematic Scene

```bash
uv run {skill_dir}/scripts/openai-sora.py "Medium shot, a detective in a noir office. He looks up from his desk and exhales cigarette smoke. Rain pattering on the window. Black and white, film noir aesthetic." -s 1280x720 -d 8 -o noir_scene.mp4
```

### High Quality with Pro Model

```bash
uv run {skill_dir}/scripts/openai-sora.py "A butterfly landing on a flower in slow motion. Macro lens, shallow depth of field, golden sunlight, nature documentary quality." -m sora-2-pro -d 4 -o butterfly.mp4
```

### Abstract/Artistic

```bash
uv run {skill_dir}/scripts/openai-sora.py "Colorful paint drops falling into water in slow motion, creating swirling abstract patterns. High-speed photography, vibrant colors." -d 8 -o paint_abstract.mp4
```

### Product Showcase

```bash
uv run {skill_dir}/scripts/openai-sora.py "A sleek smartphone rotating on a pedestal, studio lighting with soft reflections. Clean white background, product commercial style." -s 720x1280 -d 4 -o phone_showcase.mp4
```

## Environment Variables

Requires the following to be set in `.env` file:

- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_API_BASE` (optional) - Custom API base URL

For Azure OpenAI:

- `USE_AZURE_OPENAI` = `"true"`
- `OPENAI_API_BASE` - Azure endpoint URL
- `AZURE_OPENAI_API_VERSION` - API version

## Notes

- Video generation takes time (typically 1-5 minutes depending on duration and model)
- Progress updates are shown during generation
- Copyrighted characters and music are not allowed
- Real people (including public figures) cannot be generated
- Input images with human faces may be rejected
