# Guia reutilizável de Git e GitHub para pessoas e agentes

> Copie este arquivo para qualquer repositório e forneça-o como contexto aos
> agentes que trabalharão no projeto. Substitua os campos entre `<...>` pelas
> informações reais do projeto.

## 1. Finalidade

Este documento define como o trabalho deve ser registrado, implementado,
revisado e integrado. Ele pode ser usado em projetos individuais ou em equipe.

O fluxo padrão deste guia é o **GitHub Flow**:

```text
Issue → branch → commits → testes → pull request → CI → revisão → merge → limpeza
```

Apesar de ser chamado informalmente de Git Flow, este modelo não utiliza uma
branch `develop` por padrão. O Git Flow clássico só deve ser adotado quando o
projeto mantiver várias versões, possuir homologação formal ou tiver ciclos de
release independentes.

## 2. Informações do projeto

Preencha antes de iniciar:

```text
Projeto: <nome>
Repositório: <URL>
Branch principal: main
Responsável técnico: <nome ou usuário>
Comando de instalação: <comando>
Comando de testes: <comando>
Comando de lint: <comando ou não aplicável>
Comando de build: <comando ou não aplicável>
Estratégia de merge: Squash and merge
```

## 3. Regras obrigatórias

1. A branch `main` deve permanecer estável e executável.
2. Alterações relevantes devem começar por uma issue.
3. Cada issue deve possuir uma branch própria.
4. Não desenvolver diretamente na `main`, salvo correção textual realmente
   trivial e quando as regras do repositório permitirem.
5. Não misturar tarefas sem relação na mesma branch ou pull request.
6. Commits devem representar blocos lógicos completos, coerentes e possuir
   mensagens claras e descritivas. Não criar commits pequenos e vagos apenas
   para aumentar a quantidade de commits.
7. Antes do push, executar as validações compatíveis com a alteração.
8. Antes do merge, a CI deve estar aprovada.
9. Credenciais, tokens, senhas, `.env` real e dados pessoais não podem ser
   versionados, exibidos em logs ou incluídos em evidências.
10. Alterações fora do escopo da issue exigem outra issue ou autorização
    explícita.
11. Não reescrever o histórico de branches compartilhadas sem comunicar os
    envolvidos.
12. Nunca usar `git push --force` quando `--force-with-lease` for suficiente.
13. Features grandes devem ser divididas em commits por responsabilidade lógica;
    não concentrar toda a implementação, testes, configuração e documentação em
    um único commit.

## 4. Tipos de trabalho

| Tipo | Uso | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat(auth): adicionar login` |
| `fix` | Correção de comportamento | `fix(api): tratar timeout` |
| `docs` | Documentação | `docs(readme): explicar instalação` |
| `test` | Testes | `test(auth): cobrir senha inválida` |
| `refactor` | Mudança interna sem alterar comportamento | `refactor(core): separar serviços` |
| `ci` | Integração contínua | `ci(actions): executar pytest` |
| `chore` | Manutenção técnica | `chore(deps): atualizar pytest` |
| `build` | Build ou empacotamento | `build(docker): reduzir imagem` |
| `perf` | Desempenho | `perf(csv): reduzir uso de memória` |
| `security` | Segurança | `security(vault): remover segredo do log` |

## 5. Criação da issue

### Título

```text
<tipo>(<escopo>): <resultado esperado>
```

Exemplos:

```text
feat(auth): implementar recuperação de senha
fix(csv): rejeitar cabeçalho incompleto
ci(actions): automatizar testes
docs(api): documentar autenticação
```

### Modelo de issue

```markdown
## Contexto

<Por que esta alteração é necessária?>

## Objetivo

<Qual resultado deve ser entregue?>

## Escopo

- <item incluído>
- <item incluído>

## Critérios de aceite

- [ ] <comportamento verificável>
- [ ] <teste ou evidência esperada>
- [ ] A suíte automatizada passa.
- [ ] Nenhum segredo ou arquivo local foi versionado.

## Fora do escopo

- <item explicitamente excluído>

## Evidências esperadas

