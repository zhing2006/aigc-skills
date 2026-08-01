# GENIX AIGC SKILLS

[English](README.md) | [中文](README_CN.md)

AIGC generation skills for Claude Code and similar AI tools.

## Features

| Category | Provider | Capability |
| -------- | -------- | ---------- |
| **Image** | Google Gemini | Text-to-Image, Image-to-Image, Image Search Grounding |
| **Image** | OpenAI GPT | Text-to-Image, Image Edit |
| **Image** | Volcengine Seedream | Text-to-Image, Image-to-Image, Multi-Image Fusion, Group Generation (up to 4K) |
| **Image** | DashScope Qwen Image 3.0 | Text-to-Image, Image Edit, Multi-Image Fusion (invite-only) |
| **Video** | Volcengine Seedance | Text-to-Video, Image-to-Video, Multi-modal Reference, Video Edit/Extend (up to 4K) |
| **Video** | MiniMax Hailuo | Text-to-Video, Image-to-Video (first/last frame), Multi-modal Reference with voice transfer (2K native audio) |
| **Video** | DashScope HappyHorse | Text-to-Video, Image-to-Video, Reference-to-Video, Video Edit (physically realistic) |
| **Video** | Google Veo | Text-to-Video, Image-to-Video |
| **Video** | OpenAI Sora | Text-to-Video, Image-to-Video |
| **Audio** | ElevenLabs | Text-to-Speech, Sound Effects |
| **Audio** | DashScope Qwen-Audio-TTS 3.0 | WebSocket Text-to-Speech, Voice Design, Voice Clone |
| **Audio** | Volcengine | Text-to-Speech (streaming, voice instructions, dialects), Voice Design, Voice Clone, Voice Management |
| **Music** | ElevenLabs | Text-to-Music (instrumental/vocal) |
| **Music** | Google Lyria | Text-to-Music, Image-to-Music (full songs/clips) |
| **3D Model** | Tripo | Text-to-3D, Image-to-3D, Multiview-to-3D, Model Import, Rigging & Animation, Mesh Segmentation, Mesh Completion |

## Installation

### Step 1: Run Setup Script

Choose the appropriate script for your system:

| System | Command | Notes |
| ------ | ------- | ----- |
| Windows (PowerShell) | `.\setup.ps1` | Default |
| Windows (CMD) | `setup.bat` | Alternative |
| Linux / macOS | `./setup.sh` | Run `chmod +x setup.sh` first |

**What the setup script does:**

1. Installs `uv` package manager (if not present)
2. Creates `pyproject.toml` and virtual environment `.venv-genix` (Python 3.14)
3. Creates `.genix.env` file from template
4. Installs Python dependencies
5. Copies genix skill to the AI tool's skills directory

**Specify target tool (optional):**

```bash
# PowerShell
.\setup.ps1 -Tool cursor

# CMD / Shell
setup.bat cursor
./setup.sh cursor
```

Supported tools: `claude` (default), `cursor`, `codex`, `opencode`, `vscode`

### Step 2: Configure API Keys

Edit the `.genix.env` file and fill in your API keys:

#### Google API

| USE_VERTEX_AI | Required Variables |
| ------------- | ------------------ |
| `false` | `GOOGLE_CLOUD_API_KEY` |
| `true` | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` |

#### OpenAI API

| USE_AZURE_OPENAI | Required Variables |
| ---------------- | ------------------ |
| `false` | `OPENAI_API_KEY`, `OPENAI_API_BASE` (optional) |
| `true` | `OPENAI_API_KEY`, `OPENAI_API_BASE`, `AZURE_OPENAI_API_VERSION` |

#### Tripo API

| Required Variables |
| ------------------ |
| `TRIPO_API_KEY` |

#### DashScope API

| Variables |
| --------- |
| `DASHSCOPE_API_KEY` |
| `DASHSCOPE_IMAGE_BASE_URL` (optional, native image API host) |
| `DASHSCOPE_TTS_WS_URL` (optional, Qwen-Audio-TTS WebSocket endpoint) |

#### Volcengine API

| Required Variables |
| ------------------ |
| `VOLCENGINE_API_KEY` (video generation) |
| `VOLCENGINE_API_BASE` (optional, defaults to official endpoint) |
| `VOLCENGINE_TTS_API_KEY` (speech: TTS / voice clone / voice design) |
| `VOLCENGINE_TTS_BASE` (optional, defaults to official endpoint) |
| `VOLCENGINE_TTS_APPID` (voice management only) |
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` (voice management only) |

