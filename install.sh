#!/usr/bin/env bash
set -e

echo "Installation des dépendances SND 3600 Scanner..."

sudo apt update
sudo apt install -y python3 python3-tk python3-opencv python3-pil python3-pil.imagetk v4l-utils

INSTALL_DIR="$HOME/.local/share/snd3600-scanner"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"

echo "Copie des fichiers (écrase l'ancienne version)..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$APP_DIR"

# -f pour forcer l'écrasement
cp -f "$(dirname "$0")/snd3600-scanner.py" "$INSTALL_DIR/snd3600-scanner.py"
chmod +x "$INSTALL_DIR/snd3600-scanner.py"

# Installation du raccourci bureau
if [ -f "$(dirname "$0")/snd3600-scanner.desktop" ]; then
    cp -f "$(dirname "$0")/snd3600-scanner.desktop" "$APP_DIR/"
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

cat > "$BIN_DIR/snd3600-scanner" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/snd3600-scanner.py" "\$@"
EOF
chmod +x "$BIN_DIR/snd3600-scanner"

echo
echo "Installation terminée."
echo "Lancement avec : snd3600-scanner"
echo
echo "Si la commande n'est pas trouvée, ouvre un nouveau terminal"
echo "ou ajoute ~/.local/bin à PATH."
