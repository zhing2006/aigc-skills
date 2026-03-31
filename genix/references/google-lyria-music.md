# Google Lyria 3 Music Generation

Text-to-Music and Image-to-Music generation using Google's Lyria 3 models.

## Usage

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text description of the music to generate |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-i`, `--images` | None | Input image file paths for image-to-music (max 10) |
| `-m`, `--model` | `lyria-3-pro-preview` | Model to use |
| `-f`, `--format` | `mp3` | Output audio format (mp3 or wav; wav is Pro only) |
| `--instrumental` | false | Force instrumental (no vocals) |
| `--save-lyrics` | false | Save lyrics to a separate .lyrics.txt file |
| `-o`, `--output` | `generated_music.<ext>` | Output file path |

## Supported Models

| Model | Description | Duration | Output |
| ----- | ----------- | -------- | ------ |
| `lyria-3-pro-preview` | Full-length songs with complex structure (default) | Up to ~3-4 minutes | MP3, WAV |
| `lyria-3-clip-preview` | Short musical clips and loops | Fixed 30 seconds | MP3 |

**Note**: If the user does not specify model, use `lyria-3-pro-preview` as default. Use `lyria-3-clip-preview` for quick previews, loops, or when 30 seconds is sufficient.

## Supported Output Formats

| Format | Models | Description |
| ------ | ------ | ----------- |
| `mp3` | Both | Default, widely compatible |
| `wav` | Pro only | Higher quality, larger file |

## Prompt Best Practices

### Basic Structure

A good music prompt includes:

```txt
[Genre/Style] + [Mood/Emotion] + [Instruments] + [Tempo/Energy] + [Additional Details]
```

### Genre and Style

| Category | Examples |
| -------- | -------- |
| Electronic | EDM, house, techno, ambient, synthwave, lo-fi, drum and bass |
| Rock | rock, metal, punk, alternative, indie rock, grunge |
| Classical | orchestral, piano, chamber music, symphony, baroque |
| Jazz | jazz, smooth jazz, bebop, swing, jazz fusion |
| Pop | pop, dance pop, synth pop, indie pop, K-pop |
| Hip-Hop | hip-hop, trap, boom bap, R&B, old school rap |
| World | latin, bossa nova, african, celtic, reggae, flamenco |
| Cinematic | epic, trailer music, film score, dramatic, ambient score |

### Mood and Emotion

| Mood | Descriptors |
| ---- | ----------- |
| Happy | upbeat, cheerful, joyful, playful, bright |
| Sad | melancholic, somber, emotional, nostalgic, bittersweet |
| Energetic | intense, powerful, driving, dynamic, aggressive |
| Calm | peaceful, relaxing, serene, gentle, ambient |
| Dark | ominous, mysterious, tense, suspenseful, haunting |
| Epic | heroic, triumphant, majestic, grand, cinematic |

### Instruments

Specify instruments for more control:

- **Piano**: piano, grand piano, electric piano, Rhodes
- **Guitar**: acoustic guitar, electric guitar, bass guitar, 12-string
- **Strings**: violin, cello, string section, orchestra, harp
- **Synth**: synthesizer, pads, arpeggios, leads, modular synth
- **Drums**: drums, percussion, electronic drums, TR-808, brushed drums
- **Brass**: trumpet, saxophone, horn section, trombone
- **Vocals**: male vocals, female vocals, choir, harmonies

### Tempo and Energy

| Term | BPM Range | Description |
| ---- | --------- | ----------- |
| Very slow | 40-60 | ambient, meditative, drone |
| Slow | 60-80 | ballad, downtempo, chill |
| Medium | 80-120 | moderate, mid-tempo, groovy |
| Fast | 120-160 | upbeat, energetic, dance |
| Very fast | 160+ | frantic, breakbeat, speedcore |

You can specify exact BPM and key: `"120 BPM"`, `"in G major"`, `"D minor"`.

### Song Structure with Timestamps (Pro Feature)

Lyria 3 Pro supports timestamp-based song structure for precise control:

```txt
[0:00 - 0:15] Intro: Soft piano chords, ambient atmosphere
[0:15 - 0:45] Verse: Drums enter, gentle vocals, building energy
[0:45 - 1:15] Chorus: Full band, powerful and triumphant, soaring melody
[1:15 - 1:45] Verse 2: Stripped back, acoustic guitar focus
[1:45 - 2:15] Chorus: Return of full arrangement, even more intense
[2:15 - 2:30] Outro: Fade out with piano and strings
```

### Custom Lyrics

Include lyrics with section tags directly in the prompt:

```txt
[Verse 1]
Walking down the empty street at dawn
Shadows stretching long across the lawn

