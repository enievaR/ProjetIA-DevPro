#!/usr/bin/env bash
set -euo pipefail

MODELS_DIR="/app/ComfyUI/models/checkpoints"
MODEL_FILE="dreamshaper_xl_turbo_v2.safetensors"
MODEL_URL="https://huggingface.co/Lykon/dreamshaper-xl-v2-turbo/resolve/main/DreamShaperXL_Turbo_v2.safetensors"
MIN_SIZE=6500000000  # 6.5 Go minimum

# Threads CPU : par défaut PyTorch n'utilise qu'une fraction. On force le max.
# Configurable via env var COMFYUI_THREADS, sinon utilise tous les CPU dispo.
THREADS="${COMFYUI_THREADS:-$(nproc)}"
export OMP_NUM_THREADS="${THREADS}"
export MKL_NUM_THREADS="${THREADS}"

echo "[entrypoint] Threads CPU : ${THREADS}"

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
    echo "[entrypoint] Modèle absent, téléchargement de DreamShaper XL Turbo v2 (~6.94 Go)..."
    curl -fL --retry 5 --retry-delay 5 -C - --progress-bar \
        -o "${MODELS_DIR}/${MODEL_FILE}" \
        "${MODEL_URL}"
    echo "[entrypoint] Téléchargement terminé."
else
    echo "[entrypoint] Modèle déjà présent, on skip le téléchargement."
fi

echo "[entrypoint] Démarrage de ComfyUI sur 0.0.0.0:8188 (CPU)"
exec python main.py --listen 0.0.0.0 --port 8188 --cpu