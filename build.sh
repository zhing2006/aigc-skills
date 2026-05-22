#!/usr/bin/env bash
# build.sh - Package genix skill for distribution
set -euo pipefail

OUTPUT_NAME="${1:-genix-skills.zip}"
[[ "$OUTPUT_NAME" == *.zip ]] || OUTPUT_NAME="${OUTPUT_NAME}.zip"

cd "$(dirname "$0")"

rm -f "$OUTPUT_NAME"

cp LICENSE genix/LICENSE
trap 'rm -f genix/LICENSE install.ps1 install.bat install.sh' EXIT

zip -r "$OUTPUT_NAME" genix .env.template

cp installer/install.ps1 installer/install.bat installer/install.sh .
zip "$OUTPUT_NAME" install.ps1 install.bat install.sh

echo "Created: $OUTPUT_NAME"
