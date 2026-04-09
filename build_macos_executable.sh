#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 -m pip install -r requirements.txt
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name status-report-form \
  --osx-bundle-identifier com.fazaleabbas.statusreport \
  status_report_form.py

if [[ -d "$SCRIPT_DIR/dist/status-report-form.app" ]]; then
  /usr/bin/ditto -c -k --keepParent "$SCRIPT_DIR/dist/status-report-form.app" "$SCRIPT_DIR/status-report-form-macos-app.zip"
  echo "Built app bundle: $SCRIPT_DIR/dist/status-report-form.app"
  echo "Built zip archive: $SCRIPT_DIR/status-report-form-macos-app.zip"
else
  echo "Build failed: app bundle not found in $SCRIPT_DIR/dist" >&2
  exit 1
fi

