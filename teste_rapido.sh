#!/bin/bash
# Script de Teste Rápido - YARA
# Testa todas as funcionalidades principais

echo "🧬 YARA - Teste Rápido de Funcionalidades"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar sucesso
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 - FALHOU${NC}"
        exit 1
    fi
}

# 1. Verificar se dados existem
echo "1️⃣ Verificando dados de teste..."
if [ -f "data/qiime2/diversidade_alfa.tsv" ] && \
   [ -f "data/qiime2/rarefaction.tsv" ] && \
   [ -f "data/qiime2/taxonomy.tsv" ]; then
    check_success "Dados de teste encontrados"
else
    echo -e "${YELLOW}⚠️  Dados não encontrados. Gerando...${NC}"
    python3 gerar_dados_teste.py
    check_success "Dados gerados"
fi
echo ""

# 2. Testar importação de módulos
echo "2️⃣ Testando importação de módulos Python..."
python3 -c "from actions.utils.rarefaction_analyzer import RarefactionAnalyzer; print('rarefaction_analyzer OK')" 2>/dev/null
check_success "Módulo rarefaction_analyzer"

python3 -c "from actions.utils.report_generator import ReportGenerator; print('report_generator OK')" 2>/dev/null
check_success "Módulo report_generator"

python3 -c "from actions.utils.qiime_parser_module import QIIME2Parser; print('qiime_parser OK')" 2>/dev/null
check_success "Módulo qiime_parser"
echo ""

# 3. Testar análise de rarefação
echo "3️⃣ Testando análise de rarefação..."
python3 << 'EOF'
from actions.utils.rarefaction_analyzer import analyze_rarefaction_file
results = analyze_rarefaction_file('data/qiime2/rarefaction.tsv')
assert 'stats' in results
assert 'recommendation' in results
assert 'interpretation' in results
print("Análise de rarefação OK")
EOF
check_success "Análise de rarefação"
echo ""

# 4. Testar geração de relatório
echo "4️⃣ Testando geração de relatórios..."
python3 << 'EOF'
from actions.utils.report_generator import create_comprehensive_report
analyses = {
    'alpha': 'Teste de diversidade alfa',
    'beta': 'Teste de diversidade beta',
    'taxonomy': 'Teste de taxonomia'
}
md_path = create_comprehensive_report(analyses, output_format='markdown')
html_path = create_comprehensive_report(analyses, output_format='html')
import os
assert os.path.exists(md_path)
assert os.path.exists(html_path)
print(f"Relatórios gerados: {md_path}, {html_path}")
EOF
check_success "Geração de relatórios"
echo ""

# 5. Verificar arquivos de configuração Rasa
echo "5️⃣ Verificando configuração Rasa..."
if grep -q "action_analisar_rarefacao" domain.yml; then
    check_success "domain.yml atualizado"
else
    echo -e "${RED}❌ domain.yml não contém novas actions${NC}"
    exit 1
fi

if grep -q "analisar_rarefacao" data/nlu.yml; then
    check_success "nlu.yml atualizado"
else
    echo -e "${RED}❌ nlu.yml não contém novos intents${NC}"
    exit 1
fi

if grep -q "análise de rarefação" data/stories.yml; then
    check_success "stories.yml atualizado"
else
    echo -e "${RED}❌ stories.yml não contém novas stories${NC}"
    exit 1
fi
echo ""

# 6. Verificar estrutura de diretórios
echo "6️⃣ Verificando estrutura de diretórios..."
required_dirs=("actions" "actions/utils" "data" "data/qiime2" "notebooks" "models")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}  ✓${NC} $dir/"
    else
        echo -e "${RED}  ✗${NC} $dir/ - FALTANDO"
        exit 1
    fi
done
echo ""

# 7. Contar arquivos criados
echo "7️⃣ Resumo de arquivos..."
echo "  • Dados de teste: $(ls data/qiime2/*.tsv 2>/dev/null | wc -l) arquivos TSV"
echo "  • Notebooks: $(ls notebooks/*.ipynb 2>/dev/null | wc -l) notebooks"
echo "  • Módulos Python: $(ls actions/utils/*.py 2>/dev/null | wc -l) módulos"
echo "  • Actions: $(grep -c "class Action" actions/actions.py) classes"
echo ""

# 8. Teste final integrado
echo "8️⃣ Teste integrado completo..."
python3 << 'EOF'
import sys
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path.cwd()))

# Importar tudo
from actions.utils.rarefaction_analyzer import RarefactionAnalyzer, load_rarefaction_data
from actions.utils.report_generator import ReportGenerator, create_comprehensive_report
from actions.utils.qiime_parser_module import QIIME2Parser
import pandas as pd

# Teste 1: Carregar e analisar rarefação
df_rarefaction = load_rarefaction_data('data/qiime2/rarefaction.tsv')
analyzer = RarefactionAnalyzer(df_rarefaction)
stats = analyzer.get_summary_stats()
recommendation = analyzer.recommend_sampling_depth()

assert stats['total_samples'] > 0
assert recommendation['recommended_depth'] is not None

print(f"✓ Rarefação: {stats['total_samples']} amostras analisadas")
print(f"✓ Profundidade recomendada: {recommendation['recommended_depth']}")

# Teste 2: Gerar relatório
report = ReportGenerator("Teste Integrado")
report.add_section("Teste", "Conteúdo de teste", level=2)
md_path = report.generate_markdown("data/qiime2/teste_integrado.md")

assert Path(md_path).exists()
print(f"✓ Relatório gerado: {md_path}")

# Teste 3: Parser QIIME2
parser = QIIME2Parser("data/qiime2")
df_alpha = parser.load_alpha_diversity("data/qiime2/diversidade_alfa.tsv")

assert len(df_alpha) > 0
print(f"✓ Parser QIIME2: {len(df_alpha)} amostras carregadas")

print("\n🎉 Todos os testes integrados passaram!")
EOF
check_success "Teste integrado"
echo ""

# Resumo final
echo "=========================================="
echo -e "${GREEN}✅ TODOS OS TESTES PASSARAM!${NC}"
echo "=========================================="
echo ""
echo "📊 O YARA está pronto para uso!"
echo ""
echo "🚀 Próximos passos:"
echo "  1. Treinar modelo: make train"
echo "  2. Iniciar actions: make actions (Terminal 1)"
echo "  3. Iniciar chat: make shell (Terminal 2)"
echo "  4. Testar notebooks: jupyter lab"
echo ""
echo "💡 Leia GUIA_TESTE.md para instruções detalhadas"
echo ""
