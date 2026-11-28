# Pacote de continuidade — leia primeiro

> **AVISO PARA UM CHAT NOVO: ESTE PACOTE FOI PREPARADO EXPRESSAMENTE PARA QUE OUTRO CHAT/AGENTE ASSUMA O DESENVOLVIMENTO DO ZERO, SEM ACESSO A ESTA CONVERSA E SEM DEPENDER DE EXPLICAÇÕES ADICIONAIS DO USUÁRIO.** O ZIP contém o código-fonte disponível e os documentos de contexto necessários para retomar a auditoria e a reconstrução do jogo de cartas. Trate o conteúdo deste pacote como o ponto de partida da nova sessão; não peça ao usuário para repetir informações que já estejam documentadas.



## Estado atual para continuação (2026-11-27)

A revisão documental mais recente produziu um mapa estático de 12 rotas Gwent em `card-game-http-contract-map-v0.1.md/.json`, gerado por `scripts/audit-gwent-http-contracts-v0.1.py`. O mapa identificou que o backend ainda não soma custo no salvamento de deck e que `preparar_carta()` descarta `payload['custo']` porque não o retorna. A integração HTTP real continua pendente por ausência de `discord.py`/`aiosqlite` e bloqueio de DNS na instalação.

A política de combos v0.1 foi aprovada pelo usuário e já está implementada em `sistemas/gwent.py`. O novo chat deve tratá-la como regra oficial atual, não como decisão pendente. Os 27 combos agora têm mínimo explícito de duas instâncias distintas e prioridade única; a carta que recebe o bônus individual precisa contribuir com tag exigida; apenas um combo ativa por jogada; combos pendentes exigem um participante posterior. Os demais parâmetros de balanceamento (EFP, custos, raridade e teto de deck) continuam propostas não aprovadas.

**Última validação:** oito suites comportamentais, 251/251 asserts; separadamente, a suíte stateful passou 12/12 cenários. Foram percorridas quatro partidas controladas de três rodadas pelo motor em memória, com snapshots JSON; 137/137 modelos foram preparados; também foram verificados combo por jogadas normais, líder + especial climático, relíquia, clima manual, compatibilidade de snapshot legado e round-trip de `state_json` com DDL real em SQLite `:memory:`. A verificação bot/site é estática: os handlers HTTP e o wrapper assíncrono de banco não foram executados porque `discord.py` e `aiosqlite` não estão instalados no ambiente de análise. A instalação temporária via `pip` foi tentada e falhou por indisponibilidade de DNS/rede; não foram criados mocks ou stubs. Não confundir esses testes controlados com partidas competitivas, DB ou produção.

Partidas já persistidas preservam bônus de combos concedidos antes do deploy. A política nova vale nas próximas jogadas resolvidas após atualização do processo; o DB de produção não veio no ZIP e não foi migrado.

## Instrução de entrada para o próximo chat

Ao receber este pacote, faça o seguinte antes de alterar qualquer arquivo:

1. Confirme que recebeu e conseguiu abrir `soulsbo-main-handoff.zip`.
2. Leia este arquivo (`docs/README-PACOTE-CONTINUIDADE.md`) e depois siga a **Ordem obrigatória de leitura** abaixo.
3. Leia `docs/card-game-handoff.md` integralmente, inclusive o quadro de completude dos quatro blocos da Regra 8, o estado exato, o histórico e os próximos passos.
4. Consulte a auditoria, matriz de 137 cartas, catálogo EFP, especificação v0.1 e script/amostragem. Não deduza regras ausentes a partir de nomes ou de conversas anteriores.
5. Diferencie sempre: (a) comportamento comprovado no código-base, (b) requisito confirmado pelo usuário, (c) proposta ainda não aprovada e (d) hipótese que exige teste.
6. Não implemente nem remova mecânicas antes de validar as pendências registradas no handoff. Não trate `card-game-balance-spec-v0.1.md` como especificação aprovada.
7. Antes de encerrar qualquer etapa, atualize os documentos afetados, registre cada alteração por arquivo/função/campo/motivo/impacto/validação e gere um novo ZIP mestre com o projeto e todos os documentos necessários.

**Mensagem inicial sugerida para o novo chat:**

> Leia integralmente `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/card-game-mapping-audit.md` e os documentos referenciados. Assuma a continuidade do projeto a partir deste pacote, sem depender do chat anterior. Primeiro informe o estado comprovado, as lacunas conhecidas e o próximo passo autorizado. Trate `card-game-combo-policy-v0.1.md` como política de combos aprovada e implementada. Não reverta nem redecida essa política sem solicitação explícita. Diferencie-a das propostas EFP/custo/raridade ainda não aprovadas. Em toda entrega, atualize e forneça um único ZIP mestre.

Este pacote contém uma cópia do projeto-fonte disponível e toda a documentação de auditoria/continuidade produzida para o trabalho de reconstrução do jogo de cartas. Use este arquivo como índice de entrada quando iniciar um novo chat ou agente.

