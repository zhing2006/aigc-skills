# GENIX AIGC SKILLS

[English](README.md) | [中文](README_CN.md)

适用于 Claude Code 及类似 AI 工具的 AIGC 生成技能。

## 功能

| 类别 | 提供商 | 能力 |
| ---- | ------ | ---- |
| **图像** | Google Gemini | 文生图、图生图、图片搜索 Grounding |
| **图像** | OpenAI GPT | 文生图、图像编辑、原生透明背景（gpt-image-2 支持自定义尺寸，最高 4K） |
| **图像** | Volcengine Seedream | 文生图、图生图、多图融合、组图生成（最高 4K） |
| **图像** | DashScope 千问图像 3.0 | 文生图、图像编辑、多图融合（邀测） |
| **视频** | Volcengine Seedance 2.5 / 2.0 | 文生视频、图生视频、音频生视频、多模态参考、视频编辑/延长（2.5 支持 30 秒一镜到底与 1080p，2.0 最高 4K） |
| **视频** | DashScope 万相 3.0 | 文生视频、首帧/首尾帧、多模态参考、文档生视频、网页生视频（全能参考模型，最长 30 秒 / 30fps） |
| **视频** | MiniMax 海螺 | 文生视频、图生视频（首/尾帧）、多模态参考含音色迁移（2K 原生音频） |
| **视频** | DashScope HappyHorse | 文生视频、图生视频、参考生视频、视频编辑（物理真实） |
| **视频** | Google Veo | 文生视频、图生视频 |
| **视频** | OpenAI Sora | 文生视频、图生视频 |
| **音频** | ElevenLabs | 文字转语音、音效生成 |
| **音频** | DashScope 千问音频 TTS 3.0 | WebSocket 文字转语音、音色设计、音色克隆 |
| **音频** | Volcengine | 文字转语音（流式、语音指令、方言）、音色设计、音色克隆、音色管理 |
| **音乐** | ElevenLabs | 文生音乐（纯乐器/带人声） |
| **音乐** | Google Lyria | 文生音乐、图生音乐（完整歌曲/短片段） |
| **3D 模型** | Tripo | 文生 3D、图生 3D、多视图生 3D、模型导入、骨骼绑定与动画、网格分割、网格补全 |

## 安装

### 第一步：运行安装脚本

根据你的系统选择合适的脚本：

| 系统 | 命令 | 备注 |
| ---- | ---- | ---- |
| Windows (PowerShell) | `.\setup.ps1` | 默认 |
| Windows (CMD) | `setup.bat` | 备选 |
| Linux / macOS | `./setup.sh` | 先执行 `chmod +x setup.sh` |

**安装脚本做了什么：**

1. 安装 `uv` 包管理器（如未安装）
2. 创建 `pyproject.toml` 和虚拟环境 `.venv-genix`（Python 3.14）
3. 从模板创建 `.genix.env` 文件
4. 安装 Python 依赖
5. 将 genix 技能复制到 AI 工具的技能目录

**指定目标工具（可选）：**

```bash
# PowerShell
.\setup.ps1 -Tool cursor

# CMD / Shell
setup.bat cursor
./setup.sh cursor
```

支持的工具：`claude`（默认）、`cursor`、`codex`、`opencode`、`vscode`

### 第二步：配置 API 密钥

编辑 `.genix.env` 文件，填入你的 API 密钥：

#### Google API

| USE_VERTEX_AI | 必需变量 |
| ------------- | -------- |
| `false` | `GOOGLE_CLOUD_API_KEY` |
| `true` | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` |

#### OpenAI API

| USE_AZURE_OPENAI | 必需变量 |
| ---------------- | -------- |
| `false` | `OPENAI_API_KEY`, `OPENAI_API_BASE`（可选） |
| `true` | `OPENAI_API_KEY`, `OPENAI_API_BASE`, `AZURE_OPENAI_API_VERSION` |

#### Tripo API

| 必需变量 |
| -------- |
| `TRIPO_API_KEY` |

#### DashScope API

| 变量 |
| ---- |
| `DASHSCOPE_API_KEY` |
| `DASHSCOPE_IMAGE_BASE_URL`（可选，原生图像 API 地址） |
| `DASHSCOPE_TTS_WS_URL`（可选，千问音频 TTS WebSocket 地址） |
| `DASHSCOPE_WORKSPACE_ID`（可选，万相 3.0 视频的业务空间 ID） |
| `DASHSCOPE_VIDEO_BASE_URL`（可选，原生异步视频 API 地址） |

#### Volcengine API

| 必需变量 |
| -------- |
| `VOLCENGINE_API_KEY`（视频生成） |
| `VOLCENGINE_API_BASE`（可选，默认使用官方地址） |
| `VOLCENGINE_TTS_API_KEY`（语音：合成/克隆/设计） |
| `VOLCENGINE_TTS_BASE`（可选，默认使用官方地址） |
| `VOLCENGINE_TTS_APPID`（仅音色管理需要） |
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`（仅音色管理需要） |

