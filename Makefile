.PHONY: help install build up down dev logs clean restart shell-backend shell-frontend test

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 📦 Installer les dépendances
	@echo "📦 Installation des dépendances..."
	cd backend && pip install -r requirements.txt && playwright install chromium
	cd frontend && npm install

build: ## 🐳 Construire les images Docker
	@echo "🐳 Construction des images..."
	docker-compose build --no-cache

up: ## 🚀 Démarrer les conteneurs
	@echo "🚀 Démarrage des services..."
	docker-compose up -d
	@echo "✅ NexusDL 2.0 disponible sur http://localhost"

down: ## 🛑 Arrêter les conteneurs
	@echo "🛑 Arrêt des services..."
	docker-compose down

dev: ## 🔥 Démarrer en mode développement (logs en direct)
	@echo "🔥 Mode développement..."
	docker-compose up

logs: ## 📜 Voir les logs
	@echo "📜 Logs des conteneurs..."
	docker-compose logs -f

clean: ## 🧹 Nettoyer les conteneurs, volumes et données
	@echo "🧹 Nettoyage complet..."
	docker-compose down -v
	rm -rf data/downloads/* data/cache/* data/temp/* data/nexus.db
	rm -rf backend/__pycache__ frontend/node_modules

restart: down up ## 🔄 Redémarrer les conteneurs

shell-backend: ## 🐚 Shell dans le conteneur backend
	docker-compose exec backend /bin/bash

shell-frontend: ## 🐚 Shell dans le conteneur frontend
	docker-compose exec frontend /bin/sh

test: ## 🧪 Lancer les tests
	@echo "🧪 Tests en cours..."
	cd backend && pytest tests/ || echo "Tests non configurés"
