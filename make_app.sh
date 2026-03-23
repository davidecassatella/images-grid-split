#!/bin/bash
# make_app.sh — Genera "Images Grid Split.app" completamente self-contained.
#               L'app copia dentro di sé tutto il necessario (Python, Pillow, rich)
#               e può essere spostata liberamente (es. /Applications/) senza
#               dipendere da file esterni al bundle.
#
# Requisiti: Python 3 disponibile come 'python3' nel PATH + pip
#
# Uso:
#   bash make_app.sh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Images Grid Split"
APP_DIR="$PROJECT_DIR/$APP_NAME.app"
CONTENTS="$APP_DIR/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"
LAUNCHER="$MACOS/$APP_NAME"

# Trova python3 (preferisce quello del venv di sviluppo se presente)
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PY="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PY="$(command -v python3)"
else
    echo "✗  python3 non trovato nel PATH." >&2
    exit 1
fi

echo "→ Uso Python: $PY  ($(\"$PY\" --version 2>&1))"

# ── ricostruisce sempre il bundle da zero ───────────────────────────────────────
echo "→ Pulizia bundle precedente…"
rm -rf "$APP_DIR"
mkdir -p "$MACOS" "$RESOURCES"

# ── genera icona se non esiste ancora nel progetto ─────────────────────────────
ICNS="$PROJECT_DIR/assets/icon.icns"
if [ ! -f "$ICNS" ]; then
    echo "→ Generazione icona…"
    "$PY" "$PROJECT_DIR/make_icon.py"
fi

# ── copia icona nelle Resources ─────────────────────────────────────────────────
if [ -f "$ICNS" ]; then
    cp "$ICNS" "$RESOURCES/AppIcon.icns"
fi

# ── copia sorgenti Python e assets nel bundle ───────────────────────────────────
echo "→ Copia sorgenti…"
cp "$PROJECT_DIR/split_kling.py"    "$RESOURCES/"
cp "$PROJECT_DIR/split_kling_ui.py" "$RESOURCES/"
cp -r "$PROJECT_DIR/assets"          "$RESOURCES/assets"

# ── crea un venv isolato DENTRO il bundle e installa le dipendenze ──────────────
echo "→ Creazione venv interno al bundle…"
"$PY" -m venv "$RESOURCES/venv" --copies

echo "→ Installazione dipendenze (Pillow, rich) nel bundle…"
"$RESOURCES/venv/bin/pip" install --quiet --upgrade pip
"$RESOURCES/venv/bin/pip" install --quiet Pillow rich

# ── Info.plist ──────────────────────────────────────────────────────────────────
cat > "$CONTENTS/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Images Grid Split</string>
    <key>CFBundleDisplayName</key>
    <string>Images Grid Split</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.images-grid-split</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>Images Grid Split</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.graphics-design</string>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
PLIST

# ── launcher — usa SOLO il Python bundled nel bundle stesso ────────────────────
# RESOURCES_DIR viene valutato a runtime, i placeholder sono lasciati letterali.
PYTHON_BIN="$RESOURCES/venv/bin/python"

cat > "$LAUNCHER" << LAUNCHER_SCRIPT
#!/bin/bash
# Launcher self-contained: tutto ciò che serve è dentro il bundle.
BUNDLE="\$(cd "\$(dirname "\$0")/../.." && pwd)"
RESOURCES="\$BUNDLE/Contents/Resources"
PYTHON="\$RESOURCES/venv/bin/python"

if [ ! -x "\$PYTHON" ]; then
    osascript -e "display alert \"Errore avvio\" message \\
\"Python bundled non trovato in:\n\$PYTHON\n\nRigenera il bundle con: bash make_app.sh\""
    exit 1
fi

exec "\$PYTHON" "\$RESOURCES/split_kling.py" ui
LAUNCHER_SCRIPT

chmod +x "$LAUNCHER"

# ── aggiorna timestamp per svuotare cache icone macOS ──────────────────────────
touch "$APP_DIR"

echo ""
echo "✓  Bundle self-contained creato:"
echo "   $APP_DIR"
echo ""
echo "   Puoi spostarlo liberamente (es. /Applications/) senza bisogno"
echo "   della cartella di progetto o di un venv esterno."
echo ""
echo "   Dimensione bundle:"
du -sh "$APP_DIR"
echo ""
