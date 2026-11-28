# Registro de decisões — buffs, raridade, movimentação e proteção v0.1

**Data:** 2026-11-27  
**Status:** `PARTIALLY_APPROVED; BUF-001/002/012_APPROVED; OTHER_DECISIONS_OPEN`  
**Escopo:** consolidação das 14 decisões BUF-001…BUF-014 da auditoria base e da matriz cruzada v0.1.

> Este documento organiza decisões necessárias para o novo contrato. A coluna “recomendação candidata” é análise técnica, não aprovação nem implementação. O motor legado permanece preservado como fonte de evidência.

## 1. Decisões sobre raridade e atribuição de efeitos

| ID | Comportamento legado comprovado | Decisão a tomar | Alternativas relevantes | Recomendação candidata | Dependências / testes |
|---|---|---|---|---|---|
| BUF-001 | `_aplicar_potencia_raridade()` compara snapshots globais de `bonus` e não filtra pela origem semântica do delta. Deltas de hooks colaterais podem entrar no orçamento. | Como identificar o resultado elegível para amplificação? | (A) manter snapshot global; (B) amplificar somente saídas diretas do efeito; (C) declarar explicitamente eventos reativos amplificáveis. | **B + C:** somente outputs atribuídos ao efeito resolvido; um gatilho reativo só escala se declarar sua própria regra de raridade. Evita acoplamento incidental. | XI-05; auditoria base caso 8; Vingança e Rykard. |
| BUF-002 | Chama Negra Épica pode remover unidade com Vingança; o bônus reativo de Vingança entra no snapshot e recebe +1 extra do orçamento da Chama Negra. | A raridade da carta causadora pode amplificar o bônus disparado pela remoção? | (A) sim, por encadeamento; (B) não, por ser output de ciclo de vida; (C) somente se Vingança declarar escala própria. | **B por padrão; C como exceção explícita.** A raridade da carta que remove não deve capturar Vingança implicitamente. | BUF-001; IR-03/04/07; XI-08. |
| BUF-013 | A amplificação escolhe deltas pela ordem: carta atual, depois unidades do jogador e adversário na ordem das listas. Alvos “primeiro” também podem depender dessa ordem. | Como desempatar e ordenar deltas/alvos? | (A) preservar ordem do array; (B) ordenar por métrica declarada; (C) selecionar por `instance_id`/sequência estável após filtro. | **B + C:** cada efeito declara seletor/métrica; empate usa ordem estável de instância/jogada, nunca acidente de serialização. | BUF-006; `instance_id`; XI-01/02/05. |

## 2. Decisões sobre quantidade, alvo e ausência de alvo

| ID | Comportamento legado comprovado | Decisão a tomar | Alternativas relevantes | Recomendação candidata | Dependências / testes |
|---|---|---|---|---|---|
| BUF-003 | Égide Rara protege duas unidades pela fórmula `min(3, 1 + budget)`, mas o texto estático promete uma unidade. | A raridade deve aumentar a quantidade de alvos ou a Égide deve proteger só uma unidade? | (A) manter duas e alinhar texto/UI; (B) fixar uma em toda raridade; (C) tornar quantidade um parâmetro explícito de carta. | **C**, mantendo o comportamento atual de duas apenas se a tabela aprovar o parâmetro e a seleção da UI informar os dois alvos. | Auditoria base caso 3; política de seleção; textos e UI. |
| BUF-004 | Passo Raro move até duas unidades; usuário escolhe apenas a primeira, e a segunda segue ordem original do tabuleiro. Texto estático diz uma. | Quantas unidades podem ser movidas e como o usuário controla alvos secundários? | (A) uma unidade em todas as raridades; (B) quantidade escala e todos os alvos são selecionados; (C) quantidade escala e alvos secundários são automáticos por seletor declarado. | **B** é a alternativa mais previsível quando o efeito afeta outras instâncias: a UI deve selecionar exatamente o número efetivo de alvos. Não esconder movimento secundário. | Auditoria base caso 5; XI-06; BUF-006/008. |
| BUF-005 | O comportamento sem alvo varia: Juramento rejeita abaixo do mínimo; Bastião e Chifre podem ser consumidos sem efeito; Égide e Passo rejeitam; alguns efeitos usam fallback. | Como cada efeito responde quando nenhum alvo é elegível? | `reject`; `consume_no_effect`; `fallback`; `partial_if_minimum_met`. | **Política por efeito**, com `minimum_targets`, `on_no_target` e `on_partial_targets` explícitos. Não criar uma regra global que apague diferenças intencionais. | Auditoria base seção 3.3; BUF-003/004/006. |
| BUF-006 | “Primeiro” pode significar ordem do tabuleiro; “mais fraco/forte” usa poder efetivo em vários efeitos; empates podem depender da ordem da lista. | Que seletor e desempate cada efeito deve utilizar? | Ordem de jogo; menor/maior poder efetivo; menor/maior poder-base; bônus positivo; escolha do jogador; combinação com prioridade. | **Seletor explícito por efeito**; declarar filtro, métrica e `tie_breaker`. Para `first`, usar ordem de entrada/jogada registrada; para `weakest/strongest`, usar métrica declarada e desempate por `instance_id` ou sequência estável. | XI-01/02/03; BUF-013; migração de identidade física. |

