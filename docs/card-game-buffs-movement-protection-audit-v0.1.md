# Auditoria de buffs, movimentação, proteção e clima v0.1

**Data:** 2026-11-27  
**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`  
**Base examinada:** `soulsbo-main-handoff(1).zip`  
**Escopo:** buffs individuais/coletivos, transferência de bônus, movimento entre fileiras, escudos/resistências e interações com clima, combos e passivas de facção.

> Esta é uma auditoria do comportamento legado, não uma especificação aprovada. Nenhum handler do motor antigo foi substituído, removido ou alterado. Os artefatos criados nesta etapa são documentação, fixtures e testes diagnósticos isolados.

## 1. Síntese executiva

A inspeção confirma que o legado possui várias formas de fortalecimento, mas elas não compartilham uma semântica única: algumas alteram a própria unidade, outras selecionam aliados por fileira, força efetiva ou ordem de inserção; combos e líderes também aplicam bônus em momentos diferentes da jogada.

O motor não possui uma operação genérica identificada que mova um valor de `bonus` de uma unidade para outra. Há efeitos compostos que reduzem o bônus de inimigos e concedem bônus à carta que os executa, mas isso não é necessariamente transferência: origem, quantidade, condições e destino são definidos por cada handler.

Foram reproduzidos cinco achados de maior impacto:

1. **A amplificação por raridade examina deltas globais de `bonus`, não apenas deltas originados pelo efeito principal da carta.** Com a Chama Negra Épica, a remoção de uma unidade com Vingança dispara +1 aos aliados restantes; a rotina de raridade trata um desses bônus disparados como se fosse parte do efeito da Chama Negra e acrescenta outro +1 ao primeiro alvo na ordem do tabuleiro.
2. **A Égide Rara concede escudo a duas unidades**, embora a descrição estática da carta diga que concede escudo a uma unidade. O texto dinâmico de preparação contém informação de quantidade, mas o rótulo de seleção continua singular.
3. **O Passo Raro move até duas unidades**, embora a descrição estática diga que move uma. A primeira é escolhida pelo usuário ou, sem escolha, é a mais fraca; a segunda é a primeira elegível na ordem original do tabuleiro.
4. **Escudo não é uma camada universal de proteção.** Bloqueia remoções centralizadas, mas sacrifício o ignora; alguns handlers de relíquia tratam escudo individualmente; reduções de bônus e aplicações de estados podem ignorá-lo.
5. **`weather_resist` persiste no objeto arquivado ao fim da rodada**, enquanto bônus, escudo e quatro estados são zerados. O escopo temporal dessa resistência não está definido no código de ciclo de vida.

A validação nova executou 14 verificações direcionadas, todas aprovadas. As verificações confirmam o comportamento atual em estados sintéticos; não constituem teste completo de todas as cartas, raridades ou partidas.

## 2. Método e fontes

A análise foi feita por leitura estática dos handlers e por chamadas controladas às funções reais de `sistemas.gwent`, usando estados sintéticos em memória. Não foram usadas partidas de produção, banco, Discord, HTTP ou navegador.

Fontes principais:

- `sistemas/gwent.py`: rastreamento de origem de bônus, resolvedor de identidades, orçamento de raridade, combos, poder efetivo, remoção, fechamento de rodada, líderes, especiais e entrada de unidades.
- `sistemas/cartas.py`: textos e atribuições atuais das cartas, lista de cartas sem efeito especial após V18 e raridades.
- `site/app.js`: envio da ação manual de clima e mensagens de interface.
- `docs/card-game-effect-semantic-audit-v0.1.md`: famílias candidatas e alertas semânticos já catalogados.
- `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md`: regras de sacrifício e Vingança que cruzam esta auditoria.

O rastreador `BonusTrackedDict` registra a origem dos deltas para auditoria e apresentação. Porém, `_aplicar_potencia_raridade()` não consulta essa proveniência para determinar quais deltas pertencem ao efeito que está sendo amplificado: compara snapshots de `bonus` antes/depois e percorre a carta e as unidades nos dois tabuleiros.

## 3. Buffs individuais e coletivos

### 3.1 Regra geral de potência por raridade

O orçamento atual é: Comum 0; Rara 1; Épica 1; Lendária 2; Mítica 2; Primordial 3; Singular 3. A rotina não aumenta poder-base, escudo, custo, duração, compra, invocação ou condições; ela aplica +1 adicional a cada delta positivo selecionado ou -1 adicional a cada delta negativo selecionado, com piso -2 para a redução adicionada por essa rotina.

A seleção segue esta ordem:

1. delta de `bonus` da própria carta jogada;
2. unidades do tabuleiro do jogador ativo, na ordem da lista;
3. unidades do tabuleiro adversário, na ordem da lista.

Apenas uma quantidade de alvos igual ao orçamento é amplificada. O algoritmo não preserva uma associação semântica entre cada delta e o efeito que o causou. Portanto, um efeito secundário disparado durante a resolução pode consumir o orçamento da carta.

### 3.2 Buffs de fileira e de formação encontrados

| Efeito | Comportamento legado confirmado | Observação para o contrato novo |
|---|---|---|
| `gwent_chifre` / Rugido de Godfrey | +2 a cada aliado pré-existente na fileira escolhida; depois pode haver amplificação de raridade por alvo | Ordem do tabuleiro determina quais alvos recebem o +1 adicional |
| `gwent_muralha` / Bastião de Leyndell | +1 a cada aliado pré-existente na fileira escolhida | Fileira vazia gera no-op silencioso e consome a carta |
| `gwent_vinculo` / Juramento do Crisol | Exige pelo menos dois aliados pré-existentes na fileira; concede +2 a cada um | Abaixo do mínimo, retorna erro antes de consumir a carta; raridade pode amplificar um alvo |
| `estandarte` | +1 a todos os aliados na fileira de entrada | Sem filtro de força; percorre a lista do tabuleiro |
| `grey_watch` | +1 a todos os aliados na fileira de entrada | Identidade própria; não deve ser fundida automaticamente com `estandarte` sem verificar outras condições |
| `ash_guardian` | +1 ao primeiro aliado da mesma fileira e +1 à própria carta | Primeiro aliado significa primeiro na lista, não o mais fraco/forte |
| `vigil_seal` | Define `weather_resist=1` na própria carta e dá +1 ao primeiro aliado na mesma fileira | A identidade é ativa; a raridade Rara amplifica o bônus do aliado para +2 no caso testado |
| `covering_shot` | +1 ao aliado de menor poder efetivo em outra fileira | Empate depende da ordem estável da lista |
| `veiled_moon` | +1 à própria carta e +1 ao aliado mais fraco em outra fileira | A carta pode receber amplificação antes do aliado por causa da ordem global de deltas |
| `ember_kin` | +1 à própria carta e +1 ao primeiro aliado da Ordem Áurea na mesma fileira | O filtro de facção e a regra de primeiro alvo são parte da semântica |
| `v75_golden_vow` | +1 à própria carta e +1 ao aliado mais fraco da mesma fileira, se houver | Empate de poder efetivo depende da ordem do tabuleiro |
| `v75_grace_mender` | Purifica até dois aliados afetados da mesma fileira e dá +1 a cada um; sem alvos afetados, fortalece o aliado mais fraco; sem aliado, fortalece a própria carta | Efeito de purificação e buff são acoplados; raridade pode amplificar o delta de bônus selecionado |

Além desses handlers, há bônus em líderes e relíquias. Godfrey concede +2 às unidades aliadas em Corpo a Corpo. Morgott concede escudo e +1 às até duas unidades mais fortes sem escudo na fileira selecionada. A Grande Runa de Godrick concede +1 a todas as unidades aliadas; a Grande Runa dos Não Nascidos purifica Geada/Podridão elegíveis e concede +1 às unidades purificadas. Rykard sacrifica um aliado e dá +2 aos sobreviventes da fileira, interagindo com Vingança conforme a auditoria anterior.

### 3.3 Sem alvo ou quantidade mínima

O legado não adota uma política única:

- `gwent_vinculo`: recusa a jogada abaixo do mínimo de duas unidades na fileira.
- `gwent_muralha`: aceita fileira vazia, não altera unidade e consome a carta.
- `gwent_chifre`: também não exige explicitamente que exista aliado na fileira; uma fileira vazia não produz buff e a carta segue para o descarte.
- `gwent_egide`: recusa se não houver unidade aliada sem escudo.
- `gwent_passo`: recusa se não houver unidade fora da fileira de destino.

A especificação nova precisa declarar por efeito: `minimum_targets`, comportamento `on_no_target` (rejeitar, consumir sem efeito, aplicar fallback) e momento de consumo do recurso.

## 4. Transferência de bônus

Não foi localizada uma operação genérica dedicada a transferir o valor existente de `bonus` de uma unidade de origem para outra unidade de destino. Os efeitos encontrados são operações distintas:

- **Par debuff + buff:** `v75_gravity_shear` reduz em 1 o bônus de até dois inimigos com bônus positivo na fileira; se atingir dois, a carta que entrou recebe +1.
- **Sacrifício + ganho:** `v75_blood_price`, Devorar e Rykard removem/sacrificam uma unidade e calculam um ganho para outra unidade ou para as sobreviventes.
- **Redistribuição não demonstrada:** não há neste código um handler que subtraia exatamente N de A e some exatamente N em B, preservando vínculo de origem ou definindo o que acontece com valores abaixo de zero.

Essas operações não devem ser migradas para `transfer_bonus` apenas porque incluem uma redução e um aumento. Para qualquer futura regra de transferência real, será necessário decidir se ela move todo o bônus, apenas bônus positivo, um valor fixo, se o valor transferido é limitado pelo disponível e se o efeito pode selecionar a própria unidade como origem/destino.

## 5. Movimentação entre fileiras

### 5.1 Passo do Lobo (`gwent_passo`)

O destino é a fileira escolhida. São elegíveis todas as unidades aliadas cuja `row` atual seja diferente do destino.

- Com `target_id`, a unidade selecionada é a primeira do lote.
- Sem `target_id`, a primeira é a unidade com menor poder efetivo.
- As unidades restantes são acrescentadas na ordem original do tabuleiro, não em ordem crescente de poder.
- A quantidade é `min(3, 1 + orçamento_de_raridade)`. Como Passo é Raro, o comportamento atual move até duas unidades.
- O handler altera `row`, mas não altera `fileira`, campo usado como referência de fileira catalogada/base em outros pontos.

O texto estático da carta diz “Move uma unidade”; a preparação dinâmica acrescenta que a raridade Rara move até duas. A UI permite escolher uma unidade e a resolução pode mover uma segunda sem escolha explícita. É necessário fechar se essa expansão é intencional e como o alvo secundário é escolhido.

### 5.2 Gravidade do Flagelo (`star_gravity`)

A identidade seleciona a unidade inimiga com maior poder efetivo entre todas as fileiras, altera sua `row` para a fileira de entrada da carta e reduz seu `bonus` em 2, com piso -2. O campo `fileira` não é alterado. Como o poder efetivo consulta `row` atual, a penalidade climática da nova fileira passa a valer imediatamente.

No teste controlado, a unidade foi movida de Cerco para Corpo a Corpo; `fileira` continuou `siege`, `row` tornou-se `melee` e o clima de Corpo a Corpo foi aplicado na nova posição.

### 5.3 Modelo de posição ainda ambíguo

O código usa `row` como posição corrente para pontuação, efeitos e movimento, enquanto `fileira` funciona como referência de colocação/catalogação em outros caminhos. O contrato novo deve separar os conceitos explicitamente (por exemplo, `base_row` e `current_row`) e determinar se uma unidade que retorna à mão/campo mantém ou redefine a posição atual.

## 6. Proteção, escudos e resistência

### 6.1 Escudo

O helper `_remover_unidade()` verifica escudo antes de remover: em remoção normal, consome uma carga e cancela a remoção. A exceção explícita é `causa == "sacrificio"`, que ignora o escudo e remove a unidade. Remoção bloqueada não envia a unidade ao descarte, não incrementa `baixas` e não dispara Vingança.

Fontes atuais de escudo localizadas:

- Especial `gwent_egide`: protege `min(3, 1 + orçamento_de_raridade)` unidades aliadas sem escudo. A carta é Rara e, portanto, protege duas.
- Líder Morgott: seleciona até duas unidades aliadas sem escudo na fileira indicada, ordenadas por poder efetivo decrescente; concede um escudo e +1 a cada uma.
- Campos/branches antigos `escudo_ferro`, `v75_crucible_guard` e `v75_moon_ward` existem no motor, mas não representam habilidades atualmente atribuídas às cartas do catálogo efetivo após a supressão V18 ou sem binding ativo.

O escudo não protege universalmente contra mudanças de estado ou de bônus. A redução de bônus por vários handlers não consulta o escudo. A postura de fogo de `reliquia_noite_chama` e `reliquia_lamina_negra` implementa checagens próprias; a postura de Geada da primeira e outras relíquias de redução de bônus não compartilham necessariamente esse tratamento.

### 6.2 Resistência climática

O cálculo de poder efetivo é:

`max(1, poder + bonus - max(0, clima_da_row_atual - weather_resist) - min(3, geada + podrida + loucura))`.

Portanto:

- a resistência reduz apenas a penalidade do clima na fileira atual;
- ela não reduz Geada, Podridão ou Loucura;
- Sangramento não participa do cálculo de poder efetivo;
- o valor de resistência não é consumido ao reduzir o clima.

A habilidade genérica `resistencia_climatica` define `weather_resist=2` e, se nenhuma das três fileiras tiver clima ativo, concede +1 de bônus na entrada. Contudo, o Profeta de Liurnia está incluído em `CARTAS_SEM_EFEITO_IDS` após V18, então seu campo de habilidade atual fica vazio. A resistência climática ativa encontrada nesta revisão é `vigil_seal`, que define `weather_resist=1` na Confessora da Ordem Áurea.

### 6.3 Duração e ciclo de vida

Ao fim de uma rodada não final, bônus, escudos e os quatro estados são zerados nas cópias arquivadas; o clima global é zerado. `weather_resist` não é removido nem redefinido nesse caminho. A unidade preservada por Glória também recebe limpeza de bônus, escudo e estados, mas o código não redefine `weather_resist`.

Na resolução da partida final, `_resolve_round()` retorna antes do bloco comum de limpeza da rodada. Isso conserva o snapshot terminal como estado de encerramento; não se deve confundir esse comportamento com regra de duração para uma rodada seguinte.

A proposta de ciclo de vida deve decidir se `weather_resist` é atributo permanente da carta, modificador temporário da instância ou efeito com duração própria. Não inferir duração apenas porque o campo persiste no dicionário legado.

## 7. Clima, combos e passivas de facção

### 7.1 Clima

O clima é armazenado por fileira e afeta unidades dos dois lados posicionadas naquela `row`. O especial `gwent_clima` e a ação manual `action == "weather"` ativam nível mínimo 1 na fileira escolhida; `gwent_purificar` limpa as três. A UI envia efetivamente a ação `weather` e exibe confirmação. O estado climático também é limpo entre rodadas não finais.

O cálculo de resistência é local à fileira atual, mas algumas identidades verificam clima ativo em qualquer fileira. Isso deve permanecer parametrizado por escopo (`current_row`, `any_row`, `enemy_occupied_row`), em vez de ser tratado como uma regra única de clima.

### 7.2 Combos

`_aplicar_combo_de_cartas()` é executado antes de a nova unidade ser anexada ao tabuleiro. A carta precisa contribuir com tag exigida; o mínimo conta unidades participantes distintas; prioridades ordenam a escolha; uma ativação é resolvida por jogada. O bônus individual vai para a carta nova. `team_bonus`, quando definido, vai somente para aliados que já estavam no tabuleiro e possuem a mesma `row` da carta jogada.

### 7.3 Passiva de facção

A primeira unidade jogada na rodada cuja facção corresponde à facção do deck recebe +1. A marca `faction_boost_used` é atualizada e volta a `False` no início da próxima rodada. A passiva é aplicada **depois** da amplificação por raridade; portanto, não é multiplicada pela raridade.

### 7.4 Ordem efetiva da entrada da unidade

Para unidade normal, a sequência relevante do motor é: definir bônus inicial; aplicar habilidades genéricas de entrada; aplicar identidade; consumir eventual Fio Astral; aplicar combo; aplicar potência da raridade; aplicar passiva de facção; anexar a unidade ao tabuleiro; anexar eventual unidade ressuscitada. Essa ordem explica por que uma unidade recém-ressuscitada não participa do combo da mesma jogada e por que a passiva de facção não é amplificada pela raridade.

## 8. Divergências e riscos que precisam de decisão

| ID | Evidência | Risco/decisão necessária |
|---|---|---|
| BUF-001 | Potência de raridade usa deltas globais de bônus entre snapshots | Associar amplificação ao `effect_id`/saídas daquele efeito, sem capturar gatilhos colaterais (ex.: Vingança) |
| BUF-002 | Chama Negra Épica remove unidade com Vingança e raridade amplifica o primeiro aliado fortalecido pela queda | Decidir se efeitos de ciclo de vida podem consumir orçamento de raridade da carta que causou a remoção; proposta recomendada: não implicitamente |
| BUF-003 | Égide Rara protege duas unidades, texto estático promete uma | Atualizar contrato, texto e seleção da UI para quantidade real ou reduzir o efeito para um alvo |
| BUF-004 | Passo Raro move duas unidades, texto estático promete uma; segundo alvo segue ordem do tabuleiro | Definir número de alvos e política de seleção/consentimento para todos os alvos |
| BUF-005 | Bastião sem alvo é consumido como no-op, enquanto Juramento rejeita abaixo do mínimo | Padronizar `on_no_target` e `minimum_targets` por efeito |
| BUF-006 | Buffs para “primeiro”, “mais fraco” e “mais forte” podem usar diferentes critérios e empates | Formalizar filtro, métrica de força, desempate e `instance_id` |
| BUF-007 | Não há operador genérico de transferência identificado | Manter reduções + ganhos como efeitos compostos; criar transferência real somente mediante contrato próprio |
| BUF-008 | `row` muda com movimentação, `fileira` permanece | Distinguir posição base e posição corrente no modelo canônico |
| BUF-009 | Escudo bloqueia remoção normal, mas não sacrifício nem várias alterações negativas | Definir a taxonomia de efeitos que escudo pode bloquear e manter exceções explícitas |
| BUF-010 | Escudo só tem integração central na remoção; algumas relíquias tratam escudo por branch específico | Consolidar política por `effect_type` para evitar proteção diferente conforme o caminho de execução |
| BUF-011 | `weather_resist` persiste no descarte após limpeza de rodada | Definir duração: atributo persistente, modificador de rodada ou modificador com prazo próprio |
| BUF-012 | Resistência genérica e `escudo_ferro` permanecem como branches, mas estão sem binding ativo após V18 | Não migrar como habilidade ativa sem atribuição explícita no novo catálogo |
| BUF-013 | Raridade pode amplificar um bônus selecionado por ordem de inserção | Estabelecer alvo determinístico e previsível, sem depender incidentalmente da ordem do array |
| BUF-014 | Reduções de bônus usam pisos diferentes: vários handlers param em -2; Lâmina Negra e Chama não aplicam esse mesmo piso; Runa da Morte e Algemas só reduzem/removem bônus positivo | Definir limites de bônus e semântica por efeito, evitando assumir um piso universal no novo motor |

## 9. Decisões necessárias antes de aprovar o contrato canônico

Estas são perguntas de design, não alterações já aprovadas:

1. **Amplificação de raridade:** amplifica apenas resultados diretos do `effect_id` que está sendo resolvido? Recomendação: sim; gatilhos reativos (Vingança, morte, retorno, passivas de ambiente) devem declarar seu próprio modificador, se existir.
2. **Transferência:** haverá um `transfer_bonus` canônico? Se sim, definir origem, destino, valor máximo, tratamento de bônus negativos, autoseleção e resistência/bloqueio.
3. **Limites de bônus:** haverá teto positivo e piso negativo globais, ou parâmetros explícitos por efeito? A exceção atual das relíquias precisa ser decidida, não copiada implicitamente.
4. **Alvos:** adotar `first_in_play_order`, `weakest_effective_power`, `strongest_effective_power`, seleção manual e um desempate baseado em `instance_id`/sequência estável?
5. **Movimentação:** Passo move uma ou duas unidades na raridade Rara? Alvos adicionais devem ser escolhidos pelo usuário ou por regra declarada?
6. **Posição:** separar `base_row` e `current_row`; definir a posição usada em retorno à mão, ressurreição, reposicionamento e bônus de fileira.
7. **Escudo:** quais categorias ele previne — remoção, execução, dano direto, redução de bônus, status — e em quais casos é consumido? Sacrifício deve continuar ignorando escudo?
8. **Resistência climática:** seu valor persiste entre rodadas e ao retornar do descarte? A aplicação deve ser um atributo de carta ou um modificador temporário?
9. **Alvo inexistente:** padronizar rejeição, fallback ou consumo sem efeito por efeito; estabelecer `minimum_targets` quando necessário.
10. **Texto e UI:** descrições, alvos selecionáveis e quantidade efetiva devem refletir o contrato real, inclusive os aumentos por raridade.

## 10. Validação reproduzível

Novo script: `docs/scripts/audit-buffs-movement-protection-v0.1.py`  
Resultado: `docs/card-game-buffs-movement-protection-audit-v0.1.json`

**Resultado da execução:** 14 assertions; 14 aprovadas; zero falhas.

Casos cobertos:

1. Juramento rejeita fileira com apenas um aliado.
2. Bastião em fileira vazia é consumido como no-op.
3. Égide Rara concede dois escudos.
4. Rugido de Godfrey amplifica o primeiro aliado alterado pela raridade.
5. Passo Raro move duas unidades.
6. Gravidade do Flagelo muda `row` e recalcula o clima da fileira de destino.
7. Selo de Vigília define resistência climática e tem bônus de aliado amplificado pela raridade.
8. Chama Negra Épica amplifica indiretamente o bônus de Vingança.
9. Remoção normal é bloqueada e consome escudo.
10. Sacrifício ignora escudo.
11. Redução direta de bônus pode ignorar escudo.
12. Limpeza de rodada mantém o campo `weather_resist` no descarte.
13. Bônus de combo e passiva de facção acumulam na ordem observada.
14. `escudo_ferro` e `resistencia_climatica` genéricos estão sem binding ativo após V18.

Comando:

```bash
python docs/scripts/audit-buffs-movement-protection-v0.1.py
```

Suites de contexto executadas separadamente nesta continuidade:

```bash
python docs/scripts/assert-card-effect-behavior-v0.1.py
python docs/scripts/assert-combo-and-faction-passive-v0.1.py
python docs/scripts/assert-leader-effects-v0.1.py
```

Resultados reportados para essas suites: 13/13, 87/87 e 22/22, respectivamente. Não somar os conjuntos como cobertura única; os escopos se sobrepõem e são diferentes. Nenhuma dessas contagens mede balanceamento competitivo ou cobertura integral de todas as cartas.

## 11. Limites desta etapa e continuidade

- A auditoria cobre caminhos selecionados do motor e interações reproduzíveis; não equivale a revisão exaustiva de todos os 54 effect families, todos os IDs, todas as raridades e todas as combinações de cartas.
- O comportamento descrito é o comportamento legado atual, não a regra recomendada para a reconstrução.
- Não houve migração de `instance_id`, atualização de banco/API, mudança de UI, alteração de cartas, revisão de artes ou simulação competitiva.
- Os handlers legados permanecem preservados.

**Próximo passo:** consolidar as respostas às decisões BUF-001 a BUF-014 e construir a matriz cruzada final com remoção, sacrifício, estados negativos, combos e passivas. Só depois disso aprovar os contratos das famílias e iniciar a reconstrução do catálogo/resolvedores. O motor antigo continua sendo referência de evidência, não destino de arquitetura.
