# Registry de habilidades manuais — Card Engine v2 alpha v0.1

**Status:** registry de produção alpha deliberadamente vazio; infraestrutura de ativação testada isoladamente.  
**Arquivo estruturado:** `data/card_game/card-engine-v2-alpha-activated-abilities.v0.1.json`.  
**Ruleset:** `alpha-test-only.ruleset.v0.5`.

## Resultado da auditoria

As 27 cartas atualmente permitidas possuem efeitos `unit_on_play` ou comportamento passivo já executado pelo runtime. Nenhuma declara uma habilidade individual que o jogador possa ativar manualmente depois de a carta entrar em campo.

Por isso, `abilities` permanece vazio. Não transformamos efeitos de entrada em habilidades repetíveis e não inventamos novas ações para as cartas.

## Infraestrutura genérica disponível

A API de `AlphaMatchController` suporta a ativação de uma habilidade que esteja explicitamente declarada no registry do servidor. A definição controla:

- `ability_id` e conjunto de `source_card_ids` permitido;
- `action_type` entre `unit.grant_bonus`, `unit.grant_protection`, `unit.remove` e `unit.move`;
- `TargetPolicy` e parâmetros definidos no servidor;
- custo explícito por habilidade;
- usos máximos por instância na partida (o contrato atual valida `uses_per_match`);
- consumo da ação/turno.

O cliente só informa a instância de origem e escolhas de alvo/linha que a oferta do servidor permitir. Não pode fornecer magnitude de bônus, duração, causa de remoção, perfil de proteção ou outros parâmetros mecânicos.

## Segurança e consistência

- A origem precisa pertencer ao jogador ativo e estar no campo.
- O servidor valida se o `card_id` da origem está na allowlist de fontes.
- A oferta é negada quando o jogador não tem energia suficiente ou quando a instância já esgotou seu limite de usos.
- A execução valida novamente estado, turno, preço e alvo dentro da transação.
- Débito, efeito, registro de uso e conclusão de turno são gravados atomicamente.
- Rejeições não consomem energia nem uso.
- Replays idempotentes não reaplicam o efeito nem o pagamento.

## Evidência de teste

`tests/card_engine_v2/test_activated_abilities.py` usa uma habilidade sintética `ability.alpha_test_rally` somente em uma fixture de teste. Essa fixture verifica oferta server-side, pagamento, bônus, limite de uso, replay e rejeição por saldo insuficiente. Ela não é incluída no registry alpha nem habilita habilidade real para qualquer carta.

## Próxima expansão

Quando uma carta ganhar uma habilidade manual aprovada, cadastrar uma definição própria no registry e preço próprio no schedule. Não reutilizar IDs de efeitos `on_play` como habilidade manual sem uma decisão de design explícita.
