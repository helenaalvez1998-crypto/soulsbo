# Card Engine v2 — auditoria do ciclo de vida de remoção v0.1

**Status:** `ALPHA_BEHAVIOR_REVIEWED; NO_NEW_DEATH_RULE_ADDED`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev21.zip`

## Conclusão

As remoções explícitas existentes no Card Engine v2 alpha já implementam as transições aprovadas dos Grupos C e F dentro do escopo permitido. Não há uma regra aprovada de HP individual nem de destruição automática de unidades pelo dano do combate por fileira. O dano de combate incide somente em `life_by_player`.

## Comportamentos presentes

- O `GameplayResolver` valida o enum fechado de causas aprovado antes de qualquer mutação. No controlador alpha atual, a ação `unit.remove` está configurada apenas para `execution`; `unit.sacrifice` está configurada para `sacrifice`. Uma ação normal de `normal_removal` ainda não foi exposta como ação própria no `AlphaMatchController`.
- A transição remove a instância física exata de `board` para `discard`.
- Grants `board_exit` são expirados na saída do campo.
- Contadores são separados: `board_removal_count` para `normal_removal`/`execution`; `sacrifice_count` para `sacrifice`.
- Proteção bloqueia `normal_removal`/`execution` conforme perfil; `sacrifice` faz bypass conforme decisão aprovada.
- Vingança ocorre somente após remoção bem-sucedida e atinge sobreviventes na fileira original; em remoções múltiplas, todos os resultados diretos são resolvidos antes dos efeitos reativos.
- `round_archive` move unidades de `board` para `discard`, expira grants de saída e não incrementa contadores de remoção nem dispara Vingança.
- O retorno ao campo possui regras aprovadas no Grupo C (bônus, fileira e normalização), mas ainda não está exposto como ação geral no controlador alpha.

## Limites detectados

1. O combate de `combat.py` compara poder efetivo por fileira e aplica diferença à vida dos jogadores; não gera dano por unidade.
2. Não existe evento canônico `unit_died` ou estado terminal de unidade. O evento implementado é `unit_removed`; chamar remoção de “morte” confundiria transferência para descarte com morte definitiva.
3. Execução e sacrifício funcionam no recorte alpha; os efeitos de retorno Ressurgir/Réquiem/Esgar não estão expostos como ações gerais da partida alpha.
4. O contrato v7 continua draft e não congelado. A aprovação documental C/F não equivale a integração completa de todos os efeitos legados.

## Decisão de engenharia

Não adicionar HP por unidade, dano por ataque, armadura, `unit_died`, destruição automática nem novas causas de remoção sem especificação de jogo aprovada. Manter os nomes e eventos atuais (`unit_removed`, `unit_archived`) distintos.

## Evidências

- `docs/card-game-state-lifecycle-group-C-approval-v0.1.md`
- `docs/card-game-removal-causes-group-F-approval-v0.1.md`
- `docs/card-engine-v2-combat-alpha-v0.1.md`
- `docs/card-engine-v2-sacrifice-match-alpha-v0.1.md`
- `sistemas/card_engine_v2/gameplay.py`
- `sistemas/card_engine_v2/zones.py`
- `sistemas/card_engine_v2/combat.py`
