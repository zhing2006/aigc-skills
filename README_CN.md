# aigc-skills

[English](README.md) | [中文](README_CN.md)

适用于 Claude Code 及类似 AI 工具的 AIGC 生成技能。

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
2. 创建 `pyproject.toml` 和虚拟环境（Python 3.14）
3. 从模板创建 `.env` 文件
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

编辑 `.env` 文件，填入你的 API 密钥：

```env
GOOGLE_CLOUD_API_KEY = "your_google_api_key_here"
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_API_BASE = "https://api.openai.com/v1"
USE_AZURE_OPENAI = "false"
AZURE_OPENAI_API_VERSION = "2025-04-01-preview"
```

## 使用方法

1. 重启你的 AI 工具（Claude Code、Cursor 等）以加载技能
2. 向 AI 请求生成内容，例如：
   - "生成一张戴着巫师帽的可爱猫咪图片"
   - "创建一个赛博朋克城市风景，16:9 比例"
   - "生成雨打窗户的音效"

AI 会根据你的请求自动使用相应的 AIGC 技能。

## 许可证

Apache 2.0
