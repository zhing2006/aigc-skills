# ElevenLabs Sound Effects

Text-to-Sound Effect generation using ElevenLabs API.

## Usage

```bash
uv run {skill_dir}/scripts/elevenlabs-sound-effect.py "prompt" [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `prompt` | Yes | Text description of the sound effect |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-m`, `--model` | `eleven_text_to_sound_v2` | Model for sound generation |
| `-d`, `--duration` | auto | Duration in seconds (0.5-30) |
| `-p`, `--prompt-influence` | `0.3` | How closely to follow the prompt (0-1) |
| `-l`, `--loop` | false | Create seamless looping sound (v2 only) |
| `-f`, `--format` | `mp3_44100_128` | Output audio format |
| `-o`, `--output` | `generated_sound.<ext>` | Output file path |

## Supported Models

| Model | Description |
| ----- | ----------- |
| `eleven_text_to_sound_v2` | Latest model with loop support (default) |
| `eleven_text_to_sound_v1` | Original model |

**Note**: If the user does not specify model, use `eleven_text_to_sound_v2` as default.

## Supported Output Formats

**MP3**: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`

**PCM**: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`

**Opus**: `opus_48000_64`, `opus_48000_128`

**Note**: If the user does not specify format, use `mp3_44100_128` as default.

## Duration

- Range: 0.5 to 30 seconds
- If not specified, duration is automatically determined from the prompt
- Cost: 40 credits per second when manually specified

## Prompt Influence

Controls how closely the output follows the prompt:

- **High (0.7-1.0)**: More literal interpretation of the prompt
- **Medium (0.3-0.5)**: Balanced approach (default: 0.3)
- **Low (0.0-0.2)**: More creative variation with added spontaneity

## Prompt Best Practices

### Simple Effects

Use clear, direct descriptions:

- `"Glass shattering on concrete"`
- `"Heavy wooden door creaking open"`
- `"Dog barking twice"`
- `"Thunder rumbling in the distance"`

### Complex Sequences

Describe multi-step events:

- `"Footsteps on gravel, then a metallic door opens"`
- `"Car engine starting, revving, then driving away"`
- `"Phone ringing three times, then someone picks up"`

### Musical Elements

The API supports musical sounds with tempo/key specifications:

- `"Drum loop, 120 BPM, electronic style"`
- `"Synth pad, ambient, C major chord"`
- `"Brass stab, cinematic, dramatic"`

### Audio Terminology

Use these terms to enhance your prompts:

| Term | Description |
| ---- | ----------- |
| Impact | Collision and hit sounds |
| Whoosh | Movement and swoosh sounds |
| Ambience | Environmental atmospheric textures |
| One-shot | Single, non-repeating sound |
| Loop | Repeating segment |
| Braam | Cinematic impact hit for dramatic moments |
| Glitch | Malfunction sounds for transitions |
| Drone | Continuous atmospheric texture |
| Foley | Everyday sound effects (footsteps, cloth rustling) |
| Riser | Sound that builds in intensity |
| Stinger | Short dramatic accent |

## Examples

### Basic Sound Effect

```bash
uv run {skill_dir}/scripts/elevenlabs-sound-effect.py "Dog barking happily" -o dog_bark.mp3
```

### Cinematic Impact

```bash
uv run {skill_dir}/scripts/elevenlabs-sound-effect.py "Cinematic braam, deep bass impact with reverb tail" -d 3 -p 0.7 -o braam.mp3
```

### Ambient Loop

```bash
uv run {skill_dir}/scripts/elevenlabs-sound-effect.py "Gentle rain on window with distant thunder" -d 10 -l -o rain_ambient.mp3
```

### Game Sound Effect

```bash
uv run {skill_dir}/scripts/elevenlabs-sound-effect.py "8-bit coin pickup sound, retro game style" -d 0.5 -p 0.8 -o coin.mp3
```

### High Quality Output

```bash
uv run {skill_dir}/scripts/elevenlabs-sound-effect.py "Spaceship engine humming with electronic beeps" -f mp3_44100_192 -d 5 -o spaceship.mp3
```

### Horror Atmosphere

```bash
uv run {skill_dir}/scripts/elevenlabs-sound-effect.py "Creepy whispers in an abandoned hallway, eerie and unsettling" -d 8 -p 0.5 -o horror_whispers.mp3
```

## Environment Variables

Requires `ELEVENLABS_API_KEY` to be set in `.env` file.
