# Matriz cruzada — buffs, movimentação, proteção, estados, clima e combos v0.1

**Data:** 2026-11-27  
**Status:** `READ_ONLY_LEGACY_AUDIT; DIAGNOSTIC_ONLY; NOT_APPROVED_DESIGN`  
**Base:** pacote `soulsbo-main-updated.zip`; código legado preservado.  
**Escopo:** cruzamentos selecionados entre buffs, movimentação, escudos, estados negativos, clima, raridade, combos, passivas e sacrifício.

> Este documento amplia a auditoria de buffs/movimentação/proteção v0.1. Ele registra comportamento atual e dependências entre regras. Não aprova as regras para o novo motor e não altera handlers legados.

## 1. Síntese executiva

A bateria cruzada acrescenta **9 verificações reproduzíveis, 9 aprovadas e 0 falhas**. O resultado mais relevante é que várias mecânicas usam `poder efetivo`, e portanto clima e estados negativos influenciam não apenas a pontuação, mas também a seleção de alvos de efeitos de fortalecimento, purificação, reposicionamento e sacrifício.

Também foi confirmado que `row` é a posição corrente usada por combos, buffs de fileira e clima, enquanto `fileira` permanece como referência original em unidades reposicionadas. A movimentação não atualiza `player.last_row`; esse campo continua refletindo a última fileira jogada, e não a fileira para a qual uma unidade foi movida.

A ordem de uma jogada de unidade é material: identidade → combo → amplificação por raridade → passiva de facção → anexação ao tabuleiro. No caso testado, uma unidade Rara que ativa `juramento_erdtree` termina com +4: +2 do combo, +1 da amplificação de raridade e +1 da passiva. O aliado preexistente da mesma fileira recebe o `team_bonus` de +1. Isso é resultado observado do legado, não uma recomendação de balanceamento.

## 2. Matriz de interações reproduzidas

| ID | Cruzamento | Resultado confirmado no motor legado | Dependência para o contrato novo |
|---|---|---|---|
| XI-01 | Seleção do aliado mais fraco + clima + Geada | `v75_golden_vow` escolhe por `_poder_efetivo()`. A unidade de poder-base 8, com duas marcas de Geada e clima 1, tem efetivo 5 e é escolhida antes da unidade limpa de poder 7, efetivo 6. | Declarar se seletores usam `base_power`, `effective_power` ou métrica própria. No legado deste efeito, é poder efetivo. |
| XI-02 | Purificação + seleção por poder efetivo + escudo | `v75_grace_mender` ordena apenas aliados da mesma fileira que tenham pelo menos um dos quatro estados; purifica até dois e concede +1. Um escudo existente permanece intacto. Unidade limpa não entra na lista de candidatos, mesmo que tenha poder efetivo baixo. | Separar filtro de elegibilidade, ordenação e efeito de purificação. Escudo e purificação são eixos independentes no legado. |
| XI-03 | Gravidade + clima de origem/destino + resistência climática | `star_gravity` escolhe o inimigo de maior poder efetivo na posição de origem, move sua `row` para a fileira da carta e reduz seu bônus em 2. A `fileira` original permanece. O clima da nova `row`, reduzido por `weather_resist`, passa a valer imediatamente. | Movimento muda a posição corrente e recalcula o efetivo; precisa existir uma regra explícita para posição-base, posição-corrente e clima após reposicionamento. |
| XI-04 | Movimento prévio + combo com `team_bonus` | `juramento_erdtree` inclui no `team_bonus` o aliado cuja `row` atual coincide com a carta jogada, mesmo quando sua `fileira` original é outra. | Atributos de posição usados para seleção devem ser tipados; o legado usa `row` para esse efeito. |
| XI-05 | Combo + raridade + passiva de facção | A carta Rara testada recebe +2 do combo, +1 da amplificação e depois +1 da passiva de facção. O aliado já em campo, na mesma `row`, recebe +1 do `team_bonus`. | A ordem das etapas é observável. A amplificação por raridade ocorre antes da passiva; passiva fixa não é ampliada. O problema de deltas reativos de BUF-001/002 permanece separado. |
| XI-06 | Passo + buff de fileira subsequente + `last_row` | `gwent_passo` muda `row`, preserva `fileira` e não atualiza `player.last_row`. Um `gwent_chifre` posterior considera a nova `row` e concede +2 à unidade movida. | Definir se `last_row` representa última jogada, última movimentação ou histórico de posicionamento. O legado trata como última fileira jogada. |
| XI-07 | Preço em Sangue + clima + estado + escudo + sacrifício | `v75_blood_price` escolhe o aliado mais fraco por poder efetivo e usa esse valor (limitado a 1–3) para conceder bônus. A remoção por sacrifício ignora escudo, limpa o escudo e os quatro estados e envia a vítima ao descarte. | Sacrifício precisa continuar sendo causa tipada; o cálculo de ganho deve especificar a métrica de poder usada antes da remoção. |
| XI-08 | Execução/remoção + escudo + Vingança | Quando o escudo bloqueia a remoção, a unidade permanece no campo, a carga é consumida, `baixas` não aumenta e Vingança não dispara. | Vingança é consequência de remoção bem-sucedida, não da tentativa. O bypass de sacrifício é uma regra separada (IR-02/IR-04). |
| XI-09 | Combo `team_bonus` + fileira | O bônus coletivo do combo atinge apenas aliados preexistentes na mesma `row` da carta participante; aliado em outra fileira não recebe o ponto. | Escopo do bônus coletivo deve ser parte do contrato e não inferido de “equipe” ou “formação”. |

