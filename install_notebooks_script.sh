#!/bin/bash
# Script para instalar notebooks e módulos YARA

echo "📦 Instalando Notebooks e Módulos YARA..."
echo ""

cd ~/Documentos/pibic/yara

# Criar diretórios
mkdir -p notebooks
mkdir -p actions/utils
mkdir -p data/qiime2

echo "✅ Diretórios criados!"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Cole os notebooks nos arquivos:"
echo "   - notebooks/01_exploracao_qiime2.ipynb"
echo "   - notebooks/02_analise_diversidade_beta.ipynb"
echo ""
echo "2. Cole o parser em:"
echo "   - actions/utils/qiime2_parser.py"
echo ""
echo "3. Abra o VS Code:"
echo "   code ."
echo ""
echo "4. Abra um notebook e teste:"
echo "   - Clicar no arquivo .ipynb"
echo "   - Selecionar kernel: Python (YARA)"
echo "   - Executar células com Shift+Enter"
echo ""

# Criar __init__.py
touch actions/utils/__init__.py

# Criar exemplo de uso do parser
cat > actions/utils/example_usage.py << 'EOF'
"""
Exemplo de uso do QIIME2Parser
"""

from qiime2_parser import (
    QIIME2Parser,
    AlphaDiversityAnalyzer,
    load_qiime2_data
)

# Exemplo 1: Carregar diversidade alfa
print("📊 Exemplo 1: Diversidade Alfa")
print("=" * 60)

# df_alpha = load_qiime2_data('data/qiime2/shannon.tsv', 'alpha')
# analyzer = AlphaDiversityAnalyzer(df_alpha)
# stats = analyzer.get_summary_stats('shannon')
# print(stats)

print("\n💡 Descomente o código acima e adicione seus dados!")
print("\n✅ Módulo pronto para uso!")
EOF

echo "✅ Exemplo de uso criado em actions/utils/example_usage.py"
echo ""
echo "🎉 Instalação concluída!"
