# build.ps1 - Package genix skill for distribution

param(
    [string]$OutputName = "genix-skills.zip"
)

# Ensure .zip extension
if (-not $OutputName.EndsWith(".zip")) {
    $OutputName = "$OutputName.zip"
}

# 1. Remove existing zip file
if (Test-Path $OutputName) {
    Remove-Item $OutputName
}

# 2. Compress genix directory
Compress-Archive -Path "genix" -DestinationPath $OutputName

# 3. Add .env.template to root
Compress-Archive -Path ".env.template" -Update -DestinationPath $OutputName

# 4. Add LICENSE inside genix directory
Copy-Item "LICENSE" -Destination "genix\LICENSE"
Compress-Archive -Path "genix" -Update -DestinationPath $OutputName
Remove-Item "genix\LICENSE"

# 5. Add install scripts to root (copy from installer, then add, then cleanup)
Copy-Item "installer\install.ps1" -Destination "install.ps1"
Copy-Item "installer\install.bat" -Destination "install.bat"
Copy-Item "installer\install.sh" -Destination "install.sh"
Compress-Archive -Path "install.ps1", "install.bat", "install.sh" -Update -DestinationPath $OutputName
Remove-Item "install.ps1", "install.bat", "install.sh"

Write-Host "Created: $OutputName"
