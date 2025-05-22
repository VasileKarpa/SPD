#!/usr/bin/env bash
set -e

echo "🛑 Parando todos os serviços e removendo volumes..."
docker-compose down --volumes

echo "🛠️  Recompilando imagens sem usar cache..."
docker compose build --no-cache

echo "🚀 A arrancar os serviços em foreground..."
docker-compose up