## 3. Decisões sobre operações de bônus e limites

| ID | Comportamento legado comprovado | Decisão a tomar | Alternativas relevantes | Recomendação candidata | Dependências / testes |
|---|---|---|---|---|---|
| BUF-007 | Não foi encontrada operação genérica que subtraia N de uma unidade e transfira exatamente N para outra. Redução inimiga + ganho próprio, sacrifício + ganho e bônus de sobreviventes são efeitos compostos. | O catálogo novo precisa de `transfer_bonus`? | (A) não criar; (B) criar transferência estrita; (C) criar operação parametrizada com limites e casos especiais. | **A por enquanto.** Só introduzir operador genérico quando houver carta/regra que realmente mova um valor existente entre origem e destino; não converter efeitos compostos em transferência. | Efeitos `gravity_shear`, `blood_price`, Devorar e Rykard; contratos de sacrifício. |
| BUF-014 | Vários handlers têm piso -2; Lâmina Negra e Chama podem ultrapassá-lo; Runa da Morte e Algemas afetam apenas bônus positivos. | Haverá teto/piso global de bônus? | (A) limites globais; (B) limites individuais por efeito; (C) default global com override explícito. | **C:** default conservador explícito e override por efeito quando o design exigir; jamais deixar a diferença escondida no código de handler. O número do default ainda requer decisão de balanceamento. | Auditoria base; `effect_params`; EFP e custos ainda não aprovados. |

## 4. Decisões sobre posição, proteção e duração

| ID | Comportamento legado comprovado | Decisão a tomar | Alternativas relevantes | Recomendação candidata | Dependências / testes |
|---|---|---|---|---|---|
| BUF-008 | `row` muda com movimento e governa clima/combos/buffs de fileira; `fileira` persiste como referência original. `last_row` não é atualizado pelo Passo. | Como representar posição e histórico no modelo canônico? | (A) manter dois campos sem tipagem; (B) `base_row` + `current_row`; (C) posição única atual e histórico de eventos separado. | **B + histórico separado:** `base_row` conserva a fileira catalogada e `current_row` a posição em campo. O campo legado `player.last_row` foi auditado separadamente: é a fileira da última unidade jogada com sucesso, não a posição atual de uma unidade. Recomendação candidata: `last_unit_play_row` por jogador, atualizado após jogada de unidade, preservado por movimento/remoção/cartas especiais e zerado na transição de rodada; histórico de movimento fica separado. Decidir também fallback de posição ao retornar/ressuscitar. Evidência adicional: `card-game-sequence-power-state-audit-v0.1.md`, SEQ-01…SEQ-10. | XI-03/04/06; matriz remoção IR-05/10/12. |
| BUF-009 | Escudo bloqueia remoção normal/execução, consome carga e não dispara Vingança; sacrifício ignora. Reduções de bônus e estados não são bloqueadas universalmente. | Que classes de efeitos o escudo previne? | (A) só remoção/execução; (B) também status/dano/debuff; (C) categorias independentes configuradas por efeito. | **C com perfil padrão equivalente ao comportamento atual:** remoção/execução, com sacrifício explicitamente excluído. Status, redução de bônus e purificação não consomem escudo salvo regra explícita. | XI-02/07/08; IR-01/02/07; BUF-010. |
| BUF-010 | Escudo tem checagem central em `_remover_unidade()`, mas algumas relíquias implementam checagens próprias e diferem no consumo da relíquia quando bloqueadas. | Como unificar a proteção sem apagar exceções de efeitos? | (A) manter cada branch; (B) helper central por categoria com política `consume_on_block`; (C) bloquear todo efeito negativo automaticamente. | **B:** centralizar o teste de proteção e declarar, por efeito, o tipo bloqueável e o consumo em bloqueio. Não adotar C; proteção universal mudaria efeitos que hoje ignoram escudo. | Auditoria base caso 11; ramos das duas relíquias; BUF-009. |
| BUF-011 | `weather_resist` reduz clima apenas na `row` corrente e persiste na cópia arquivada após o reset da rodada. | A resistência climática é permanente, temporária ou vinculada à instância em campo? | (A) atributo persistente da carta; (B) modificador enquanto em campo; (C) efeito com duração em rodadas; (D) atributo separado da carta + buff temporário. | **D:** distinguir resistência intrínseca de modificador temporário; o efeito `vigil_seal` deve declarar duração/expiração. Não inferir persistência em descarte a partir do legado. | XI-03; auditoria base caso 12; regras de retorno/ressurreição. |

