# =============================================================================
# ProjetIA-DevPro — Makefile
# Raccourcis pour le développement local. Tout passe par docker compose.
# =============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

# Couleurs
GREEN  := \033[32m
YELLOW := \033[33m
BLUE   := \033[34m
RESET  := \033[0m

# -----------------------------------------------------------------------------
# Help auto-généré à partir des commentaires `## ` après la cible
# -----------------------------------------------------------------------------
.PHONY: help
help: ## Affiche cette aide
	@echo ""
	@echo "$(BLUE)ProjetIA-DevPro — commandes disponibles$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Stack Docker
# =============================================================================

.PHONY: up
up: ## Lance toute la stack en arrière-plan
	docker compose up -d

.PHONY: up-light
up-light: ## Lance la stack légère (sans ComfyUI) — utile en dev rapide
	docker compose up -d postgres redis
	docker compose up -d gradio worker

.PHONY: down
down: ## Stoppe la stack (conserve les volumes)
	docker compose down

.PHONY: down-v
down-v: ## Stoppe la stack ET supprime les volumes (DB + Redis vidés !)
	docker compose down -v

.PHONY: build
build: ## (Re)build toutes les images
	docker compose build

.PHONY: rebuild
rebuild: ## Rebuild from scratch (no cache)
	docker compose build --no-cache

.PHONY: restart
restart: ## Restart tous les services
	docker compose restart

.PHONY: ps
ps: ## Liste les containers et leur état
	docker compose ps

# =============================================================================
# Logs
# =============================================================================

.PHONY: logs
logs: ## Suit les logs de tous les services (Ctrl+C pour quitter)
	docker compose logs -f --tail=100

.PHONY: logs-gradio
logs-gradio: ## Logs du service Gradio
	docker compose logs -f --tail=100 gradio

.PHONY: logs-worker
logs-worker: ## Logs du worker
	docker compose logs -f --tail=100 worker

.PHONY: logs-comfyui
logs-comfyui: ## Logs de ComfyUI
	docker compose logs -f --tail=100 comfyui

.PHONY: logs-db
logs-db: ## Logs de Postgres
	docker compose logs -f --tail=100 postgres

# =============================================================================
# Shells / debug
# =============================================================================

.PHONY: shell-gradio
shell-gradio: ## Shell dans le container Gradio
	docker compose exec gradio /bin/bash

.PHONY: shell-worker
shell-worker: ## Shell dans le container Worker
	docker compose exec worker /bin/bash

.PHONY: db-shell
db-shell: ## psql interactif sur la DB
	docker compose exec postgres psql -U $${POSTGRES_USER:-projetia} -d $${POSTGRES_DB:-projetia}

.PHONY: redis-cli
redis-cli: ## redis-cli interactif
	docker compose exec redis redis-cli

# =============================================================================
# Reset / nettoyage
# =============================================================================

.PHONY: reset-db
reset-db: ## Réinitialise la DB (recharge le schéma init)
	docker compose down postgres
	docker volume rm projetia-devpro_postgres-data 2>/dev/null || true
	docker compose up -d postgres

.PHONY: clean-images
clean-images: ## Vide le dossier des images générées (./data/images/*)
	find ./data/images -mindepth 1 -not -name '.gitkeep' -delete

# =============================================================================
# Scripts de test
# =============================================================================

.PHONY: test-comfyui
test-comfyui: ## Lance un test bout-en-bout de ComfyUIBackend (génère 1 image)
	docker compose exec worker python -m scripts.test_comfyui

.PHONY: test-mock
test-mock: ## Lance un test du MockBackend (génère 3 placeholders)
	docker compose exec worker python -m scripts.test_mock

.PHONY: test-db
test-db: ## Lance un test du repository DB (CRUD batches/images)
	docker compose exec worker python -m scripts.test_db

.PHONY: test-worker
test-worker: ## Lance un test bout-en-bout du worker (DB + Redis + backend)
	docker compose exec worker python -m scripts.test_worker

.PHONY: test-prompt-builder
test-prompt-builder: ## Affiche les prompts construits pour quelques combinaisons
	docker compose exec worker python -m scripts.test_prompt_builder

# =============================================================================
# Code (à activer plus tard quand on aura uv en local et les tests)
# =============================================================================

.PHONY: lint
lint: ## Lance ruff (lint + format check) dans le container worker
	docker compose exec worker ruff check src/
	docker compose exec worker ruff format --check src/

.PHONY: fix
fix: ## Auto-fix avec ruff
	docker compose exec worker ruff check --fix src/
	docker compose exec worker ruff format src/