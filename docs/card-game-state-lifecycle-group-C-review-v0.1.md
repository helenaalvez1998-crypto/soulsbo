# Grupo C — Auditoria de ciclo de vida, estados e duração v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev9.zip`  
**Status:** `TECHNICAL_PROPOSAL_FOR_OWNER_REVIEW_NOT_APPROVED`  
**Aprovações mantidas:** Grupos A e B.  
**Runtime/DB/API/frontend alterados:** não.  
**Contrato v0.3 congelado:** não.

## 1. Objetivo

Fechar a auditoria técnica que alimenta CI-008/009, BUF-008/009/010/011/014 e RSRX-07/08/10. Este relatório não aprova automaticamente as recomendações: descreve evidências do legado, identifica lacunas do candidato e apresenta políticas explícitas para decisão do proprietário.

## 2. Evidências confirmadas no motor legado

### 2.1. Bônus, escudo e estados não têm uma única política de ciclo de vida

`_remover_unidade()` (`sistemas/gwent.py:995-1018`) retorna cedo quando o escudo bloqueia a remoção. Nesse caminho, a zona não muda e os estados permanecem; apenas uma carga do escudo é consumida. Quando a remoção é bem-sucedida, limpa `escudo` e os quatro contadores (`sangramento`, `geada`, `podrida`, `loucura`), move a unidade para o descarte e incrementa `baixas`. Preserva `bonus`, `weather_resist` e `combo_ativado`.

Sacrifício usa o mesmo caminho, mas ignora o teste de escudo. Logo, sacrifício limpa estados/escudo e move para descarte; a semântica de Vingança foi aprovada no Grupo B com lista final de causas ainda dependente do Grupo F.

### 2.2. Encerramento normal e terminal divergem

No fechamento não terminal (`_resolve_round`, linhas 1153–1202), as unidades que ainda estão no campo são copiadas ao descarte ou retidas por Glória. Nas cópias afetadas, o motor zera bônus, escudo e os quatro estados, e remove `combo_ativado`. `weather_resist` permanece. O laço não percorre cartas que já estavam no descarte, mão ou pilha; assim, uma unidade removida antes do encerramento pode levar bônus antigo ao descarte e mantê-lo após a transição de rodada.

No encerramento terminal, `_resolve_round()` define `status/phase = finished` e retorna nas linhas 1146–1152 antes da limpeza não terminal. O snapshot final pode, portanto, manter bônus, escudos, estados, marcadores e clima transitórios. Isso é comportamento do código, não regra aprovada.

**Implicação:** `round_close` deve ser um evento global da partida aplicado às instâncias de todas as zonas, após congelar o resultado da rodada. A limpeza terminal também precisa ocorrer depois do snapshot imutável de pontuação. Se a interface precisar exibir o último campo sem limpeza, deve usar o snapshot de resultado, não manter estados transitórios ativos no estado operacional.

### 2.3. Estados negativos

`status-registry-candidate.v1.json` descreve quatro estados, cada contador com teto 2. Geada, Podridão e Loucura integram uma penalidade combinada com teto 3; Sangramento não reduz diretamente poder efetivo. As consequências de limiar são propostas para ocorrer somente na transição de menos de duas para duas marcas. Todos têm expiração `round_close`, limpeza em remoção bem-sucedida e purificação seletiva.

O módulo `sistemas/card_status_candidate.py` valida e aplica essa proposta, e os 41 testes existentes passaram. Entretanto, o módulo ainda representa as marcas como contadores sem origem/instante por aplicação e calcula clima lendo `weather_resist` escalar. É um resolvedor isolado e não está integrado ao motor.

A auditoria anterior identificou duas diferenças de comportamento que precisam continuar explícitas: Malenia pode repetir a corrosão quando o alvo já está no limite; Oráculo da Geada pode conceder bônus ao aplicador mesmo quando a marca não aumentou. A proposta de transição de limiar elimina essas repetições, mas essa mudança permanece pendente de aprovação.

### 2.4. Resistência climática

`_poder_efetivo()` (`sistemas/gwent.py:987-992`) aplica `max(0, weather_level - weather_resist)`. `weather_resist` é um inteiro escalar. `vigil_seal` atribui 1; o branch genérico `resistencia_climatica` atribui 2, mas a aprovação BUF-012 exige binding ativo verificado antes de promover um branch legado a capacidade do catálogo novo. O escalar não permite distinguir valor intrínseco da carta de buff temporário, nem registrar origem e expiração.

