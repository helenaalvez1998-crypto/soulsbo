# Grupo F — Auditoria de causas de remoção, sacrifício e Vingança v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev12.zip`  
**Status:** `AUDITED_READ_ONLY; DECISIONS_PENDING_OWNER_APPROVAL`  
**Runtime/DB/API/catálogo/frontend:** sem alterações.

## 1. Escopo

O Grupo F fecha a semântica de saída do campo e seus efeitos causais. A matriz de dependências anterior lista CI-008/011/014, BUF-009/010 e RSRX-03/04/05/10 como bloqueadores de `removal_sacrifice_resolver`. O Grupo D foi aprovado nesta revisão; o Grupo E continua responsável por persistência concorrente, CAS, ledger durável, replay e migração.

Esta auditoria lê o motor legado, os call sites ativos e o registry candidato. Reproduz cenários em memória e não promove o registry candidato a regra aprovada.

## 2. Evidências do motor legado

### 2.1 Resolvedor central

`_remover_unidade(side, unit, causa="remocao")` em `sistemas/gwent.py:995-1021`:

1. Retorna sem efeito se a unidade não está no campo.
2. Se `causa != "sacrificio"` e há escudo, consome uma carga e não remove a unidade, não a envia ao descarte, não incrementa `baixas` e não dispara Vingança.
3. Caso contrário, remove a unidade do campo, remove seu escudo, zera `sangramento`, `geada`, `podrida` e `loucura`, envia a unidade ao descarte e incrementa `baixas`.
4. Depois da remoção bem-sucedida, verifica `unit.get("habilidade") == "vinganca"` e concede +1 de bônus a cada aliado remanescente na mesma fileira.

A condição de escudo é binária e especial-cased para sacrifício. O método não valida um enum fechado de `causa`: qualquer string diferente de `"sacrificio"` cai no caminho de remoção comum/escudável. O teste com `round_close_archive` reproduz esse comportamento permissivo.

### 2.2 Causas e call sites ativos

| Causa canônica candidata | Alias legado | Call sites observados | Escudo | Vingança após sucesso |
|---|---|---|---|---|
| `normal_removal` | `remocao` / default | Chama Negra (`gwent_queima`, linha 1620) | Bloqueia e consome 1 carga | Sim |
| `execution` | `execucao` | Lâmina da Morte Destinada (`gwent_execucao`, linha 1638) | Bloqueia e consome 1 carga | Sim |
| `sacrifice` | `sacrificio` | Preço em Sangue (linha 598), Rykard (1433), Devorar (1876) | Ignora escudo | Sim |

A lista de três causas também aparece no `data/card_game/removal-resurrection-registry-candidate.v1.json`, que permanece `CANDIDATE_FOR_REVIEW_NOT_APPROVED`.

### 2.3 Vingança e escudo

- Vingança só dispara depois de uma saída bem-sucedida pelo resolvedor central.
- Uma tentativa bloqueada por escudo não remove, não incrementa `baixas` e não dispara Vingança.
- Sacrifício ignora escudo; se a unidade sacrificada tem `habilidade == "vinganca"`, a habilidade dispara.
- O bônus é aplicado aos aliados remanescentes na mesma fileira, uma vez por unidade removida com Vingança.
- Duas unidades diferentes com Vingança removidas em duas operações geram dois disparos independentes.

### 2.4 Rykard e saídas compostas

O handler `rykard_devour` em `sistemas/gwent.py:1427-1436` escolhe a unidade aliada mais fraca da fileira, chama `_remover_unidade(..., "sacrificio")` e depois concede +2 de bônus às unidades remanescentes da fileira.

Quando a vítima possui Vingança, o comportamento legado observado é:

1. Evento reativo de Vingança: +1 aos aliados remanescentes da mesma fileira.
2. Evento direto do líder Rykard: +2 aos aliados remanescentes da fileira.
3. Os dois outputs se acumulam; o total observado para cada sobrevivente elegível é +3.

A causalidade já foi aprovada no Grupo B como separação de fontes/eventos. A aditividade e os valores numéricos não foram congelados como balanceamento: são proposta do Grupo F e devem continuar parâmetros explícitos em release.

### 2.5 Contador `baixas`

O mesmo incremento `side["baixas"] += 1` é executado para remoção comum, execução e sacrifício bem-sucedidos. Tentativas bloqueadas e alvos que já não estão no campo não incrementam. Portanto, `baixas` não significa “mortes”; mistura saídas por efeito, execução e sacrifício.

### 2.6 Arquivamento de rodada não é remoção

`_resolve_round()` (`sistemas/gwent.py:1113-1195`) calcula e registra a pontuação antes de arquivar unidades. No ramo não terminal, as unidades são copiadas ao descarte diretamente; `_remover_unidade` não é chamado e `baixas` não é incrementado. É uma transição de ciclo de vida/arquivamento, não uma remoção causada por carta e não deve disparar Vingança.

No ramo terminal, `_resolve_round()` marca o estado como concluído e retorna antes de arquivar o campo. Este comportamento legado não altera a distinção semântica: encerramento/arquivamento não é uma causa de remoção para Vingança. A regra global de `round_close` já aprovada no Grupo C é a referência para o novo sistema.

