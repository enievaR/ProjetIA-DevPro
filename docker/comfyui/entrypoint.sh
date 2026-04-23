#!/usr/bin/env bash
set -euo pipefail

MODELS_DIR="/app/ComfyUI/models/checkpoints"
MODEL_FILE="dreamshaper_8.safetensors"
MODEL_URL="https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"
MIN_SIZE=2000000000  # 2 Go minimum (le vrai fichier fait ~2.13 Go)

mkdir -p "${MODELS_DIR}"

# Si le fichier existe mais est trop petit, on le supprime (téléchargement précédent corrompu)
if [[ -f "${MODELS_DIR}/${MODEL_FILE}" ]]; then
    SIZE=$(stat -c%s "${MODELS_DIR}/${MODEL_FILE}")
    if [[ "${SIZE}" -lt "${MIN_SIZE}" ]]; then
        echo "[entrypoint] Modèle présent mais incomplet (${SIZE} octets), suppression."
        rm -f "${MODELS_DIR}/${MODEL_FILE}"
    fi
fi

if [[ ! -f "${MODELS_DIR}/${MODEL_FILE}" ]]; then
    echo "[entrypoint] Modèle absent, téléchargement de DreamShaper 8 (~2.13 Go)..."
    # -C - : reprise de téléchargement partiel si possible
    # --retry 5 + delay : robustesse réseau
    # -f : échec sur HTTP 4xx/5xx (au lieu de sauver une page d'erreur)
    curl -fL --retry 5 --retry-delay 5 -C - \
        -o "${MODELS_DIR}/${MODEL_FILE}" \
        "${MODEL_URL}"
    echo "[entrypoint] Téléchargement terminé."
else
    echo "[entrypoint] Modèle déjà présent, on skip le téléchargement."
fi

echo "[entrypoint] Démarrage de ComfyUI sur 0.0.0.0:8188 (CPU)"
exec python main.py --listen 0.0.0.0 --port 8188 --cpu