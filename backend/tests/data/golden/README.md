# Datasets científicos golden

Fixtures mínimas, sintéticas e sem dados pessoais usadas pela integração
contínua. Os valores esperados estão declarados em `expected.json`.

Comparações de ponto flutuante usam tolerância absoluta `1e-8` e tolerância
relativa `1e-6`. As tolerâncias absorvem diferenças numéricas legítimas entre
versões compatíveis de NumPy/SciPy sem esconder regressões científicas.

| Arquivo | Finalidade |
|---|---|
| `alpha.tsv` | estatísticas de diversidade alfa |
| `beta.tsv` | estatísticas da matriz de distâncias |
| `taxonomy.tsv` | extração e contagem no nível de filo |
| `rarefaction.tsv` | plateau, saturação e profundidade recomendada |
| `qc.tsv` | contrato de reads por amostra |
| `statistics.tsv` | Kruskal-Wallis entre dois grupos |
