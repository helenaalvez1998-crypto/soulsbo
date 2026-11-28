# Manifesto do pacote mestre de continuidade

- Projeto: `soulsbo-main`
- Revisão: 2026-11-27
- Pacote canônico: `soulsbo-main-handoff.zip` (a cópia mais recente substitui a anterior)
- Conteúdo desta revisão: **229 entradas ZIP (215 arquivos + 14 diretórios)**; inclui mapa estático de contratos HTTP e script de reprodução; sem caches, bytecode, banco local, `.env` preenchido ou arquivos binários de fontes tipográficas. A revisão imediatamente anterior tinha 226 entradas.
- Finalidade: permitir que um novo chat/agente assuma o projeto do zero, sem depender do histórico desta conversa.
- Estado funcional atual: **uma alteração funcional aprovada** em `sistemas/gwent.py` implementa a política oficial de combos v0.1. Não foram alterados schema/DB, endpoints/APIs, frontend, IDs/atributos de cartas, pipeline de imagens ou arte. Os relatórios v0.1 de combo são históricos pré-patch.
- Estado de validação: mapa estático das **12 rotas HTTP Gwent** (sem dispatch real), oito suites comportamentais, **251/251 asserts** (32 regressões específicas da política, incluindo `aplicar_jogada(action="play")`); separadamente, **12/12 cenários stateful** aprovados (quatro partidas controladas de três rodadas, snapshots JSON, 137 payloads de catálogo, combo por turno, líder/especial/clima, relíquia, clima manual, snapshot legado e DDL/`state_json` em SQLite `:memory:`). A auditoria pós-política cobre 4.422 pares e 287.430 trincas, zero ativações solo e 2.582/2.582 eventos posteriores com carta participante. HTTP real ainda não foi executado.
- Comparação histórica com o ZIP fonte original: 152 arquivos não tipográficos foram comparados; 151 permanecem byte a byte idênticos e a única alteração funcional aprovada está em `sistemas/gwent.py`.
- Comparação com o pacote imediatamente anterior: os 143 arquivos fora de `docs/` permanecem byte a byte idênticos; esta etapa alterou apenas documentação e o script de auditoria estática em `docs/scripts/`.

## Revisão mais recente — mapa estático dos contratos HTTP Gwent v0.1 (2026-11-27)

O script `docs/scripts/audit-gwent-http-contracts-v0.1.py` identificou **12 rotas** e gerou `card-game-http-contract-map-v0.1.md/.json`. O mapa cruza registro de rota/handler em `bot.py`, campos e sinais de consumo em `site/app.js`, chamadas do motor, uso de DB e chaves retornadas por `preparar_carta()`.

Achado de custo: o salvamento do deck não soma custo nem aplica orçamento. As rotas podem preencher `payload['custo']` antes de `preparar_carta()`, mas a função reconstrói o dicionário sem `custo`, descartando o valor antes da resposta final. Não corrigir esse contrato até custo/schema/orçamento serem aprovados.

**Limite:** auditoria estática somente. Sem `discord.py` e `aiosqlite`, e instalação bloqueada por falha DNS, não houve `aiohttp.TestClient`, dispatch real, classe `Database`, gateway Discord, navegador ou integração de produção. O relatório não prova comportamento HTTP, autorização ou transações em runtime.

Histórico de alterações por arquivo/função/campo/motivo/impacto: tabela no fim de `card-game-handoff.md` e histórico desta revisão neste manifesto. Os 251 asserts comportamentais e os 12 cenários stateful continuam sendo validações separadas.

## Revisão imediatamente anterior — integração stateful de partidas v0.1 (2026-11-27)

A suíte `docs/scripts/assert-full-match-stateful-v0.1.py` passou **12/12 cenários**, em separado dos 251/251 asserts comportamentais. Foram percorridas quatro partidas controladas de três rodadas pelo motor em memória, snapshots JSON, 137/137 payloads preparados, combo por jogadas normais, líder + carta climática, reset de clima, relíquia, clima manual, snapshot legado e round-trip SQLite de `state_json` usando o DDL extraído de `database.py`. O relatório é `card-game-match-snapshot-integration-v0.1.md/.json`.

