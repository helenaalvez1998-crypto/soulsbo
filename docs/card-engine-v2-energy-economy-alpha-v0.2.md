# Economia de energia — Card Engine v2 alpha v0.2

**Ruleset ativo:** `data/card_game/card-engine-v2-alpha-ruleset.v0.5.json` (`alpha-test-only.ruleset.v0.5`).  
**Status:** implementação alpha funcional; os preços por ID são experimentais e não aprovados para release.

## Regra de energia

- Energia inicial configurada: 0.
- O jogador recebe +1 no início de cada turno individual.
- Máximo: 5.
- O saldo persiste entre rodadas até ser gasto.
- O jogador que inicia a partida recebe seu primeiro ponto ao iniciar o primeiro turno; o outro jogador recebe energia quando seu primeiro turno começa.
- Energia, turnos iniciados e pagamentos são persistidos no runtime sidecar da partida; não há mudança de `CardInstance v0.7`, schema SQLite ou DDL.

## Custos ativos no ruleset alpha v0.5

A baseline possui uma tabela provisória com 27 preços por `card_id` e dez preços por `leader_id`. Os preços de cartas variam de 1 a 5; os custos de líderes variam de 2 a 3. A tabela completa e sua justificativa estão em `docs/card-engine-v2-alpha-energy-cost-schedule-v0.1.md` e no JSON hash-pinado pelo `AlphaCatalog`.

Os preços são propostas para playtest controlado, ainda sem validação humana/telemetria e sem aprovação de balanceamento final. Eles foram estimados por poder-base e impacto/alcance de efeitos implementados, condicionalidade e oportunidade de ação consumida. Raridade e `deck_cost_legacy` são explicitamente excluídos como entradas do cálculo.

## Cobrança e recusa

- `play_unit` e `play_special` cobram o custo do `card_id` exato.
- `activate_leader` cobra o custo do `leader_id`; cada líder continua limitado a uma ativação por partida e a ativação consome o turno.
- `activate_card_ability` só é permitido para um `ability_id` cadastrado no registry server-side, com preço explícito e alvo ofertado pelo servidor.
- Preço ausente, ID não permitido ou saldo insuficiente rejeita a ação. Não há ação não precificada liberada gratuitamente na baseline v0.5.
- Uma ação rejeitada não consome carta, energia, uso, ativação ou turno.
- Efeito aceito e débito de energia são gravados na mesma transação; o evento `player_energy_spent` registra o pagamento.
- Sacrifício segue sendo ação de turno sem custo de energia nesta alpha.

## Habilidades manuais

O registry ativo (`card-engine-v2-alpha-activated-abilities.v0.1.json`) está vazio: nenhuma das 27 cartas alpha declara habilidade manual. Efeitos `unit_on_play` acontecem quando a carta entra em campo e não podem ser ativados de novo pelo novo endpoint. A API genérica está testada com uma habilidade sintética isolada, não cadastrada no jogo.

## Testes e limites

- A suíte principal desta revisão: 150/150 testes.
- Um teste percorre cada uma das 27 cartas e dos dez líderes, aceitando o saldo exato e rejeitando o saldo imediatamente inferior.
- Testes de unidade adicionais verificam cobrança de unidade, especial e líder, persistência, limite máximo, idempotência e rejeições sem mutação.
- As simulações reproduzíveis de gameplay usam uma fixture uniforme de custo 1 exclusivamente para isolar combate, efeitos, combos e passivas; essas simulações não validam o equilíbrio dos preços da tabela provisória. Os testes de economia usam o schedule real por ID.
- A integração segue restrita ao `AlphaMatchController` isolado. Não há Discord/HTTP/frontend, banco publicado, adapter assíncrono, telemetria nem playtests humanos nesta entrega.

A revisão da tabela deve ocorrer depois de partidas controladas. Não interpretar os preços atuais como balanceamento final.
