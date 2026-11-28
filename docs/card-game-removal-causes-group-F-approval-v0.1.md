# Aprovação do Grupo F — causas de remoção, sacrifício e Vingança v0.1

**Status:** `OWNER_APPROVED`  
**Baseline auditado:** `soulsbo-main-continuity-2026-11-27-rev12.zip`  
**Aceite:** o proprietário respondeu “aprovo” imediatamente após o pedido explícito de aprovação de FCAUSE-001 a FCAUSE-005.  
**Runtime/DB/API/catálogo/frontend alterados:** não.

## 1. Escopo aprovado

O aceite cobre as cinco resoluções do registro `docs/card-game-removal-causes-group-F-decisions-v0.1.json`:

1. **FCAUSE-001 — Causas elegíveis de Vingança:** disparar uma vez depois de remoção bem-sucedida por `normal_removal`, `execution` ou `sacrifice`; não disparar por bloqueio, arquivamento, movimento, recuperação ou ressurreição.
2. **FCAUSE-002 — Contadores separados:** derivar `board_removal_count` de `normal_removal` + `execution`, e `sacrifice_count` de `sacrifice`. O adaptador legado calcula `baixas = board_removal_count + sacrifice_count`; `baixas` não é contador de mortes. `round_archive` não entra em nenhum dos dois.
3. **FCAUSE-003 — Vingança/Rykard separados e aditivos:** `effect.vengeance_on_removal` e `leader.rykard_devour` produzem outputs causais independentes que podem se acumular no mesmo alvo. Os valores observados (+1 e +2) não são congelados; permanecem parâmetros de release.
4. **FCAUSE-004 — Enum fechado de causas:** aceitar apenas `normal_removal`, `execution` e `sacrifice` no resolvedor de remoção. Aliases legados são tratados somente no adaptador. Valores desconhecidos falham antes de mutar o estado. `round_archive` é evento de transição de zona separado, não causa de remoção.
5. **FCAUSE-005 — ID canônico de Vingança:** usar `effect.vengeance_on_removal`. `habilidade == "vinganca"` é apenas alias de leitura/migração. O fixture histórico v4 permanece preservado como evidência.

## 2. Fronteiras da aprovação

- A aprovação não congela os parâmetros numéricos de Vingança/Rykard nem cria orçamento de balanceamento.
- Não autoriza alterar `_remover_unidade`, handlers, registry ativo, catálogo, bot, API, banco ou frontend.
- Não fecha o Grupo E: persistência, CAS, idempotência durável, outbox e migração continuam pendentes.
- O comportamento legado reproduzido permanece evidência histórica; a regra aprovada é a semântica candidata do novo motor.

## 3. Consequência documental

O Grupo F pode ser incorporado ao draft `CardInstance v0.6`. A validação de schema/harness não equivale a implementação, migração, teste HTTP ou produção.
