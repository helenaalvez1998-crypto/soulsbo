# Card Engine v2 — sacrifício normal no controlador alpha v0.1

**Status:** `ISOLATED_ALPHA_IMPLEMENTATION_NOT_PRODUCTION_READY`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev20.zip`  
**Revisão resultante:** rev. 21 (2026-11-28)  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado e não congelado  
**Ruleset:** `alpha-test-only.ruleset.v0.2` (sem alteração)

## Objetivo

Conectar o handler genérico `unit.sacrifice` do `GameplayResolver` ao fluxo de ações do `AlphaMatchController`, mantendo a semântica aprovada no Grupo F e usando o mesmo caminho transacional, CAS e idempotência das demais ações da partida alpha.

## API interna do controlador

### Oferta

`AlphaMatchController.sacrifice_target_offer(match_id, actor_player_id=...)`

- Só está disponível ao jogador cujo turno está ativo.
- Usa a `TargetPolicy` de aliado no campo (`manual_single`).
- A oferta é produzida pelo servidor e contém `state_revision`, candidatos e métricas de exibição.
- Não aceita identidade de alvo fornecida pelo cliente para construir a lista.

### Confirmação

`AlphaMatchController.sacrifice_unit(match_id, actor_player_id=..., target_instance_id=..., expected_revision=..., operation_id=...)`

- Exige UUIDv4 para a instância-alvo e `expected_revision` da oferta mais recente.
- A execução revalida o alvo e a propriedade durante a transação.
- O request externo interno é registrado como `match.sacrifice_unit`; ele é encaminhado à ação registrada `unit.sacrifice` com causa `sacrifice`.
- A oferta obsoleta resulta em `rejected/revision_conflict`, sem mutar snapshot, runtime ou journal.
- A operação aprovada consome uma ação do turno alpha e alterna para o próximo jogador elegível. Se o oponente já passou, o jogador ativo continua podendo realizar ações até também passar, conforme o ciclo existente.
- O custo atual é somente `turn_consumed=true`. Energia, moedas, custo de carta e limite de sacrifícios por rodada não foram adicionados.

## Semântica de remoção preservada

A implementação reutiliza `GameplayResolver._resolve_removal`; não duplica a lógica de transição de zona.

- Causa aceita: somente `sacrifice` para esta ação.
- Alvo: uma instância aliada que ainda está no campo.
- Transição: `board` → `discard`, pelo `instance_id` físico exato.
- Proteção: sacrifício ignora escudo/Égide; a carga protegida não é consumida pelo bypass.
- Contador: incrementa `sacrifice_count`; `board_removal_count` permanece inalterado.
- Vingança: após remoção bem-sucedida, dispara `effect.vengeance_on_removal` uma vez e aplica o grant aos aliados sobreviventes na fileira original. A remoção direta e o evento reativo mantêm fontes e causalidade distintas.
- Idempotência: replay da mesma `operation_id` e fingerprint retorna o recibo persistido e não repete efeitos.

## Eventos

- `unit_removed`: evento direto, `payload.cause_id="sacrifice"`, transição de `board` para `discard`.
- `vengeance_bonus_applied` ou `vengeance_triggered_no_targets`: evento reativo causal, quando a unidade removida carrega `effect.vengeance_on_removal`.
- `turn_action_completed`: evento de sistema que identifica `action="sacrifice_unit"`, causa `sacrifice` e número do turno; é causado pelo último evento da resolução.

Snapshot, runtime, operação e eventos são persistidos pelo mesmo `SQLiteMatchRepository.execute_operation` transaction boundary.

## Testes adicionados

`tests/card_engine_v2/test_playable_match.py`:

1. `test_sacrifice_is_a_revision_bound_turn_action_and_replays_idempotently` — oferta autoritativa, transição, contador, consumo do turno e replay.
2. `test_sacrifice_bypasses_egide_and_triggers_vengeance_for_survivors` — bypass de escudo, preservação da carga, Vingança na mesma fileira e causalidade.
3. `test_stale_sacrifice_offer_is_rejected_without_removing_target` — rejeição por revisão obsoleta sem mutação.

## Validação da revisão

- `py_compile` de módulos, scripts e testes: aprovado.
- Suíte Card Engine v2: 120/120 testes aprovados (baseline rev. 20: 117/117).
- Script `test-card-engine-v2-playable-alpha-v0.4.py`: aprovado.
- Validação de staging histórico v0.2: aprovada; 137 modelos, 27 alpha-only e 110 bloqueados.
- Simulação Bo3 v0.3: Player A vence 2–1; SQLite `quick_check`, `integrity_check`, foreign keys e sequências aprovados.
- Demonstração combo/passiva/líder v0.1: aprovada; 25 eventos e SQLite íntegro.
- Nenhum banco publicado, runtime Discord/HTTP/frontend ou motor legado foi acessado.

## Limites

- O sacrifício agora é uma ação interna funcional do controlador alpha, não uma interação já disponível no Discord ou frontend.
- O custo é apenas o turno; não existe sistema integral de energia/recursos/limites por rodada.
- A ação é um primitive alpha independente. Não autoriza inferir nem ativar automaticamente o catálogo de efeitos de sacrifício histórico ainda bloqueado.
- Morte de unidade, HP/armadura individual, exaustão de deck, catálogo integral, integração de rede e migração continuam pendentes.
- O motor legado permanece preservado; nenhum dos cinco arquivos centrais foi intencionalmente alterado nesta revisão.