## Manifesto do pacote

Consulte também [`docs/PACOTE-MANIFESTO.md`](PACOTE-MANIFESTO.md) para escopo, modificações e validações desta revisão.

## Ordem obrigatória de leitura

1. `docs/card-game-handoff.md` — estado atual, política de combo aprovada, histórico da implementação, compatibilidade e próximos passos.
2. `docs/card-game-combo-policy-v0.1.md` — contrato oficial dos 27 combos, tabela de prioridades, mínimos, destinatário do bônus e decisões implementadas.
3. `docs/card-game-behavior-validation-v0.3.md/.json` + `docs/scripts/summarize-card-game-behavior-v0.3.py` — oito suites, 251/251 asserts comportamentais isolados.
4. `docs/card-game-match-snapshot-integration-v0.1.md/.json` + `docs/scripts/assert-full-match-stateful-v0.1.py` — 12/12 cenários stateful: quatro partidas controladas de três rodadas, snapshots, líderes/especiais/clima, relíquia, compatibilidade e DDL SQLite. Limite: HTTP real não executado.
5. `docs/card-game-http-contract-map-v0.1.md/.json` + `docs/scripts/audit-gwent-http-contracts-v0.1.py` — mapa estático das 12 rotas; registra o contrato de custo ausente. Não substitui teste HTTP real.
6. `docs/card-game-combo-overlap-v0.2.md/.json` + `docs/scripts/audit-combo-overlap-v0.2.py` — auditoria enumerativa após a correção.
7. `docs/scripts/assert-combo-policy-v0.1.py` + `docs/card-game-combo-policy-assertions-v0.1.json` — regressões específicas da política aprovada.
8. `docs/card-game-mapping-audit.md` — mapa da arquitetura, arquivos, APIs, banco, eventos, habilidades, combos, líderes, relíquias e falhas remanescentes.
9. `docs/card-game-effect-source-map-v0.2.json` + `docs/scripts/build-effect-source-map-v0.2.py` — mapa AST atual. O v0.1 é histórico congelado; seu script recusa sobrescrita no runtime pós-política.
10. Suites individuais e relatórios JSON: `card-game-effect-behavior-assertions-v0.1.json`, `card-game-identity-behavior-assertions-v0.1.json`, `card-game-generic-unit-assertions-v0.1.json`, `card-game-lifecycle-assertions-v0.1.json`, `card-game-special-relic-assertions-v0.1.json`, `card-game-leader-assertions-v0.1.json`, `card-game-combo-faction-assertions-v0.1.json` e `card-game-combo-policy-assertions-v0.1.json`, junto dos scripts homônimos.
11. `docs/card-game-stale-identity-disposition-v0.1.md/.json` + script — classificação de 28 ramos antigos; recomendações, não remoções.
12. `docs/card-game-card-traceability.md/.csv/.json` — matriz dos 137 modelos do baseline. Confirmar se algum campo derivado precisa ser regenerado após futuras alterações ao catálogo.
13. `docs/card-game-effect-score-catalog.json` e `docs/card-game-efp-methodology-v0.2.md` — EFP preliminar/metodologia, ainda não aprovados.
14. `docs/card-game-balance-spec-v0.1.md` e `docs/card-game-balance-validation-v0.1.md` — propostas e validação exploratória de custo/raridade; não implementadas.
15. `docs/card-game-deck-cost-sampling-v0.2.json` + script e `docs/card-game-combo-activation-v0.1.json` + script — amostragens exploratórias, não simulações competitivas.
16. `docs/card-game-combo-overlap-v0.1.md/.json` — **auditoria histórica congelada do baseline pré-correção**. O script v0.1 está arquivado e recusa execução no runtime atual para não sobrescrever o baseline; somente um checkout pré-política pode reproduzi-lo. Para o estado atual, use o script/relatório v0.2.
17. `docs/card-game-handler-coverage-v0.1.json`, `docs/card-game-effect-runtime-smoke-v0.1.json` e scripts associados — cobertura estática e smoke tests com limites declarados.
18. Os demais arquivos de `docs/` — documentação preexistente; conferir as advertências do handoff antes de tratá-los como regra atual.

## Resumo de orientação da proposta de balanceamento v0.1

> A proposta é **rascunho técnico, não aprovada e não implementada**. Não aplicar estes números ao runtime sem simulação e aprovação do usuário.