- <logs, testes, imagens ou artefatos sem dados sensíveis>
```

Uma issue deve descrever resultados verificáveis, não apenas “fazer ajustes”.

## 6. Preparação da branch

Atualize a base:

```bash
git switch main
git pull --ff-only origin main
git fetch --prune origin
```

Crie a branch usando o número da issue:

```bash
git switch -c <tipo>/<numero>-<descricao-curta>
```

Exemplos:

```text
feature/15-recuperacao-senha
fix/22-cabecalho-csv
docs/31-guia-deploy
chore/40-atualizar-dependencias
```

Use nomes sem espaços, acentos ou informações pessoais.

## 7. Desenvolvimento e commits

### Regra de granularidade

Os commits devem seguir a divisão lógica indicada pelo manual do projeto. A meta
não é produzir a maior nem a menor quantidade possível de commits, mas criar um
histórico que explique como a solução foi construída.

Não são aceitos commits pequenos e vagos como:

```text
ajustes
correções
mais mudanças
tentativa final
atualizar arquivos
```

Também não se deve colocar uma feature grande inteira em um único commit quando
ela contém responsabilidades claramente separáveis. Separe, por exemplo:

```text
feat(auth): implementar serviço de autenticação refs #15
feat(auth): integrar autenticação ao endpoint de sessão refs #15
test(auth): cobrir credenciais válidas e inválidas refs #15
docs(auth): documentar configuração e uso refs #15
```

Cada commit deve:

- entregar um bloco lógico completo e compreensível;
- possuir uma mensagem que descreva objetivamente a alteração;
- agrupar arquivos que participam da mesma responsabilidade;
- ser grande o suficiente para representar uma mudança real;
- ser separado quando outra responsabilidade puder ser revisada isoladamente;
- manter relação direta com a issue em desenvolvimento.

Não divida alterações inseparáveis apenas para gerar mais commits. Por exemplo,
uma implementação pequena e seu teste diretamente associado podem permanecer no
mesmo commit quando formarem uma única unidade lógica. Em features maiores,
implementação, integrações, testes, infraestrutura e documentação normalmente
constituem blocos distintos.

Antes de cada commit:

```bash
git status
git diff
```

Adicione apenas os arquivos relacionados à unidade lógica:

```bash
git add <arquivos-específicos>
git diff --cached
git commit -m "<tipo>(<escopo>): <ação> refs #<issue>"
```

Exemplo de divisão atômica:

```text
feat(auth): implementar serviço de autenticação refs #15
test(auth): cobrir credenciais inválidas refs #15
docs(auth): documentar variáveis necessárias refs #15
```

Um commit organizado por bloco lógico:

- representa uma mudança lógica;
- pode ser explicado em uma frase;
- não contém arquivos sem relação;
- mantém o projeto em estado compreensível;
- evita mensagens como `ajustes`, `final`, `correção` ou `agora funciona`;
- não fragmenta artificialmente uma mesma responsabilidade;
- não concentra responsabilidades independentes em um único commit.

## 8. Validação antes do push

Execute apenas verificações relevantes e disponíveis no projeto:

```bash
<comando de testes>
<comando de lint>
<comando de build>
git diff --check
git status
```

Não declare que algo foi testado se o comando não foi executado. Registre também
limitações, como integrações externas que dependem de credenciais ou ambiente
indisponível.

## 9. Publicação e pull request

Publique a branch:

```bash
git push -u origin <nome-da-branch>
```

### Modelo de pull request

```markdown
## Issue relacionada

Closes #<numero>

## O que foi feito

- <alteração objetiva>
- <alteração objetiva>

## Como validar

```text
<comandos reproduzíveis>
```

## Evidências

- <resultado dos testes>
- <build, log ou captura relevante>

## Checklist

