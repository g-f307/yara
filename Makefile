.PHONY: help dev test clean install docker-up docker-down docker-build

PYTHON=python

help:
	@echo "🧬 YARA — Comandos Disponíveis"
	@echo ""
	@echo "  make install      - Instala dependências do python-core"
	@echo "  make dev          - Inicia servidor FastAPI (desenvolvimento)"
	@echo "  make test         - Testa imports e endpoints"
	@echo "  make clean        - Limpa cache"
	@echo ""
	@echo "  make docker-up    - Sobe frontend + python-core via Docker"
	@echo "  make docker-down  - Para containers"
	@echo "  make docker-build - Rebuilda imagens"
	@echo ""

install:
	@echo "📦 Instalando dependências..."
	cd backend && pip install -r requirements.txt

dev:
	@echo "🚀 Iniciando FastAPI..."
	cd backend && $(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "🧪 Testando imports..."
	cd backend && $(PYTHON) -c "\
		from analysis.qiime_parser import QIIME2Parser; \
		from analysis.alpha_diversity import AlphaDiversityAnalyzer; \
		from analysis.beta_diversity import BetaDiversityAnalyzer; \
		from analysis.rarefaction import RarefactionAnalyzer; \
		from analysis.statistics import calculate_kruskal_wallis; \
		from analysis.report_generator import ReportGenerator; \
		print('✅ Todos os imports OK')"

clean:
	@echo "🧹 Limpando cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Limpeza concluída!"

docker-up:
	@echo "🐳 Subindo containers..."
	docker compose up -d

docker-down:
	@echo "🐳 Parando containers..."
	docker compose down

docker-build:
	@echo "🐳 Rebuilding imagens..."
	docker compose build --no-cache
