# aigc-skills

[English](README.md) | [中文](README_CN.md)

AIGC generation skills for Claude Code and similar AI tools.

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

```env
GOOGLE_CLOUD_API_KEY = "your_google_api_key_here"
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_API_BASE = "https://api.openai.com/v1"
USE_AZURE_OPENAI = "false"
AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
```

## Usage

1. Restart your AI tool (Claude Code, Cursor, etc.) to load the skills
2. Ask the AI to generate content, for example:
   - "Generate an image of a cute cat wearing a wizard hat"
   - "Create a cyberpunk city landscape in 16:9 aspect ratio"
   - "Generate sound effects of rain on a window"

The AI will automatically use the appropriate AIGC skill based on your request.

## License

Apache 2.0