## 3. Interações cruzadas já documentadas em etapas anteriores

Estas dependências foram mantidas como referências, sem duplicar testes nesta bateria:

- **Raridade + Vingança:** Chama Negra Épica pode remover unidade com Vingança; o delta reativo de Vingança entra no snapshot global e pode ser amplificado pela raridade (BUF-001/002). Ver `card-game-buffs-movement-protection-audit-v0.1.md`, caso 8.
- **Rykard + Vingança:** o sacrifício dispara primeiro +1 de Vingança; depois Rykard dá +2 aos sobreviventes da fileira, total observado +3. Ver `card-game-removal-resurrection-interaction-matrix-v0.1.md`, IR-04.
- **Devorar + Vingança:** aliados preexistentes da mesma fileira recebem Vingança; a carta Devorar recebe separadamente seu ganho do sacrifício. Ver matriz de remoção, IR-03.
- **Ressurreição + combo:** a unidade ressuscitada entra depois da verificação do combo da jogada de retorno; pode participar em jogadas posteriores. Ver matriz de remoção, IR-05/IR-06.
- **Escudo + debuff/status:** escudo não bloqueia universalmente reduções de bônus nem aplicação de estado. Algumas relíquias fazem sua própria checagem. Ver auditoria de buffs, caso 11, e revisão de estados negativos.
- **`weather_resist` + fechamento:** o campo persiste no objeto arquivado após limpeza da rodada; duração ainda não é especificada. Ver auditoria de buffs, caso 12.

## 4. Ordem observada de resolução

Para uma unidade comum jogada pelo caminho normal, o fluxo relevante é:

1. Bônus inicial e habilidades genéricas de entrada.
2. Identidade da carta.
3. Combo (`_aplicar_combo_de_cartas()`), incluindo `team_bonus` sobre aliados já no tabuleiro.
4. Amplificação por raridade (`_aplicar_potencia_raridade()`), que compara snapshots de `bonus` da carta e dos tabuleiros.
5. Passiva de facção (+1, uma vez por rodada, sem amplificação posterior).
6. Anexação da carta ao tabuleiro.
7. Anexação eventual da unidade ressuscitada.

