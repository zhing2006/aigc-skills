# Genix Skills Setup Script
# Initialize Python development environment

param(
    [ValidateSet("claude", "cursor", "codex", "opencode", "vscode")]
    [string]$Tool = "claude"
)

$ErrorActionPreference = "Stop"

# Skills directory mapping for each tool
$SkillsDirectories = @{
    "claude"   = ".claude\skills"
    "cursor"   = ".cursor\skills"
    "codex"    = ".codex\skills"
    "opencode" = ".claude\skills"  # OpenCode uses Claude skills directory
    "vscode"   = ".claude\skills"  # VSCode uses Claude skills directory
}

Write-Host "=== Genix Skills Setup ===" -ForegroundColor Cyan
Write-Host "Target tool: $Tool" -ForegroundColor Cyan

# 1. Check/Install uv
Write-Host "`n[1/6] Checking uv installation..." -ForegroundColor Yellow
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing uv..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression

    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "Error: uv installation failed. Please restart terminal and try again." -ForegroundColor Red
        exit 1
    }
    Write-Host "uv installed successfully!" -ForegroundColor Green
} else {
    $uvVersion = uv --version
    Write-Host "uv is already installed: $uvVersion" -ForegroundColor Green
}

# 2. Create pyproject.toml if not exists
Write-Host "`n[2/6] Checking pyproject.toml..." -ForegroundColor Yellow
if (!(Test-Path "pyproject.toml")) {
    Write-Host "Creating pyproject.toml with Python 3.14..." -ForegroundColor Yellow
    uv init --bare --python 3.14
    Write-Host "pyproject.toml created!" -ForegroundColor Green
} else {
    Write-Host "pyproject.toml already exists." -ForegroundColor Green
}

# 3. Create virtual environment if not exists
Write-Host "`n[3/6] Checking virtual environment..." -ForegroundColor Yellow
if (!(Test-Path ".venv")) {
    Write-Host "Creating Python 3.14 virtual environment..." -ForegroundColor Yellow
    uv venv --python 3.14
    Write-Host "Virtual environment created!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# 4. Create .env from template if not exists
Write-Host "`n[4/6] Checking .env file..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    if (Test-Path ".env.template") {
        Copy-Item ".env.template" ".env"
        Write-Host ".env created from template. Please update with your API keys." -ForegroundColor Green
    } else {
        Write-Host "Warning: .env.template not found, skipping .env creation." -ForegroundColor Yellow
    }
} else {
    Write-Host ".env already exists." -ForegroundColor Green
}

# 5. Install dependencies
Write-Host "`n[5/6] Installing dependencies..." -ForegroundColor Yellow
uv add python-dotenv asyncio aiofiles aiohttp elevenlabs google-genai openai pillow -U --link-mode=copy
Write-Host "Dependencies installed!" -ForegroundColor Green

# 6. Copy genix to tool's skills directory
Write-Host "`n[6/6] Installing genix skill to $Tool..." -ForegroundColor Yellow
$targetDir = $SkillsDirectories[$Tool]
$genixTarget = Join-Path $targetDir "genix"

# Create skills directory if not exists
if (!(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "Created skills directory: $targetDir" -ForegroundColor Gray
}

# Remove existing genix skill if exists
if (Test-Path $genixTarget) {
    Remove-Item -Path $genixTarget -Recurse -Force
    Write-Host "Removed existing genix skill." -ForegroundColor Gray
}

# Copy genix directory
Copy-Item -Path "genix" -Destination $genixTarget -Recurse
Write-Host "Genix skill installed to: $genixTarget" -ForegroundColor Green

# Done
Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
