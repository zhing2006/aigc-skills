# ElevenLabs Text-to-Speech

Text-to-Speech generation using ElevenLabs API with voice search support.

## Usage

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "text" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `text` | Yes | Text to convert to speech |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-v`, `--voice-id` | `21m00Tcm4TlvDq8ikWAM` | Voice ID to use |
| `-s`, `--voice-search` | None | Search query to find a voice |
| `-m`, `--model` | `eleven_multilingual_v2` | Model for speech generation |
| `-f`, `--format` | `mp3_44100_128` | Output audio format |
| `--stability` | None | Voice stability (0-1) |
| `--similarity` | None | Voice similarity boost (0-1) |
| `--speed` | None | Speech speed (0.7-1.2) |
| `-o`, `--output` | `generated_speech.<ext>` | Output file path |

## Supported Models

| Model | Description |
| ----- | ----------- |
| `eleven_v3` | Most expressive, emotionally rich, 70+ languages, 5K chars |
| `eleven_multilingual_v2` | Natural speech, 29 languages, 10K chars (default) |
| `eleven_flash_v2_5` | Ultra-low latency ~75ms, 32 languages |
| `eleven_turbo_v2_5` | High quality, low latency ~250ms, 32 languages |

**Note**: If the user does not specify model, use `eleven_multilingual_v2` as default.

## Voice Selection

### Using Voice ID

Provide a voice ID directly with `-v`:

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "Hello" -v JBFqnCBsd6RMkjVDRZzb
```

### Using Voice Search

Search for a voice by description with `-s`:

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "Hello" -s "British male"
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "Hello" -s "female narrator calm"
```

The search looks through voice names, descriptions, and labels.

### Default Voice

If neither `-v` nor `-s` is provided, uses Rachel (21m00Tcm4TlvDq8ikWAM).

### Common Voice IDs

| Name | Voice ID | Gender | Accent | Use Case |
| ---- | -------- | ------ | ------ | -------- |
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Female | American | Calm narration |
| Brian | `nPczCjzI2devNBz1zQrb` | Male | American | Deep narration |
| George | `JBFqnCBsd6RMkjVDRZzb` | Male | British | Raspy narration |
| Alice | `Xb7hH8MSUJpSbSDYk0k2` | Female | British | Confident news |
| Adam | `pNInz6obpgDQGcFmaJgB` | Male | American | Deep narration |
| Matilda | `XrExE9yKIg1WjnnlVkGX` | Female | American | Warm audiobook |
| Daniel | `onwK4e9ZLuTAKqWW03F9` | Male | British | Deep news |

## Text Formatting Best Practices

### Audio Tags (Eleven v3 Only)

Eleven v3 supports bracketed audio tags for emotional and tonal control. These tags are embedded directly in the text.

**Emotion Tags:**

| Tag | Effect |
| --- | ------ |
| `[excited]` | Excited, energetic delivery |
| `[sad]` | Sorrowful tone |
| `[angry]` | Intense, angry delivery |
| `[nervous]` | Anxious, uncertain tone |
| `[frustrated]` | Annoyed delivery |
| `[tired]` | Fatigued, low energy |
| `[curious]` | Inquisitive tone |
| `[sarcastic]` | Sarcastic delivery |

**Vocal Expression Tags:**

| Tag | Effect |
| --- | ------ |
| `[whispers]` | Soft, quiet voice |
| `[shouts]` | Loud, shouting |
| `[laughs]` | Laughter |
| `[sighs]` | Sighing |
| `[crying]` | Tearful voice |
| `[clears throat]` | Throat clearing |
| `[gulps]` | Swallowing nervously |
| `[hesitates]` | Uncertain pause |
| `[stammers]` | Stuttering |

**Tone & Delivery Tags:**

| Tag | Effect |
| --- | ------ |
| `[cheerfully]` | Happy, upbeat |
| `[flatly]` | Monotone, emotionless |
| `[deadpan]` | Dry, unemotional |
| `[playfully]` | Light, teasing |
| `[dramatically]` | Theatrical |
| `[matter-of-fact]` | Straightforward |
| `[mischievously]` | Playful, sneaky |

**Accent Tags:**

| Tag | Effect |
| --- | ------ |
| `[British accent]` | British English accent |
| `[Australian accent]` | Australian accent |
| `[Southern US accent]` | Southern American accent |
| `[strong X accent]` | Emphasized accent (replace X) |

**Character Tags:**

| Tag | Effect |
| --- | ------ |
| `[pirate voice]` | Pirate character |
| `[evil scientist voice]` | Villain archetype |
| `[childlike tone]` | Young, innocent |

### Audio Tag Examples

```text
[whispers] I think someone is watching us.

[excited] Oh my gosh, I can't believe we won!

[nervously] I... I'm not sure this is going to work. [gulps] But let's try anyway.