[Chorus]
We'll find our way back home
No matter how far we roam

[Bridge]
The stars above remind me of your eyes
```

The model generates melody and vocal performance to match the lyrics.

### Image-to-Music

Provide reference images to influence mood, style, and atmosphere:

- A sunset photo → warm, nostalgic, ambient music
- An action scene → intense, driving, percussive music
- A forest landscape → peaceful, organic, nature-inspired music

Images are inspiration, not literal interpretation. Combine with text for best results.

### Multi-language Vocals

Write your prompt and lyrics in the target language. The model adapts vocal style and pronunciation accordingly. For example, write lyrics in Japanese for J-pop style vocals.

### Instrumental Mode

Use the `--instrumental` flag to generate music without vocals. This is equivalent to appending "Instrumental only, no vocals." to your prompt.

## Examples

### Calm Instrumental Piano

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Calm piano melody, ambient and relaxing, soft and gentle, suitable for meditation, in C major, 70 BPM" --instrumental -o calm_piano.mp3
```

### Epic Orchestral with Timestamps (Pro)

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "[0:00-0:20] Soft strings intro, mysterious atmosphere. [0:20-1:00] Drums enter, building tension, brass crescendo. [1:00-1:40] Full orchestra, triumphant and powerful, heroic theme. [1:40-2:00] Gentle fade with solo violin" --instrumental -o epic_orchestral.mp3
```

### Pop Song with Custom Lyrics

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Upbeat pop song, bright and cheerful, synth pop style, female vocals. [Verse 1] City lights are shining bright tonight, every star is dancing in your eyes. [Chorus] We're on top of the world, nothing can stop us now, we're on top of the world." -o pop_song.mp3 --save-lyrics
```

### Image-to-Music

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Create warm, nostalgic music inspired by these images, acoustic guitar and soft vocals" -i sunset_beach.jpg autumn_forest.jpg -o inspired_music.mp3
```

### 30-Second Clip

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Energetic electronic beat, synth leads, festival-ready drop, high energy, 128 BPM" -m lyria-3-clip-preview --instrumental -o edm_clip.mp3
```

### Electronic Dance

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Deep house track, groovy bassline, atmospheric pads, subtle vocal chops, 124 BPM, in A minor" --instrumental -o deep_house.mp3
```

### Jazz Instrumental

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Smooth jazz, saxophone lead with improvisation, walking bass, brushed drums, Rhodes piano comping, elegant and sophisticated, cafe ambiance" --instrumental -o jazz_cafe.mp3
```

### WAV High-Quality Output (Pro)

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Cinematic ambient soundscape, ethereal pads, distant piano, vast and atmospheric, 48kHz stereo" --instrumental -f wav -o cinematic_hq.wav
```

### Lo-fi Background

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "Lo-fi hip-hop beat, relaxing and chill, vinyl crackle, mellow piano chords, tape saturation, perfect for studying, 85 BPM" --instrumental -o lofi_study.mp3
```

### Multi-language Vocal

```bash
{python} {skill_dir}/scripts/google-lyria-music.py "J-pop style song, bright and energetic, 130 BPM. [Verse] 夜空に輝く星を見上げて、君のことを思い出す。[Chorus] 二人で歩いた道、忘れない、ずっと忘れない。" -o jpop_song.mp3 --save-lyrics
```

## Environment Variables

Requires one of the following to be set in `.genix.env` file:

- `GOOGLE_CLOUD_API_KEY` — when `USE_VERTEX_AI = false` (default)
- `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` — when `USE_VERTEX_AI = true`

## Notes

- Both models are in **preview** status; behavior and pricing may change
- All generated audio includes an imperceptible **SynthID watermark**
- Pricing: $0.08 per song (Pro), $0.04 per song (Clip)
- No free tier available for Lyria models
- Generation is **non-deterministic**: the same prompt may produce different results each time
- Lyria 3 is single-turn only: no iterative editing across turns
