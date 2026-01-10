# ElevenLabs Music

Text-to-Music generation using ElevenLabs Music API.

## Usage

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text description of the music to generate |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-m`, `--model` | `music_v1` | Model for music generation |
| `-d`, `--duration` | `30` | Duration in seconds (10-300) |
| `-i`, `--instrumental` | false | Force instrumental (no vocals) |
| `-f`, `--format` | `mp3_44100_128` | Output audio format |
| `-o`, `--output` | `generated_music.<ext>` | Output file path |

## Supported Models

| Model | Description |
| ----- | ----------- |
| `music_v1` | Current music generation model (default) |

**Note**: If the user does not specify model, use `music_v1` as default.

## Supported Output Formats

**MP3**: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`

**PCM**: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`

**Opus**: `opus_48000_64`, `opus_48000_128`, `opus_48000_192`

**Note**: If the user does not specify format, use `mp3_44100_128` as default.

## Duration

- Range: 10 to 300 seconds (10s - 5 minutes)
- Default: 30 seconds
- Longer tracks consume more credits

## Prompt Best Practices

### Basic Structure

A good music prompt includes:

```txt
[Genre/Style] + [Mood/Emotion] + [Instruments] + [Tempo/Energy] + [Additional Details]
```

### Genres and Styles

| Category | Examples |
| -------- | -------- |
| Electronic | EDM, house, techno, ambient, synthwave, lo-fi |
| Rock | rock, metal, punk, alternative, indie rock |
| Classical | orchestral, piano, chamber music, symphony |
| Jazz | jazz, smooth jazz, bebop, swing |
| Pop | pop, dance pop, synth pop, indie pop |
| Hip-Hop | hip-hop, trap, boom bap, R&B |
| World | latin, bossa nova, african, asian, celtic |
| Cinematic | epic, trailer music, film score, dramatic |

### Mood and Emotion

| Mood | Descriptors |
| ---- | ----------- |
| Happy | upbeat, cheerful, joyful, playful, bright |
| Sad | melancholic, somber, emotional, nostalgic |
| Energetic | intense, powerful, driving, dynamic |
| Calm | peaceful, relaxing, serene, gentle, ambient |
| Dark | ominous, mysterious, tense, suspenseful |
| Epic | heroic, triumphant, majestic, grand |

### Instruments

Specify instruments for more control:

- **Piano**: piano, grand piano, electric piano
- **Guitar**: acoustic guitar, electric guitar, bass guitar
- **Strings**: violin, cello, string section, orchestra
- **Synth**: synthesizer, pads, arpeggios, leads
- **Drums**: drums, percussion, electronic drums, beats
- **Brass**: trumpet, saxophone, horn section
- **Vocals**: male vocals, female vocals, choir

### Tempo and Energy

| Term | Description |
| ---- | ----------- |
| Slow | ballad, ambient, downtempo |
| Medium | moderate, mid-tempo, groovy |
| Fast | upbeat, energetic, high-tempo |
| Building | crescendo, rising, intensifying |
| Dynamic | varies throughout, changing energy |

### Song Structure

You can describe the structure:

- `"Starts soft, builds to a powerful chorus"`
- `"Intro with piano, then full band kicks in"`
- `"Verse-chorus structure with a bridge"`

## Examples

### Calm Piano

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Calm piano melody, ambient and relaxing, soft and gentle, suitable for meditation" -d 60 -i -o calm_piano.mp3
```

### Epic Orchestral

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Epic orchestral theme, heroic and triumphant, full orchestra with brass and strings, cinematic trailer style" -d 30 -i -o epic_theme.mp3
```

### Electronic Dance

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Energetic EDM track, driving beats, synth leads, festival-ready drop, high energy" -d 45 -i -o edm_track.mp3
```

### Lo-fi Hip-Hop

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Lo-fi hip-hop beat, relaxing and chill, vinyl crackle, mellow piano chords, perfect for studying" -d 60 -i -o lofi_study.mp3
```

### Pop with Vocals

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Upbeat pop song about summer love, catchy melody, female vocals, bright and cheerful" -d 90 -o summer_pop.mp3
```

### Cinematic Tension

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Dark cinematic music, suspenseful and tense, deep strings, ominous atmosphere, thriller movie style" -d 30 -i -o tension.mp3
```

### Jazz Background

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Smooth jazz, saxophone lead, walking bass, brushed drums, elegant and sophisticated, cafe ambiance" -d 120 -i -o jazz_cafe.mp3
```

### High Quality Output

```bash
uv run {skill_dir}/scripts/elevenlabs-music.py "Acoustic guitar ballad, emotional and heartfelt, gentle fingerpicking" -d 60 -i -f mp3_44100_192 -o ballad_hq.mp3
```

## Environment Variables

Requires `ELEVENLABS_API_KEY` to be set in `.env` file.

## Notes

- Music generation is only available for paid ElevenLabs accounts
- Commercial use may require additional licensing for advertising, film, TV, and games
- Use `-i` (instrumental) flag when you want music without AI-generated vocals