- **Poder:** unidades com `power_base` entre 1 e 15; especiais com `power_base=null` é uma convenção proposta, ainda sujeita à confirmação.
- **Pureza:** mínimo de `ceil(0,30 × N_modelos)`; usando 137 modelos e considerando especiais inelegíveis, a proposta aponta para 42 unidades puras. Uma meta operacional de 35% também é sugerida.
- **EFP:** escala provisória para estimar poder, remoção, compra, ressurreição, escudo, purificação, movimento e combos. Scores são hipóteses; `null` significa efeito incompleto/não validado, não efeito zero.
- **Custo:** unidades `C = clamp(ceil((P + 2E) / 3,5), 1, 10)`; especiais `C = clamp(ceil((2E) / 3,5), 1, 10)`.
- **Deck:** teto experimental 32 foi testado em cenários de 12 cartas + `leader_load`, com e sem relíquia equipada. A inclusão de relíquia e carga do líder no orçamento, bem como o teto, ainda não foi aprovada. As regras atuais do deck builder (12 cartas, mínimo 8 unidades, máximo 4 especiais) permanecem distintas da proposta.
- **Raridade:** `R = 2P + 3E + 0,5(10-C)`, com faixas de Comum a Singular documentadas no spec. Raridade não deve aumentar secretamente a força do efeito.
- **Distribuição:** manifesto versionado por `card_id`; nenhuma seleção mecânica por sorteio/hash. RNG, se mantido, apenas para cosméticos.
- **Lore/facções:** Ordem Áurea, Véu Carmesim, Lua Negra e Os Esquecidos têm diretrizes temáticas próprias; lore separada da descrição mecânica.

A amostragem de 100.000 decks é uma análise de distribuição de custo, **não** simulação de partidas nem prova de equilíbrio. A primeira amostragem v0.1 está superada; o v0.2 inclui cenários com/sem relíquia, mas ainda depende de EFP estimado. A frequência de combos foi medida separadamente sob ordem aleatória; isso não mede efeito no resultado. Consulte `card-game-balance-validation-v0.1.md` antes de qualquer alteração.

## Estado desta entrega

- Baseline do projeto: ZIP recebido `soulsbo-main(1).zip`, datado no registro da auditoria como 2026-11-27; pacote mestre atualizado após cada etapa.
- Trabalho funcional concluído nesta etapa: política de combos v0.1 aprovada e implementada em `sistemas/gwent.py`. Nenhum outro arquivo funcional, schema de banco, endpoint, frontend ou imagem foi modificado.
- Regras atuais de combos: `minimum: 2` em todas as 27 definições; `priority` único; carta atual contribui com tag requerida; uma ativação por jogada; combo pendente só dispara por participante posterior; bônus individual para a carta participante; bônus de equipe existente preservado.
- Diagnósticos atuais: mapa estático das 12 rotas Gwent, sem dispatch HTTP real; oito suites comportamentais, 251/251 asserts; separadamente, integração stateful 12/12. Quatro partidas controladas de três rodadas percorreram o motor em memória; 137 payloads foram preparados; combo por jogadas normais, líder/especial/clima, relíquia, clima manual, snapshot legado e round-trip de `state_json` passaram. A análise bot/site é estática e HTTP não foi executado.
- Trabalho documental: regra oficial de combos, relatório pós-política, regressões, mapa de fonte AST e mapa estático das 12 rotas HTTP atualizados; auditorias pré-patch preservadas como histórico.
- Limitações: o `POST /api/gwent/deck` ainda não calcula orçamento; `preparar_carta()` não devolve `custo` e descarta esse atributo dos payloads que o recebem antes da preparação. A análise é estática; partidas ativas conservam bônus já concedidos; DB de produção, credenciais, configuração de execução, estado publicado de R2 e artes aprovadas não vieram com o ZIP. Não houve migração/inspeção de produção.
- Próximos passos: obter um ambiente com `discord.py==2.7.1` e `aiosqlite==0.22.1` instalados (ou wheels locais, pois o pip não alcançou o índice por falha de DNS nesta sessão); executar dispatch HTTP real com `aiohttp.TestClient`, persistência pela classe `Database`, convites, solo/IA, autenticação e recompensas; validar respostas no browser e imagens/R2. Depois ampliar partidas para decks legais obtidos pelo deck builder, testar interações cruzadas/IA e só então simular equilíbrio e calibrar EFP/custo/raridade. A proposta de balanceamento v0.1 permanece não aprovada.
- `docs/CARD_GAME_REDESIGN.md` permanece documentação antiga e não deve prevalecer sobre o motor nem sobre regras aprovadas no handoff.

## Regra de continuidade

A cada nova entrega, atualizar os documentos afetados e recriar um único ZIP contendo o projeto disponível e todos os materiais de handoff. O arquivo mais recente é a referência; não exigir que o próximo chat consulte mensagens anteriores. Consulte `docs/card-game-handoff.md`, seção **Regra permanente de pacote de continuidade**.

## Exclusões conscientes do pacote

Arquivos de cache Python (`__pycache__`, `*.pyc`) e binários locais de fontes tipográficas não são incluídos neste pacote de handoff. O código-fonte e as referências a esses recursos permanecem presentes. O pacote é destinado à continuidade da análise e desenvolvimento; para validar renderização visual pixel a pixel, os assets tipográficos originais do ambiente do projeto podem ser necessários.