A verificação de `bot.py` ↔ `site/app.js` foi estática. Não houve dispatch HTTP, gateway Discord, execução da classe `Database`/`aiosqlite`, browser, convites, partida solo/IA nem produção. O ambiente não possui `discord.py` nem `aiosqlite`; a tentativa de instalar as versões fixadas no `requirements.txt` foi bloqueada por falha de DNS/rede. Nenhum arquivo funcional adicional foi alterado nesta etapa; a única alteração funcional aprovada permanece a política de combos em `sistemas/gwent.py`.

## Estado atual — política de combos aprovada

A política de `card-game-combo-policy-v0.1.md` foi aprovada pelo usuário e implementada: 27 combos com `minimum: 2` instâncias distintas e `priority` única; a carta atual deve contribuir com tag exigida; prioridade crescente decide qual combo ativa; no máximo um combo ativa por jogada; combos pendentes só disparam por participante posterior; bônus individual vai para a carta participante atual e `team_bonus` permanece. Cada combo continua limitado a uma utilização por jogador/rodada pelo estado `synergy_used`.

A alteração funcional está em `sistemas/gwent.py`, nos dados `SYNERGY_COMBOS`, na função `_aplicar_combo_de_cartas()` e nas descrições mecânicas dos combos. Não há migração DB. Partidas já persistidas conservam bônus aplicados antes do patch. EFP, custos, raridades e orçamento de deck permanecem propostas não aprovadas.



## Histórico desta revisão — implementação aprovada da política de combos

| Arquivo | Função/campo/trecho | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `sistemas/gwent.py` | `SYNERGY_COMBOS` (27 definições) | Três combos sem mínimo explícito; sem prioridade declarada; texto não explicitava todos os participantes | `minimum: 2` e `priority` inteiro único em todos os 27; descrições atualizadas para identificar a carta participante | Aplicar a política aprovada: duas instâncias distintas, precedência determinística e participação real | Modifica somente futuras resoluções de combos no motor; bônus, líderes, passivas, DB e APIs não foram migrados | 27 mínimos e prioridades únicos; 32 regressões dedicadas; enumeração pós-patch |
| `sistemas/gwent.py` | `_aplicar_combo_de_cartas()` | Carta com qualquer tag podia recolher combo já completo; ordem do dicionário escolhia; contagem de participantes podia ser implícita | Exige tag atual requerida, todas as tags presentes no campo, mínimo de instâncias distintas, prioridade crescente, no máximo um combo por jogada | Impedir bônus para não participante, ativação solo e precedência incidental | Bônus individual vai à carta participante atual; `team_bonus`, `synergy_used` e reset por rodada preservados | 251/251 asserts em oito suites; auditoria 4.422 pares/287.430 trincas |
| `docs/card-game-combo-policy-v0.1.md`, `docs/scripts/assert-combo-policy-v0.1.py`, `docs/card-game-combo-policy-assertions-v0.1.json` | Nova especificação e regressões | Inexistentes | Contrato oficial e 32 cenários reprodutíveis, incluindo integração pelo `aplicar_jogada()` | Preservar a decisão aprovada e bloquear regressões | Apenas documentação/harness | 32/32 aprovados |
| `docs/scripts/audit-combo-overlap-v0.2.py`, `docs/card-game-combo-overlap-v0.2.md/.json` | Auditoria pós-patch | Apenas diagnóstico v0.1 do defeito original | Nova enumeração com o resolvedor corrigido | Medir o resultado após correção sem apagar baseline | Somente diagnóstico; nenhum efeito adicional no jogo | Zero solo; 2.582/2.582 eventos posteriores participantes |
| `docs/scripts/build-effect-source-map-v0.2.py`, `docs/card-game-effect-source-map-v0.2.json` | Mapa AST atualizado | Índice gerado contra o baseline | Referências AST regeneradas a partir do runtime pós-política | Manter o mapa de evidências sincronizado com o código atual | Somente documentação | 59 genéricas, 22 identidades, 10 líderes, 27 combos |
| `docs/scripts/summarize-card-game-behavior-v0.3.py`, `docs/card-game-behavior-validation-v0.3.md/.json` | Agregador e relatório atual | Sete suites/219 asserts pré-política | Oito suites/251 asserts, incluindo regressões novas | Consolidar estado pós-patch | Somente diagnóstico/documentação | 251/251 aprovados |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/card-game-balance-validation-v0.1.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura, regras e histórico | Indicavam a política de combos como pendente e exibiam métricas pré-patch como atuais | Política registrada como aprovada/implementada; v0.1 marcado histórico; métricas v0.2/v0.3 como atuais | Evitar handoff contraditório | Só documentação; fornece contexto técnico exato ao próximo chat | Links, números, catálogo de combos e SHA conferidos |
| `docs/scripts/assert-full-match-stateful-v0.1.py`, `docs/card-game-match-snapshot-integration-v0.1.md/.json` | Testes stateful e relatório de integração | Suites anteriores cobriam principalmente cenários isolados e não percorriam partidas/snapshots | Adicionados 12 cenários stateful; quatro partidas controladas de três rodadas, 137 payloads, combo, líder, clima, relíquia, snapshot legado e SQLite DDL/state_json | Encontrar defeitos de transição e serialização sem afirmar integração de produção | Apenas testes/documentação; nenhum código funcional alterado | 12/12 cenários; HTTP estático apenas; discord.py/aiosqlite ausentes |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura e pendências | Indicavam partidas completas/snapshots como trabalho futuro | Registram 12/12 stateful concluídos, limites de fixtures e próximo passo HTTP real | Evitar novo chat considerar a integração mais completa do que foi | Somente documentação | Testes e relatório JSON reproduzidos; runtime unchanged |