### 2.7 Efeitos que não são remoção

Noite/Chama reduz poder/bônus e Lâmina Negra reduz bônus; seus blocos não chamam `_remover_unidade`. Não devem ser modelados como `normal_removal`, nem disparar Vingança apenas por modificar poder ou bônus.

### 2.8 Identidade e nomenclatura do efeito

O legado identifica Vingança por `habilidade == "vinganca"`, não por `effect_id` no snapshot da definição. O registry candidato usa `effect.vengeance_on_removal`, enquanto o exemplo histórico v4 usa `unit.vengeance_on_removal` em `source_effect_id`. Há drift de nomenclatura que precisa ser corrigido no contrato/exemplo futuro; esta auditoria não altera os artefatos históricos v4.

## 3. Decisões propostas para aprovação

O registro estruturado está em `docs/card-game-removal-causes-group-F-decisions-v0.1.json`. Todas as decisões abaixo permanecem `PENDING_OWNER_APPROVAL`.

### FCAUSE-001 — Causas elegíveis de Vingança

**Recomendação:** disparar Vingança uma vez depois de uma saída bem-sucedida causada por `normal_removal`, `execution` ou `sacrifice`. Não disparar em tentativa bloqueada por escudo, alvo ausente, movimento, recuperação/ressurreição ou `round_archive`.

**Motivo:** é compatível com o comportamento legado comprovado e com o registry candidato, sem confundir arquivamento/alteração de bônus com remoção.

### FCAUSE-002 — Contadores semânticos

**Recomendação:** substituir no novo domínio a ambiguidade de `baixas` por projeções derivadas dos eventos: `board_removal_count` para `normal_removal` + `execution`, e `sacrifice_count` separado. Se houver necessidade de compatibilidade, `legacy_baixas = board_removal_count + sacrifice_count` será apenas adaptador. `round_archive` não entra em nenhum desses contadores. Não usar nomes que impliquem morte.

### FCAUSE-003 — Vingança e Rykard como outputs aditivos separados

**Recomendação:** preservar dois eventos distintos quando a mesma resolução sacrifica uma unidade com Vingança: output reativo de Vingança e output direto de Rykard. Ambos podem atingir os mesmos sobreviventes e se acumulam sem deduplicação entre fontes. Os valores +1 e +2 observados devem ser parâmetros explícitos do release; o total +3 é evidência de legado, não balanceamento congelado.

### FCAUSE-004 — Enum fechado de causas e arquivamento separado

**Recomendação:** o novo resolver aceita somente `normal_removal`, `execution` e `sacrifice` como causas de remoção. Aliases legados são traduzidos por adaptador (`remocao`/default, `execucao`, `sacrificio`). `round_archive` é evento de transição de zona/ciclo de vida, nunca `cause_id` de remoção. Causa desconhecida é erro interno de contrato antes de mutação/commit; não deve cair silenciosamente no caminho normal.

### FCAUSE-005 — ID canônico de Vingança

**Recomendação:** adotar `effect.vengeance_on_removal` como `effect_id` canônico, porque já está no registry candidato; mapear `habilidade == "vinganca"` apenas como compatibilidade legada durante conversão/adapter. Corrigir o uso de `unit.vengeance_on_removal` em futuros exemplos/contratos novos, sem reescrever o fixture v4 histórico.

## 4. Relação com decisões já aprovadas

- **Grupo B:** aprovou a separação causal de Vingança e Rykard e a remoção da amplificação por raridade. Não aprovou a lista definitiva de causas nem congelou o +1/+2.
- **Grupo C:** aprovou políticas de limpeza e retorno, incluindo `round_close` e `board_exit`; não definiu causas de Vingança.
- **Grupo D:** aprovado; request/offer/result, outcomes e custos são aplicáveis, mas os códigos finais de causa e parâmetros por carta ainda dependem do registry/release.
- **Grupo E:** continua aberto para CAS, persistência, ledger durável, replay, rollback e migração. Esta auditoria não testa concorrência real.

## 5. Resultados e limites

- Grupo F: **29/29** verificações passaram.
- Suites reproduzem comportamento legado, handlers reais em memória e consistência de registry/exemplo.
- Os testes não significam que as propostas estejam aprovadas nem que o novo resolver esteja implementado.
- Não houve HTTP, Discord, SQLite real, R2, concorrência multi-processo ou execução de produção.
- Os testes de Rykard/Devour/Preço em Sangue usam fixtures em memória; o banco/catalogo ativo não foi alterado.

## 6. Guardrails

- Nenhuma alteração em `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, catálogo ativo ou registry candidato.
- Nenhuma migração, API, resolvedor, ledger persistente ou integração foi criada.
- O runtime antigo permanece referência comportamental até aprovação de F e fechamento de E.
- O Grupo F não autoriza por si só a substituição do motor legado.

## 7. Próximo gate

Aprovar ou ajustar FCAUSE-001 a FCAUSE-005. Depois, incorporar a semântica aprovada em `CardInstance v0.6` como draft. O Grupo E permanece pendente e será necessário antes de integração/migração real.
