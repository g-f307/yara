.PHONY: help train shell actions test clean install

help:
	@echo "🧬 YARA - Comandos Disponíveis"
	@echo ""
	@echo "  make install   - Instala dependências"
	@echo "  make train     - Treina modelo Rasa"
	@echo "  make shell     - Chat interativo"
	@echo "  make actions   - Servidor de actions"
	@echo "  make test      - Testa modelo"
	@echo "  make clean     - Limpa cache"
	@echo ""

install:
	@echo "📦 Instalando dependências..."
	pip install -r requirements.txt

train:
	@echo "🎓 Treinando modelo..."
	rasa train

shell:
	@echo "💬 Iniciando chat..."
	rasa shell

actions:
	@echo "⚡ Iniciando servidor de actions..."
	rasa run actions

test:
	@echo "🧪 Testando modelo..."
	rasa test

clean:
	@echo "🧹 Limpando cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".rasa" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Limpeza concluída!"