## Ordem recomendada de leitura

1. `README-PACOTE-CONTINUIDADE.md` — orientação obrigatória para chat novo.
2. `card-game-handoff.md` — estado, quatro blocos da Regra 8, histórico e próximos passos.
3. `card-game-combo-policy-v0.1.md` — regra aprovada e implementada; não redecidir sem pedido.
4. `card-game-behavior-validation-v0.3.md/.json` + `scripts/summarize-card-game-behavior-v0.3.py` — oito suites/251 asserts comportamentais.
5. `card-game-match-snapshot-integration-v0.1.md/.json` + `scripts/assert-full-match-stateful-v0.1.py` — 12/12 cenários stateful, quatro partidas controladas e snapshots; HTTP real permanece pendente.
7. `card-game-combo-overlap-v0.2.md/.json` + `scripts/audit-combo-overlap-v0.2.py` — enumeração pós-correção.
8. `card-game-mapping-audit.md` — baseline histórico com as seções 21 (política) e 22 (integração stateful) como atualizações vigentes.
9. `card-game-effect-source-map-v0.2.json` + `scripts/build-effect-source-map-v0.2.py` — mapa AST do runtime atual; v0.1 é baseline histórico.
10. `scripts/assert-combo-policy-v0.1.py` + `card-game-combo-policy-assertions-v0.1.json` — 32 regressões da política.
11. Suites individuais e relatórios JSON de identidade, genéricas, ciclo de vida, especiais/relíquias, líderes e combos/passivas.
12. `card-game-stale-identity-disposition-v0.1.md/.json` — classificação dos 28 ramos sem associação ativa; recomendações, não remoções.
13. `card-game-card-traceability.md/.csv/.json` — matriz dos 137 modelos do baseline; nenhum redesign dos dados de carta foi aplicado ainda.
14. `card-game-balance-validation-v0.1.md`, `card-game-efp-methodology-v0.2.md`, `card-game-balance-spec-v0.1.md` e `card-game-effect-score-catalog.json` — evidências/propostas quantitativas não aprovadas.
15. `card-game-deck-cost-sampling-v0.2.json` + script e `card-game-combo-activation-v0.1.json` + script — amostragens exploratórias, não simulações competitivas.
16. `card-game-combo-overlap-v0.1.md/.json` — **histórico congelado do defeito pré-patch**. O script v0.1 recusa execução no runtime atual; para estado vigente use v0.2.
17. `card-game-handler-coverage-v0.1.json`, `card-game-effect-runtime-smoke-v0.1.json` e scripts associados — cobertura estática e smoke tests com limites declarados.
18. Os demais arquivos de `docs/` — documentação preexistente; conferir as advertências do handoff antes de tratá-los como regra atual.


## Documentos principais incluídos

