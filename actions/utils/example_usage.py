"""
Exemplo de uso do QIIME2Parser
"""

# Import correto - usando caminho relativo
from .qiime_parser_module import (
    QIIME2Parser,
    AlphaDiversityAnalyzer,
    load_qiime2_data
)

# Exemplo comentado para não executar automaticamente
"""
# Exemplo 1: Carregar diversidade alfa
print("📊 Exemplo 1: Diversidade Alfa")
print("=" * 60)

df_alpha = load_qiime2_data('data/qiime2/shannon.tsv', 'alpha')
analyzer = AlphaDiversityAnalyzer(df_alpha)
stats = analyzer.get_summary_stats('shannon')
print(stats)
"""

print("✅ Módulo QIIME2Parser importado com sucesso!")
print("💡 Descomente o código acima para testar!")