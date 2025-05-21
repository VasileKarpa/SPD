.PHONY: start down build up

# Target por omissão
start: down build up
	@echo "Iniciando a aplicação..."

# Desliga e remove volumes
down:
	docker-compose down --volumes

# Recompila as imagens sem usar cache
build:
	docker compose build --no-cache

# Sobe os serviços em foreground
up:
	docker-compose up