Consequências: o combo pode observar efeitos da identidade da carta atual; a raridade pode amplificar deltas do combo e deltas colaterais presentes no snapshot; a passiva é posterior à amplificação; e unidades que ainda não foram anexadas não recebem efeitos que selecionam somente cartas preexistentes.

Para especiais, o handler específico resolve antes do helper genérico de raridade. Para relíquias, o helper de raridade é explicitamente ignorado. Líderes seguem outro caminho. Não há uma única ordem universal aplicável a todos os tipos de carta.

## 5. Contratos que podem ser derivados como requisitos, mas ainda não aprovados

Os testes dão evidência para exigir que o novo catálogo declare, por efeito:

- `target_filter`, `target_metric` e `tie_breaker` — por exemplo, poder efetivo ou bônus positivo, filtro de fileira e desempate estável;
- `position_scope` — `current_row` ou outra referência explícita;
- `on_no_target` e `minimum_targets`;
- `effect_phase` — entrada, identidade, combo, modificador de raridade, passiva, remoção, limpeza ou fechamento;
- `rarity_scope` — quais deltas são saídas diretas do efeito e quais são gatilhos reativos que não devem ser capturados implicitamente;
- `protection_scope` — classes de operações prevenidas por escudo e exceções explícitas;
- `sacrifice_policy` — interação com escudo, estados, descarte, `baixas` e Vingança;
- `row_model` — posição-base e posição-corrente;
- `duration` para resistência climática e outros modificadores temporários.

Esses nomes são requisitos conceituais para a modelagem; não são nomes de campos aprovados do schema.

## 6. Decisões ainda abertas

Esta matriz **não fecha** as decisões BUF-001 a BUF-014. Os cruzamentos reforçam especialmente:

- BUF-001/002/013: atribuição de raridade e seleção determinística de deltas;
- BUF-004/006: quantidade de alvos e desempate após movimento/clima/estados;
- BUF-008: separação entre posição original e corrente; semântica de `last_row`;
- BUF-009/010: taxonomia de proteção e exceções de relíquias/sacrifício;
- BUF-011: duração de `weather_resist`;
- BUF-014: limites diferentes de redução de bônus.

Permanecem também em aberto: operador genérico de transferência de bônus (BUF-007), alvos inexistentes (BUF-005), atribuições de habilidades legadas sem binding ativo (BUF-012), e decisões relacionadas a `instance_id` e cópias físicas registradas na matriz de remoção.

## 7. Validação reproduzível

- Script: `docs/scripts/audit-buffs-cross-interactions-v0.1.py`
- Resultado: `docs/card-game-buffs-cross-interactions-v0.1.json`
- Resultado desta execução: **9/9 assertions aprovadas; 0 falhas**.

Comando a partir da raiz:

```bash
python docs/scripts/audit-buffs-cross-interactions-v0.1.py
```

Bateria anterior de buffs/movimento/proteção: 14/14. Suites complementares reexecutadas nesta continuidade: status candidato 41/41; remoção/ressurreição 49/49; combos/passiva 87/87; líderes 22/22; comportamento genérico 13/13. Cada conjunto mede escopo diferente; não somar para alegar cobertura única ou equilíbrio competitivo.

## 8. Limites

- Fixtures sintéticas em memória e funções reais selecionadas do motor legado.
- Sem partida competitiva integral, DB de produção, HTTP, Discord, navegador ou R2.
- Sem alteração em `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, dados do catálogo, custo, imagens ou persistência.
- Nenhum contrato novo foi integrado; a matriz descreve o legado.
- As 14 decisões BUF continuam abertas até revisão e aprovação explícita.

**Próximo passo:** preparar a folha de decisão BUF-001…BUF-014 com evidências, impacto, recomendação e alternativas, sem editar o motor. Depois da decisão do proprietário, congelar os contratos canônicos e planejar a reconstrução dos resolvedores. O motor antigo continua preservado como baseline de comportamento, não como arquitetura de destino.
