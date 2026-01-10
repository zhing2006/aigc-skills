# GENIX AIGC SKILLS

[English](README.md) | [中文](README_CN.md)

AIGC generation skills for Claude Code and similar AI tools.

## Features

| Category | Provider | Capability |
| -------- | -------- | ---------- |
| **Image** | Google Gemini | Text-to-Image, Image-to-Image |
| **Image** | OpenAI GPT | Text-to-Image, Image Edit |
| **Video** | Google Veo | Text-to-Video, Image-to-Video |
| **Video** | OpenAI Sora | Text-to-Video, Image-to-Video |
| **Audio** | ElevenLabs | Text-to-Speech, Sound Effects |
| **Music** | ElevenLabs | Text-to-Music (instrumental/vocal) |

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
2. Creates `pyproject.toml` and virtual environment (Python 3.14)
3. Creates `.env` file from template
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

Edit the `.env` file and fill in your API keys:

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

#### Example `.env` file

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

The AI will automatically select the appropriate skill and optimize your prompt following best practices for best results.

## License

Apache 2.0
