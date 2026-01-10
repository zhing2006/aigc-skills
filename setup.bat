@echo off
setlocal enabledelayedexpansion

REM Genix Skills Setup Script
REM Initialize Python development environment

REM Parse arguments
set "TOOL=claude"
if not "%~1"=="" set "TOOL=%~1"

REM Validate tool argument
if not "%TOOL%"=="claude" if not "%TOOL%"=="cursor" if not "%TOOL%"=="codex" if not "%TOOL%"=="opencode" if not "%TOOL%"=="vscode" (
    echo Error: Invalid tool. Supported: claude, cursor, codex, opencode, vscode
    exit /b 1
)

REM Skills directory mapping
if "%TOOL%"=="claude" set "TARGET_DIR=.claude\skills"
if "%TOOL%"=="cursor" set "TARGET_DIR=.cursor\skills"
if "%TOOL%"=="codex" set "TARGET_DIR=.codex\skills"
if "%TOOL%"=="opencode" set "TARGET_DIR=.claude\skills"
if "%TOOL%"=="vscode" set "TARGET_DIR=.claude\skills"

echo === Genix Skills Setup ===
echo Target tool: %TOOL%

REM 1. Check/Install uv
echo.
echo [1/6] Checking uv installation...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo uv not found. Installing uv...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo Error: uv installation failed. Please restart terminal and try again.
        exit /b 1
    )
    echo uv installed successfully!
) else (
    for /f "tokens=*" %%i in ('uv --version') do echo uv is already installed: %%i
)

REM 2. Create pyproject.toml if not exists
echo.
echo [2/6] Checking pyproject.toml...
if not exist "pyproject.toml" (
    echo Creating pyproject.toml with Python 3.14...
    uv init --bare --python 3.14
    echo pyproject.toml created!
) else (
    echo pyproject.toml already exists.
)

REM 3. Create virtual environment if not exists
echo.
echo [3/6] Checking virtual environment...
if not exist ".venv" (
    echo Creating Python 3.14 virtual environment...
    uv venv --python 3.14
    echo Virtual environment created!
) else (
    echo Virtual environment already exists.
)

REM 4. Create .env from template if not exists
echo.
echo [4/6] Checking .env file...
if not exist ".env" (
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo .env created from template. Please update with your API keys.
    ) else (
        echo Warning: .env.template not found, skipping .env creation.
    )
) else (
    echo .env already exists.
)

REM 5. Install dependencies
echo.
echo [5/6] Installing dependencies...
uv add python-dotenv asyncio elevenlabs google-genai openai pillow -U --link-mode=copy
echo Dependencies installed!

REM 6. Copy genix to tool's skills directory
echo.
echo [6/6] Installing genix skill to %TOOL%...
set "GENIX_TARGET=%TARGET_DIR%\genix"

REM Create skills directory if not exists
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
    echo Created skills directory: %TARGET_DIR%
)

REM Remove existing genix skill if exists
if exist "%GENIX_TARGET%" (
    rmdir /s /q "%GENIX_TARGET%"
    echo Removed existing genix skill.
)

REM Copy genix directory
xcopy "genix" "%GENIX_TARGET%" /e /i /q >nul
echo Genix skill installed to: %GENIX_TARGET%

echo.
echo === Setup Complete ===
endlocal
