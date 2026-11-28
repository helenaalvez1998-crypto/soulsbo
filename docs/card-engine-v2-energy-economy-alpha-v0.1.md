# Card Engine v2 — economia de energia alpha v0.1

**Status:** implementado no runtime alpha isolado; parâmetros sujeitos a balanceamento e não aprovados para publicação.  
**Ruleset:** `alpha-test-only.ruleset.v0.4`.  
**Baseline de entrada:** revisão 23.

## 1. Referência de regras e decisões preservadas

`docs/CARD_GAME_REDESIGN.md`, seção 10, define o início do turno com ganho de 1 energia até o máximo de 5, seguido de jogar cartas pagando energia e ativar habilidades. O ruleset alpha v0.4 implementa o ciclo básico de energia.

A decisão aprovada no Grupo B (`docs/card-game-snapshot-causality-group-B-approval-v0.1.md`, BUF-001) estabelece que raridade é classificatória e não pode alterar parâmetros de execução. Portanto, `rarity_id`, `rarity_cost_table_legacy` e `RARITY_EFFECT_BUDGET` não são usados para calcular energia.

O campo histórico `deck_cost_legacy` pertence ao inventário/custo de construção de deck. Ele não é automaticamente convertido em custo de energia por turno. Alguns modelos também têm divergência entre `deck_cost_legacy` e `rarity_cost_table_legacy`, reforçando que esses campos não formam uma tabela de custo energético aprovada.

## 2. Regra ativa na alpha

- Energia inicial de cada jogador: 0.
- O jogador que inicia a partida começa com 1 energia, representando o primeiro ganho no início do seu turno.
- O outro jogador recebe 1 energia quando seu primeiro turno começa.
- Cada início subsequente de turno concede +1 energia.
- Limite de energia: 5.
- O saldo não é zerado no fechamento de rodada; permanece até ser gasto, limitado a 5.
- A energia é independente por jogador e fica no runtime sidecar persistido.
- `view()` expõe energia atual, máximo e quantidade de turnos iniciados.

A persistência usa o mesmo `state_revision`/CAS do estado da partida. Não houve alteração de `CardInstance v0.7`/schema 7, nem migração/DDL SQLite.

## 3. Custos explícitos

O ruleset contém dois mapas versionados e com chaves por identidade estável:

- `energy_economy.card_energy_cost_by_card_id`: custos de `play_unit` e `play_special`.
- `energy_economy.leader_activation_energy_cost_by_leader_id`: custos de `activate_leader`.

A baseline deixa ambos vazios. Assim, as 27 cartas alpha atuais continuam jogáveis sem cobrança, até que custos explícitos por ID sejam definidos e revisados. Isso evita transformar a tabela de raridade, o antigo custo de deck ou uma fórmula exploratória em custo energético sem aprovação.

Quando uma entrada explícita existe:

1. O controlador valida energia suficiente antes de executar qualquer efeito ou mutação de zona.
2. Energia insuficiente rejeita a operação sem consumir carta, ativação, turno ou saldo.
3. Após execução aceita, o custo é deduzido na mesma transação que persiste os eventos e a mudança de estado.
4. O custo não é reembolsado após a ação bem-sucedida.
5. O evento `player_energy_spent` registra ator, origem, ação, saldo anterior, valor gasto e saldo posterior.

Se a chave de custo não existe, a política de compatibilidade alpha permite a ação sem cobrança. A resposta indica `energy_cost_configured=false`, `energy_spent=0` e o saldo remanescente. Essa exceção é temporária e impede que cartas sem preço aprovado sejam acidentalmente bloqueadas.

Custos devem ser inteiros não negativos e não podem exceder o máximo de energia (5). Referências a cartas fora da allowlist ou a líderes fora do registry são rejeitadas ao carregar o catálogo.

## 4. Ações e limites

| Ação | Energia na baseline | Custo explícito suportado |
|---|---:|---|
| Jogar unidade | 0 se sem configuração | Sim, por `card_id` |
| Jogar especial | 0 se sem configuração | Sim, por `card_id` |
| Ativar líder | 0 se sem configuração | Sim, por `leader_id` |
| Sacrificar unidade | 0 | Não; consome a ação/turno já existente |
| Passar | 0 | Não |

A ativação de líder permanece limitada a uma vez por partida e consome a ação de turno conforme o contrato alpha já existente. O mapa de custo de líder permite cobrar energia quando houver valor explícito.

Ainda não existe uma API genérica de ativação de toda habilidade de carta. Esta revisão não inventa custos para habilidades que ainda não possuem uma ação de gameplay própria.

## 5. Integridade e eventos

O runtime valida:

- mapa de energia cobrindo exatamente os participantes;
- valores inteiros, não booleanos, entre zero e máximo;
- máximo de energia positivo;
- contador de turnos iniciados por jogador, com o mesmo conjunto de participantes e valores não negativos.

Eventos adicionados:

- `player_energy_gained`: início do turno, ganho efetivo, saldo e se o limite foi atingido;
- `player_energy_spent`: pagamento de ação, custo configurado e saldo posterior.

Os eventos são persistidos no journal append-only junto da operação. O saldo é parte do runtime JSON armazenado na mesma transação do snapshot.

## 6. Testes e limites

A suíte `tests/card_engine_v2/test_energy_economy.py` cobre ganho inicial e por turno, limite 5, persistência entre rodadas, cartas sem custo configurado, recusa por saldo insuficiente, pagamento de unidade/especial/líder, validação dos mapas de IDs e rejeição de runtime acima do limite.

Esta é uma infraestrutura funcional de energia, mas ainda não é economia completa: os mapas de custo de produção permanecem vazios; custos individuais das 27 cartas e dos dez líderes precisam de uma tabela de balanceamento explícita; habilidades genéricas ainda não têm uma ação universal; integração Discord/HTTP/frontend e playtests humanos não foram feitos.

## 7. Próxima prioridade

Construir uma tabela de custo energético por ID de carta, avaliada por poder-base, impacto real do efeito, tipo de carta e ritmo de compra — sem usar raridade como substituto. Revisar os dez líderes separadamente e, em seguida, definir a interface de ativação das demais habilidades. Só depois conectar essa economia ao catálogo ampliado e à integração externa.