- `README-PACOTE-CONTINUIDADE.md` — aviso para chat novo, mensagem inicial sugerida, ordem de leitura e regra de continuidade.
- `card-game-handoff.md` — estado exato, decisões confirmadas, quatro blocos da Regra 8, pendências, histórico e próximos passos.
- `card-game-mapping-audit.md` — mapa do baseline e atualização pós-política: arquivos, funções, APIs, banco, eventos, catálogo de efeitos, líderes, relíquias, arte, falhas de ligação e catálogo atual de combos.
- `card-game-card-traceability.md`, `.csv`, `.json` — matriz individual dos 137 modelos de carta.
- `card-game-effect-score-catalog.json` — scores EFP preliminares; não aprovados.
- `card-game-effect-source-map-v0.1.json` — mapa AST histórico congelado; o gerador v0.1 tem fail-fast no runtime atual.
- `card-game-effect-source-map-v0.2.json` — mapa AST regenerado após a alteração de combos.
- `card-game-efp-methodology-v0.2.md` — decomposição proposta do EFP por componentes, condições, alvos, duração, bloqueios e valor esperado; não aprovada.
- `card-game-balance-spec-v0.1.md` — proposta de poder, pureza, custo, raridade, orçamento, distribuição e lore; não aprovada.
- `card-game-balance-validation-v0.1.md` — limitações metodológicas, amostragens, frequência de combos, cobertura de handlers e próximos passos.
- `card-game-deck-cost-sampling-v0.1.json` — resultado histórico/superado, preservado para rastreabilidade.
- `card-game-deck-cost-sampling-v0.2.json` — amostragem corrigida de custo com/sem relíquia equipada.
- `card-game-combo-activation-v0.1.json` — frequência observada dos 27 combos sob ordem aleatória.
- `card-game-combo-policy-v0.1.md` — política de combos aprovada e implementada.
- `card-game-combo-policy-assertions-v0.1.json` — 32 regressões específicas da política.
- `card-game-combo-overlap-v0.2.md/.json` — auditoria pós-correção do runtime atual.
- `card-game-combo-overlap-v0.1.md/.json` — diagnóstico histórico pré-patch congelado; o script v0.1 tem fail-fast no runtime atual.
- `card-game-handler-coverage-v0.1.json` — relatório estático de catálogo, handlers, identidades antigas e tags órfãs.
- `card-game-effect-runtime-smoke-v0.1.json` — testes de fumaça do motor em estados sintéticos; não representam cobertura total.
- `card-game-effect-behavior-assertions-v0.1.json` — primeira bateria histórica de 13 asserts, preservada como registro da fase inicial.
- `card-game-behavior-validation-v0.2.md/.json` — agregado histórico pré-política, sete suites/219 asserts.
- `card-game-behavior-validation-v0.3.md/.json` — agregado atual pós-política, oito suites/251 asserts.
- `card-game-http-contract-map-v0.1.md/.json` — mapa estático de 12 rotas Gwent; identifica falta de orçamento e perda de `custo` no payload preparado; não executa HTTP.
- `card-game-match-snapshot-integration-v0.1.md/.json` — 12 cenários stateful: quatro partidas controladas, snapshots, preparação de catálogo e DDL SQLite; sem dispatch HTTP real.
- `scripts/assert-full-match-stateful-v0.1.py` — runner reproduzível dos 12 cenários stateful.
- `card-game-leader-assertions-v0.1.json` — 22 cenários, incluindo todos os dez handlers de líder e casos negativos/limite.
- `card-game-combo-faction-assertions-v0.1.json` — 87 cenários relativos aos 27 combos e às quatro passivas de facção.
- `card-game-stale-identity-disposition-v0.1.md/.json` — classificação dos 28 ramos de identidade sem associação ativa, sem exclusão aplicada.
- Relatórios individuais de identidade, habilidades genéricas, ciclo de vida, especiais e relíquias.
- Documentação preexistente em `docs/` preservada do projeto-base, com ressalvas registradas no handoff.

## Scripts reproduzíveis em `docs/scripts/`

