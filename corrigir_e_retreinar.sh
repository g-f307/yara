#!/bin/bash
# Script de Correção e Retreinamento - YARA
# Corrige problemas de reconhecimento de intents e retreina o modelo

echo "🔧 YARA - Correção e Retreinamento"
echo "===================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Verificar ambiente
echo "1️⃣ Verificando ambiente..."
if [[ "$CONDA_DEFAULT_ENV" != "yara_rasa" ]]; then
    echo -e "${RED}❌ Ambiente errado!${NC}"
    echo -e "${YELLOW}Execute: conda activate yara_rasa${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Ambiente yara_rasa ativo${NC}"
echo ""

# 2. Verificar arquivos de configuração
echo "2️⃣ Verificando arquivos de configuração..."

required_files=(
    "config.yml"
    "domain.yml"
    "data/nlu.yml"
    "data/stories.yml"
    "data/rules.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓${NC} $file"
    else
        echo -e "${RED}  ✗${NC} $file - FALTANDO"
        exit 1
    fi
done
echo ""

# 3. Verificar rules
echo "3️⃣ Verificando rules..."
if grep -q "action_analisar_rarefacao" data/rules.yml && \
   grep -q "action_exportar_relatorio" data/rules.yml && \
   grep -q "action_comparar_grupos" data/rules.yml && \
   grep -q "action_mostrar_grupos_taxonomicos" data/rules.yml; then
    echo -e "${GREEN}✅ Todas as rules estão configuradas${NC}"
else
    echo -e "${RED}❌ Rules incompletas!${NC}"
    echo -e "${YELLOW}Execute o script de correção primeiro${NC}"
    exit 1
fi
echo ""

# 4. Limpar modelos antigos
echo "4️⃣ Limpando modelos antigos..."
if [ -d "models" ]; then
    model_count=$(ls -1 models/*.tar.gz 2>/dev/null | wc -l)
    if [ $model_count -gt 0 ]; then
        echo -e "${YELLOW}  Encontrados $model_count modelos antigos${NC}"
        read -p "  Deseja remover modelos antigos? (s/N): " response
        if [[ "$response" =~ ^[Ss]$ ]]; then
            rm -f models/*.tar.gz
            echo -e "${GREEN}  ✓ Modelos antigos removidos${NC}"
        else
            echo -e "${BLUE}  ⊙ Mantendo modelos antigos${NC}"
        fi
    else
        echo -e "${BLUE}  ⊙ Nenhum modelo antigo encontrado${NC}"
    fi
else
    mkdir -p models
    echo -e "${GREEN}  ✓ Diretório models/ criado${NC}"
fi
echo ""

# 5. Validar configuração
echo "5️⃣ Validando configuração Rasa..."
rasa data validate --domain domain.yml --data data/ 2>&1 | tee /tmp/rasa_validate.log

if grep -q "error" /tmp/rasa_validate.log; then
    echo -e "${RED}❌ Erros encontrados na validação!${NC}"
    echo -e "${YELLOW}Verifique o log acima${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Configuração válida${NC}"
fi
echo ""

# 6. Treinar modelo
echo "6️⃣ Treinando novo modelo..."
echo -e "${BLUE}Isso pode levar 2-5 minutos...${NC}"
echo ""

rasa train --domain domain.yml --config config.yml --data data/

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Modelo treinado com sucesso!${NC}"
else
    echo ""
    echo -e "${RED}❌ Erro no treinamento!${NC}"
    exit 1
fi
echo ""

# 7. Verificar modelo gerado
echo "7️⃣ Verificando modelo gerado..."
latest_model=$(ls -t models/*.tar.gz 2>/dev/null | head -1)

if [ -n "$latest_model" ]; then
    model_size=$(du -h "$latest_model" | cut -f1)
    echo -e "${GREEN}✅ Modelo gerado: $latest_model${NC}"
    echo -e "${BLUE}   Tamanho: $model_size${NC}"
else
    echo -e "${RED}❌ Nenhum modelo encontrado!${NC}"
    exit 1
fi
echo ""

# 8. Resumo
echo "===================================="
echo -e "${GREEN}✅ CORREÇÃO E RETREINAMENTO CONCLUÍDOS!${NC}"
echo "===================================="
echo ""
echo "📊 Resumo:"
echo "  • Arquivos validados: ${#required_files[@]}"
echo "  • Rules configuradas: 11"
echo "  • Modelo treinado: $(basename $latest_model)"
echo ""
echo "🚀 Próximos passos:"
echo ""
echo "  Terminal 1 - Iniciar actions server:"
echo -e "  ${BLUE}make actions${NC}"
echo ""
echo "  Terminal 2 - Iniciar chat:"
echo -e "  ${BLUE}make shell${NC}"
echo ""
echo "💬 Testes sugeridos:"
echo "  • 'quais dados tenho disponíveis?'"
echo "  • 'analisa rarefação'"
echo "  • 'quais os grupos mais abundantes?'"
echo "  • 'exporta relatório'"
echo "  • 'como comparar grupos?'"
echo "  • 'o que é diversidade beta?'"
echo "  • 'mostra taxonomia'"
echo ""
echo "📚 Documentação:"
echo "  • GUIA_TESTE.md - Guia completo de testes"
echo "  • IMPLEMENTACOES_REALIZADAS.md - Documentação técnica"
echo ""