#### MiniMax API

| Variables |
| --------- |
| `MINIMAX_API_KEY` (video generation) |
| `MINIMAX_API_BASE` (optional, defaults to official endpoint) |

#### Example `.genix.env` file

```env
# Google API (choose one mode)
USE_VERTEX_AI = "false"
GOOGLE_CLOUD_API_KEY = "your_google_api_key_here"      # When USE_VERTEX_AI = false
GOOGLE_CLOUD_PROJECT = "your_project_name"             # When USE_VERTEX_AI = true
GOOGLE_CLOUD_LOCATION = "us-central1"                  # When USE_VERTEX_AI = true

# ElevenLabs API
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"

# OpenAI API (choose one mode)
USE_AZURE_OPENAI = "false"
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_API_BASE = "https://api.openai.com/v1"          # Optional for OpenAI, required for Azure
AZURE_OPENAI_API_VERSION = "2025-04-01-preview"        # When USE_AZURE_OPENAI = true

# Tripo API
TRIPO_API_KEY = "your_tripo_api_key_here"

# DashScope API (Alibaba Cloud)
DASHSCOPE_API_KEY = "your_dashscope_api_key_here"
DASHSCOPE_IMAGE_BASE_URL = "https://dashscope.aliyuncs.com"  # Optional; workspace domain recommended for Qwen Image
DASHSCOPE_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"  # Optional; Qwen-Audio-TTS

# Volcengine API (ByteDance)
VOLCENGINE_API_KEY = "your_volcengine_api_key_here"
VOLCENGINE_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"  # Optional
VOLCENGINE_TTS_API_KEY = "your_volcengine_tts_api_key_here"       # Speech (TTS/clone/design)
VOLCENGINE_TTS_BASE = "https://openspeech.bytedance.com"      # Optional
VOLCENGINE_TTS_APPID = "your_volcengine_tts_appid_here"           # Voice management only
VOLCENGINE_ACCESS_KEY = "your_volcengine_access_key_here"         # Voice management only
VOLCENGINE_SECRET_KEY = "your_volcengine_secret_key_here"         # Voice management only

# MiniMax API (Hailuo video)
MINIMAX_API_KEY = "your_minimax_api_key_here"
MINIMAX_API_BASE = "https://api.minimaxi.com"                     # Optional
```

## Usage

1. Restart your AI tool (Claude Code, Cursor, etc.) to load the skills
2. Ask the AI to generate content, for example:

**Image Generation:**

- "Generate an image of a cute cat wearing a wizard hat"
- "Create a cyberpunk city landscape in 16:9 aspect ratio"

**Video Generation:**

- "Create a video of ocean waves at sunset, 8 seconds"
- "Generate a video from this image with camera zoom effect"

**Audio Generation:**

- "Generate sound effects of rain on a window"
- "Create a text-to-speech audio saying 'Hello World'"

**Music Generation:**

- "Create a calm piano melody, 30 seconds, instrumental"
- "Generate an epic orchestral theme for a trailer"
- "Create a 2-minute jazz fusion track with saxophone and piano"
- "Generate music inspired by this sunset photo, calm and nostalgic"

**3D Model Generation:**

- "Generate a 3D model of a cute cartoon cat"
- "Convert this image to a 3D model"
- "Create a wooden chair 3D model and export as FBX"
- "Use P1 model to generate a low-poly medieval sword with 3000 faces for game use"

The AI will automatically select the appropriate skill and optimize your prompt following best practices for best results.

## License

Apache 2.0