- `build-effect-source-map-v0.1.py` — gerador arquivado; só pode ser usado em checkout pré-política e recusa o runtime atual.
- `build-effect-source-map-v0.2.py` — gera o mapa AST do runtime pós-política.
- `assert-card-effect-behavior-v0.1.py` — valida resultados explícitos de 13 efeitos em fixtures sintéticos; não é cobertura completa.
- `sample-deck-cost-v0.1.py` — histórico/superado; não usar para recomendar orçamento (combo parcial e sem líder/relíquia).
- `sample-deck-cost-v0.2.py` — amostragem corrigida de custo, ainda dependente de EFP estimado e hipóteses de líder/relíquia.
- `simulate-combo-activation-v0.1.py` — chama `_aplicar_combo_de_cartas()` para estimar ativação sob ordem aleatória.
- `audit-effect-handler-coverage-v0.1.py` — cruzamento AST/runtime de catálogo, handlers, identidade e tags.
- `validate-card-effect-smoke-v0.1.py` — testes sintéticos de ação/hook no motor atual; não cobre todos os caminhos condicionais.
- `assert-card-identity-behavior-v0.1.py` — 22 identidades positivas e 11 casos negativos/limite.
- `assert-generic-unit-effects-v0.1.py` — 39 assertions para habilidades genéricas de unidade.
- `assert-card-lifecycle-effects-v0.1.py` — hooks de remoção/fim de rodada, incluindo `gloria` e ausência de `sobrevivente`.
- `assert-special-and-relic-effects-v0.1.py` — especiais e seis relíquias pelo fluxo real de ação.
- `assert-leader-effects-v0.1.py` — todos os dez handlers de líder e 12 rejeições/limites; 22/22.
- `assert-combo-and-faction-passive-v0.1.py` — 27 combos com um par ativador cada, requisitos incompletos, bloqueio de repetição, quatro passivas de facção e exclusão do efeito de especiais; 87/87.
- `audit-combo-overlap-v0.1.py` — script arquivado; só roda em checkout pré-política e recusa o runtime atual.
- `audit-combo-overlap-v0.2.py` — enumera o resolvedor corrigido em 4.422 pares e 287.430 trincas de IDs distintos.
- `audit-stale-identity-branches-v0.1.py` — classifica os 28 ramos de identidade sem associação ativa.
- `assert-combo-policy-v0.1.py` — 32 regressões da política aprovada.
- `summarize-card-game-behavior-v0.2.py` — agrega sete suites históricas/219 asserts.
- `summarize-card-game-behavior-v0.3.py` — agrega oito suites/251 asserts e métricas pós-política.
- `audit-gwent-http-contracts-v0.1.py` — inventaria 12 rotas/handlers, campos de request, sinais frontend, DB/motor e contrato de custo por AST/inspeção estática; não executa handlers.
- `assert-full-match-stateful-v0.1.py` — testa quatro partidas controladas de três rodadas, snapshots JSON, payloads, combos, líder, clima, relíquia, snapshot legado e round-trip SQLite; 12/12.

## Resultados e validações atuais pós-política

- Política dos combos: aprovada e implementada em `sistemas/gwent.py`.
- Catálogo: 27 combos; todos possuem `minimum: 2` e `priority` única; carta atual participa por tag; um combo por jogada; uso por ID uma vez por jogador/rodada.
- Testes comportamentais: oito suites, 251/251 assertions aprovadas; 32 assertions são regressões específicas da política. Ver `card-game-behavior-validation-v0.3.md/.json`.
- Mapa HTTP: 12 rotas mapeadas estaticamente; 0 dispatches reais, pendente por dependências indisponíveis.
- Testes stateful: 12/12 cenários aprovados, incluindo quatro partidas controladas de três rodadas e round-trip JSON/SQLite. Ver `card-game-match-snapshot-integration-v0.1.md/.json`.
- Enumeração pós-correção: 4.422 pares e 287.430 trincas; zero ativações solo; 152 pares com sobreposição elegível sob prioridade declarada; 2.582 trincas com múltiplos combos em jogadas sucessivas; todas as 2.582 cartas posteriores participantes por tag. Ver `card-game-combo-overlap-v0.2.md/.json`.
- Único arquivo funcional alterado nesta etapa: `sistemas/gwent.py`. Nenhuma alteração em DB/schema, `bot.py`, frontend, APIs, imagens ou assets do jogo. Partidas já persistidas mantêm bônus antigos; o ZIP não contém DB de produção.
- Os resultados do v0.1 abaixo descrevem o baseline anterior e são preservados apenas para comparação. EFP, custos, raridades, orçamento e redesign de cartas continuam propostas não aprovadas.

## Resultados e limites principais do baseline (histórico pré-política)