#### MiniMax API

| 变量 |
| ---- |
| `MINIMAX_API_KEY`（视频生成） |
| `MINIMAX_API_BASE`（可选，默认使用官方地址） |

#### `.genix.env` 文件示例

```env
# Google API（二选一）
USE_VERTEX_AI = "false"
GOOGLE_CLOUD_API_KEY = "your_google_api_key_here"      # USE_VERTEX_AI = false 时需要
GOOGLE_CLOUD_PROJECT = "your_project_name"             # USE_VERTEX_AI = true 时需要
GOOGLE_CLOUD_LOCATION = "us-central1"                  # USE_VERTEX_AI = true 时需要

# ElevenLabs API
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"

# OpenAI API（二选一）
USE_AZURE_OPENAI = "false"
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_API_BASE = "https://api.openai.com/v1"          # OpenAI 可选，Azure 必填
AZURE_OPENAI_API_VERSION = "2025-04-01-preview"        # USE_AZURE_OPENAI = true 时需要

# Tripo API
TRIPO_API_KEY = "your_tripo_api_key_here"

# DashScope API（阿里云）
DASHSCOPE_API_KEY = "your_dashscope_api_key_here"
DASHSCOPE_IMAGE_BASE_URL = "https://dashscope.aliyuncs.com"  # 可选；千问图像建议使用业务空间专属域名
DASHSCOPE_TTS_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"  # 可选；千问音频 TTS
DASHSCOPE_WORKSPACE_ID = "your_dashscope_workspace_id_here"   # 可选；万相 3.0 视频的业务空间 ID
DASHSCOPE_VIDEO_BASE_URL = "https://dashscope.aliyuncs.com"   # 可选；HappyHorse / 万相 3.0 视频地址

# Volcengine API（字节跳动）
VOLCENGINE_API_KEY = "your_volcengine_api_key_here"
VOLCENGINE_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"  # 可选
VOLCENGINE_TTS_API_KEY = "your_volcengine_tts_api_key_here"       # 语音（合成/克隆/设计）
VOLCENGINE_TTS_BASE = "https://openspeech.bytedance.com"      # 可选
VOLCENGINE_TTS_APPID = "your_volcengine_tts_appid_here"           # 仅音色管理需要
VOLCENGINE_ACCESS_KEY = "your_volcengine_access_key_here"         # 仅音色管理需要
VOLCENGINE_SECRET_KEY = "your_volcengine_secret_key_here"         # 仅音色管理需要

# MiniMax API（海螺视频）
MINIMAX_API_KEY = "your_minimax_api_key_here"
MINIMAX_API_BASE = "https://api.minimaxi.com"                     # 可选
```

## 使用方法

1. 重启你的 AI 工具（Claude Code、Cursor 等）以加载技能
2. 向 AI 请求生成内容，例如：

**图像生成：**

- "生成一张戴着巫师帽的可爱猫咪图片"
- "创建一个赛博朋克城市风景，16:9 比例"

**视频生成：**

- "生成一段日落时分海浪的视频，8秒"
- "把这张图片生成带有镜头推进效果的视频"

**音频生成：**

- "生成雨打窗户的音效"
- "创建一段说'你好世界'的语音"

**音乐生成：**

- "创作一段平静的钢琴旋律，30秒，纯乐器"
- "生成一段史诗级的管弦乐预告片主题曲"
- "创作一段 2 分钟的爵士融合曲目，带萨克斯和钢琴"
- "根据这张日落照片生成音乐，氛围平静怀旧"

**3D 模型生成：**

- "生成一个可爱的卡通猫 3D 模型"
- "把这张图片转换成 3D 模型"
- "创建一把木椅的 3D 模型，导出为 FBX 格式"
- "用 P1 模型生成一把低模中世纪宝剑，面数限制 3000，用于游戏"

AI 会自动选择合适的技能，并按照最佳实践优化你的提示词以获得最佳效果。

## 许可证

Apache 2.0
