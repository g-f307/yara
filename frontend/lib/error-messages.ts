type FriendlyError = {
  message: string;
  hint?: string;
};

const ERROR_PATTERNS: Array<{ match: string; friendly: FriendlyError }> = [
  {
    match: "Não foram encontrados dados válidos para a análise de alpha",
    friendly: {
      message: "Nenhum arquivo de diversidade alfa foi encontrado.",
      hint: "Envie uma tabela TSV com colunas como shannon, observed_features, faith_pd, chao1 ou simpson.",
    },
  },
  {
    match: "Não foram encontrados dados válidos para a análise de beta",
    friendly: {
      message: "Nenhuma matriz de diversidade beta foi encontrada.",
      hint: "Envie uma matriz de distâncias quadrada exportada do QIIME 2, como Bray-Curtis ou Jaccard.",
    },
  },
  {
    match: "Não foram encontrados dados válidos para a análise de taxonomy",
    friendly: {
      message: "Nenhum arquivo de taxonomia foi reconhecido.",
      hint: "Envie uma tabela com coluna Taxon/Taxonomy ou um artefato QIIME 2 contendo classificação taxonômica.",
    },
  },
  {
    match: "Não foram encontrados dados válidos para a análise de rarefaction",
    friendly: {
      message: "Nenhum dado de rarefação foi reconhecido.",
      hint: "Envie uma tabela de rarefação com profundidades de sequenciamento nas colunas.",
    },
  },
  {
    match: "Arquivos do projeto",
    friendly: {
      message: "Os arquivos ainda não estão disponíveis no backend científico.",
      hint: "Aguarde alguns segundos após o upload e tente a análise novamente.",
    },
  },
  {
    match: "Coluna de grupos não encontrada",
    friendly: {
      message: "Não encontrei uma coluna de grupos para comparar as amostras.",
      hint: "Use uma coluna como Grupo, Tratamento ou Condition nos metadados.",
    },
  },
  {
    match: "Métrica não encontrada",
    friendly: {
      message: "Não encontrei a métrica solicitada na tabela.",
      hint: "Tente shannon, observed_features, faith_pd, chao1 ou simpson, se estiverem no arquivo.",
    },
  },
];

export function getFriendlyError(rawError?: string): FriendlyError {
  if (!rawError) {
    return { message: "A análise falhou.", hint: "Tente novamente ou verifique os arquivos enviados." };
  }

  const matched = ERROR_PATTERNS.find((item) => rawError.includes(item.match));
  return matched?.friendly ?? { message: rawError };
}