- Catálogo: 59 habilidades genéricas; 56 possuem handler direto de jogada, 2 são hooks de ciclo de vida (`vinganca`, `espolios`) e 1 (`sobrevivente`) não tem handler correspondente identificado. `gloria` é um hook oculto em `_resolve_round()` e está fora de `HABILIDADES`.
- Identidades: 22 associações ativas, todas com referência no resolvedor; 28 ramos de identidade continuam sem mapeamento ativo e exigem decisão antes de limpeza.
- Líderes: 10 definições com referências de execução.
- Combos: 27 definições; 72 IDs na tabela de tags, 67 IDs de cartas atuais e cinco IDs órfãos. Todos os combos têm provedores para cada tag requerida, mas isso não prova alcançabilidade em todos os decks/estados.
- Sobreposição: 154/4.422 pares ordenados (3,4826%) têm mais de um combo elegível; 11.780/287.430 trincas ativam ao menos dois combos em sequência. Em 8.096/11.784 eventos posteriores (68,7033%), a carta que recebe o combo não contribui com tag requerida. `eco_convergente` ativa solo por `gwent_unidade_eco`; três combos não declaram `minimum`. Ver relatório completo e exemplos em `card-game-combo-overlap-v0.1.md`.

- Smoke test: 56 ações diretas concluídas sem exceção; 22/22 identidades geraram evento; hooks foram tratados separadamente. Isto não equivale a testes de branch completa nem a partidas competitivas.
- Testes comportamentais v0.2: sete suites, 219/219 assertions aprovadas (13 iniciais + 33 identidades + 39 unidades genéricas + 7 lifecycle + 18 especiais/relíquias + 22 líderes + 87 combos/passivas). Os 87 novos cenários incluem um par ativador por combo, ausência de parceiro, bloqueio de repetição do mesmo combo, passivas nas quatro facções e exclusão de especiais. São fixtures sintéticos selecionados, não 219 habilidades únicas, nem cobertura de todos os estados/raridades ou integração de produção.
- Combos: 100.000 decks aleatórios, seed 42; 57,19% tiveram pelo menos um combo ativado e a média foi 0,956 ativação na mão de dez cartas assumida jogada na mesma rodada. Não mede taxa de vitória nem EV.
- Custo: amostragem v0.2 com 100.000 decks por cenário, seed 42; teto 32 aceita 68,8% sem relíquia e 45,4% com relíquia sob premissas do script. Isso não valida o teto.
- EFP: scores v0.1 são hipóteses fixas não calibradas. A metodologia v0.2 propõe vetores mecânicos e simulação de partidas; não há scores aprovados.

## Modificações desta revisão (mapa de fonte e EFP v0.2)

