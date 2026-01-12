#!/bin/bash

# Genix Skills Install Script

set -e

# Parse arguments
TOOL="${1:-claude}"
VENV_NAME=".venv-genix"

# Validate tool argument
case "$TOOL" in
    claude|cursor|codex|opencode|vscode)
        ;;
    *)
        echo "Error: Invalid tool. Supported: claude, cursor, codex, opencode, vscode"
        exit 1
        ;;
esac

# Skills directory mapping
case "$TOOL" in
    claude)   TARGET_DIR=".claude/skills" ;;
    cursor)   TARGET_DIR=".cursor/skills" ;;
    codex)    TARGET_DIR=".codex/skills" ;;
    opencode) TARGET_DIR=".claude/skills" ;;
    vscode)   TARGET_DIR=".claude/skills" ;;
esac

echo "=== Genix Skills Install ==="
echo "Target tool: $TOOL"

# 1. Check/Install uv
echo ""
echo "[1/5] Checking uv installation..."
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the env to get uv in path
    source "$HOME/.local/bin/env" 2>/dev/null || true
    if ! command -v uv &> /dev/null; then
        echo "Error: uv installation failed. Please restart terminal and try again."
        exit 1
    fi
    echo "uv installed successfully!"
else
    echo "uv is already installed: $(uv --version)"
fi

# 2. Create virtual environment if not exists
echo ""
echo "[2/5] Checking virtual environment ($VENV_NAME)..."
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating Python 3.14 virtual environment..."
    uv venv "$VENV_NAME" --python 3.14
    echo "Virtual environment created!"
else
    echo "Virtual environment already exists."
fi

# 3. Create .genix.env from template if not exists
echo ""
echo "[3/5] Checking .genix.env file..."
if [ ! -f ".genix.env" ]; then
    if [ -f ".env.template" ]; then
        cp ".env.template" ".genix.env"
        echo ".genix.env created from template. Please update with your API keys."
    else
        echo "Warning: .env.template not found, skipping .genix.env creation."
    fi
else
    echo ".genix.env already exists."
fi

# 4. Install dependencies
echo ""
echo "[4/5] Installing dependencies..."
uv pip install --python "$VENV_NAME/bin/python" python-dotenv aiofiles aiohttp elevenlabs google-genai openai pillow tripo3d
echo "Dependencies installed!"

# 5. Move genix to tool's skills directory
echo ""
echo "[5/5] Installing genix skill to $TOOL..."
GENIX_TARGET="$TARGET_DIR/genix"

# Check if source genix directory exists
if [ ! -d "genix" ]; then
    if [ -d "$GENIX_TARGET" ]; then
        echo "Genix skill already installed at: $GENIX_TARGET"
    else
        echo "Error: genix directory not found. Please re-extract the package."
        exit 1
    fi
else
    # Create skills directory if not exists
    if [ ! -d "$TARGET_DIR" ]; then
        mkdir -p "$TARGET_DIR"
        echo "Created skills directory: $TARGET_DIR"
    fi

    # Remove existing genix skill if exists
    if [ -d "$GENIX_TARGET" ]; then
        rm -rf "$GENIX_TARGET"
        echo "Removed existing genix skill."
    fi

    # Move genix directory (instead of copy)
    mv "genix" "$GENIX_TARGET"
    echo "Genix skill installed to: $GENIX_TARGET"
fi

echo ""
echo "=== Install Complete ==="
echo "Python path: $VENV_NAME/bin/python"
