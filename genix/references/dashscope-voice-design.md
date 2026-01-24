# DashScope Voice Design

Create custom AI voices using natural language descriptions via Alibaba DashScope Qwen Voice Design API.

## Usage

```bash
# Create a new custom voice
{python} {skill_dir}/scripts/dashscope-voice-design.py create "voice_prompt" -t "preview_text" [options]

# List all custom voices
{python} {skill_dir}/scripts/dashscope-voice-design.py list [options]

# Query details of a specific voice
{python} {skill_dir}/scripts/dashscope-voice-design.py query <voice_name>

# Delete a specific voice
{python} {skill_dir}/scripts/dashscope-voice-design.py delete <voice_name>
```

## Create Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `voice_prompt` | Yes | Description of the desired voice (max 2048 chars, Chinese/English only) |
| `-t`, `--preview-text` | Yes | Text to preview the voice (max 1024 chars) |

## Create Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-n`, `--name` | Auto | Preferred name identifier (max 16 chars, alphanumeric/underscore) |
| `-l`, `--language` | `zh` | Voice language: zh/en/de/it/pt/es/ja/ko/fr/ru |
| `-r`, `--sample-rate` | `24000` | Sample rate: 8000/16000/24000/48000 Hz |
| `-f`, `--format` | `wav` | Audio format: mp3/wav/pcm/opus |
| `-o`, `--output` | Auto | Output file path for preview audio |
| `--target-model` | `qwen3-tts-vd-realtime-2025-12-16` | Target TTS model |

## List Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--page-index` | `0` | Page index (0-based) |
| `--page-size` | `10` | Number of items per page |

## Voice Prompt Best Practices

### Core Principles

1. **Specific, not vague**: Use concrete descriptors like "low-pitched", "crisp", "moderate speed". Avoid subjective words like "nice" or "good"
2. **Multi-dimensional**: Combine multiple dimensions (gender, age, emotion, etc.) for distinctive voices
3. **Objective**: Focus on physical and perceptual characteristics, not personal preferences
4. **Original**: Describe voice qualities, don't request imitation of celebrities
5. **Concise**: Every word should add meaning, avoid redundant emphasis

### Description Dimensions

| Dimension | Examples |
| --------- | -------- |
| Gender | male, female, neutral |
| Age | child (5-12), teenager (13-18), young adult (19-35), middle-aged (36-55), elderly (55+) |
| Pitch | high, medium, low |
| Speed | fast, medium, slow |
| Emotion | cheerful, calm, gentle, serious, lively, soothing |
| Characteristics | magnetic, crisp, raspy, mellow, sweet, deep, powerful |
| Use Case | news broadcast, advertising, audiobook, animation, voice assistant, documentary |

### Effective Chinese Prompts

| Goal | Voice Prompt |
| ---- | ------------ |
| Professional news anchor | `"沉稳的中年男性播音员，音色低沉浑厚，富有磁性，语速平稳，吐字清晰，适合用于新闻播报或纪录片解说"` |
| Sweet young female | `"温柔甜美的年轻女性声音，语速适中，适合情感类内容"` |
| Lively child | `"活泼可爱的儿童声音，大约8岁女孩，说话略带稚气，适合动画角色配音"` |
| Professional customer service | `"友好专业的女性客服声音，温暖亲切，语速适中"` |
| Audiobook narrator | `"温柔知性的女性，30岁左右，语调平和，适合有声书朗读"` |

### Effective English Prompts

| Goal | Voice Prompt |
| ---- | ------------ |
| Professional narrator | `"A professional female narrator with a warm, clear voice suitable for audiobooks and podcasts"` |
| News anchor | `"Mature, authoritative male voice with clear articulation, news anchor style"` |
| Documentary | `"A deep male voice with resonance, suitable for documentary narration"` |

### What to Avoid

- Vague descriptions like "好听的声音" or "nice voice"
- Celebrity imitation requests
- Redundant emphasis like "非常非常好听"

## Examples

### Create a Professional Narrator Voice

```bash
{python} {skill_dir}/scripts/dashscope-voice-design.py create "沉稳的中年男性播音员，音色低沉浑厚，富有磁性，语速平稳，吐字清晰，适合用于新闻播报或纪录片解说" -t "各位听众朋友，大家好，欢迎收听晚间新闻" -n announcer -o narrator_preview.wav
```

### Create an English Female Voice

```bash
{python} {skill_dir}/scripts/dashscope-voice-design.py create "A professional female narrator with a warm, clear voice suitable for audiobooks" -t "Welcome to our podcast. Today we will discuss..." -l en -o narrator_en.mp3 -f mp3
```

### Create a Japanese Anime Voice

```bash
{python} {skill_dir}/scripts/dashscope-voice-design.py create "元気で可愛らしい若い女性の声、アニメキャラクターに適した声" -t "こんにちは、お元気ですか" -l ja -n anime_girl -o anime_preview.wav
```