A resistência escalar não é limpa por `_remover_unidade()` nem pelo reset normal de rodada. Portanto, a persistência observada não prova que `vigil_seal` deva ser permanente. O novo contrato precisa separar `intrinsic_weather_resistance` de `weather_resistance_modifiers[]` com `source_effect_id`, `source_instance_id`, `amount`, `applied_event_id` e `expires_on`.

### 2.5. Escudos e proteção

O escudo legado é um contador `escudo`. A remoção comum e execução são bloqueadas pelo ponto central; sacrifício passa direto. Aplicações de Geada, Podridão, Sangramento e Loucura não consultam escudo como regra geral. Há exceções locais em duas relíquias:

- Noite/Chama: o escudo consome uma carga e bloqueia a alteração de poder/bônus; a ativação da relíquia é consumida mesmo bloqueada.
- Lâmina Negra: o escudo consome uma carga e bloqueia a redução; a relíquia não é consumida.

As exceções locais não justificam proteção universal contra estados ou debuffs. O novo sistema deve separar `protection_category`, perfil de proteção, consumo da carga e custo/consumo da ação causadora.

### 2.6. Bônus e limites

O `bonus` é um escalar agregado. O legado usa pisos distintos: em diversos efeitos -2, em Podridão/Loucura 0, e em outros não há clamp explícito. `BonusTrackedDict` tenta registrar texto heurístico da origem de alterações, limitado aos 100 registros mais recentes; não substitui o ledger append-only de eventos aprovado no Grupo B e não informa duração por origem.

No encerramento normal, bônus de unidades ainda no campo é zerado. Unidades já removidas para o descarte não entram nesse laço. A nova regra deve declarar `clamp_policy_id` por efeito/regra de balanceamento e expiração de bônus independentemente da zona.

### 2.7. Posição e sequência

O contrato v0.3 já separa `printed_row` (DefinitionSnapshot) e `current_row` (estado). O audit de sequência estabeleceu que `last_row` legado pertence ao jogador/rodada: atualiza na jogada bem-sucedida de unidade, não na movimentação, carta especial nem retorno; limpa na transição da rodada. Proposta: renomear semanticamente para `last_unit_play_row`; `current_row` é posição atual; opcionalmente manter `last_board_row` para retorno quando a instância estiver fora de `board`.

### 2.8. Retorno do descarte

- Ressurgir e Réquiem zeram bônus e removem escudo, mas não limpam explicitamente estados legados stale.
- Esgar força a fileira escolhida, soma +1 ao bônus salvo, remove escudo e zera os quatro estados.
- Lágrima Sagrada move o mesmo objeto para a mão sem normalização adicional; no caminho normal de remoção, escudo/estados já foram limpos, enquanto bônus e resistência climática sobreviveram.
- Nenhum desses retornos reexecuta hooks de entrada, passiva de facção ou combo no momento da chegada. Unidades retornadas podem participar de verificações de combo em jogadas futuras.

## 3. Proposta de políticas para revisão

### 3.1. Matriz de transição

| Transição | Política candidata |
|---|---|
| Movimento no campo | Atualizar somente `current_row`; preservar bônus, escudo, estados e modificadores ainda válidos; não atualizar `last_unit_play_row`. |
| Remoção bloqueada | Consumir uma carga compatível; manter zona/estados/bônus; emitir evento `blocked`; não gerar remoção nem Vingança. O custo da carta/relíquia é decidido separadamente por efeito. |
| Remoção/sacrifício bem-sucedido | Mover a mesma instância ao descarte; limpar estados transitórios e concessões de proteção; manter bônus round-scoped até seu evento de expiração; preservar resistência intrínseca; expirar modificadores `board_exit` apenas. |
| Recuperação para a mão | Mover a mesma instância sem hooks de entrada; preservar apenas modificadores ainda válidos conforme `expires_on`; não acrescentar limpeza implícita além da transição que criou o descarte. |
| Ressurreição ao campo | Limpar estados transitórios e proteção; aplicar bônus/fileira por efeito; manter resistência intrínseca e modificadores não expirados; não repetir on-play/passiva/combo. |
| Fechamento de rodada | Depois de congelar pontuação, expirar todos os estados/modificadores `round_close` em todas as instâncias e zonas; limpar marcadores de combo e `last_unit_play_row`; aplicar também na última rodada. |
| Purificação | Remover somente `status_id`s listados no efeito purificador; bônus, escudos e resistência não são alterados sem outputs declarados separados. |

### 3.2. Resistência climática