- [ ] Trabalhei somente no escopo da issue.
- [ ] Revisei o diff completo.
- [ ] Adicionei ou atualizei testes quando necessário.
- [ ] Atualizei a documentação quando necessário.
- [ ] A CI passou.
- [ ] Não incluí segredos ou dados pessoais.
- [ ] Não deixei logs, caches ou arquivos temporários versionados.
```

## 10. Revisão de código

O revisor deve conferir:

1. aderência à issue e aos critérios de aceite;
2. comportamento correto nos caminhos de sucesso e erro;
3. testes compatíveis com o risco;
4. ausência de credenciais e dados sensíveis;
5. clareza dos nomes, mensagens e documentação;
6. ausência de mudanças fora do escopo;
7. resultado da CI;
8. impacto em compatibilidade, segurança e operação.

Possíveis decisões:

- **Approve:** não há bloqueadores;
- **Request changes:** existem problemas que precisam ser corrigidos;
- **Comment:** há observações não bloqueantes ou dúvidas.

Uma nova revisão deve verificar as correções e também possíveis regressões.

## 11. Fluxo em equipe

Em equipe:

- o autor da mudança não deve ser o único aprovador;
- atribua a issue a uma pessoa responsável;
- divida o trabalho por unidades independentes;
- cada integrante deve usar sua própria conta e identidade Git;
- evite duas pessoas alterando os mesmos arquivos simultaneamente;
- comunique dependências entre issues;
- use draft PR quando o trabalho ainda não estiver pronto;
- novas alterações após aprovação devem provocar nova revisão;
- conflitos devem ser resolvidos pelo autor da branch, com auxílio da equipe.

Configuração recomendada para proteção da `main`:

- exigir pull request;
- exigir pelo menos uma aprovação;
- invalidar aprovação após novos commits;
- exigir resolução das conversas;
- exigir checks da CI;
- bloquear force push e exclusão.

## 12. Fluxo individual

Em projeto solo, mantenha issues, branches, CI e PRs para obter rastreabilidade e
autorrevisão. Você acumula os papéis de autor e mantenedor.

Recomendações:

- não exigir aprovação externa se ninguém puder fornecê-la;
- exigir CI antes do merge;
- revisar o PR pela aba **Files changed**;
- aguardar alguns minutos antes da revisão final quando a mudança for relevante;
- registrar limitações e evidências como faria em uma equipe.

Proteções úteis para projeto solo:

- exigir pull request;
- exigir checks da CI;
- exigir resolução das conversas;
- bloquear force push e exclusão.

## 13. Merge e limpeza

Use **Squash and merge** como padrão para manter um commit por PR na `main`.

Título do merge:

```text
<tipo>(<escopo>): <resultado> (#<PR>)
```

Após o merge:

```bash
git switch main
git pull --ff-only origin main
git fetch --prune origin
git branch -d <branch>
```

Depois de `Squash and merge`, o Git pode não reconhecer a branch como integrada,
pois os hashes foram substituídos. Após confirmar o merge no GitHub:

```bash
git branch -D <branch>
```

`git fetch --prune` remove referências remotas obsoletas, mas não exclui branches
locais.

## 14. Correção urgente

Para uma falha urgente em produção:

```bash
git switch main
git pull --ff-only origin main
git switch -c hotfix/<numero>-<descricao>
```

O hotfix ainda deve possuir issue, testes proporcionais, PR, CI e revisão. Urgência
reduz o tempo do ciclo, não elimina rastreabilidade nem validação.

## 15. Releases e versionamento

Use versionamento semântico:

```text
MAJOR.MINOR.PATCH
```

- `MAJOR`: mudança incompatível;
- `MINOR`: funcionalidade compatível;
- `PATCH`: correção compatível.

Exemplos:

```text
v1.0.0 primeira versão estável
v1.1.0 nova funcionalidade compatível
v1.1.1 correção de defeito
```

Só publique uma release quando:

- a `main` estiver atualizada e estável;
- issues bloqueadoras estiverem encerradas;
- CI e testes estiverem aprovados;
- build ou deploy tiver sido validado;
- documentação estiver coerente;
- não houver segredos ou artefatos indevidos;
- evidências necessárias estiverem registradas.

## 16. Reescrita de histórico

Reorganizar commits é aceitável antes do compartilhamento. Se a branch já estiver
no remoto, confirme que ninguém está trabalhando nela e use:

```bash
git push --force-with-lease origin <branch>
```

Não reescreva `main`, branches protegidas ou branches compartilhadas sem
autorização explícita.

## 17. Regras específicas para agentes

Ao fornecer este arquivo como memória, instrua o agente a seguir estas regras:

1. Ler esta documentação e os arquivos de orientação do repositório antes de agir.
2. Inspecionar `git status`, branch atual e histórico recente.
3. Preservar alterações existentes do usuário.
4. Não implementar itens fora da issue.
5. Criar ou usar a branch associada à issue antes de editar.
6. Explicar resumidamente o plano antes de alterar arquivos.
7. Fazer commits claros por blocos lógicos e responsabilidades técnicas, sem
   fragmentação vaga e sem concentrar uma feature grande em um único commit.
8. Executar testes e relatar resultados reais.
9. Não fazer merge, criar release, excluir branch ou reescrever histórico sem
   autorização explícita.
10. Não publicar credenciais nem reproduzi-las na resposta.
11. Ao revisar PR, separar bloqueadores de sugestões opcionais.
12. Ao terminar, informar arquivos alterados, commits, testes, limitações e próximo
    passo no GitHub.

### Prompt reutilizável para agentes

```text
Leia integralmente o arquivo <CAMINHO_DESTE_GUIA> e siga o fluxo definido nele.

Trabalhe somente na Issue #<NUMERO>: <TITULO>.

Antes de editar:
- verifique a branch atual, git status e histórico recente;
- confirme o escopo e os critérios de aceite;
- preserve alterações preexistentes.

Durante o trabalho:
- mantenha a main intacta;
- use uma branch própria;
- divida o trabalho em commits atômicos;
- não inclua segredos;
- execute as validações adequadas.

Não faça merge, release, exclusão de branch ou reescrita de histórico remoto sem
minha autorização explícita.

Ao concluir, entregue:
- resumo do que foi feito;
- lista dos commits;
- testes e resultados;
- limitações;
- texto sugerido para o pull request;
- próximos passos manuais.
```

## 18. Checklist rápido

```text
[ ] Issue criada e atribuída
[ ] Escopo e fora do escopo definidos
[ ] Main atualizada
[ ] Branch criada a partir da main
[ ] Commits atômicos e claros
[ ] Testes executados
[ ] Diff revisado
[ ] Branch publicada
[ ] PR ligado à issue
[ ] CI aprovada
[ ] Revisão concluída
[ ] Merge realizado
[ ] Issue encerrada
[ ] Branch remota excluída
[ ] Main local atualizada
[ ] Branch local removida
[ ] Release criada, quando aplicável
```