## 5. Decisão sobre atribuições legadas

| ID | Comportamento legado comprovado | Decisão a tomar | Alternativas relevantes | Recomendação candidata | Dependências / testes |
|---|---|---|---|---|---|
| BUF-012 | `escudo_ferro` e `resistencia_climatica` ainda têm branches no runtime, mas as cartas correspondentes aparecem sem habilidade ativa após V18; `vigil_seal` é atribuição ativa de resistência climática. | Migrar os branches genéricos sem binding para o catálogo novo? | (A) migrar o código como efeito disponível; (B) manter apenas atribuições ativas; (C) manter aliases arquivados sem atribuição. | **B + C:** migrar só efeitos com atribuição atual comprovada; preservar os aliases/branches em baseline de compatibilidade até concluir a política de remoção de código antigo. | Auditoria base caso 14; catálogo legado; traceability das cartas. |

## 6. Resumo de estado

- **14 decisões abertas:** nenhuma está aprovada por este registro.
- **Recomendações candidatas:** preferir semântica explícita por efeito, atribuição de outputs a `effect_id`, seletores determinísticos, posição corrente separada de posição-base, e proteção tipada por categoria.
- **Não iniciar integração:** este registro não autoriza conectar resolvedores, alterar descrições de cartas, mudar APIs, migrar dados, editar `sistemas/gwent.py` ou remover branches antigos.
- **Critério para fechar:** cada decisão precisa ser aceita, rejeitada ou ajustada; decisões dependentes devem ser fechadas em conjunto (especialmente BUF-001/002/013, BUF-006/008 e BUF-009/010/011).

## 7. Fontes internas

