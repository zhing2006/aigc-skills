# DashScope Text-to-Speech

Synthesize speech from text using Alibaba DashScope Qwen TTS over WebSocket, with system voices or custom voices (Voice Design / Voice Clone). The two current Qwen-Audio-TTS models use the `tts_v2` protocol; legacy Qwen3 realtime models remain supported for existing voices.

## Contents

- [Usage](#usage)
- [Models](#models)
- [System Voices](#system-voices)
- [Using Custom Voices](#using-custom-voices)
- [Examples](#examples)
- [Official References](#official-references)

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
| `-v`, `--voice` | Model-specific | Voice name or custom voice ID |
| `-m`, `--model` | `qwen-audio-3.0-tts-flash` | TTS model (see Models below) |
| `-f`, `--format` | `wav` | Output format: pcm/wav/mp3/opus |
| `-r`, `--sample-rate` | `24000` | Sample rate: 8000/16000/22050/24000/44100/48000 Hz |
| `-o`, `--output` | Auto | Output file path |
| `--volume` | `50` | Volume level (0-100) |
| `--speed` | `1.0` | Speech speed (0.5-2.0) |
| `--pitch` | `1.0` | Pitch adjustment (0.5-2.0) |
| `--instruction` | None | Natural-language control of emotion, dialect, or character (new models) |
| `--language-hint` | None | Target language: zh/en (WebSocket new models) |
| `--seed` | `0` | Reproducible seed, 0-65535 (new models) |
| `--bit-rate` | None | Opus bitrate, 6-510 kbps |
| `--ssml` | Off | Treat input as SSML (new models) |

## Models

| Model | Description |
| ----- | ----------- |
| `qwen-audio-3.0-tts-flash` | Current low-latency Qwen-Audio-TTS model; default voice `longanhuan_v3.6` |
| `qwen-audio-3.0-tts-plus` | Higher-quality Qwen-Audio-TTS model; default voice `longanlingxin` |
| `qwen3-tts-flash-realtime` | Legacy realtime system-voice model; default voice `Cherry` |
| `qwen3-tts-vd-realtime-2025-12-16` | Voice Design model (for designed voices) |
| `qwen3-tts-vc-realtime-2026-01-15` | Voice Clone model (latest) |
| `qwen3-tts-vc-realtime-2025-11-27` | Voice Clone model (snapshot) |

**Important**: A voice can only be used with the model family it belongs to. The two new Qwen-Audio-TTS models have separate voice lists and are not interchangeable with legacy Qwen3 voices:

- Qwen-Audio-TTS system voices: `longanhuan_v3.6` / `longjielidou_v3.6` / `loongeva_v3.6` / `loongjohn` (Flash), `longanlingxin` / `longanlufeng` (Plus)
- Qwen-Audio-TTS cloned voices: `qwen-audio-3.0-tts-flash-*` or `qwen-audio-3.0-tts-plus-*`, matching the target model used during cloning
- Voice Design voices (`qwen-tts-vd-*`) require `qwen3-tts-vd-realtime-2025-12-16`
- Legacy Voice Clone voices (`qwen-tts-vc-*`) require the corresponding `qwen3-tts-vc-realtime-*` model

The Qwen-Audio-TTS non-realtime API is separate from this script. This skill uses the WebSocket API for low-latency synthesis. Set `DASHSCOPE_TTS_WS_URL` when using a workspace-specific endpoint:

```env
DASHSCOPE_TTS_WS_URL = "wss://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference"
```

The public Beijing endpoint (`wss://dashscope.aliyuncs.com/api-ws/v1/inference`) is the default. Qwen-Audio-TTS realtime is currently documented for the Beijing region; use a Beijing API key.

### Qwen-Audio-TTS Voices

| Model | Voice | Language / character |
| ----- | ----- | -------------------- |
| Flash | `longanhuan_v3.6` | Chinese/English female |
| Flash | `longjielidou_v3.6` | Chinese/English boy |
| Flash | `loongeva_v3.6` | English female |
| Flash | `loongjohn` | English male |
| Plus | `longanlingxin` | Chinese/English female |
| Plus | `longanlufeng` | Chinese/English male |

Both models support emotion and rich-language tags directly in the text, for example `[excited]今天真开心！[laughing]`. Common tags include `[sad]`, `[angry]`, `[serious]`, `[very slowly]`, `[gasp]`, `[sighing]`, `[giggles]`, and `[cough]`.

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

### TTS with a Qwen-Audio-TTS cloned voice

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "你好，这是新版克隆音色测试" \
  -v "qwen-audio-3.0-tts-flash-your-voice-id" \
  -m "qwen-audio-3.0-tts-flash" \
  -o qwen_audio_clone.wav
```

## Examples

### Basic Chinese TTS

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "你好，欢迎使用语音合成服务" -v longanhuan_v3.6 -o hello.wav
```

### English TTS with Professional Voice

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "Welcome to our product demonstration" -m qwen3-tts-flash-realtime -v Jennifer -o welcome.mp3
```

### News Broadcast Style

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "各位观众朋友，大家好，欢迎收看晚间新闻" -m qwen3-tts-flash-realtime -v Neil -o news.mp3
```

### Audiobook with Adjusted Speed

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py -i story.txt -m qwen3-tts-flash-realtime -v Serena --speed 0.9 -o audiobook.mp3
```

### High Quality WAV Output

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py "高品质音频输出测试" -m qwen3-tts-flash-realtime -v Ethan -f wav -r 48000 -o high_quality.wav
```

### Emotion and instruction control

```bash
{python} {skill_dir}/scripts/dashscope-text-speech.py \
  "[excited]欢迎来到今天的节目！[laughing]" \
  -v longanlingxin -m qwen-audio-3.0-tts-plus \
  --instruction "温暖、亲切，像在和朋友聊天" -o expressive.wav
```

## Official References

- [Realtime TTS user guide](https://help.aliyun.com/zh/model-studio/realtime-tts-user-guide)
- [Qwen-Audio-TTS voice list](https://help.aliyun.com/zh/model-studio/qwen-audio-tts-voice-list)
- [WebSocket API reference](https://help.aliyun.com/zh/model-studio/cosyvoice-websocket-api)
