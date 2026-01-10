# pack.ps1 - Package genix skill for distribution

$zipName = "genix-package.zip"

# 1. Remove existing zip file
if (Test-Path $zipName) {
    Remove-Item $zipName
}

# 2. Compress genix directory
Compress-Archive -Path "genix" -DestinationPath $zipName

# 3. Add .env.template to root
Compress-Archive -Path ".env.template" -Update -DestinationPath $zipName

# 4. Add LICENSE inside genix directory
Copy-Item "LICENSE" -Destination "genix\LICENSE"
Compress-Archive -Path "genix" -Update -DestinationPath $zipName
Remove-Item "genix\LICENSE"

# 5. Add install scripts to root (copy from installer, then add, then cleanup)
Copy-Item "installer\install.ps1" -Destination "install.ps1"
Copy-Item "installer\install.bat" -Destination "install.bat"
Copy-Item "installer\install.sh" -Destination "install.sh"
Compress-Archive -Path "install.ps1", "install.bat", "install.sh" -Update -DestinationPath $zipName
Remove-Item "install.ps1", "install.bat", "install.sh"

Write-Host "Created: $zipName"
