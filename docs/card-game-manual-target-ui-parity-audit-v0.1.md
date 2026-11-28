# Auditoria de paridade entre seleção manual de alvos, interface e motor — v0.1

**Data:** 2026-11-27  
**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`  
**Escopo:** `opcoes_de_alvo()`, `target_id`, seletor do frontend, resolução automática de alvos em cartas especiais e seleção de alvos para relíquias.

> O relatório registra o comportamento do runtime legado e da interface atual. Não aprova regras de design, não altera catálogo, backend, frontend, persistência ou dados de partidas. O motor antigo permanece preservado.

## 1. Resultado

**12/12 verificações passaram; zero falhas.** Os testes chamam `opcoes_de_alvo()`, `opcoes_de_reliquia()` e `aplicar_jogada()` com estados sintéticos e verificam trechos pontuais de `site/app.js`.

O resultado demonstra que seleção manual, seleção automática, seleção secundária e apresentação visual são contratos distintos. A interface pede uma escolha primária em algumas cartas, mas o motor pode aplicar o efeito a outros alvos sem nova confirmação.

## 2. Evidência reproduzível

| ID | Caso | Resultado observado |
|---|---|---|
| TUI-001 | Resumo da opção de alvo | `_resumo_alvo()` expõe `id`, nome, poder, bônus, fileira e estados/escudo; não expõe `instance_id` nem `exemplar_id`. |
| TUI-002 | IDs repetidos | Duas cópias com mesmo `id` aparecem como opções distintas por nome, mas o frontend envia somente o `id`; o backend resolve a primeira cópia elegível na ordem do tabuleiro. Não é possível escolher a segunda inequivocamente. O caso demonstra risco estrutural em estado com IDs repetidos; não afirma que o construtor atual de deck permita duplicatas ordinárias. |
| TUI-003 | Lâmina da Morte Destinada | Elegibilidade usa poder efetivo (inclui clima/estados); o seletor exibe `poder + bonus`. Uma unidade elegível com poder efetivo 6 pode ser apresentada como 9. |
| TUI-004 | Filtro de fileira | `opcoes_de_alvo()` envia candidatos de mais de uma fileira e um `filtro_fileira`; `app.js` filtra localmente pela fileira escolhida. `aplicar_jogada()` repete a validação e rejeita alvo de outra fileira. |
| TUI-005 | Automático da Lágrima Sagrada | Sem `target_id`, escolhe `candidates[-1]`, ou seja, o último candidato elegível na ordem do descarte. |
| TUI-006 | Automático do Réquiem | Sem `target_id`, escolhe o candidato de maior poder-base; em empate, o primeiro candidato pela ordem de entrada vence por estabilidade do `max()`. |
| TUI-007 | Métrica mostrada na Lágrima Sagrada | Elegibilidade usa poder-base; o seletor apresenta poder-base + bônus. Uma unidade de poder-base 4 e bônus +5 é elegível pelo limite 4, mas aparece com valor 9. |
| TUI-008 | Égide — alvos secundários | O seletor pede uma unidade. Na raridade Rara, o motor aplica escudo a duas: primeiro a escolhida; depois a unidade de maior poder efetivo entre as demais elegíveis. |
| TUI-009 | Passo — alvos secundários | O seletor pede uma unidade. Na raridade Rara, o motor move duas: primeiro a escolhida; depois a primeira unidade elegível na ordem original do tabuleiro, não a de maior/menor poder. |
| TUI-010 | Opções de relíquia | O endpoint publica `relic_options`, mas `site/app.js` não lê esse campo; o modal deriva alvos de `opponent.board` e filtra a fileira no cliente. |
| TUI-011 | Lâmina Negra e escudo | O alvo protegido aparece no seletor; ao resolver, o escudo é consumido e a relíquia permanece não consumida (`relic_used == false`). |
| TUI-012 | Algemas sem bônus positivo | O alvo é aceito mesmo com bônus zero; o valor continua zero, mas `relic_used` passa a `true`. O motor não filtra a elegibilidade por bônus positivo. |

## 3. Regras automáticas não são uniformes

O botão visual **Automático** envia `target_id` vazio. O motor então aplica um fallback específico por habilidade:

| Carta/efeito | Fallback legado | Métrica/ordem |
|---|---|---|
| Lágrima Sagrada (`gwent_medico`) | Último candidato elegível no descarte | Ordem do descarte (`candidates[-1]`) |
| Réquiem (`gwent_requiem`) | Maior poder-base no descarte | `base_power DESC`; empate conserva primeira entrada |
| Lâmina da Morte Destinada (`gwent_execucao`) | Menor poder efetivo na fileira escolhida | `effective_power ASC`; empate conserva primeira entrada |
| Égide (`gwent_egide`) | Maior poder efetivo como alvo primário | `effective_power DESC`; alvos adicionais também são escolhidos por essa métrica |
| Passo (`gwent_passo`) | Menor poder efetivo como alvo primário | `effective_power ASC`; alvos adicionais seguem a ordem original do tabuleiro |

Logo, **“Automático” não é uma política genérica**. O catálogo novo deve declarar o fallback por efeito, inclusive métrica e desempate, e não usar um resolvedor universal implícito.

## 4. Divergências e riscos identificados

### 4.1 Identidade do exemplar no contrato de alvo

A opção serializada expõe apenas o `id` atual da unidade. O frontend envia esse mesmo valor em `data-gwent-target`, e os handlers encontram a primeira unidade com esse ID. Se duas instâncias com o mesmo ID estiverem simultaneamente elegíveis, a interface pode exibi-las como linhas diferentes, mas não consegue distinguir qual foi clicada.

A correção arquitetural candidata é propagar `instance_id` físico e usar essa chave de ponta a ponta: resumo público, atributos do seletor, payload da ação, validação e resolvedor. Essa recomendação é coerente com a decisão de identidade física já aberta em remoção/ressurreição; não equivale a aprovar uma migração agora.

### 4.2 Métrica de poder exibida versus métrica de elegibilidade

O seletor genérico mostra `poder + bonus`. A Execução valida `effective_power`; Lágrima Sagrada e Réquiem validam `base_power`. Clima, estados e bônus podem fazer o número exibido divergir da métrica que torna a unidade elegível.

Candidata: exibir explicitamente a métrica do efeito (por exemplo, `Poder efetivo: 6` ou `Poder-base: 4`) e, quando útil, manter `poder + bônus` como informação secundária. Não recalcular no cliente usando lógica duplicada; a fonte de verdade deve ser um resumo calculado pelo servidor.

### 4.3 Efeitos com alvos secundários

Égide e Passo recebem uma seleção primária e completam o restante automaticamente. Hoje a interface não informa quais unidades secundárias serão afetadas nem permite revisão individual delas. Além da quantidade, a regra secundária difere: Égide ordena por poder efetivo decrescente; Passo usa ordem do tabuleiro.

Candidata: a API deve devolver o conjunto completo que será afetado antes da confirmação, ou a interface deve declarar claramente o critério e número de efeitos. A definição depende da decisão de design sobre escolha manual versus automática.

### 4.4 Contrato redundante para relíquias

`opcoes_de_reliquia()` é publicado na resposta da partida, mas o frontend recompõe opções a partir do placar público. Isso cria duas implementações do formato de opções. A validação final ainda ocorre no motor, mas a fonte de verdade para elegibilidade/serialização deve ser decidida para evitar divergência futura.

### 4.5 Algemas aceita alvo sem bônus positivo

A descrição sugere remoção de bônus positivo, mas o backend aceita qualquer inimigo na fileira. Se o alvo tem bônus 0 ou negativo, a operação não altera o estado e ainda consome a relíquia. Isso pode ser uma escolha de custo/risco, mas precisa ser declarada, não inferida.

## 5. Requisitos candidatos para o novo contrato

Para cada seletor manual/automático, declarar explicitamente:

- `target_identity`: `instance_id` (não apenas modelo/card ID).
- `eligibility_metric`: `base_power`, `effective_power`, `bonus` ou ausência de métrica.
- `display_metric`: a métrica mostrada ao jogador, derivada do servidor.
- `row_scope` e `row_basis`: escopo e posição corrente usados na validação.
- `manual_primary_target`: se existe escolha do jogador.
- `secondary_target_policy`: ranking ou ordem para alvos adicionais.
- `target_limit` e `on_partial_targets`.
- `automatic_fallback`: métrica, direção, desempate e ordem de entrada.
- `on_no_target`: rejeitar, consumir sem efeito, fallback ou outro comportamento declarado.
- `protection_policy`: efeitos bloqueáveis e `consume_on_block` por carta.

## 6. Decisões pendentes resultantes

1. **Identidade:** exigir `instance_id` ponta a ponta nos seletores e ações, fechando em conjunto com identidade na remoção/ressurreição.
2. **Métricas apresentadas:** mostrar poder efetivo para Execução e poder-base para Lágrima Sagrada/Réquiem; confirmar se o seletor deve também mostrar bônus.
3. **Automático:** manter o fallback específico de cada carta ou padronizar? Recomendação candidata: manter por efeito, explicitamente registrado.
4. **Alvos secundários:** Égide e Passo devem escolher automaticamente os adicionais ou pedir ao jogador o conjunto completo?
5. **Fonte de verdade de relíquias:** a UI deve consumir `relic_options` do servidor em vez de reconstruir alvos localmente?
6. **Algemas:** permitir consumo sem alteração quando não há bônus positivo, ou restringir opções/validação a `bonus > 0`?
7. **Lâmina Negra bloqueada:** preservar o comportamento atual em que o escudo é consumido e a relíquia permanece disponível?

Estas são perguntas de especificação, não defeitos automaticamente aprovados. As recomendações são candidatas.

## 7. Fontes e reprodução

- `sistemas/gwent.py`: `_resumo_alvo()`, `opcoes_de_alvo()`, `opcoes_de_reliquia()` e validações em `aplicar_jogada()`.
- `site/app.js`: `gwentOpcoesDoAlvo()`, `openGwentTargetPicker()`, `openGwentRelicPicker()` e `sendGwentAction()`.
- `bot.py`: serialização pública que inclui `alvos` e `relic_options`.
- `docs/scripts/audit-manual-target-ui-parity-v0.1.py` — executar na raiz do repositório: `python docs/scripts/audit-manual-target-ui-parity-v0.1.py`.
- `docs/card-game-manual-target-ui-parity-audit-v0.1.json` — resultados dos 12 casos.

**Limites:** os testes são fixtures sintéticas e verificações estáticas de frontend; não são testes em browser real, request HTTP, partida de produção, Discord, banco ou R2. Os 12 resultados não equivalem a cobertura integral de todos os especiais e relíquias.

**Integridade:** somente documentação e script de auditoria foram adicionados/atualizados nesta etapa. Nenhum arquivo funcional do runtime foi alterado.
