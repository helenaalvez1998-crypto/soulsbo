# Validação comportamental do motor de cartas — v0.3 (pós-política de combos)

> **STATUS: validação sintética pós-alteração funcional.** A política de combos foi aprovada pelo usuário e implementada em `sistemas/gwent.py`. Os asserts executam funções reais do motor em estados controlados em memória; não são teste de integração de produção nem prova de equilíbrio competitivo.

- Data: 2026-11-27.
- Runner: `docs/scripts/summarize-card-game-behavior-v0.3.py`.
- Relatório JSON: `docs/card-game-behavior-validation-v0.3.json`.
- Runtime modificado: sim, exclusivamente `sistemas/gwent.py` nesta etapa funcional.

## 1. Resultado agregado

**251/251 asserts aprovados em 8 suites; zero falhas.**

| Suite | Assertions | Aprovados | Falhas |
|---|---:|---:|---:|
| Initial representative effect cases | 13 | 13 | 0 |
| 22 active identity effects plus negative/limit cases | 33 | 33 | 0 |
| Generic unit effects, selected positive and negative cases | 39 | 39 | 0 |
| Removal and round-end lifecycle effects | 7 | 7 | 0 |
| Selected special effects and all six relic handlers | 18 | 18 | 0 |
| All ten leader handlers plus negative/limit cases | 22 | 22 | 0 |
| All 27 combos plus four faction passives and special exclusion | 87 | 87 | 0 |
| Approved combo policy: explicit priority, tag contribution, two participants, pending combo targeting, public play entrypoint | 32 | 32 | 0 |
| **Total** | **251** | **251** | **0** |

As contagens representam cenários, não efeitos únicos. Há sobreposição deliberada entre suites; especialmente, a suite combo/facção cobre a ativação básica e a suite da política cobre invariantes novos.

## 2. Política de combos validada

Ver `card-game-combo-policy-v0.1.md`.

- Os 27 combos têm `minimum: 2` explícito.
- Os 27 combos têm `priority` inteiro único; menor número resolve primeiro.
- A carta recém-jogada precisa contribuir com ao menos uma tag exigida pelo combo específico.
- O mínimo conta instâncias distintas de unidades participantes; uma carta híbrida não vale como dois participantes.
- No máximo um combo por jogada. Um combo pendente só pode ser ativado por jogada posterior que também contribua com tag exigida.
- O bônus individual vai para a carta participante que ativa o combo. `team_bonus` existente continua indo para aliados na mesma fileira.
- `synergy_used` continua limitando uma ativação de cada combo por jogador/rodada e é resetado no fechamento da rodada.

A suite nova tem 32 assertions: 27 tentativas solo (uma por combo), integridade de mínimos/prioridades, precedência independente da ordem de inserção, sequência pendente com uma carta não participante e uma carta participante posterior, deduplicação de instância e uma jogada de integração via `aplicar_jogada(action="play")`.

## 3. Auditoria enumerativa pós-correção

O script `docs/scripts/audit-combo-overlap-v0.2.py` reproduz a enumeração completa do universo observado de cartas com tags:

| Medida | Resultado pós-política |
|---|---:|
| Unidades atuais com tags | 67 |
| Combos | 27 |
| Ativações solo | 0 |
| Pares ordenados examinados | 4,422 |
| Pares com múltiplos combos elegíveis | 152 |
| Trincas ordenadas examinadas | 287,430 |
| Trincas que ativam pelo menos dois combos | 2,582 |
| Eventos posteriores analisados | 2,582 |
| Eventos posteriores com tag exigida | 2,582 |

A política elimina os casos solo e os acionamentos posteriores por cartas sem tag exigida no universo enumerado. Ainda há sobreposições legítimas; elas são resolvidas por prioridade explícita. Os detalhes, exemplos e comparação com o baseline estão em `card-game-combo-overlap-v0.2.md/.json`.

## 4. Alterações funcionais e compatibilidade

- `SYNERGY_COMBOS` em `sistemas/gwent.py`: adicionado `priority` único e `minimum: 2` explícito em todas as 27 definições; descrições de participação atualizadas.
- `_aplicar_combo_de_cartas()`: filtragem por tag exigida da carta atual, contagem de instâncias distintas, ordenação explícita por prioridade e uma ativação por jogada.
- Não houve mudança no schema de banco, deck builder, endpoints, frontend, imagens, custo, raridade ou valores de bônus.
- Partidas persistidas conservam bônus já concedidos antes da atualização. A política nova se aplica às novas resoluções de jogada após o deploy; não foi possível inspecionar DB/produção.

## 5. Limitações

- Suites sintéticas em memória; não validam 12 cartas completas, snapshots serializados, HTTP, browser, Discord, DB de produção, Cloudflare R2 nem artes publicadas.
- A suite nova cobre um exemplo de sobreposição pendente, além dos 27 casos solo. Não executa todas as sequências de 12 cartas.
- A enumeração cobre pares e trincas de IDs distintos, não todas as combinações de deck/partida.
- Os asserts não estimam valor esperado, EFP, taxa de vitória ou equilíbrio por facção.
- As 28 ramificações antigas de identidade seguem sem decisão de keep/merge/redesign/remove; `gloria` e `sobrevivente` permanecem pendências separadas.
- Banco de produção, configuração operacional, estado de R2 e imagens aprovadas não vieram no pacote fonte.

## 6. Próximos passos

1. Estender regressões a sequências stateful de 12 cartas e pares sobrepostos adicionais.
2. Testar serialização/desserialização de snapshots e o payload de `/api/gwent/cards` após a mudança de descrição.
3. Definir o tratamento operacional de partidas já ativas no deploy.
4. Cobrir clima, mudanças de rodada, IA e interações cruzadas.
5. Resolver destino das 28 ramificações antigas e dos hooks `gloria`/`sobrevivente`.
6. Construir simulador determinístico de partidas por facção; só depois calibrar EFP, custos, raridades e orçamento de deck.
