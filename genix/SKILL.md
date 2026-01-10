---
name: genix
description: AIGC image/video/audio/music generation skills
compatibility: Designed for Claude Code (or similar products)
license: Apache 2.0. LICENSE.txt has complete terms
metadata:
  version: "0.1"
  author: zhing2006
---

# AIGC Skills

## Workflow

1. **Select generation method**: Choose the appropriate method based on user request. If not specified, use the first method listed for that content type
2. **Read reference file**: Read the corresponding reference file for the selected method
3. **Rewrite prompt**: Transform the user's input into an optimized prompt following the "Prompt Best Practices" section in the reference file
4. **Generate**: Run the script with the optimized prompt and parameters as instructed in the reference file
5. **Report result**: Tell the user where the generated file was saved. Do not read the generated file content

## Image Skills

- [Nano Banana Pro Image generation](references/google-nano-banana.md)
- [OpenAI GPT Image generation](references/openai-gpt-image.md)

## Audio Skills

- [ElevenLabs sound effects generation](references/elevenlabs-sound-effect.md)
- [ElevenLabs text-to-speech generation](references/elevenlabs-text-speech.md)

## Video Skills

- [Google Veo video generation](references/google-veo.md)
- [OpenAI Sora video generation](references/openai-sora.md)

## Music Skills

- [ElevenLabs music generation](references/elevenlabs-music.md)
