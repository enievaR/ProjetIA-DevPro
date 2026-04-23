# ProjetIA-DevPro

Générateur d'images IA — MVP école.

Service de génération d'images par texte basé sur **Stable Diffusion (SD-Turbo)**, accessible via une interface web. L'utilisateur saisit une description en langage naturel et choisit un style, une ambiance et un cadrage. Le système génère un lot d'images sans exposer aucun paramètre technique.

## Architecture

5 services communiquant via une queue Redis et une base Postgres partagée :

| Service | Rôle |
|---|---|
| `gradio` | UI web + soumission des jobs |
| `worker` | Orchestration : dépile Redis, construit le prompt enrichi, appelle ComfyUI |
| `comfyui` | Moteur d'inférence (SD-Turbo en CPU) |
| `redis` | Queue de jobs |
| `postgres` | Persistance des batches et images |

Le worker dépend d'une abstraction `InferenceBackend` (pattern d'inversion de dépendance) qui permet de remplacer ComfyUI par un backend distant (ex. RunPod) sans modifier le code d'orchestration.

## Démarrage rapide

```bash
cp .env.example .env
docker compose up -d
```

UI accessible sur http://localhost:7860

## Stack technique

- **Langage** : Python 3.12 (uv pour la gestion des dépendances)
- **UI** : Gradio 4.x
- **Queue** : Redis 7 + arq
- **DB** : Postgres 16 (asyncpg)
- **Inférence** : ComfyUI + SD-Turbo
- **Conteneurisation** : Docker Compose (dev), Kubernetes (prod, sprint 3)