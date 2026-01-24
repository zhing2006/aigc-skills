# DashScope Text-to-Speech

Synthesize speech from text using Alibaba DashScope Qwen TTS with system voices or custom voices (Voice Design / Voice Clone).

## Usage

```bash
# Synthesize text to speech
{python} {skill_dir}/scripts/dashscope-text-speech.py "text to speak" [options]

# Synthesize from text file
{python} {skill_dir}/scripts/dashscope-text-speech.py -i input.txt [options]
```

## Arguments

| Argument | Required | Description |
| -------- | -------- | ----------- |
| `text` | Yes* | Text to synthesize (*or use `-i` for file input) |
| `-i`, `--input` | No | Path to text file to synthesize |

## Options

| Option | Default | Description |
| ------ | ------- | ----------- |
| `-v`, `--voice` | `Cherry` | Voice name or custom voice ID |
| `-m`, `--model` | `qwen3-tts-flash-realtime` | TTS model (see Models below) |
| `-f`, `--format` | `mp3` | Output format: pcm/wav/mp3/opus |
| `-r`, `--sample-rate` | `24000` | Sample rate: 8000/16000/22050/24000/44100/48000 Hz |
| `-o`, `--output` | Auto | Output file path |
| `--volume` | `50` | Volume level (0-100) |
| `--speed` | `1.0` | Speech speed (0.5-2.0) |
| `--pitch` | `1.0` | Pitch adjustment (0.5-2.0) |

## Models

| Model | Description |
| ----- | ----------- |
| `qwen3-tts-flash-realtime` | Default model for system voices |
| `qwen3-tts-vd-realtime-2025-12-16` | Voice Design model (for designed voices) |
| `qwen3-tts-vc-realtime-2026-01-15` | Voice Clone model (latest) |
| `qwen3-tts-vc-realtime-2025-11-27` | Voice Clone model (snapshot) |

**Important**: Custom voices must use their corresponding model:

- Voice Design voices (`qwen-tts-vd-*`) require `qwen3-tts-vd-realtime-2025-12-16`
- Voice Clone voices (`qwen-tts-vc-*`) require `qwen3-tts-vc-realtime-2026-01-15`

## System Voices

### Chinese Female Voices

| Voice | Name | Description |
| ----- | ---- | ----------- |
| `Cherry` | 芊悦 | Sunny, friendly young woman |
| `Serena` | 苏瑶 | Gentle young woman |
| `Chelsie` | 千雪 | Anime-style virtual girlfriend |
| `Momo` | 茉兔 | Playful, cute |
| `Vivian` | 十三 | Cool, slightly rebellious |
| `Maia` | 四月 | Intellectual and warm |
| `Bella` | 萌宝 | Cute little girl |
| `Mia` | 乖小妹 | Sweet and obedient |
| `Bunny` | 萌小姬 | Cute loli |
| `Nini` | 邻家妹妹 | Sweet neighbor girl |
| `Stella` | 少女阿月 | Sweet magical girl |
| `Seren` | 小婉 | Soothing, for sleep |

### Chinese Male Voices

| Voice | Name | Description |
| ----- | ---- | ----------- |
| `Ethan` | 晨煦 | Sunny, warm young man |
| `Moon` | 月白 | Cool and handsome |
| `Kai` | 凯 | Relaxing, magnetic |
| `Nofish` | 不吃鱼 | Designer with unique accent |
| `Mochi` | 沙小弥 | Smart young boy |
| `Vincent` | 田叔 | Husky, storytelling |
| `Neil` | 阿闻 | Professional news anchor |
| `Arthur` | 徐大爷 | Elderly storyteller |
| `Pip` | 顽屁小孩 | Mischievous child |
| `Eldric Sage` | 沧明子 | Wise elder |

### English Voices

| Voice | Name | Description |
| ----- | ---- | ----------- |
| `Jennifer` | 詹妮弗 | Professional female, brand-quality |
| `Ryan` | 甜茶 | Expressive male, dramatic |
| `Katerina` | 卡捷琳娜 | Mature female |
| `Aiden` | 艾登 | Friendly young male |
| `Elias` | 墨讲师 | Educational female narrator |

### Dialect Voices

| Voice | Name | Dialect |
| ----- | ---- | ------- |
| `Jada` | 阿珍 | Shanghai |
| `Dylan` | 晓东 | Beijing |
| `Li` | 老李 | Nanjing |
| `Marcus` | 秦川 | Shaanxi |
| `Roy` | 阿杰 | Hokkien/Taiwanese |
| `Peter` | 李彼得 | Tianjin |
| `Sunny` | 晴儿 | Sichuan (female) |
| `Eric` | 程川 | Sichuan (male) |
| `Rocky` | 阿强 | Cantonese (male) |
| `Kiki` | 阿清 | Cantonese (female) |

### International Voices

| Voice | Name | Language/Region |
| ----- | ---- | --------------- |
| `Bodega` | 博德加 | Spanish (male) |
| `Sonrisa` | 索尼莎 | Spanish (female) |
| `Alek` | 阿列克 | Russian |
| `Dolce` | 多尔切 | Italian |
| `Sohee` | 素熙 | Korean |
| `Ono Anna` | 小野杏 | Japanese |
| `Lenn` | 莱恩 | German |
| `Emilien` | 埃米尔安 | French |
| `Andre` | 安德雷 | Portuguese |

## Using Custom Voices

Custom voices created with Voice Design or Voice Clone can be used by specifying the voice ID and corresponding model.

### List Custom Voices

```bash
# List Voice Design voices
{python} {skill_dir}/scripts/dashscope-voice-design.py list

# List Voice Clone voices
{python} {skill_dir}/scripts/dashscope-voice-clone.py list
```

### TTS with Voice Design Voice

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "你好，这是自定义音色测试" \
  -v "qwen-tts-vd-your-voice-id" \
  -m "qwen3-tts-vd-realtime-2025-12-16" \
  -o custom_voice.wav
```

### TTS with Voice Clone Voice

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "你好，这是克隆音色测试" \
  -v "qwen-tts-vc-your-voice-id" \
  -m "qwen3-tts-vc-realtime-2026-01-15" \
  -o cloned_voice.wav
```

## Examples

### Basic Chinese TTS

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "你好，欢迎使用语音合成服务" -v Cherry -o hello.mp3
```

### English TTS with Professional Voice

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "Welcome to our product demonstration" -v Jennifer -o welcome.mp3
```

### News Broadcast Style

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "各位观众朋友，大家好，欢迎收看晚间新闻" -v Neil -o news.mp3
```

### Audiobook with Adjusted Speed

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py -i story.txt -v Serena --speed 0.9 -o audiobook.mp3
```

### High Quality WAV Output

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "高品质音频输出测试" -v Ethan -f wav -r 48000 -o high_quality.wav
```
