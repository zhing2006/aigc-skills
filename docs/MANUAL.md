# Genix Skills User Manual

[English](MANUAL.md) | [中文](MANUAL_CN.md)

This manual provides detailed instructions for installing and using the Genix AIGC Skills package.

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Download Package](#download-package)
  - [Run Install Script](#run-install-script)
  - [Configure API Keys](#configure-api-keys)
- [Upgrading from v0.1](#upgrading-from-v01)
- [Skills Overview](#skills-overview)
- [Image Generation](#image-generation)
  - [Google Gemini (Nano Banana Pro)](#google-gemini-nano-banana-pro)
  - [OpenAI GPT Image](#openai-gpt-image)
  - [Volcengine Seedream](#volcengine-seedream)
  - [DashScope Qwen Image 3.0](#dashscope-qwen-image-30)
- [Video Generation](#video-generation)
  - [Volcengine Seedance](#volcengine-seedance)
  - [MiniMax Hailuo](#minimax-hailuo)
  - [DashScope HappyHorse](#dashscope-happyhorse)
  - [Google Veo](#google-veo)
  - [OpenAI Sora](#openai-sora)
- [Audio Generation](#audio-generation)
  - [ElevenLabs Sound Effects](#elevenlabs-sound-effects)
  - [ElevenLabs Text-to-Speech](#elevenlabs-text-to-speech)
  - [DashScope Text-to-Speech](#dashscope-text-to-speech)
  - [DashScope Voice Design](#dashscope-voice-design)
  - [DashScope Voice Clone](#dashscope-voice-clone)
  - [Volcengine Text-to-Speech](#volcengine-text-to-speech)
  - [Volcengine Voice Design](#volcengine-voice-design)
  - [Volcengine Voice Clone](#volcengine-voice-clone)
- [Music Generation](#music-generation)
  - [ElevenLabs Music](#elevenlabs-music)
  - [Google Lyria Music](#google-lyria-music)
- [3D Model Generation](#3d-model-generation)
  - [Tripo 3D](#tripo-3d)
- [Advanced Workflows](#advanced-workflows)
  - [Text to Image to Video Pipeline](#text-to-image-to-video-pipeline)
  - [Image Editing to Video Pipeline](#image-editing-to-video-pipeline)
  - [Multi-Asset Production](#multi-asset-production)

---

## Installation

### Prerequisites

- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Internet Connection**: Required for downloading dependencies and API calls
- **API Keys**: At least one API key from a supported provider (Google, OpenAI, ElevenLabs, DashScope, Volcengine, MiniMax, or Tripo)

### Download Package

1. Download `genix-skills.zip` from the release page
2. Extract the zip file to your **project root directory** (where you want to use the skills)

After extraction, your directory structure should look like:

```txt
your-project/
├── genix/                  # Skills folder (will be moved during install)
├── .env.template           # API key template
├── install.ps1             # Windows PowerShell installer
├── install.bat             # Windows CMD installer
└── install.sh              # Linux/macOS installer
```

### Run Install Script

Choose the appropriate script for your system:

#### Windows (PowerShell) - Recommended

```powershell
.\install.ps1
```

To install for a specific AI tool:

```powershell
.\install.ps1 -Tool cursor    # For Cursor editor
.\install.ps1 -Tool claude    # For Claude Code (default)
.\install.ps1 -Tool codex     # For Codex CLI
.\install.ps1 -Tool opencode  # For OpenCode
.\install.ps1 -Tool vscode    # For VS Code with Claude extension
```

#### Windows (Command Prompt)

```cmd
install.bat
install.bat cursor    # For specific tool
```

#### Linux / macOS

```bash
chmod +x install.sh   # First time only
./install.sh
./install.sh cursor   # For specific tool
```

#### What the Install Script Does

1. **Checks/Installs uv**: The `uv` package manager (by Astral) for fast Python dependency management
2. **Creates Virtual Environment**: Isolated Python environment in `.venv-genix/` (separate from your project's `.venv`)
3. **Creates .env File**: Copies `.env.template` to `.env` for API key configuration
4. **Installs Dependencies**: All required Python packages into `.venv-genix/`
5. **Moves Genix Skill**: Moves `genix/` folder to the AI tool's skills directory

After installation:

- Skills location: `.claude/skills/genix/`, `.cursor/skills/genix/`, or `.codex/skills/genix/`
- Python environment: `.venv-genix/` (does not conflict with existing `.venv`)
- Environment file: `.genix.env` (API keys configuration)

### Configure API Keys

Edit the `.genix.env` file in your project root with your API keys:

```env
# Google API (for Gemini image and Veo video)
USE_VERTEX_AI = "false"
GOOGLE_CLOUD_API_KEY = "your_google_api_key_here"

# ElevenLabs API (for audio, speech, music)
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"

# OpenAI API (for GPT image and Sora video)
USE_AZURE_OPENAI = "false"
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_API_BASE = "https://api.openai.com/v1"

# Tripo API (for 3D model generation)
TRIPO_API_KEY = "your_tripo_api_key_here"

# DashScope API (for Qwen Image, Qwen-Audio-TTS, Voice Design, Voice Clone)
DASHSCOPE_API_KEY = "your_dashscope_api_key_here"
DASHSCOPE_IMAGE_BASE_URL = "https://dashscope.aliyuncs.com"  # Optional; workspace domain recommended
DASHSCOPE_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"  # Optional; Qwen-Audio-TTS WebSocket

# Volcengine API (for Seedance video and Doubao speech)
VOLCENGINE_API_KEY = "your_volcengine_api_key_here"               # Video generation
VOLCENGINE_TTS_API_KEY = "your_volcengine_tts_api_key_here"       # Speech (TTS/clone/design)
VOLCENGINE_TTS_APPID = "your_volcengine_tts_appid_here"           # Voice management only
VOLCENGINE_ACCESS_KEY = "your_volcengine_access_key_here"         # Voice management only
VOLCENGINE_SECRET_KEY = "your_volcengine_secret_key_here"         # Voice management only

# MiniMax API (for Hailuo video)
MINIMAX_API_KEY = "your_minimax_api_key_here"
MINIMAX_API_BASE = "https://api.minimaxi.com"                     # Optional
```

**Note**: You only need to configure the API keys for the providers you plan to use.

---

## Upgrading from v0.1

If you are upgrading from Genix Skills v0.1, please note the following **breaking changes**:

### Environment File Renamed

The environment file has been renamed from `.env` to `.genix.env` to avoid conflicts with your project's own `.env` file.

**Migration Steps:**

1. Rename your existing `.env` file to `.genix.env`:

   ```bash
   # Windows PowerShell
   Rename-Item .env .genix.env

   # Linux/macOS
   mv .env .genix.env
   ```

2. Add the new Tripo API key (if you want to use 3D generation):

   ```env
   TRIPO_API_KEY = "your_tripo_api_key_here"
   ```

3. Re-run the install script to update the skill files:

   ```powershell
   .\install.ps1
   ```

### New Features in v0.2

- **3D Model Generation**: Text-to-3D, Image-to-3D, and Multiview-to-3D using Tripo API
- **Isolated Environment**: Uses `.venv-genix` to avoid conflicts with project's `.venv`

### New Features in v0.4.2

- **Volcengine Speech**: Streaming TTS (Doubao Seed-TTS 2.0 with voice instructions & dialects), Voice Design, Voice Clone, and voice instance management
- **New Environment Variables**: `VOLCENGINE_TTS_API_KEY`, plus `VOLCENGINE_TTS_APPID` / `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` for voice management

### New Features in v0.4.3

- **Volcengine Seedream**: Image generation with Doubao Seedream 5.0 pro / 5.0 lite / 4.5 / 4.0 — Text-to-Image, Image-to-Image, Multi-Image Fusion, Group Generation, and web search (reuses `VOLCENGINE_API_KEY`)

### New Features in v0.6

- **MiniMax Hailuo Video**: 2K video generation with native synchronized audio using `MiniMax-H3` — Text-to-Video, Image-to-Video (first frame, last frame, or both), and Multi-modal Reference with voice transfer from reference audio. Durations are any integer from 4 to 15 seconds
- **New Environment Variables**: `MINIMAX_API_KEY`, plus optional `MINIMAX_API_BASE`
- **Documentation**: The DashScope HappyHorse video skill (shipped earlier) is now documented in this manual

---

## Skills Overview

| Skill | Provider | Input | Output | Use Case |
| ----- | -------- | ----- | ------ | -------- |
| Nano Banana | Google | Text, Images | Image | High-quality image generation, style transfer, Image Search grounding |
| GPT Image | OpenAI | Text, Images | Image | Image generation, editing, transparent backgrounds |
| Seedream | Volcengine | Text, Images | Image | Chinese/English text rendering, multi-image fusion, group generation |
| Qwen Image 3.0 | DashScope | Text, 1-3 Images | Image | Text rendering, precise editing, multi-image fusion (invite-only) |
| Seedance | Volcengine | Text, Image, Video, Audio | Video | Multi-modal video generation with audio (default) |
| Hailuo | MiniMax | Text, Image, Video, Audio | Video | 2K video with native audio, voice transfer from reference audio |
| HappyHorse | DashScope | Text, Image, Video | Video | Physically realistic motion, reference-to-video, video editing |
| Veo | Google | Text, Image | Video | Video generation with audio |
| Sora | OpenAI | Text, Image | Video | Cinematic video generation |
| Sound Effects | ElevenLabs | Text | Audio | Sound effects, ambient sounds |
| Text-to-Speech | ElevenLabs | Text | Audio | Voice narration, dialogue |
| Text-to-Speech | DashScope | Text | Audio | Chinese/multilingual TTS, custom voices |
| Voice Design | DashScope | Text | Voice | AI-designed custom voices |
| Voice Clone | DashScope | Audio | Voice | Clone voices from audio samples |
| Text-to-Speech | Volcengine | Text | Audio | Streaming TTS with voice instructions, dialects, cloned voices |
| Voice Design | Volcengine | Text, Image | Voice | Design voices from text descriptions or images |
| Voice Clone | Volcengine | Audio | Voice | Clone voices, manage/renew voice instances |
| Music | ElevenLabs | Text | Audio | Background music, songs |
| Lyria Music | Google | Text, Images | Audio | Full songs, clips, custom lyrics |
| Tripo 3D | Tripo | Text, Images, 3D Models | 3D Model | 3D model generation, model import, rigging & animation, segmentation, completion (GLB, FBX, OBJ) |

---

## How It Works

When you make a generation request, the AI assistant will:

1. **Select the appropriate skill** based on your request (image, video, audio, or music)
2. **Optimize your prompt** following best practices for that specific API (adding cinematography terms, lighting descriptions, style modifiers, etc.)
3. **Generate the content** using the selected skill with optimized parameters
4. **Report the result** with the output file location

You can provide simple, natural language requests - the AI will automatically enhance your prompt for best results.

---

## Image Generation

### Google Gemini (Nano Banana)

Best for: High-resolution images, style transfer, character consistency, Image Search grounding

#### Basic Text-to-Image

Ask your AI assistant:
> "Generate a photorealistic image of a cat wearing a wizard hat in a magical library"

#### With Specific Parameters

> "Create a 16:9 landscape image of a cyberpunk city at night, 4K resolution"

#### Image-to-Image (Style Transfer)

> "Transform this photo into Studio Ghibli anime style, keep the composition the same"
> (attach your image)

#### Character Consistency

> "Using these reference images, create the same character now sitting in a coffee shop"
> (attach 3-5 reference images)

#### Image Search Grounding (Nano Banana 2)

> "Generate a photorealistic image of the Sydney Opera House at golden hour, use image search for accurate architecture"

**Supported Options**:

- Models: `gemini-3.1-flash-image-preview` (default, Nano Banana 2), `gemini-3-pro-image-preview` (Pro)
- Aspect Ratios: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`, plus `4:1`, `1:4`, `8:1`, `1:8` (Nano Banana 2 only)
- Resolutions: `1K` (1024px), `2K` (2048px), `4K` (4096px)
- Image Search Grounding: Use real photos from Google Image Search as references (Nano Banana 2 only)

---

### OpenAI GPT Image

Best for: Precise editing, transparent backgrounds, text in images

#### Basic Text-to-Image

> "Generate a modern app icon for a music streaming service with gradient colors"

#### With Transparent Background

> "Create a cartoon robot mascot on transparent background for use as a sticker"

#### Image Editing

> "Edit this photo by changing the sky to a dramatic sunset"
> (attach your image)

#### Multiple Variations

> "Generate 4 different tropical cocktail designs, overhead view"

**Supported Options**:

- Models: `gpt-image-1.5` (best), `gpt-image-1`, `gpt-image-1-mini`
- Sizes: `1024x1024`, `1536x1024` (landscape), `1024x1536` (portrait)
- Quality: `auto`, `high`, `medium`, `low`
- Background: `auto`, `transparent`, `opaque`

---

### Volcengine Seedream

Best for: Chinese/English text rendering in images, multi-image fusion, group (sequential) generation, precise editing

#### Basic Text-to-Image

> "Use Seedream to generate a poster of a spring tea promotion with the title '春日限定' in elegant Chinese calligraphy"

#### Image Editing

> "Change the sky in this photo to a pink-purple sunset, keep everything else unchanged"
> (attach your image)

#### Multi-Image Fusion

> "Put the person from image 1 into the snowy mountain scene of image 2, wearing the red jacket from image 3"
> (attach 3 images)

#### Group Generation (5.0 lite / 4.5 / 4.0)

> "Generate a 4-panel comic of a shiba inu learning to bake a cake, Japanese minimalist style"

#### With Web Search (5.0 lite)

> "Generate a product render of the latest flagship phone, use web search for accurate appearance"

**Supported Options**:

- Models: `doubao-seedream-5-0-pro-260628` (default), `doubao-seedream-5-0-lite-260128`, `doubao-seedream-4-5-251128`, `doubao-seedream-4-0-250828`
- Sizes: resolution presets (`1K`/`2K`/`3K`/`4K`, model-dependent) or explicit `<width>x<height>` pixels
- Group Generation: up to 15 images per request (5.0 lite / 4.5 / 4.0 only)
- Web Search: real-time internet grounding (5.0 lite only)

---

### DashScope Qwen Image 3.0

Best for: Chinese/English text rendering, precise image editing, and combining up to three reference images

> Qwen Image 3.0 is currently invite-only. Enable `qwen-image-3.0-pro` in the Alibaba Cloud Model Studio model marketplace before use.

#### Basic Text-to-Image

> "Use Qwen Image 3.0 to create a spring coffee poster with the exact title 'SPRING SPECIAL', warm natural light, modern editorial layout"

#### Image Editing

> "Change the person's clothing to a dark gray business suit while keeping the face, hairstyle, pose, and background unchanged"
> (attach your image)

#### Multi-Image Fusion

> "Put the person from image 1 into the cafe from image 2, wearing the shirt from image 3; preserve the person's facial features"
> (attach 3 images)

**Supported Options**:

- Model: `qwen-image-3.0-pro`
- Reference images: 1-3 JPG/JPEG, PNG, BMP, TIFF, WEBP, or GIF files, up to 10MB each
- Size: model-selected by default, or explicit `<width>x<height>` with total pixels from `512x512` to `2048x2048`
- Output count: 1-6 PNG images per request
- Controls: prompt extension (on by default), negative prompt, seed, and watermark
- Configuration: `DASHSCOPE_API_KEY`; optional `DASHSCOPE_IMAGE_BASE_URL` for a workspace-specific Beijing or Singapore native API host

Beijing and Singapore API keys and endpoints are separate and cannot be mixed. Generated URLs expire after 24 hours, but the skill downloads the files immediately.

---

## Video Generation

### Volcengine Seedance

Best for: Multi-modal video generation, video editing/extending, synchronized audio, product ads

#### Basic Text-to-Video

> "Create a video of a cat walking on the beach at golden hour, cinematic quality"

#### Image-to-Video (First Frame)

> "Animate this image, the cat slowly turns its head and looks at the camera"
> (attach your image)

#### First + Last Frame

> "Generate a smooth transition video from this winter scene to this summer scene"
> (attach two images)

#### Multi-modal Reference

> "Use image 1 as the character, follow video 1's camera angle, use audio 1 as background music"
> (attach reference images, videos, audio)

#### With Dialogue

> "A woman holds up a product and says 'This cream is amazing, so lightweight and hydrating!'"

#### Silent Video

> "Create a silent video of dewdrops sliding off flower petals in slow motion, macro lens"

**Supported Options**:

- Models: `doubao-seedance-2-0-260128` (highest quality, default), `doubao-seedance-2-0-fast-260128` (faster), `doubao-seedance-2-0-mini-260615` (cheapest)
- Aspect Ratios: `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, `adaptive` (default)
- Durations: `4` to `15` seconds, or `-1` for auto
- Resolutions: `480p`, `720p` (default), `1080p`, `4k` — `1080p` and `4k` require the full model
- Audio: Enabled by default (synchronized dialogue, SFX, music)
- Multi-modal input: Up to 9 reference images, 3 reference videos, 3 reference audios

---

### MiniMax Hailuo

Best for: 2K output, native synchronized audio, voice transfer from a reference audio clip

#### Basic Text-to-Video

> "Create a cinematic 10 second trailer of a starship fleet jumping away, leaving the captain alone at the observation window"

#### Image-to-Video (First Frame)

> "Animate this image, push the camera slowly toward the figure in the background and add more steam to the bowl"
> (attach your image)

#### Last Frame Only

> "Have the character walk down the corridor and end exactly on this frame"
> (attach one image as the last frame)

#### First + Last Frame

> "Generate a smooth transition from this winter scene to this summer scene"
> (attach two images)

#### Multi-modal Reference with Voice Transfer

> "The character says 'Follow the wind, live free' using the timbre of audio 1, appearance from image 1, and the camera rhythm of video 1"
> (attach reference image, video, audio)

#### Product Ad with Asset Mapping

> "Mood and film texture from image 1, character from image 2, product from image 3, ending logo from image 4 — a three-shot vertical ad"

**Supported Options**:

- Models: `MiniMax-H3` (the only model on this API)
- Aspect Ratios: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `adaptive` — text-to-video requires a concrete ratio, image-to-video always follows the input image
- Durations: any integer from `4` to `15` seconds (default `5`)
- Resolutions: `2K` only
- Audio: Native synchronized audio; reference audio can transfer voice timbre
- Multi-modal input: Up to 9 reference images, 3 reference videos, 3 reference audios (12 assets combined)

**Note**: A text prompt is required in every mode, including image-to-video. First/last frame mode and multi-modal reference mode cannot be combined in one request.

---

### DashScope HappyHorse

Best for: Physically realistic motion, reference-to-video, editing an existing video

#### Basic Text-to-Video

> "Create a video of a gymnast performing a backflip on a beam, natural physics, smooth motion"

#### Image-to-Video

> "Animate this image, the character raises their hand and waves"
> (attach your image)

#### Reference-to-Video

> "Use [Image 1] as the character and [Image 2] as the outfit, have them walk through a rainy street"
> (attach 1-9 reference images)

#### Video Edit

> "Edit this video: replace the perfume bottle on the table with the cream jar, keep the camera and lighting unchanged"
> (provide a public video URL)

**Supported Options**:

- Models: auto-derived from the mode and version — `happyhorse-1.1-t2v` / `-i2v` / `-r2v` (default version `1.1`), `happyhorse-1.0-video-edit`
- Aspect Ratios: `16:9` (default), `9:16`, `1:1`, `4:3`, `3:4`, `4:5`, `5:4`, `9:21`, `21:9` — text-to-video and reference-to-video only
- Durations: `3` to `15` seconds (default `5`); video edit follows the source
- Resolutions: `720P`, `1080P` (default)
- Watermark: A "Happy Horse" watermark is added by default; it can be disabled

**Note**: The source video for editing must be a public http(s) URL. A prompt is optional for image-to-video.

---

### Google Veo

Best for: Videos with native audio, dialogue, sound effects

#### Basic Text-to-Video

> "Create a video of ocean waves crashing on rocks at sunset, 8 seconds"

#### With Dialogue and Sound Effects

> "Generate a video of a detective in a noir office saying 'Of all the offices in this town, you had to walk into mine.' with rain sounds on the window"

#### Image-to-Video

> "Animate this image of a cat, make it slowly turn its head and look at the camera"
> (attach your image)

#### Portrait Video (9:16)

> "Create a vertical video of a woman smiling, soft lighting, for social media"

**Supported Options**:

- Models: `veo-3.1-generate-001` (full quality), `veo-3.1-fast-generate-001` (faster)
- Aspect Ratios: `16:9` (landscape), `9:16` (portrait)
- Durations: `4`, `6`, `8` seconds
- Resolutions: `720p`, `1080p` (1080p only with 8s + 16:9)

---

### OpenAI Sora

Best for: Cinematic quality, smooth motion, artistic styles

#### Basic Text-to-Video

> "Create a 4 second video of a butterfly landing on a flower in slow motion"

#### Landscape Cinematic

> "Generate an 8 second aerial drone shot flying over misty mountains at sunrise"

#### Image-to-Video

> "Use this image and animate the scene with gentle camera movement"
> (attach your image)

#### High Quality Pro Model

> "Create a professional quality video of paint drops falling into water, use the pro model"

**Supported Options**:

- Models: `sora-2` (fast, default), `sora-2-pro` (higher quality)
- Sizes: `720x1280` (portrait), `1280x720` (landscape), `1024x1792`, `1792x1024`
- Durations: `4`, `8`, `12` seconds

---

## Audio Generation

### ElevenLabs Sound Effects

Best for: Environmental sounds, action sounds, ambient audio, game SFX

#### Single Sound Effect

> "Generate a sound effect of thunder and rain"

#### Looping Ambient Sound

> "Create 10 seconds of forest ambiance with birds chirping, make it loop seamlessly"

#### Action Sounds with Prompt Influence

> "Generate a sci-fi laser gun firing sound effect, high prompt influence for accurate result"

#### Cinematic Sound

> "Create a cinematic braam impact sound with deep bass and reverb tail"

**Supported Options**:

- Models: `eleven_text_to_sound_v2` (default)
- Duration: 0.5 to 30 seconds (auto-determined if not specified)
- Prompt Influence: 0-1 (0.3 default, higher = more literal)
- Loop: Seamless looping
- Formats:
  - MP3: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`
  - PCM: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`
  - Opus: `opus_48000_64`, `opus_48000_128`

---

### ElevenLabs Text-to-Speech

Best for: Narration, dialogue, voice-overs, character voices

#### Basic Speech

> "Convert this text to speech: 'Welcome to the future of AI-generated content'"

#### Voice Search

> "Generate speech saying 'Hello' with a British male narrator voice"

#### Emotional Expression (V3 Model)

> "Generate speech with emotional tags: '[excited] Oh my gosh, I can't believe we won!'"

**Supported Options**:

- Models:
  - `eleven_v3`: Most expressive, 70+ languages, audio tags support
  - `eleven_multilingual_v2`: Natural speech, 29 languages (default)
  - `eleven_flash_v2_5`: Ultra-low latency ~75ms
- Voice Selection: By ID or search query (e.g., "British female calm")
- Voice Settings: Stability (0-1), Similarity (0-1), Speed (0.7-1.2)
- Audio Tags (V3 only): `[excited]`, `[whispers]`, `[sad]`, `[British accent]`, etc.
- Formats:
  - MP3: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`
  - PCM: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`
  - Opus: `opus_48000_64`, `opus_48000_128`

---

### DashScope Text-to-Speech

Best for: Chinese/multilingual TTS, custom voice characters, game dialogue

#### Basic Chinese TTS

> "Generate Chinese speech saying 'Hello everyone, welcome to our show' with a warm female voice"

#### English TTS with Professional Voice

> "Create English narration saying 'Welcome to our product demonstration' using Jennifer voice"

#### News Broadcast Style

> "Generate Chinese news anchor style speech reading this article"

#### Using Custom Voice

> "Synthesize this text using my custom Voice Design voice for the game character"

**Supported Options**:

- Models:
  - `qwen-audio-3.0-tts-flash`: Current low-latency Qwen-Audio-TTS model (default voice `longanhuan_v3.6`)
  - `qwen-audio-3.0-tts-plus`: Higher-quality Qwen-Audio-TTS model (default voice `longanlingxin`)
  - `qwen3-tts-flash-realtime`: Legacy realtime model (default voice `Cherry`)
  - `qwen3-tts-vd-realtime-2025-12-16`: For Voice Design custom voices
  - `qwen3-tts-vc-realtime-2026-01-15`: For Voice Clone custom voices
- Qwen-Audio-TTS voices: `longanhuan_v3.6`, `longjielidou_v3.6`, `loongeva_v3.6`, `loongjohn`, `longanlingxin`, `longanlufeng`
- Voice Parameters: Volume (0-100), Speed (0.5-2.0), Pitch (0.5-2.0)
- Formats: PCM, WAV, MP3, Opus
- Sample Rates: 8000, 16000, 22050, 24000, 44100, 48000 Hz
- New model controls: natural-language `--instruction`, `--language-hint`, `--seed`, and `--ssml`; emotion tags such as `[excited]` and `[laughing]`

The script uses the Qwen-Audio-TTS WebSocket endpoint (`/api-ws/v1/inference`). The default public Beijing endpoint works without a workspace ID; set `DASHSCOPE_TTS_WS_URL` to a workspace-specific Beijing endpoint when needed. Use a Beijing DashScope API key.

---

### DashScope Voice Design

Best for: Creating unique AI voices for characters, narration, brand voices

#### Create a Professional Narrator

> "Design a voice: mature male announcer, deep and magnetic, steady pace, clear articulation, suitable for news or documentary"

#### Create a Sweet Young Female Voice

> "Design a voice: gentle and sweet young female, medium pace, suitable for emotional content"

#### Create an Anime Character Voice

> "Design a voice: lively and cute child voice, about 8-year-old girl, slightly childish speech, suitable for anime character dubbing"

**Voice Design Tips**:

- Be specific: Use concrete descriptors like "low-pitched", "crisp", "moderate speed"
- Multi-dimensional: Combine gender, age, emotion, and characteristics
- Avoid vague terms: Don't use "nice" or "good", describe actual voice qualities
- Include use case: Specify intended use (news, audiobook, game, etc.)

**Supported Options**:

- Languages: Chinese, English, German, Italian, Portuguese, Spanish, Japanese, Korean, French, Russian
- Output: Voice ID + preview audio
- Sample Rates: 8000, 16000, 24000, 48000 Hz
- Formats: MP3, WAV, PCM, Opus

---

### DashScope Voice Clone

Best for: Cloning real voices, maintaining voice consistency, custom narrators

#### Clone from Audio File

> "Clone a voice from this audio recording for use as a narrator"
> (attach audio file)

#### Clone with Language Specification

> "Clone this English voice recording for podcast narration"
> (attach audio file)

**Audio Requirements**:

- Duration: 10-20 seconds recommended (max 60 seconds)
- Format: WAV (16-bit), MP3, or M4A
- File size: Under 10 MB
- Quality: Clear speech, no background music/noise, mono channel
- Sample rate: 24 kHz or higher recommended

**Supported Options**:

- Languages: Chinese, English, German, Italian, Portuguese, Spanish, Japanese, Korean, French, Russian
- Target Models: `qwen-audio-3.0-tts-plus`, `qwen-audio-3.0-tts-flash`, `qwen3-tts-vc-realtime-2026-01-15` (latest), `qwen3-tts-vc-realtime-2025-11-27`
- Actions: Create, List, Delete

---

### Volcengine Text-to-Speech

Best for: Expressive Chinese TTS, emotional narration, dialects, synthesizing with cloned/designed voices

#### Basic Chinese TTS

> "Use Volcengine to generate Chinese speech saying '夜色渐浓，城市的灯火次第亮起'"

#### Emotional Delivery with a Voice Instruction

> "Read this line with a furious, roaring tone: '放肆！我是龙族的女王！'"

> "Read this line with a trembling, heartbroken crying tone: '我逆转时空九十九次救你……'"

#### Dialect Delivery

> "Read this line in Sichuan dialect with the Vivi voice: '巴适得板，走嘛一起去吃火锅'"

#### Synthesize with a Cloned Voice

> "Use my cloned voice S_abc12345 to read this script"

**Supported Options**:

- Voices: Official Seed-TTS 2.0 voices (`*_uranus_bigtts`) and cloned/designed voices (`S_xxx`, auto-routed)
- Voice Instructions: emotion/tone/speed/volume control for the whole request, plus quoting the previous turn (official 2.0 voices and cloned expressive voices, free, one per request)
- CoT Voice Tags: inline `<cot text=急促难耐>…</cot>` per-sentence control (cloned voices on `seed-tts-2.0-expressive` only)
- Dialects: Sichuan, Shaanxi, Dongbei (dialect-capable voices such as Vivi 2.0)
- Formats: MP3, WAV, PCM, OGG_OPUS; Sample Rates: 8000-48000 Hz
- Extras: speed/loudness (-50 to 100), pitch (-12 to 12), `section_id` context across calls, `<phoneme>` SSML, word-level subtitles, trailing silence, LaTeX reading, AIGC watermark

---

### Volcengine Voice Design

Best for: Creating voices from text descriptions or character images

#### Design from a Text Description

> "Design a Volcengine voice: 女性，语速中等偏快，语调低沉有力"

#### Design from a Character Image

> "Design a voice that matches this character portrait"
> (attach the image)

**Voice Design Tips**:

- Be specific: cover gender, age, pitch, speed, timbre, and style/role
- Image prompts take priority over text prompts when both are given
- Each speaker ID has a limited number of design attempts

**Supported Options**:

- Prompt: text description (max 200 chars) or image (local file / URL, max 10MB)
- Languages: Chinese, English
- Output: demo audio (downloaded immediately; URL valid for 1 hour)

---

### Volcengine Voice Clone

Best for: Cloning real voices (Voice Clone 2.0), managing purchased voice instances

#### Clone from an Audio Sample

> "Clone a Volcengine voice from this recording onto speaker S_abc12345"
> (attach audio file)

#### Check Status and Listen to the Demo

> "Check the training status of S_abc12345 and download the demo audio"

#### Manage Voice Instances

> "List all my Volcengine voices and their expiry dates"

**Audio Requirements**:

- Duration: 10-15 seconds recommended (longer audio is truncated)
- Format: WAV, MP3, OGG, M4A, AAC, or PCM (24kHz mono); under 10 MB
- Quality: single speaker, low noise, steady emotion

**Supported Options**:

- Actions: Train, Status, Upgrade (V1→V3), List, Order, Renew
- Languages: 17 languages including Chinese, English, Japanese, Spanish
- Extras: denoising, volume normalization control, demo preview text

**Billing Note**: `Order` and `Renew` purchase/extend paid voice instances and are billed to your Volcengine account. For postpaid custom speaker IDs, the first synthesis call activates the voice and bills the slot fee.

---

## Music Generation

### ElevenLabs Music

Best for: Background music, theme songs, ambient tracks, jingles

#### Instrumental Music

> "Create a 30 second calm piano melody, ambient and relaxing, instrumental only"

#### With Vocals

> "Generate a 60 second upbeat pop song about summer love with female vocals"

#### Specific Genre and Structure

> "Create epic orchestral music for a movie trailer, 45 seconds, starts soft then builds to powerful climax"

#### Lo-fi Background Music

> "Generate lo-fi hip-hop beat, relaxing and chill, vinyl crackle, mellow piano, perfect for studying, 2 minutes"

**Supported Options**:

- Models: `music_v2` (default, better vocals and arrangement), `music_v1`
- Duration: 10 to 300 seconds (5 minutes max)
- Instrumental: Force instrumental-only output (no AI vocals)
- Formats:
  - MP3: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`
  - PCM: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`
  - Opus: `opus_48000_64`, `opus_48000_128`, `opus_48000_192`

### Google Lyria Music

Best for: Full-length songs, custom lyrics, image-inspired music, high-fidelity clips

#### Instrumental Music

> "Create a calm ambient piano piece, 2 minutes, gentle and relaxing, instrumental"

#### Song with Custom Lyrics

> "Write a pop song with these lyrics: [Verse 1] Walking down the empty street at dawn... [Chorus] We'll find our way back home"

#### Image-to-Music

> "Generate music inspired by this sunset beach photo, nostalgic and warm"

#### Quick 30-Second Clip

> "Create a 30-second energetic electronic loop for a game menu, use Clip model"

**Supported Options**:

- Models: `lyria-3-pro-preview` (default, full songs up to ~3-4 min), `lyria-3-clip-preview` (30s clips)
- Instrumental: Force no vocals
- Image input: Up to 10 reference images
- Custom lyrics: Use `[Verse]`, `[Chorus]`, `[Bridge]` section tags
- Timestamps: Control song structure with `[0:00-0:30] Intro: ...` (Pro only)
- Output: MP3 (both models), WAV (Pro only)
- Lyrics: Auto-returned, optionally saved to `.lyrics.txt` file

---

## 3D Model Generation

### Tripo 3D

Best for: Game assets, product visualization, character models, 3D printing

#### Text-to-3D

> "Generate a 3D model of a cute cartoon cat with big eyes, sitting pose"

#### Text-to-3D with High Quality

> "Create a detailed medieval treasure chest 3D model with iron bands and wood texture, detailed geometry"

#### Image-to-3D

> "Convert this product photo into a 3D model"
> (attach your image)

#### Multiview-to-3D

> "Generate a 3D model from these 4 angles of my character design"
> (attach front, left, back, right images)

#### Export to Different Formats

> "Create a 3D model of a simple chair and export it as FBX for Unity"

#### Rig and Animate a Model

> "Rig this cat model and make it walk and run"
> (auto-rigs the skeleton, then exports walk/run animation clips in one GLB)

#### Rig Your Own Model

> "Import my character.glb and make it walk"
> (uploads your model file, then rigs and animates it — works with GLB/OBJ/FBX/STL)

#### Segment a Model into Parts

> "Split this character model into separate named parts"

#### Complete Hidden Geometry of Parts

> "Complete the occluded geometry of the segmented parts so each part is a closed mesh"

**Supported Options**:

- Models: `v3.1-20260211` (latest, default), `v3.0-20250812`, `v2.5-20250123`, `P1-20260311` (low-poly), `Turbo-v1.0-20250506` (fast)
- Quality: `standard` or `detailed` (for texture and geometry)
- Output Formats: `GLB` (default), `GLTF`, `FBX`, `OBJ`, `STL`, `USDZ`, `3MF`
- Face Limit: Control polygon count for game-ready models
- Rigging: 8 skeleton types (biped/quadruped/hexapod/octopod/avian/serpentine/aquatic/others), Tripo or Mixamo spec, 16 preset animations (idle/walk/run/jump/slash/shoot etc.)
- Segmentation: granularity `simple`/`balanced`/`detailed`, optional reference image guidance

**Tips for Best Results**:

- Keep prompts concise: "Subject + 1-3 adjectives + style"
- Focus on materials (glossy, matte, metallic) over lighting
- Generate one object at a time for best quality
- Use negative prompt to exclude unwanted features
- For images: use clean backgrounds, pre-extract foreground if possible

---

## Advanced Workflows

### Text to Image to Video Pipeline

This workflow demonstrates creating a complete scene from scratch:

#### Step 1: Generate Base Image

> "Generate a photorealistic image of a majestic lion sitting on a rock in the African savanna at golden hour. 16:9 aspect ratio, high detail."

The AI will create the image (e.g., `lion_savanna.png`).

#### Step 2: Refine the Image (Optional)

> "Edit the image to add more dramatic lighting and a few birds in the distant sky"
> (reference the generated image)

This creates a refined version (e.g., `lion_savanna_v2.png`).

#### Step 3: Animate to Video

> "Use this lion image and create an 8 second video where the lion slowly turns its head, wind blowing through its mane. Add ambient savanna sounds."
> (reference the refined image)

Final output: A complete video with your custom-generated content.

---

### Image Editing to Video Pipeline

Start with an existing photo and transform it:

#### Step 1: Style Transfer

> "Transform this photo of my cat into a majestic oil painting style, keep the pose exact"
> (attach your photo)

Creates an artistic version of your photo.

#### Step 2: Animate the Art

> "Animate this oil painting of a cat. Subtle movement like breathing, slight ear twitch, cinematic lighting. 6 seconds."
> (reference the styled image)

Result: Your photo transformed into a living artwork.

---

### Multi-Asset Production

Create a complete media package for a project:

#### Step 1: Hero Image

> "Create a hero image for a fantasy RPG game: a warrior standing before a dragon in a volcanic landscape. Epic composition, 16:9"

#### Step 2: Character Portrait

> "Using the same warrior design, create a portrait shot showing just the upper body. 3:4 aspect ratio for character selection screen"

#### Step 3: Background Music

> "Create 60 seconds of epic orchestral battle music for a fantasy game boss fight"

#### Step 4: Sound Effects

> "Generate a dragon roar sound effect, deep and terrifying"

#### Step 5: Cinematic Trailer

> "Using the hero image, create an 8 second cinematic video. Camera slowly zooms toward the warrior as the dragon breathes fire in the background. Do not generate audio."

Result: A complete set of game assets from a single creative session, ready for further refinement in post-production software.

---

### Tips for Chained Workflows

1. **Maintain Consistency**: When creating related assets, reference previous outputs
   - "Using the same character from the previous image..."
   - "Match the color palette of the hero image..."

2. **Build Incrementally**: Start with the base asset, then refine
   - Generate rough concept first
   - Edit and refine details
   - Final polish before animation

3. **Use Appropriate Tools**:
   - Google Gemini: Best for initial concepts and style transfer
   - OpenAI GPT: Best for precise edits and transparent assets
   - Volcengine Seedance: Best all-round default, and the only option for 4K or video editing
   - MiniMax Hailuo: Best for 2K output and transferring a voice from reference audio
   - DashScope HappyHorse: Best for physically realistic motion
   - Google Veo: Best when you need audio with video
   - OpenAI Sora: Best for cinematic quality

4. **Save Intermediate Results**: Keep versions at each step for flexibility
   - `concept_v1.png` → `concept_v2.png` → `final.png` → `animated.mp4`

5. **Match Aspect Ratios**: Ensure image aspect ratio matches video target
   - 16:9 image → 16:9 or 1280x720 video
   - 9:16 image → 9:16 or 720x1280 video

---

## Troubleshooting

### API Key Issues

**Error**: "API key not found" or "Authentication failed"

- Check `.genix.env` file exists in project root
- Verify API key is correctly copied (no extra spaces)
- Ensure the correct environment variables are set
- If upgrading from v0.1, rename `.env` to `.genix.env`

### Generation Failures

**Error**: "Content policy violation"

- Avoid generating real people's faces
- Check for copyrighted content in prompts
- Review platform content guidelines

**Error**: "Rate limit exceeded"

- Wait a few minutes before retrying
- Consider upgrading API plan for higher limits

### Installation Issues

**Error**: "uv not found" after install

- Restart your terminal/IDE
- Check if `~/.local/bin` is in your PATH

**Error**: "Python 3.14 not found"

- Run `uv python install 3.14` manually
- Or modify install script to use available Python version

---

## Getting Help

- **GitHub Issues**: Report bugs or request features
