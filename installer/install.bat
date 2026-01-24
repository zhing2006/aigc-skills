@echo off
setlocal enabledelayedexpansion

REM Genix Skills Install Script

REM Parse arguments
set "TOOL=claude"
if not "%~1"=="" set "TOOL=%~1"

set "VENV_NAME=.venv-genix"

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

echo === Genix Skills Install ===
echo Target tool: %TOOL%

REM 1. Check/Install uv
echo.
echo [1/5] Checking uv installation...
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

REM 2. Create virtual environment if not exists
echo.
echo [2/5] Checking virtual environment (%VENV_NAME%)...
if not exist "%VENV_NAME%" (
    echo Creating Python 3.14 virtual environment...
    uv venv %VENV_NAME% --python 3.14
    echo Virtual environment created!
) else (
    echo Virtual environment already exists.
)

REM 3. Create .genix.env from template if not exists
echo.
echo [3/5] Checking .genix.env file...
if not exist ".genix.env" (
    if exist ".env.template" (
        copy ".env.template" ".genix.env" >nul
        echo .genix.env created from template. Please update with your API keys.
    ) else (
        echo Warning: .env.template not found, skipping .genix.env creation.
    )
) else (
    echo .genix.env already exists.
)

REM 4. Install dependencies
echo.
echo [4/5] Installing dependencies...
uv pip install --python "%VENV_NAME%\Scripts\python.exe" python-dotenv aiofiles aiohttp elevenlabs google-genai openai pillow tripo3d dashscope
echo Dependencies installed!

REM 5. Move genix to tool's skills directory
echo.
echo [5/5] Installing genix skill to %TOOL%...
set "GENIX_TARGET=%TARGET_DIR%\genix"

REM Check if source genix directory exists
if not exist "genix" (
    if exist "%GENIX_TARGET%" (
        echo Genix skill already installed at: %GENIX_TARGET%
    ) else (
        echo Error: genix directory not found. Please re-extract the package.
        exit /b 1
    )
) else (
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

    REM Move genix directory
    move "genix" "%GENIX_TARGET%" >nul
    echo Genix skill installed to: %GENIX_TARGET%
)

echo.
echo === Install Complete ===
echo Python path: %VENV_NAME%\Scripts\python.exe
endlocal