- `docs/card-game-buffs-movement-protection-audit-v0.1.md` — evidências BUF-001…BUF-014.
- `docs/card-game-buffs-cross-interactions-v0.1.md` — nove cruzamentos reproduzíveis.
- `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — escudo, sacrifício, Vingança, retorno e combo.
- `docs/card-game-status-effects-review-v0.1.md` — estados, poder efetivo, purificação e escala por raridade.
- `sistemas/gwent.py` — runtime legado observado; não foi modificado nesta etapa.

**Próximo passo:** revisão das decisões com o proprietário. Somente após fechar o conjunto dependente será possível congelar os contratos do novo catálogo sem atribuir ao legado autoridade de design.


## 8. Adendo — seleção de alvos e escopo de fileira (TGT v0.1)

A auditoria `docs/card-game-target-selection-row-scope-audit-v0.1.md` adiciona 15 casos reproduzíveis de identidades ativas e líderes. **15/15 passaram**, sem alteração no runtime. Isso não fecha BUF-006 nem BUF-013; apenas torna as alternativas mais concretas.

- **BUF-006 — seletor por efeito:** os casos comprovam que `effective_power` é utilizado em Fenda do Vazio, Juramento Dourado, Marca da Dinastia, Preço em Sangue, Regressão Serena e líderes de seleção; já Cisalhamento Gravitacional usa bônus bruto positivo como filtro e bônus bruto como métrica. Portanto, o contrato precisa declarar `target_side`, `row_scope`, `eligibility`, `sort_metric`, direção, quantidade e fallback por efeito.
- **BUF-008 — posição:** os seletores em campo consultam `row` corrente. Gravidade do Flagelo altera `row` e preserva `fileira`; a seleção posterior deve operar na posição atual, não na referência original.
- **BUF-013 — desempate:** `max()` retorna a primeira instância empatada na ordem da lista; `sorted()` é estável e preserva essa ordem entre chaves iguais. É comportamento legado observável, não política nova aprovada. Recomenda-se chave estável de instância/sequência para não depender de ordem incidental de array.
- **Ramos sem binding ativo:** `covering_shot` e `counterflame` continuam no corpo do helper, mas seus IDs foram filtrados por V18; `v75_blood_pursuit` e `v75_moon_ward` não têm atribuição individual ativa. Não incluir esses branches como capacidades ativas no registry sem reatribuição aprovada.

A recomendação candidata é separar o pipeline em filtro de elegibilidade → ranking por métrica declarada → limite → fallback/ausência de alvo → resolução dos efeitos colaterais. Nenhum destes campos ou comportamentos está aprovado ainda.

**Fonte nova:** `docs/card-game-target-selection-row-scope-audit-v0.1.md/.json` e `docs/scripts/audit-target-selection-row-scope-v0.1.py`.


## 9. Adendo — paridade entre seletor manual, UI e motor (TUI v0.1)

A auditoria `docs/card-game-manual-target-ui-parity-audit-v0.1.md` adiciona 12 casos reproduzíveis para opções de alvo, payload `target_id`, fallback automático, alvos secundários e relíquias. **12/12 passaram** em fixtures sintéticas e verificações estáticas de `site/app.js`; o runtime não foi alterado. Esta evidência não fecha nenhuma decisão BUF nem aprova design.

- **BUF-006/013 — métrica, desempate e identidade:** `_resumo_alvo()` serializa `id`, mas não `instance_id`/`exemplar_id`; o backend resolve `target_id` pelo primeiro ID igual. Se duas instâncias com o mesmo ID aparecem juntas, a UI mostra duas entradas nominais, mas a ação não distingue a segunda. O caso é uma demonstração estrutural em fixture; a ocorrência em estados reais depende das garantias de unicidade atuais e de partidas antigas.
- **Métrica visual:** Execução filtra por poder efetivo e Lágrima Sagrada/Réquiem por poder-base, enquanto `openGwentTargetPicker()` apresenta `poder + bonus`. O número mostrado pode divergir da métrica de elegibilidade. Recomenda-se que a API envie a métrica efetiva para exibição, sem duplicar cálculo no cliente.
- **Fallback por efeito:** o botão “Automático” envia `target_id` vazio, mas os handlers não compartilham uma regra: Lágrima Sagrada escolhe o último candidato elegível do descarte; Réquiem, o maior poder-base; Execução, o menor poder efetivo; Égide, o maior poder efetivo; Passo, o menor poder efetivo. Preservar como regra por efeito ou padronizar é decisão aberta; recomendação candidata: declarar cada fallback no contrato.
- **Alvos secundários:** Égide (Rara) protege a unidade escolhida e a unidade de maior poder efetivo entre as demais; Passo (Rara) move a escolhida e a primeira elegível na ordem do tabuleiro. A UI solicita somente um alvo e não antecipa o conjunto secundário. Isso amplia BUF-004/006: alvo primário, política secundária, limite e apresentação visual devem ser campos separados.
- **Relíquias:** `relic_options` é enviado na resposta pública, mas o `app.js` recompõe o seletor a partir de `opponent.board`. Lâmina Negra: escudo bloqueia, consome o escudo, mas não consome a relíquia. Algemas aceita alvo com bônus 0; não altera o bônus e consome a relíquia. Definir se a elegibilidade deve exigir `bonus > 0`.

**Decisões abertas decorrentes:** identidade física no seletor; métrica apresentada; fallback automático por carta; seleção manual ou automática dos alvos secundários; fonte de verdade do seletor de relíquias; elegibilidade de Algemas; custo de Lâmina Negra quando bloqueada.

**Fonte nova:** `docs/card-game-manual-target-ui-parity-audit-v0.1.md/.json` e `docs/scripts/audit-manual-target-ui-parity-v0.1.py`.


## 10. Adendo de aprovação do Grupo B (2026-11-27)

O proprietário aprovou formalmente as decisões BUF-001, BUF-002 e BUF-012 no registro `docs/card-game-snapshot-causality-group-B-approval-v0.1.md`.

- **BUF-001 — aprovada, Alternativa A:** raridade é classificatória e não amplifica magnitude, limiar, quantidade/seleção de alvos, duração ou outro output mecânico. O novo sistema não usa `RARITY_EFFECT_BUDGET`.
- **BUF-002 — aprovada:** efeitos reativos mantêm `source_effect_id` e evento causal próprios; não herdam parâmetros ou raridade do efeito que os disparou.
- **BUF-012 — aprovada:** somente bindings ativos e verificados entram como capacidades no registry novo. Handlers órfãos e aliases inativos permanecem apenas no baseline histórico/compatibilidade até reatribuição explícita.

As demais BUF-003…BUF-011, BUF-013 e BUF-014 não são aprovadas por este adendo. BUF-013 já possui aprovação anterior do Grupo A, conforme `docs/card-game-identity-group-A-approval-v0.1.md`; assim, entre as 14 decisões BUF, BUF-001/002/012/013 estão aprovadas e as demais permanecem abertas.

Nenhum handler ou arquivo de runtime foi alterado por esta aprovação.
