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
.\.venv\Scripts\activate    # Windows
source .venv/bin/activate   # Linux/Mac

# Add dependencies
uv add <package_name>

# Sync dependencies
uv sync
```

## Architecture

### Skills System

Skills are self-contained modules installed to tool-specific directories:

- Source skill definitions live in `/genix`
- Installed to `.claude/skills/genix`, `.cursor/skills/genix`, etc.
- Each skill has a `SKILL.md` metadata file, `references/` for documentation, and `scripts/` for helper code

### API Providers

The project integrates with multiple AIGC APIs (configured via `.env`):

- **Google Generative AI** (`google-genai`) - Image generation
- **OpenAI** (`openai`) - Various AI capabilities
- **ElevenLabs** (`elevenlabs`) - Text-to-audio/speech

### Current Skill Capabilities (genix)

- Text-to-Image (t2i)
- Image-to-Image (i2i)
- Text-to-Audio (t2a)
- Video and Music generation are planned (TODO)

## Environment Setup

Copy `.env.template` to `.env` and configure API keys:

- `GOOGLE_CLOUD_API_KEY`
- `ELEVENLABS_API_KEY`
- `OPENAI_API_KEY`
- `OPENAI_API_BASE` (optional, defaults to OpenAI)

## Technical Stack

- Python 3.14+
- Package manager: `uv` (Astral)
- Async/await pattern for API calls