Forma recomendada (conceitual; não é schema aprovado):

- `intrinsic_weather_resistance`: atributo da definição imutável (ausência equivale a zero na versão do catálogo);
- `weather_resistance_modifiers[]`: modificadores da instância com `source_effect_id`, `source_instance_id`, `amount`, `applied_event_id` e `expires_on`;
- resistência efetiva = atributo intrínseco + modificadores ativos, limitado a zero mínimo;
- duração de `vigil_seal` requer decisão explícita: `board_exit` (enquanto estiver no campo), `round_close` ou `permanent_instance`. Não inferir permanência a partir do escalar legado.

Não migrar o branch genérico `resistencia_climatica` como efeito ativo sem binding verificado, conforme BUF-012 aprovado.

### 3.3. Escudo

Recomendação de política:

- Perfil padrão bloqueia `unit_removal` e `execution`.
- `sacrifice` bypassa o perfil padrão.
- Status/debuffs ignoram escudo salvo se o efeito recebido declarar explicitamente uma interação bloqueável.
- A checagem é centralizada; o perfil define categoria(s) e a operação define `consume_charge_on_block`.
- Cada concessão de proteção deve carregar `grant_id`, `profile_id`, `charges`, fonte, `applied_event_id` e `expires_on`; `shield_charges` pode ser uma projeção agregada.
- `action_cost_on_block` pertence à carta/relíquia causadora e não deve ser deduzido do consumo da carga de escudo.
- As exceções de Noite/Chama e Lâmina Negra devem ser declaradas explicitamente por efeito, preservando ou substituindo o comportamento atual apenas mediante decisão de balanceamento.

### 3.4. Bônus

Manter `bonus` como projeção inteira do estado, mas respaldada por concessões rastreáveis (`bonus_grants[]`) ou reconstruível sem ambiguidade pelo ledger causal. Cada concessão deve registrar `grant_id`, `amount`, `source_effect_id`, `source_instance_id`, `applied_event_id`, `clamp_policy_id` e `expires_on`; eventos registram delta, valor anterior/novo e política de clamp. O balance release e/ou effect params declaram pisos/tetos explícitos. Não criar um piso/teto global oculto. Um evento `round_close` expira apenas concessões com `expires_on=round_close`, em todas as zonas, inclusive descarte e mão; efeitos explicitamente permanentes não são apagados por conveniência.

Os contadores de estados negativos podem continuar como projeções para leitura rápida, mas a origem, aplicação, consumo e expiração de cada marca precisam ser reconstruíveis por eventos ou registros de aplicação. O limiar deve ser disparado pela transição de contagem, não por cada chamada repetida quando o alvo já está no teto.

### 3.5. Ressurreição

Políticas candidatas por efeito:

| Efeito | `bonus_policy` | `row_policy` | Estado de entrada |
|---|---|---|---|
| Ressurgir | `reset_to_zero` | preservar última fileira válida; fallback para fileira escolhida válida; senão melee | estados e escudo limpos |
| Réquiem | `reset_to_zero` | preservar última fileira válida; fallback para fileira escolhida válida; senão melee | estados e escudo limpos |
| Esgar | `previous_bonus_plus_one` (espelha o legado; requer aprovação) | `force_requested_row` | estados e escudo limpos |
| Lágrima Sagrada | não é ressurreição; transferência para mão | guardar última fileira válida para eventual retorno | manter estado remanescente válido, sem hooks de entrada |

Todos mantêm o mesmo `instance_id` e a mesma definição congelada. Nenhum retorno dispara novamente Vingança, passiva de facção, habilidade de entrada ou combo no próprio momento da chegada.

## 4. Decisões pendentes do Grupo C