| Arquivo(s) | Alteração | Motivo/impacto |
|---|---|---|
| `docs/scripts/build-effect-source-map-v0.1.py`, `docs/card-game-effect-source-map-v0.1.json` | Gerador e índice AST histórico pré-política | Mapa de evidências do baseline, antes do patch | Script guardado com fail-fast no runtime atual; JSON congelado; v0.2 é o mapa atual | Evitar sobrescrever o registro histórico | Apenas documentação/harness | 59 genéricas, 22 identidades, 10 líderes, 27 combos no baseline |
| `docs/card-game-efp-methodology-v0.2.md` | Nova metodologia de decomposição por precondições, alvos/caps, consequências imediatas/atrasadas, bloqueios, duração, testes e EV. | Evita transformar pesos subjetivos em EFP definitivo; permanece proposta não aprovada. |
| `docs/scripts/assert-card-effect-behavior-v0.1.py`, `docs/card-game-effect-behavior-assertions-v0.1.json` | Primeira bateria de 13 asserts explícitos para resultados mecânicos selecionados. | Diferencia ação sem exceção de efeito com resultado esperado; preservada como fase inicial, superada em escopo pelas suites agregadas v0.2. |
| `docs/card-game-balance-validation-v0.1.md` | Acrescentada a seção 11 sobre o mapa de fonte e o método EFP v0.2. | Registra evidência e sequência de validação. |
| `docs/card-game-balance-spec-v0.1.md` | Referência explícita ao mapa de source e à metodologia EFP v0.2. | Mantém os scores v0.1 marcados como não calibrados. |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md` | Atualizados estado, ordem de leitura, próxima etapa e histórico. | Novo chat encontra as evidências e sabe que asserts e simulação continuam pendentes. |
| `docs/PACOTE-MANIFESTO.md` | Atualizado manifesto do pacote. | Inventaria documentos/scripts e os limites da revisão. |

| `docs/scripts/assert-card-identity-behavior-v0.1.py`, `docs/card-game-identity-behavior-assertions-v0.1.json` | Nova suite para identidades | 33 assertions: 22 identidades ativas em cenário positivo e 11 casos negativos/limite. | Confirmar efeitos de identidade por resultado de estado. | Diagnóstico apenas; nenhum impacto no runtime. | 33/33 passaram. |
| `docs/scripts/assert-generic-unit-effects-v0.1.py`, `docs/card-game-generic-unit-assertions-v0.1.json` | Nova suite de habilidades de unidade | 39 cenários positivos/negativos para habilidades genéricas de unidade. | Expandir além do smoke de ausência de exceção. | Diagnóstico apenas. | 39/39 passaram. |
| `docs/scripts/assert-card-lifecycle-effects-v0.1.py`, `docs/card-game-lifecycle-assertions-v0.1.json` | Nova suite de ciclo de vida | Testes de remoção, fim de rodada, vitória/derrota e status de `sobrevivente`. | Verificar hooks fora da ação comum de jogar carta. | Diagnóstico apenas; evidencia `gloria` e `sobrevivente`. | 7/7 passaram. |
| `docs/scripts/assert-special-and-relic-effects-v0.1.py`, `docs/card-game-special-relic-assertions-v0.1.json` | Nova suite de especiais e relíquias | 11 handlers especiais adicionais, seis relíquias e um caso de bloqueio. | Verificar o caminho de resolução de especiais/relíquias. | Diagnóstico apenas. | 18/18 passaram. |
| `docs/scripts/assert-leader-effects-v0.1.py`, `docs/card-game-leader-assertions-v0.1.json` | Nova suite para líderes | Dez handlers positivos e 12 casos negativos/limite. | Fechar a ausência de testes da ação de líder. | Diagnóstico apenas; usa `aplicar_jogada(action="leader")`. | 22/22 passaram. |
| `docs/scripts/audit-stale-identity-branches-v0.1.py`, `docs/card-game-stale-identity-disposition-v0.1.md/.json` | Classificação de ramos antigos | Separados 18 V18, quatro campos legados e seis ramos V75, total 28. | Evitar exclusão prematura sem conferir cartas/tags. | Nenhuma remoção funcional. | AST/runtime confirmou decomposição 18+4+6. |
| `docs/scripts/assert-combo-and-faction-passive-v0.1.py`, `docs/card-game-combo-faction-assertions-v0.1.json` | Nova suite de combos/passivas | 87 cenários sobre os 27 combos e quatro passivas; um par concreto por combo. | Verificar o resolvedor de combos e regra global de facção no estado sintético. | Somente harness/JSON; nenhum efeito no runtime. | 87/87 passaram; pares alternativos/precedência sobreposta não exauridos. |
| `docs/scripts/audit-combo-overlap-v0.1.py`, `docs/card-game-combo-overlap-v0.1.json/.md` | Auditoria histórica de pares/trincas | Congelou o comportamento pré-política: 67 unidades, 4.422 pares, 287.430 trincas, bônus posterior a não participante e ativação solo. | Adicionado fail-fast no script atual; JSON/Markdown preservados como registro histórico. | Evitar executar sobre o runtime pós-política e confundir a saída com baseline. | Só reproduz em checkout pré-política; relatório pós-patch v0.2 é a autoridade atual. |
| `docs/scripts/summarize-card-game-behavior-v0.2.py`, `docs/card-game-behavior-validation-v0.2.md/.json` | Agregador e relatório consolidado | Soma/valida sete suites e agrega auditoria estática. | Manter um resultado único reproduzível para o handoff. | Ferramenta e docs apenas. | 219 asserts, 219 aprovados, 0 falhas. |

## Validações da etapa documental pré-política (histórico)

- `build-effect-source-map-v0.1.py` foi executado no baseline pré-política e seu JSON foi congelado. No runtime atual, o gerador recusa execução; consulte o mapa atual v0.2 (59 genéricos, 56 handlers diretos, 2 hooks, 1 sem handler, 22 identidades, 10 líderes e 27 combos).
- As sete suites comportamentais foram executadas: 219 asserts passaram, nenhum falhou. Os casos são sintéticos e selecionados; não representam 219 habilidades únicas nem cobertura completa. Os 27 combos foram testados com um par ativador concreto cada; todas as quatro passivas de facção foram testadas com unidade estrangeira, primeira/segunda unidade e reset de rodada.
- `audit-combo-overlap-v0.1.py` foi executado no baseline pré-política e seu JSON/Markdown foram congelados. Após o patch, o script recebeu fail-fast no checkout atual; os achados antigos não representam a regra vigente. A política agora está aprovada/implementada e a auditoria atual é v0.2.

- O script de mapa de fonte passou por `py_compile`.
- Resultados anteriores de custo, combo, cobertura e smoke permanecem incluídos; seus métodos e limites estão descritos em `card-game-balance-validation-v0.1.md`.
- Hashes dos principais módulos funcionais continuam iguais ao baseline; nenhuma alteração de runtime, API, DB, frontend ou imagem foi feita nesta etapa.
- Histórico: o ZIP mestre da revisão stateful anterior continha **198 arquivos/entradas** e passou em `unzip -t`, sem erros. A revisão atual passou a **226 entradas (212 arquivos + 14 diretórios)** e foi verificada com `unzip -t` sem erros. A comparação com `soulsbo-main(1).zip` confirmou 143 arquivos não documentais do projeto byte a byte idênticos; apenas três fontes tipográficas (`DejaVuSans*.ttf`) foram intencionalmente excluídas. Caches Python, bytecode, bancos locais, `.env` preenchido e binários locais de fontes são excluídos. O único arquivo de exemplo de ambiente é `.env.r2.example`, com valores de credenciais vazios.

## Limitações do baseline e decisões ainda não aprovadas

- EFP, custo individual, raridade, orçamento 32, `leader_load`, inclusão de relíquia e definição de especiais continuam propostas.
- Nenhuma amostragem de custo ou frequência de combos substitui partidas completas nem comprova equilíbrio.
- Nove modelos estão excluídos da amostragem de custo por IDs sem score/canonicalização.
- O contrato HTTP de custo ainda está incompleto: sem orçamento em `POST /deck` e sem `custo` no dicionário final de `preparar_carta()`. Corrigir somente após aprovar a regra/schema.
- A semântica dos combos foi decidida e implementada após esse baseline; consulte `card-game-combo-policy-v0.1.md`. Já foram testadas quatro partidas controladas de três rodadas pelo motor em memória, mas continuam pendentes partidas com decks legais do builder, integração HTTP/API/DB assíncrono, convites, IA, recompensas, browser, arte/R2 e simulação competitiva por facção. Os 251 asserts e 12 cenários stateful são testes automatizados de escopo controlado, não prova de equilíbrio ou integração em produção.
- DB de produção, credenciais/configuração, ambiente publicado, estado R2 e artes aprovadas não vieram no ZIP-fonte.
- Histórico Git do código original não foi fornecido; não inventar a procedência de código legado.
- Nenhum artefato diagnóstico substitui testes de integração no ambiente publicado.

## Histórico desta revisão — mapa estático HTTP Gwent

| Arquivo | Função/campo/trecho | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `docs/scripts/audit-gwent-http-contracts-v0.1.py` | AST de rotas/handlers e `preparar_carta()` | Sem índice reproduzível de endpoints Gwent e conexões frontend/DB/motor | Script identifica 12 rotas e gera JSON/Markdown; foi corrigido para detectar chamadas diretas ao motor por nomes AST | Completar a rastreabilidade bot/site/motor sem declarar integração não executada | Apenas docs/harness; sem impacto no runtime | 12 rotas; `deck_cost_budget_enforced=false`; `prepared_payload_includes_cost=false` |
| `docs/card-game-http-contract-map-v0.1.md/.json` | Novos relatórios | Inexistentes | Contratos, campos, handlers, custos e fluxos de partida inventariados | Tornar pendências visíveis ao próximo chat | Apenas handoff | Gerados e revisados contra fonte |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem, pendências e histórico | Foco parava na análise stateful | Novo estado HTTP estático no topo; etapa stateful preservada como anterior; custo payload ausente explicitado | Atualizar continuidade e evitar que o próximo chat repita análise | Documentação somente | 12 rotas e limitações cruzadas; testes separados preservados |

## SHA-256 dos arquivos funcionais — referência atual

- `sistemas/cartas.py`: `3bed48cbd496de431d92b76653518bda54a59ae5ee7ec8586b448b9fd19a0192`
- `sistemas/gwent.py`: `f69e8865759862ddc5bef9ff26ee2ddb43bcfbe33d3e61c985d4b118c6e42383`
- `bot.py`: `a735b2380176a5871f45770d99489825c587033d4a0d760b48b108a6e2a885ff`
- `database.py`: `ead936a2813335e5a98b31276a9e08ea6dc3a6121543300dd24decc7d69a3ed2`
- `site/app.js`: `9aafa6ba1ef2641fce9ab169192b27d28b92d2b92ee15881ca5db9984b39386b`
