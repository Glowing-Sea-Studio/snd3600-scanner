#!/usr/bin/env bash

# Permet de démarrer le script depuis le dossier courant, sans l'installer.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Démarrage de SND 3600 Scanner..."
exec python3 "$SCRIPT_DIR/snd3600-scanner.py" "$@"