| ID | Decisão proposta | Questão que exige aceite |
|---|---|---|
| CI-008 | `transition_policy_id` versionada para cada transição; expiração global por zona, após snapshot da pontuação, inclusive em partida terminal. | Confirmar expiração de concessões `round_close` fora do campo e na última rodada. |
| CI-009 / BUF-011 | Resistência intrínseca na definição; modificadores temporários com origem, evento de aplicação e expiração. | Escolher a duração de `vigil_seal`: `board_exit`, `round_close` ou `permanent_instance`. |
| BUF-008 | `printed_row`, `current_row`, `last_board_row` e `last_unit_play_row` têm semânticas distintas. | `last_board_row` será projeção persistida (recomendado) ou derivada do último evento de movimento/transição? |
| BUF-009 | Escudo por categoria, sem imunidade universal; padrão para remoção/execução e sacrifício faz bypass. | Manter as exceções explícitas de Noite/Chama e Lâmina Negra ou aposentá-las? |
| BUF-010 | Resolver de proteção centralizado; custo da ação separado do consumo da carga. | Confirmar consumo de uma carga compatível quando o bloqueio ocorre e mapear o custo de cada efeito. |
| BUF-014 | Bônus com grants/origem/expiração e `clamp_policy_id` por efeito/release; sem clamp global oculto. | Aprovar a estrutura, não os números; confirmar expiração de grants `round_close` em todas as zonas. |
| RSRX-07 | Ressurgir/Réquiem usam `reset_to_zero`; Esgar usa `previous_bonus_plus_one`. | Manter o +1 de Esgar somado ao bônus anterior ou entrar com exatamente +1? |
| RSRX-08 | Ressurgir/Réquiem preservam última fileira válida; Esgar força a escolhida. | Confirmar fallback para melee quando não há contexto válido e a fileira forçada de Esgar. |
| RSRX-10 | Retorno limpa estados/proteções transitórios, aplica política por efeito, mantém resistência intrínseca e modificadores ainda válidos; não repete hooks de entrada. | Definir o tratamento de modificadores `board_exit`, `zone_exit` e `permanent_instance` durante saída/retorno. |

**Recomendação operacional:** bônus, escudos e marcas devem ser projeções de concessões/aplicações com fonte e expiração explícitas. Isso evita tentar inferir duração retrospectivamente a partir de um escalar agregado. A expiração da rodada é um evento de sistema posterior ao snapshot de resultado, nunca uma consequência acidental de copiar apenas a lista `board`.

### Resolução preferida para aprovação

| Decisão | Caminho recomendado |
|---|---|
| CI-008 | `round_close` global após snapshot; todas as zonas e rodada terminal; expirar apenas grants marcados `round_close`. |
| CI-009 | Resistência intrínseca no `DefinitionSnapshot`; modificadores temporários separados, com origem e expiração. |
| BUF-008 | Persistir `last_board_row` como projeção; manter `last_unit_play_row` separado no estado do jogador/rodada. |
| BUF-009/010 | Escudo padrão bloqueia remoção/execução; sacrifício bypassa; exceções das duas relíquias ficam explícitas; uma carga é consumida no bloqueio, mas custo da ação é separado. Noite/Chama consome a ativação; Lâmina Negra não. |
| BUF-011 | `vigil_seal` expira em `board_exit`. É uma mudança de design proposta; o legado não prova essa duração. |
| BUF-014 | `bonus_grants` rastreáveis e `clamp_policy_id` por efeito/release; sem limites globais implícitos. |
| RSRX-07 | Ressurgir/Réquiem: `reset_to_zero`; Esgar: `previous_bonus_plus_one`, com o +1 em grant/evento próprio. |
| RSRX-08 | Ressurgir/Réquiem preservam `last_board_row`, com fallback para row solicitada e depois melee; Esgar força a row solicitada e inválida é rejeitada. |
| RSRX-10 | Retorno limpa status/proteção, aplica bônus/fileira por efeito, preserva grants ainda ativos e não repete hooks de entrada. |

Este caminho é recomendação para simplificar o contrato. Os dez IDs continuam pendentes até aprovação explícita do proprietário.

## 5. Regressões já reexecutadas

| Suite | Resultado |
|---|---:|
| Harness do Grupo C — evidência, decisão e fixture | 43/43 |
| Grupo A — identidade | 30/30 |
| Grupo B — snapshot/causalidade | 20/20 (artefato anterior; escopo preservado) |
| CardInstance v0.3 + Grupo B | 42/42 |
| Matriz cruzada | 272/272 |
| Estados candidatos | 41/41 |
| Remoção/ressurreição | 49/49 |

Os resultados são de suites estáticas/sintéticas ou do runtime em memória; não representam integração DB/API/Discord ou partidas de produção. O Grupo C continua sem aprovação e o resolvedor candidato permanece isolado.

## 6. Guardrails e próximos passos

- Não alterar o runtime legado nem os módulos candidatos existentes nesta revisão.
- Não congelar schema v4 nem publicar release de estados/proteção antes do aceite do Grupo C.
- Não alterar regras aprovadas de Grupo A/B; raridade permanece exclusivamente classificatória e causalidade segue o ledger do Grupo B.
- Depois do aceite, atualizar CardInstance para v0.4 (draft), schemas e fixtures; depois avançar aos grupos D/F/E.
