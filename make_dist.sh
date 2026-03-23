#!/bin/bash
# make_dist.sh — Build distribuibile per macOS (PyInstaller + DMG).
#
# Genera:
#   dist/Images Grid Split.app   ← app completamente self-contained
#   dist/Images Grid Split.dmg   ← installer da caricare su GitHub Releases
#
# Requisiti (solo per il build, non per l'utente finale):
#   • Python 3 + .venv configurato  (bash make_app.sh crea il venv)
#   • Xcode Command Line Tools      (xcode-select --install)
#
# Uso:
#   bash make_dist.sh
#
# Per pubblicare su GitHub:
#   1. Esegui questo script → ottieni dist/Images Grid Split.dmg
#   2. Crea una Release su GitHub e carica il .dmg come asset
#   3. Gli utenti scaricano il .dmg, lo aprono e trascinano l'app in /Applications/

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Images Grid Split"
VERSION="1.0"

# ── venv di sviluppo ──────────────────────────────────────────────────────────
VENV="$PROJECT_DIR/.venv"
if [ ! -d "$VENV" ]; then
    echo "✗  .venv non trovato. Crea prima l'ambiente di sviluppo:" >&2
    echo "   python3 -m venv .venv" >&2
    echo "   source .venv/bin/activate" >&2
    echo "   pip install -r requirements.txt" >&2
    exit 1
fi
source "$VENV/bin/activate"

# ── dipendenze build ──────────────────────────────────────────────────────────
echo "→ Verifica dipendenze build…"
pip install --quiet pyinstaller Pillow rich

# ── icona ─────────────────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/assets/icon.icns" ]; then
    echo "→ Generazione icona…"
    python "$PROJECT_DIR/make_icon.py"
fi

# ── pulizia ───────────────────────────────────────────────────────────────────
echo "→ Pulizia build precedente…"
rm -rf "$PROJECT_DIR/build" "$PROJECT_DIR/dist" "$PROJECT_DIR"/*.spec

# ── PyInstaller build ─────────────────────────────────────────────────────────
echo "→ Build con PyInstaller (può richiedere qualche minuto)…"
cd "$PROJECT_DIR"
pyinstaller \
    --windowed \
    --name "$APP_NAME" \
    --icon "assets/icon.icns" \
    --add-data "assets:assets" \
    --add-data "split_kling.py:." \
    --hidden-import "PIL._tkinter_finder" \
    --collect-all "PIL" \
    --collect-all "rich" \
    --noconfirm \
    --clean \
    launcher.py

# ── verifica ─────────────────────────────────────────────────────────────────
APP_PATH="$PROJECT_DIR/dist/$APP_NAME.app"
if [ ! -d "$APP_PATH" ]; then
    echo "✗  Build fallita: $APP_PATH non trovato." >&2
    exit 1
fi
echo "✓  App costruita: $(du -sh "$APP_PATH" | cut -f1)"

# ── crea DMG ─────────────────────────────────────────────────────────────────
echo "→ Creazione DMG…"
DMG_TMP="$PROJECT_DIR/dist/${APP_NAME}_tmp.dmg"
DMG_OUT="$PROJECT_DIR/dist/${APP_NAME}_v${VERSION}.dmg"

# Crea una cartella staging con l'app + symlink ad /Applications
STAGING="$PROJECT_DIR/dist/_dmg_staging"
rm -rf "$STAGING"
mkdir "$STAGING"
cp -r "$APP_PATH" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

# Crea il DMG compresso
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$STAGING" \
    -ov \
    -format UDZO \
    -imagekey zlib-level=9 \
    "$DMG_OUT"

rm -rf "$STAGING"

echo ""
echo "════════════════════════════════════════════"
echo "✓  Build completata!"
echo ""
echo "   App : dist/$APP_NAME.app   ($(du -sh "$APP_PATH" | cut -f1))"
echo "   DMG : dist/${APP_NAME}_v${VERSION}.dmg   ($(du -sh "$DMG_OUT" | cut -f1))"
echo ""
echo "   Per pubblicare su GitHub:"
echo "   1. Vai su github.com → tuo repo → Releases → New Release"
echo "   2. Tag: v${VERSION}"
echo "   3. Carica come asset: dist/${APP_NAME}_v${VERSION}.dmg"
echo ""
echo "   Gli utenti potranno:"
echo "   • Scaricare il .dmg"
echo "   • Aprirlo e trascinare l'app in /Applications"
echo "   • Avviarla con doppio clic — nessun Python necessario"
echo "════════════════════════════════════════════"
