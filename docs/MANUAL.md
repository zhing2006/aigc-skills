# Genix Skills User Manual

[English](MANUAL.md) | [中文](MANUAL_CN.md)

This manual provides detailed instructions for installing and using the Genix AIGC Skills package.

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Download Package](#download-package)
  - [Run Install Script](#run-install-script)
  - [Configure API Keys](#configure-api-keys)
- [Skills Overview](#skills-overview)
- [Image Generation](#image-generation)
  - [Google Gemini (Nano Banana Pro)](#google-gemini-nano-banana-pro)
  - [OpenAI GPT Image](#openai-gpt-image)
- [Video Generation](#video-generation)
  - [Google Veo](#google-veo)
  - [OpenAI Sora](#openai-sora)
- [Audio Generation](#audio-generation)
  - [ElevenLabs Sound Effects](#elevenlabs-sound-effects)
  - [ElevenLabs Text-to-Speech](#elevenlabs-text-to-speech)
- [Music Generation](#music-generation)
  - [ElevenLabs Music](#elevenlabs-music)
- [Advanced Workflows](#advanced-workflows)
  - [Text to Image to Video Pipeline](#text-to-image-to-video-pipeline)
  - [Image Editing to Video Pipeline](#image-editing-to-video-pipeline)
  - [Multi-Asset Production](#multi-asset-production)

---

## Installation

### Prerequisites

- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Internet Connection**: Required for downloading dependencies and API calls
- **API Keys**: At least one API key from supported providers (Google, OpenAI, ElevenLabs)

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
2. **Creates pyproject.toml**: Initializes Python 3.14 project configuration
3. **Creates Virtual Environment**: Isolated Python environment in `.venv/`
4. **Creates .env File**: Copies `.env.template` to `.env` for API key configuration
5. **Installs Dependencies**: All required Python packages
6. **Moves Genix Skill**: Moves `genix/` folder to the AI tool's skills directory

After installation, the skills will be in:

- Claude Code: `.claude/skills/genix/`
- Cursor: `.cursor/skills/genix/`
- Codex: `.codex/skills/genix/`

### Configure API Keys

Edit the `.env` file in your project root with your API keys:

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
```

**Note**: You only need to configure the API keys for the providers you plan to use.

---

## Skills Overview

| Skill | Provider | Input | Output | Use Case |
| ----- | -------- | ----- | ------ | -------- |
| Nano Banana Pro | Google | Text, Images | Image | High-quality image generation, style transfer |
| GPT Image | OpenAI | Text, Images | Image | Image generation, editing, transparent backgrounds |
| Veo | Google | Text, Image | Video | Video generation with audio |
| Sora | OpenAI | Text, Image | Video | Cinematic video generation |
| Sound Effects | ElevenLabs | Text | Audio | Sound effects, ambient sounds |
| Text-to-Speech | ElevenLabs | Text | Audio | Voice narration, dialogue |
| Music | ElevenLabs | Text | Audio | Background music, songs |

---

## Image Generation

### Google Gemini (Nano Banana Pro)

Best for: High-resolution images, style transfer, character consistency

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

**Supported Options**:

- Aspect Ratios: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`
- Resolutions: `1K` (1024px), `2K` (2048px), `4K` (4096px)

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

## Video Generation

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

- Models: `eleven_text_to_sound_v2` (default, supports loops), `eleven_text_to_sound_v1`
- Duration: 0.5 to 30 seconds (auto-determined if not specified)
- Prompt Influence: 0-1 (0.3 default, higher = more literal)
- Loop: Seamless looping (v2 only)
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

#### Long Narration with Custom Settings

> "Create a voice narration, use warm female voice, slower speed for audiobook style"

**Supported Options**:

- Models:
  - `eleven_v3`: Most expressive, 70+ languages, audio tags support
  - `eleven_multilingual_v2`: Natural speech, 29 languages (default)
  - `eleven_flash_v2_5`: Ultra-low latency ~75ms
  - `eleven_turbo_v2_5`: High quality, low latency ~250ms
- Voice Selection: By ID or search query (e.g., "British female calm")
- Voice Settings: Stability (0-1), Similarity (0-1), Speed (0.7-1.2)
- Audio Tags (V3 only): `[excited]`, `[whispers]`, `[sad]`, `[British accent]`, etc.
- Formats:
  - MP3: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`
  - PCM: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`
  - Opus: `opus_48000_64`, `opus_48000_128`

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

- Models: `music_v1` (default)
- Duration: 10 to 300 seconds (5 minutes max)
- Instrumental: Force instrumental-only output (no AI vocals)
- Formats:
  - MP3: `mp3_22050_32`, `mp3_44100_64`, `mp3_44100_128`, `mp3_44100_192`
  - PCM: `pcm_16000`, `pcm_22050`, `pcm_44100`, `pcm_48000`
  - Opus: `opus_48000_64`, `opus_48000_128`, `opus_48000_192`

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

> "Using the hero image, create an 8 second cinematic video. Camera slowly zooms toward the warrior as the dragon breathes fire in the background."

Result: A complete set of game assets from a single creative session.

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

- Check `.env` file exists in project root
- Verify API key is correctly copied (no extra spaces)
- Ensure the correct environment variables are set

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
