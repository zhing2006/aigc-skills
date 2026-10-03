# ElevenLabs Text-to-Speech

Text-to-Speech generation using ElevenLabs API with voice search support. Defaults to Eleven v4, with v4 Turbo available for lower latency.

## Contents

- [Usage](#usage)
- [Supported Models](#supported-models)
- [Voice Selection](#voice-selection)
- [Prompt Best Practices](#prompt-best-practices)
- [Voice Search Best Practices](#voice-search-best-practices)
- [Voice Settings](#voice-settings)
- [Examples](#examples)
- [Environment Variables](#environment-variables)
- [Official References](#official-references)

## Usage

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "text" [options]
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
| `-m`, `--model` | `eleven_v4` | Model for speech generation |
| `-f`, `--format` | `mp3_44100_128` | Output audio format |
| `--stability` | None | Voice stability (0-1) |
| `--similarity` | None | Voice similarity boost (0-1) |
| `--speed` | None | Speech speed (0.7-1.2), v3/v2 models only |
| `-o`, `--output` | `generated_speech.<ext>` | Output file path |

## Supported Models

| Model | Description |
| ----- | ----------- |
| `eleven_v4` | Highest quality, expressive speech, 90+ languages, 10K chars (default) |
| `eleven_v4_turbo` | Expressive, low-latency speech, 90+ languages, 10K chars |
| `eleven_v3` | Previous expressive model, 70+ languages, 5K chars |
| `eleven_multilingual_v2` | Natural speech, 29 languages, 10K chars |
| `eleven_flash_v2_5` | Ultra-low latency ~75ms, 32 languages, 40K chars |

**Default**: If the user does not specify a model, use `eleven_v4`. Existing workflows can explicitly select `-m eleven_multilingual_v2`, `-m eleven_v3`, or `-m eleven_flash_v2_5`.

Empty text and text above the selected model's character limit are rejected before calling the API. Split longer text into shorter requests; the script does not automatically chunk it.

**V4 migration**: V4 models accept stability and similarity settings, but do not support speed, style, or SSML. The script rejects `--speed` with either v4 model; choose a v3/v2 model if numeric speed control is required. This command generates one voice per request and saves the audio to a file.

## Voice Selection

### Using Voice ID

Provide a voice ID directly with `-v`:

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "Hello" -v JBFqnCBsd6RMkjVDRZzb
```

### Using Voice Search

Search for a voice by description with `-s`:

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "Hello" -s "British male"
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "Hello" -s "female narrator calm"
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

## Prompt Best Practices

The official guide now focuses on [Prompting Eleven v4](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices#prompting-eleven-v4); its v3 section refers to the same techniques.

### Preparing Supplied Dialogue

Keep supplied words and meaning, including laughter and narration. Add context-appropriate auditory tags beside the relevant phrase; do not move narration into brackets. Avoid visual directions.

Original:

```text
哈哈，原来你也在这里！
```

Enhanced:

```text
[laughs] 哈哈，原来你也在这里！
```

Do not delete onomatopoeia when adding tags; removing words requires a rewriting request.

### Audio Tags (Eleven v4 / v4 Turbo / v3)

Eleven v4, v4 Turbo, and v3 support bracketed audio tags for emotional and tonal control. Embed tags directly in the text; v4 is the recommended default.

Treat the following tags as examples, not an API enum or guaranteed effects. Accent and character cues are experimental.

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

**Accent Tags (Experimental):**

| Tag | Effect |
| --- | ------ |
| `[British accent]` | British English accent |
| `[Australian accent]` | Australian accent |
| `[Southern US accent]` | Southern American accent |
| `[strong X accent]` | Emphasized accent (replace X) |

**Character Tags (Exploratory Prompt Examples):**

| Tag | Effect |
| --- | ------ |
| `[pirate voice]` | Pirate character |
| `[evil scientist voice]` | Villain archetype |
| `[childlike tone]` | Young, innocent |

### Vocal Delivery and Sound Effects

Use explicit voice descriptions to avoid confusing delivery with sound effects. Optional environmental cues such as `[applause]` belong in sound-design requests; do not add them during ordinary dialogue enhancement.

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

These cues do not specify exact pause durations. V4 and v3 do not support SSML `<break>` tags.

### Tag Layering

Tags can be combined for nuanced delivery:

```text
[nervously] [whispers] Do you think they heard us?

[excited] [British accent] Brilliant! Absolutely brilliant!
```

### Pronunciation and Normalization

V4 supports inline `/IPA/` for selected difficult words; include stress marks. Results vary by voice.

```text
Please say /həˈləʊ/ after the tone.
```

Normalize numbers, dates and abbreviations only when preparing a spoken adaptation; clarify ambiguous locale or currency. Keep verbatim scripts unchanged.

The script forwards `text` unchanged. It has no normalization switch or pronunciation-dictionary option; prepare any authorized spoken adaptation before calling it. Inline IPA is documented for `eleven_v4`; do not assume it works identically on the other model choices.

### Voice and Speaker Selection

Choose a voice suited to the intended delivery. Tags can guide a voice beyond its usual style, but results still depend on the voice.

The current script sends one `voice_id` per Text-to-Speech request. Writing `Speaker 1:` and `Speaker 2:` in `text` does not assign separate voices and may be read aloud. ElevenLabs offers a separate [Text to Dialogue API](https://elevenlabs.io/docs/overview/capabilities/text-to-dialogue) for multiple voices; this script does not expose it. Do not present the official multi-speaker examples as commands supported by this script.

### Validation and Paid Calls

For documentation or code maintenance, use local checks or mocked requests. Do not spend API credits on samples, comparisons, or retries without explicit user authorization covering that work. A request to update the integration is not a request to synthesize audio. When generation is authorized, stay within the requested scope and provide links to every output for listening.

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

For v3 only, other values are automatically adjusted to the nearest valid value. V4 models accept values throughout the 0-1 range without this adjustment.

### Similarity (0-1)

Controls adherence to original voice characteristics:

- **High (0.7-1.0)**: Closer to original voice
- **Low (0.0-0.3)**: More variation allowed

### Speed (0.7-1.2)

Available for `eleven_v3`, `eleven_multilingual_v2`, and `eleven_flash_v2_5` only. V4 models reject `--speed`, including `--speed 1.0`; use audio tags and punctuation to guide pacing instead.

Controls speech velocity on the supported models:

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
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "Hello, welcome to our application." -o welcome.mp3
```

### TTS with Voice Search

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "The weather today is sunny with a high of 75 degrees." -s "British male news" -o weather.mp3
```

### TTS with Specific Voice ID

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "Once upon a time in a distant land..." -v XrExE9yKIg1WjnnlVkGX -o story.mp3
```

### TTS with Custom Voice Settings

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "This is a very important announcement." --stability 0.8 --similarity 0.9 -o announcement.mp3
```

### Emotional Speech with V4

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "[excited] We did it! [laughs] I can hardly believe it." -m eleven_v4 -o excited.mp3
```

### Low-Latency V4 Turbo

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "[cheerfully] How can I help you today?" -m eleven_v4_turbo -o quick.mp3
```

### Legacy Model with Numeric Speed Control

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "This is a very important announcement." -m eleven_multilingual_v2 --speed 0.9 -o slower.mp3
```

### Flash Model

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "Quick response needed." -m eleven_flash_v2_5 -o quick.mp3
```

### High Quality Output

```bash
{python} {skill_dir}/scripts/elevenlabs-text-speech.py "Premium audio quality for professional use." -f mp3_44100_192 -o premium.mp3
```

## Environment Variables

Requires `ELEVENLABS_API_KEY`. The CLI loads `.genix.env` from the current working directory, or uses the process environment.

## Official References

Verified on 2026-10-03. Both v4 models were also checked through `GET /v1/models` and short generations through the existing Text-to-Speech endpoint.

- [Eleven v4 release announcement (2026-09-28)](https://elevenlabs.io/blog/eleven-v4)
- [V4 model settings and migration behavior](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4)
- [Models and character limits](https://elevenlabs.io/docs/overview/models)
- [Text-to-Speech API](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
- [Prompting Eleven v4](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices#prompting-eleven-v4)
- [Prompting Eleven v3](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices#prompting-eleven-v3)
- [Audio tag model support](https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-do-audio-tags-work-with-eleven-v3-and-v4)