[British accent] Good morning, how may I help you today?

It was a VERY long day [sighs] ... nobody listens anymore.
```

### Punctuation Control

| Technique | Effect |
| --------- | ------ |
| `...` (ellipsis) | Creates pauses and emphasis |
| `CAPS` | Increases vocal stress |
| `—` (dash) | Brief pause |
| `?` / `!` | Natural intonation |

### Tag Layering

Tags can be combined for nuanced delivery:

```text
[nervously] [whispers] Do you think they heard us?

[excited] [British accent] Brilliant! Absolutely brilliant!
```

### Important Notes

1. **V3 only**: Audio tags work best with `eleven_v3` model
2. **Voice compatibility**: Some tags work better with certain voices
3. **Test first**: Results vary by voice, test before production use
4. **No SSML breaks**: V3 does not support `<break>` tags, use punctuation instead
5. **Remove onomatopoeia**: When using vocal expression tags, remove corresponding onomatopoeia from text

**Example - Avoid duplication:**

```text
# Wrong - duplicates the laugh effect
[laughs] Haha, that's so funny!

# Correct - tag handles the laugh
[laughs] That's so funny!

# Wrong - duplicates the sigh
[sighs] Hahhh... I'm so tired.

# Correct - tag handles the sigh
[sighs] I'm so tired.
```

## Voice Search Best Practices

The `-s` parameter searches through voice names, descriptions, and labels. The search looks in both your own voices and the Voice Library (5000+ community voices).

### Search Keywords

| Category | Keywords |
| -------- | -------- |
| Gender | `male`, `female` |
| Age | `young`, `middle aged`, `old` |
| Accent | `American`, `British`, `Australian`, `Irish`, `Swedish` |
| Tone | `deep`, `calm`, `warm`, `raspy`, `soft`, `confident`, `seductive` |
| Use Case | `narration`, `news`, `audiobook`, `video games`, `conversational` |
| Language | `English`, `Chinese`, `Japanese`, `Korean`, `Spanish`, `French`, `German` |

### Effective Search Examples

| Goal | Search Query |
| ---- | ------------ |
| British male narrator | `"British male narration"` |
| Calm female for meditation | `"female calm meditation"` |
| Deep voice for documentary | `"deep male documentary"` |
| Young energetic voice | `"young excited"` |
| News presenter style | `"news presenter confident"` |
| Audiobook narrator | `"warm audiobook female"` |
| Video game character | `"video games character"` |

### Tips

1. **Combine keywords**: Use 2-3 keywords for better results (e.g., `"British female calm"`)
2. **Use case matters**: Include the intended use (e.g., `"narration"`, `"news"`, `"audiobook"`)
3. **Accent specificity**: Be specific about accent when needed (e.g., `"British"` vs `"Australian"`)
4. **Fallback to default**: If no voice is found, the script automatically uses Rachel (default)

## Voice Settings

### Stability (0-1)

Controls emotional range and consistency:

- **High (0.7-1.0)**: More consistent, stable delivery
- **Low (0.0-0.3)**: Broader emotional range, more expressive

**For eleven_v3 model**: Stability is limited to three values:

| Value | Mode | Description |
| ----- | ---- | ----------- |
| `0.0` | Creative | Most expressive, may have hallucinations |
| `0.5` | Natural | Closest to original voice recording |
| `1.0` | Robust | Highly stable, less responsive to audio tags |

Other values are automatically adjusted to the nearest valid value.

### Similarity (0-1)

Controls adherence to original voice characteristics:

- **High (0.7-1.0)**: Closer to original voice
- **Low (0.0-0.3)**: More variation allowed

### Speed (0.7-1.2)

Controls speech velocity:

- **0.7**: Slower speech
- **1.0**: Normal speed (default)
- **1.2**: Faster speech

## Supported Output Formats

**MP3**: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`

**PCM**: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`

**Opus**: `opus_48000_64`, `opus_48000_128`

## Examples

### Basic TTS with Default Voice

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "Hello, welcome to our application." -o welcome.mp3
```

### TTS with Voice Search

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "The weather today is sunny with a high of 75 degrees." -s "British male news" -o weather.mp3
```

### TTS with Specific Voice ID

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "Once upon a time in a distant land..." -v XrExE9yKIg1WjnnlVkGX -o story.mp3
```

### TTS with Custom Voice Settings

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "This is a very important announcement." --stability 0.8 --similarity 0.9 --speed 0.9 -o announcement.mp3
```

### Low-Latency Streaming Model

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "Quick response needed." -m eleven_flash_v2_5 -o quick.mp3
```

### High Quality Output

```bash
uv run {skill_dir}/scripts/elevenlabs-text-speech.py "Premium audio quality for professional use." -f mp3_44100_192 -o premium.mp3
```

## Environment Variables

Requires `ELEVENLABS_API_KEY` to be set in `.env` file.
