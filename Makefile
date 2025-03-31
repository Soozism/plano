.PHONY: build up down logs shell test lint format clean help

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start Docker containers"
	@echo "  make down     - Stop Docker containers"
	@echo "  make logs     - View Docker container logs"
	@echo "  make shell    - Open shell in API container"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run code linting"
	@echo "  make format   - Format code"
	@echo "  make clean    - Remove Docker containers and volumes"

build:
	docker-compose -f docker/docker-compose.yml build

up:
	docker-compose -f docker/docker-compose.yml up -d

down:
	docker-compose -f docker/docker-compose.yml down

logs:
	docker-compose -f docker/docker-compose.yml logs -f

shell:
	docker-compose -f docker/docker-compose.yml exec api /bin/bash

test:
	docker-compose -f docker/docker-compose.yml exec api pytest

lint:
	docker-compose -f docker/docker-compose.yml exec api flake8 .

format:
	docker-compose -f docker/docker-compose.yml exec api black .
	docker-compose -f docker/docker-compose.yml exec api isort .

clean:
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f 