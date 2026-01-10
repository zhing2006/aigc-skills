# Google Veo 3.1 Video Generation

Text-to-Video and Image-to-Video generation using Google's Veo 3.1 model.

## Usage

```bash
{python} {skill_dir}/scripts/google-veo.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text prompt for video generation |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--image` | None | Input image file path for image-to-video |
| `-m`, `--model` | `veo-3.1-generate-001` | Model to use |
| `-a`, `--aspect-ratio` | `16:9` | Video aspect ratio |
| `-d`, `--duration` | `8` | Video duration in seconds |
| `-r`, `--resolution` | `720p` | Video resolution |
| `-n`, `--negative-prompt` | None | Content to avoid generating |
| `--no-audio` | False | Disable audio generation |
| `--seed` | None | Seed for reproducibility (0-4294967295) |
| `-o`, `--output` | `generated_video.mp4` | Output file path |

## Supported Models

| Model | Description |
| ----- | ----------- |
| `veo-3.1-generate-001` | Full quality, highest fidelity (default) |
| `veo-3.1-fast-generate-001` | Faster generation, lower latency |

**Note**: If the user does not specify model, use `veo-3.1-generate-001` as default.

## Supported Aspect Ratios

`16:9` (landscape, default), `9:16` (portrait)

## Supported Durations

`4`, `6`, `8` seconds (default: 8)

## Supported Resolutions

`720p` (default), `1080p`

**Important**: 1080p resolution is only available with 8s duration and 16:9 aspect ratio.

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

### Audio Prompting

Veo 3.1 generates native audio. Use these techniques to guide sound:

**Dialogue:**

```txt
The detective looks up at the woman and says in a weary voice, "Of all the offices in this town, you had to walk into mine."
```

**Sound Effects (SFX):**

```txt
SFX: thunder cracks in the distance
SFX: The rustle of dense leaves, distant exotic bird calls
```

**Ambient Noise:**

```txt
Ambient noise: the quiet hum of a starship bridge
Ambient noise: gentle orchestral score swelling
```

### Lighting Descriptors

| Mood | Description |
| ---- | ----------- |
| Clinical | "Harsh fluorescent overhead lights" |
| Sci-fi | "Green glow of monochrome monitor" |
| Golden | "Soft morning light" |
| Theatrical | "Dramatic spotlight from the front" |
| Melancholic | "Cool blue tones" |
| Energetic | "Lens flare" |

### Artistic Styles

| Category | Examples |
| -------- | -------- |
| Realistic | "Photorealistic", "shot on 8K camera" |
| Cinematic | "Cinematic", "shot on 35mm film" |
| Animation | "Japanese anime style", "Pixar-like 3D animation" |
| Art Movement | "In the style of Van Gogh", "Art Deco design" |
| Period | "Retro aesthetic", "1980s color film" |

### Negative Prompt Tips

Describe what to exclude descriptively rather than using negation:

```txt
# Effective
"a desolate landscape with no buildings or roads"

# Less Effective
"no man-made structures"
```

Common negative prompts: `"cartoon, drawing, low quality, blurry, distorted, amateur"`

## Examples

### Basic Text-to-Video

```bash
{python} {skill_dir}/scripts/google-veo.py "A cat walking on the beach at golden hour sunset. Wide shot, gentle waves in the background. Photorealistic, cinematic." -o cat_beach.mp4
```

### Image-to-Video

```bash
{python} {skill_dir}/scripts/google-veo.py "The cat slowly turns its head and looks directly at the camera, curious expression. Shallow depth of field." -i cat_photo.png -o cat_animated.mp4
```

### Cinematic with Camera Movement

```bash
{python} {skill_dir}/scripts/google-veo.py "Crane shot starting low on a lone hiker and ascending high above, revealing they are standing on the edge of a colossal, mist-filled canyon at sunrise. Epic fantasy style, awe-inspiring, soft morning light." -a 16:9 -d 8 -r 1080p -o epic_reveal.mp4
```

### With Dialogue and Audio

```bash
{python} {skill_dir}/scripts/google-veo.py "Medium shot, a detective in a noir office. He looks up from his desk and says in a weary voice, 'Of all the offices in this town, you had to walk into mine.' SFX: Rain pattering on the window. Ambient noise: distant jazz music from a radio." -o noir_scene.mp4
```

### Fast Model for Quick Preview

```bash
{python} {skill_dir}/scripts/google-veo.py "A butterfly landing on a flower in slow motion. Macro lens, shallow depth of field, golden sunlight." -m veo-3.1-fast-generate-001 -d 4 -o butterfly_preview.mp4
```

### Portrait Video (9:16)

```bash
{python} {skill_dir}/scripts/google-veo.py "Close-up of a woman's face as she smiles, soft natural lighting, bokeh background with city lights. Cinematic, shallow depth of field." -a 9:16 -o portrait_smile.mp4
```

### With Negative Prompt

```bash
{python} {skill_dir}/scripts/google-veo.py "A peaceful mountain lake at dawn, mist rising from the water. Wide shot, drone perspective slowly descending. Photorealistic." -n "people, boats, buildings, text, watermark" -o mountain_lake.mp4
```

## Environment Variables

Requires `GOOGLE_CLOUD_API_KEY` to be set in `.env` file.
