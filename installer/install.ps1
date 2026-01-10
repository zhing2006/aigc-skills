# Genix Skills Install Script

param(
    [ValidateSet("claude", "cursor", "codex", "opencode", "vscode")]
    [string]$Tool = "claude"
)

$ErrorActionPreference = "Stop"

$VenvName = ".venv-genix"

# Skills directory mapping for each tool
$SkillsDirectories = @{
    "claude"   = ".claude\skills"
    "cursor"   = ".cursor\skills"
    "codex"    = ".codex\skills"
    "opencode" = ".claude\skills"  # OpenCode uses Claude skills directory
    "vscode"   = ".claude\skills"  # VSCode uses Claude skills directory
}

Write-Host "=== Genix Skills Install ===" -ForegroundColor Cyan
Write-Host "Target tool: $Tool" -ForegroundColor Cyan

# 1. Check/Install uv
Write-Host "`n[1/5] Checking uv installation..." -ForegroundColor Yellow
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

# 2. Create virtual environment if not exists
Write-Host "`n[2/5] Checking virtual environment ($VenvName)..." -ForegroundColor Yellow
if (!(Test-Path $VenvName)) {
    Write-Host "Creating Python 3.14 virtual environment..." -ForegroundColor Yellow
    uv venv $VenvName --python 3.14
    Write-Host "Virtual environment created!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# 3. Create .env from template if not exists
Write-Host "`n[3/5] Checking .env file..." -ForegroundColor Yellow
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

# 4. Install dependencies
Write-Host "`n[4/5] Installing dependencies..." -ForegroundColor Yellow
uv pip install --python "$VenvName\Scripts\python.exe" python-dotenv aiofiles aiohttp elevenlabs google-genai openai pillow
Write-Host "Dependencies installed!" -ForegroundColor Green

# 5. Move genix to tool's skills directory
Write-Host "`n[5/5] Installing genix skill to $Tool..." -ForegroundColor Yellow
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

# Move genix directory (instead of copy)
Move-Item -Path "genix" -Destination $genixTarget
Write-Host "Genix skill installed to: $genixTarget" -ForegroundColor Green

# Done
Write-Host "`n=== Install Complete ===" -ForegroundColor Cyan
Write-Host "Python path: $VenvName\Scripts\python.exe" -ForegroundColor Gray
