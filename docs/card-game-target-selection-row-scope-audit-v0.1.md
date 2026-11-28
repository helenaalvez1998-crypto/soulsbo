# Auditoria de seleção de alvos e escopo de fileira — v0.1

**Data:** 2026-11-27  
**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`  
**Escopo:** seleção de alvos em identidades ativas V75 e habilidades de líder; métricas de poder; filtros por lado, fileira corrente, estado e escudo; desempate por ordem de tabuleiro.

> Este relatório descreve o comportamento do runtime legado. Não aprova as regras observadas como design definitivo e não altera handlers, catálogo, banco, API ou frontend.

## 1. Resultado

**15/15 verificações passaram; zero falhas.**

A auditoria demonstra que “mais forte” e “mais fraco” não podem ser tratados como um seletor universal. Entre os efeitos ativos testados, a seleção pode ocorrer por:

- Poder efetivo, depois de filtrar lado, fileira, estado ou escudo.
- Bônus bruto, sem ordenar por poder efetivo.
- Escopo global de um campo ou restrição à fileira corrente/fixa.
- Um conjunto elegível de alvos, seguido de quantidade máxima e fallback.

O campo `row` é a posição corrente e governa os filtros de fileira. O campo legado `fileira` conserva a referência original; a movimentação pode separá-los. O histórico `last_row` do jogador é outro estado e não participa desses seletores por posição.

## 2. Evidência reproduzível

| ID | Caso | Resultado observado |
|---|---|---|
| TGT-001 | Poder efetivo | `poder + bonus - clima - estados`, com penalidade agregada de estados limitada a 3 e piso final de 1. `weather_resist` reduz o clima aplicado à `row` corrente. |
| TGT-002 | Fenda do Vazio | Seleciona o inimigo de maior poder efetivo em todo o campo adversário; a fileira escolhida para a carta não restringe esse alvo. |
| TGT-003 | Empate em `max()` | Quando dois alvos empatam na métrica, o primeiro na ordem atual da lista vence. |
| TGT-004 | Juramento Dourado | Filtra aliados por `row` corrente e escolhe o menor poder efetivo na mesma fileira. |
| TGT-005 | Marca da Dinastia | Filtra inimigos pela `row` corrente e seleciona o maior poder efetivo. Unidade movida para fora não permanece elegível apenas porque `fileira` conserva a origem; unidade movida para dentro passa a ser elegível. |
| TGT-006 | Cisalhamento Gravitacional | Filtra inimigos com bônus positivo e ordena por bônus bruto decrescente, não por poder efetivo. Quando atinge dois alvos, a própria carta recebe +1. |
| TGT-007 | Preço em Sangue | Escolhe o aliado de menor poder efetivo na `row` corrente; o ganho corresponde ao poder efetivo da vítima, com mínimo 1 e teto +3. Sacrifício remove a vítima pela rotina central. |
| TGT-008 | Regressão Serena | Filtra aliados da mesma `row` com ao menos um dos quatro estados e escolhe até dois de menor poder efetivo. Os estados são limpos e cada alvo recebe +1. |
| TGT-009 | Fallback de Regressão Serena | Sem aliado com estado na fileira, escolhe o aliado mais fraco da `row` corrente e concede +1. |
| TGT-010 | Fallback sem aliados | Sem alvo com estado e sem aliado na fileira, a própria carta recebe +1. |
| TGT-011 | Gravidade do Flagelo | Seleciona o inimigo de maior poder efetivo global, move sua `row` para a fileira da carta e reduz seu bônus. O campo `fileira` original não muda. |
| TGT-012 | Morgott | Seleciona até dois aliados sem escudo na fileira escolhida, ordenados pelo maior poder efetivo. Unidades com escudo são excluídas antes do ranking. |
| TGT-013 | Mohg | Seleciona os dois inimigos de maior poder efetivo na fileira escolhida; unidades mais fortes em outras fileiras não interferem. |
| TGT-014 | Astel | Aplica Geada a até três inimigos de maior poder efetivo na fileira escolhida. |
| TGT-015 | Loretta | Exige Longa Distância e fortalece as duas unidades de maior poder efetivo nessa fileira fixa. |

### 2.1 Fórmula legada de poder efetivo

Referência: `sistemas/gwent.py`, `_poder_efetivo()`.

```text
clima_aplicado = max(0, clima[row] - weather_resist)
estados = min(3, geada + podrida + loucura)
poder_efetivo = max(1, poder + bonus - clima_aplicado - estados)
```

Sangramento não aparece nessa fórmula. Ele pode atuar como filtro de elegibilidade para alguns efeitos, mas não reduz diretamente o poder efetivo neste helper.

## 3. Matriz de escopo e métrica

| Efeito ativo | Lado | Escopo/filtro | Métrica | Quantidade/fallback |
|---|---|---|---|---|
| `void_rend` / Fenda do Vazio | Inimigo | Campo adversário inteiro | Maior poder efetivo | 1; sem alvo, efeito sem alteração |
| `v75_golden_vow` / Juramento Dourado | Aliado | `row` corrente igual à fileira da carta | Menor poder efetivo | 1 aliado; a carta também recebe +1 |
| `v75_blood_mark` / Marca da Dinastia | Inimigo | `row` corrente igual à fileira da carta | Maior poder efetivo | 1 |
| `v75_gravity_shear` / Cisalhamento Gravitacional | Inimigo | `row` corrente e bônus positivo | Maior bônus bruto | Até 2; carta recebe +1 se atingir 2 |
| `v75_blood_price` / Preço em Sangue | Aliado | `row` corrente igual à fileira da carta | Menor poder efetivo | 1 sacrifício; sem alvo, carta recebe +1 |
| `v75_grace_mender` / Regressão Serena | Aliado | `row` corrente e algum estado ativo | Menor poder efetivo | Até 2; se nenhum status, menor aliado; sem aliado, carta recebe +1 |
| `star_gravity` / Gravidade do Flagelo | Inimigo | Campo adversário inteiro | Maior poder efetivo | 1; movimenta para a fileira atual da carta |
| Morgott | Aliado | `row` corrente e sem escudo | Maior poder efetivo | Até 2 |
| Mohg | Inimigo | `row` escolhida | Maior poder efetivo | Até 2 |
| Astel | Inimigo | `row` escolhida | Maior poder efetivo | Até 3 |
| Loretta | Aliado | `ranged` fixa | Maior poder efetivo | Até 2; ativação rejeitada se não houver alvo |

**Importante:** a matriz descreve apenas os casos testados e os filtros efetivamente encontrados. Não generalizar a métrica de poder efetivo para todos os handlers.

## 4. Vínculos ativos versus ramos arquivados

A execução de `_aplicar_habilidade_identidade()` depende de `CARD_IDENTITY_ABILITIES`. Logo após a declaração dessa tabela, o runtime filtra as entradas cujos IDs estão em `CARTAS_SEM_EFEITO_IDS` (`sistemas/gwent.py`, próximo à definição da tabela; origem em `sistemas/cartas.py`, V18).

Foram identificados ramos que permanecem escritos na função, mas não constituem atribuições ativas após esse filtro:

- `covering_shot` / Tiro de Cobertura (`arma_arco_peregrino`): a rastreabilidade da carta marca a identidade antiga como filtrada/desativada; a carta permanece com a habilidade geral `impeto` e suas tags de combo.
- `counterflame` / Contrafogo (`magia_chama_fria`): identidade antiga filtrada/desativada; a carta permanece com a habilidade geral `sangue_frio` e suas tags de combo.
- `v75_blood_pursuit` não tem vínculo ativo em `CARD_IDENTITY_ABILITIES`; o Caçador das Catacumbas de Mohgwyn é descrito como sem habilidade individual e participa de combo por tags.
- `v75_moon_ward` não tem vínculo ativo em `CARD_IDENTITY_ABILITIES`; a Guardiã do Juramento Lunar é descrita como sem habilidade individual e participa de combo por tags.

Esses ramos não foram tratados como regras ativas nem usados para aprovar semântica. Sua permanência no código é um item de limpeza/arquivamento futuro, não evidência de que as cartas os executem.

## 5. Achados e riscos de arquitetura

### 5.1 Métrica não é uniforme

Em alguns efeitos, “mais forte/mais fraco” significa `poder_efetivo`. Em Cisalhamento Gravitacional, o critério é explicitamente o bônus bruto positivo. O novo catálogo não deve ter um parâmetro genérico `strongest` que esconda a métrica.

### 5.2 Fileira deve ser um filtro explícito

Os handlers consultam `unit.row` para elegibilidade e clima. Movimento atualiza esse campo. `fileira` persiste como referência de origem e não deve ser usado implicitamente para seleção de alvos em campo.

### 5.3 Empates dependem hoje da ordem da lista

`max()`/`min()` mantêm o primeiro elemento empatado; `sorted()` é estável e preserva a ordem de entrada entre chaves iguais. Isso é reproduzível no estado em memória, mas deixa o resultado sujeito à ordem de array após reconstrução/serialização. O novo contrato deve declarar desempate estável por identidade de instância ou sequência de entrada/jogada.

### 5.4 Filtro, ranking e limite devem ser etapas distintas

A ordem lógica observada é: filtrar lado e escopo; aplicar elegibilidade (estado/escudo/bônus); ordenar por métrica específica; aplicar limite; resolver fallback ou ausência de alvo. Essa ordem deve ser explícita no catálogo, em vez de ficar implícita em comprehensions e chamadas isoladas a `max`, `min` ou `sorted`.

## 6. Requisitos candidatos para o novo contrato

Para efeitos com seleção automática, registrar explicitamente:

- `target_side`: `self`, `ally`, `enemy`, `any`.
- `row_scope`: `global`, `selected_row`, `fixed_row`, `different_from_selected_row`, ou equivalente tipado.
- `row_basis`: posição corrente (`current_row`), não posição-base, para alvos no campo.
- `eligibility`: filtros como `status_any`, `bonus_gt_zero`, `shield_absent`.
- `sort_metric`: `effective_power`, `base_power`, `bonus`, `played_order` ou métrica tipada adicional.
- `sort_direction`: `asc`/`desc`.
- `target_limit` e política para alvo parcial.
- `on_no_target`: `reject`, `consume_no_effect`, `fallback_self`, `fallback_weakest`, entre opções explicitamente aceitas.
- `tie_breaker`: identidade estável de instância/sequência, não ordem acidental de JSON.
- efeitos colaterais após seleção, separados do seletor (sacrifício, movimento, status, escudo, bônus).

**Recomendação candidata:** reaproveitar `BUF-006` para fechar esses campos e `BUF-013` para o desempate. Não aprovar uma família abstrata única de seleção sem parâmetros por efeito.

## 7. Validação reproduzível

- Script: `docs/scripts/audit-target-selection-row-scope-v0.1.py`
- Resultado: `docs/card-game-target-selection-row-scope-audit-v0.1.json`
- Resultado: **15/15 assertions; zero falhas**.
- Chamadas reais: `_poder_efetivo()`, `_aplicar_habilidade_identidade()` e `aplicar_jogada(..., action="leader")`.
- Fixtures sintéticas em memória; não acessa DB, HTTP, Discord, navegador, produção ou serviço externo.

Comando a partir da raiz do repositório:

```bash
python docs/scripts/audit-target-selection-row-scope-v0.1.py
```

## 8. Limites e continuidade

- Não é auditoria exaustiva de todo ID de carta, relíquia ou handler; prioriza seletores ativos documentados na tabela e nos líderes.
- Não valida UI e divergência da lista apresentada para alvos manuais; não simula reordenação real de JSON nem colisões de ID entre cópias físicas.
- O desempate por ordem de lista é fato legado, não recomendação de design.
- Nenhuma decisão BUF foi aprovada; este relatório acrescenta evidência para BUF-006, BUF-008 e BUF-013.
- Nenhum arquivo funcional do runtime foi alterado.

**Próximo passo:** completar o inventário de seletores de cartas especiais e relíquias, incluindo diferença entre opções exibidas pela UI, validação de `target_id` e execução efetiva; depois consolidar BUF-001…BUF-014 com as evidências TGT. O motor antigo permanece apenas como baseline de auditoria.
