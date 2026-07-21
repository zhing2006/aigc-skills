# AGENTS.md

This file provides guidance for AI agents working with code in this repository.

## Project Overview

This is an AIGC (AI-Generated Content) skills framework for Claude Code and similar AI tools. It provides skills for generating images, audio, video, and music using various AI APIs.

## Development Commands

```powershell
# Initial setup (Windows PowerShell)
.\setup.ps1 -Tool claude    # Install for Claude Code (default)
.\setup.ps1 -Tool cursor    # Install for Cursor editor

# Activate virtual environment
.\.venv-genix\Scripts\activate    # Windows
source .venv-genix/bin/activate   # Linux/Mac

# Add dependencies
uv add <package_name>

# Sync dependencies
uv sync

# Build distribution package
.\build.ps1                         # Creates genix-skills.zip (default)
.\build.ps1 -OutputName "custom"    # Creates custom.zip
```

## Distribution

To distribute the skills package:

1. Run `.\build.ps1` to create `genix-skills.zip`
2. The zip contains: `genix/`, `.env.template`, and install scripts
3. Users follow `docs/MANUAL.md` for installation and usage instructions

## Architecture

### Skills System

Skills are self-contained modules installed to tool-specific directories:

- Source skill definitions live in `/genix`
- Installed to `.claude/skills/genix`, `.cursor/skills/genix`, etc.
- Each skill has a `SKILL.md` metadata file, `references/` for documentation, and `scripts/` for helper code

### API Providers

The project integrates with multiple AIGC APIs (configured via `.env`):

- **Google Generative AI** (`google-genai`) - Image and Video generation
- **OpenAI** (`openai`) - Image and Video generation
- **ElevenLabs** (`elevenlabs`) - Audio, Speech, and Music generation
- **Alibaba Bailian / DashScope** - Image generation and editing, Speech, and Video generation

### Current Skill Capabilities (genix)

- **Image**: Text-to-Image, Image-to-Image, Multi-Image Fusion (Google Gemini, OpenAI GPT, DashScope Qwen Image 3.0)
- **Video**: Text-to-Video, Image-to-Video (Google Veo, OpenAI Sora)
- **Audio**: Sound Effects, Text-to-Speech (ElevenLabs, DashScope Qwen-Audio-TTS 3.0)
- **Music**: Text-to-Music with vocals or instrumental (ElevenLabs)

## Environment Setup

Copy `.env.template` to `.env` and configure API keys:

- `GOOGLE_CLOUD_API_KEY`
- `ELEVENLABS_API_KEY`
- `OPENAI_API_KEY`
- `OPENAI_API_BASE` (optional, defaults to OpenAI)
- `DASHSCOPE_API_KEY`
- `DASHSCOPE_IMAGE_BASE_URL` (optional, native Qwen Image API host)
- `DASHSCOPE_TTS_WS_URL` (optional, Qwen-Audio-TTS WebSocket endpoint)

## Technical Stack

- Python 3.14+
- Package manager: `uv` (Astral)
- Async/await pattern for API calls

## Documentation

- `README.md` / `README_CN.md` - Quick start guide
- `docs/MANUAL.md` / `docs/MANUAL_CN.md` - Detailed user manual with advanced workflows

## Versioning

- **Patch releases** (e.g., v0.1.0 → v0.1.1): Do NOT update `genix/SKILL.md` version
- **Minor releases** (e.g., v0.1.x → v0.2.0): Update `genix/SKILL.md` version to match
