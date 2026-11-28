# Grupo A — revisão de decisões de identidade física v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev5.zip`  
**Status:** `TECHNICAL_PROPOSAL_FOR_OWNER_REVIEW_NOT_APPROVED`  
**Integração:** nenhuma. Runtime, catálogo ativo, DB, API e frontend permanecem inalterados.

> **Atualização posterior:** o proprietário aprovou explicitamente as oito decisões deste Grupo A após este parecer, conforme `docs/card-game-identity-group-A-approval-v0.1.md`. A matriz `OPEN_NOT_APPROVED` abaixo registra o estado original na data de publicação; para o estado vigente, prevalece o documento de aprovação.

> Este documento inicia o fechamento do Grupo A. Ele apresenta resoluções candidatas para CI-001/002/003/004/006/010, BUF-013 e RSRX-09. Nenhuma recomendação é considerada aprovada pelo pedido de continuidade. O contrato `CardInstance v0.1` e seu schema permanecem candidatos históricos; este adendo corrige inconsistências que devem ser resolvidas antes de uma revisão v0.2.

## 1. Decisão operacional do Grupo A

**Objetivo:** garantir que toda ocorrência física/virtual possa ser identificada, validada e selecionada sem confundir modelo, exemplar de coleção ou posição numa lista.

**Conclusão:** a arquitetura de três identidades é válida, mas CI-004 precisa de correção em relação ao banco atual e CI-006 precisa distinguir equipamento de ativação. CI-001/002/003/010, BUF-013 e RSRX-09 têm uma recomendação coerente, mas continuam abertas até aprovação explícita.

O Grupo A não aprova políticas de estado, causalidade, persistência concorrente, migração ou integração. Esses assuntos continuam nos Grupos B, C, D, F e E.

## 2. Evidências verificadas no pacote rev. 5

| Evidência | Fonte | Consequência para o Grupo A |
|---|---|---|
| `cartas_exemplares.id` é `INTEGER PRIMARY KEY AUTOINCREMENT`; a linha também contém `user_id` e `card_id`. | `database.py`, definição de `cartas_exemplares` | O `exemplar_id` atual é uma chave primária da tabela, não um contador local independente por proprietário. A posse continua sendo verificada por `user_id`. |
| O endpoint de gravação exige 12 `card_id` distintos (`len(set(ids)) == 12`). | `bot.py`, `_api_gwent_deck_save()` | A regra atual do deck builder é separada do modelo de instâncias e não deve ser removida por CI-003. |
| O carregador de snapshot percorre os 12 `card_ids`, resolve um exemplar por carta e exige 12 cartas retornadas, mas não repete explicitamente a validação de unicidade de `card_id`. | `bot.py`, `_gwent_deck_snapshots()` | A criação da partida deve validar a política de deck salva antes de construir as instâncias; isso não muda o contrato genérico de identidade. |
| O caminho normal chama `preparar_carta(payload)` e anexa o retorno sem recolocar `exemplar_id`; `preparar_carta()` retorna `id`/dados de carta, mas não o exemplar. | `bot.py`, `_gwent_deck_snapshots()`; `sistemas/gwent.py`, `preparar_carta()` | A origem do exemplar é conhecida no carregador, mas se perde antes de `novo_estado()`. O novo construtor de instâncias deve receber metadados de origem antes da projeção para payload de combate, ou preservá-los explicitamente num DTO interno. |
| `preparar_carta_pessoal()` faz um caminho separado e recoloca `card_id`, `exemplar_id` e `id` composto. | `sistemas/gwent.py`, `preparar_carta_pessoal()` | Não usar o campo legado `id` como contrato universal: carta normal e carta pessoal têm formatos distintos. |
| `novo_estado()` copia os decks para `hand`/`draw_pile`, mas não gera `instance_id`. | `sistemas/gwent.py`, `novo_estado()` | A identidade de partida deve ser criada no servidor durante a construção do estado, não inferida depois pelo cliente. |
| `_resumo_alvo()` publica `id`; o handler lê `target_id` e o motor procura o primeiro `id` igual. | `sistemas/gwent.py`, `_resumo_alvo()`/`aplicar_jogada()`; `bot.py`, rota de ação | A interface atual não distingue com segurança instâncias de mesmo modelo; o novo protocolo precisa de `target_instance_id`. |
| A relíquia equipada é guardada como `equipped_relic_id`/`relic_card_owned`; na ativação, o motor cria `relic_payload` e o acrescenta temporariamente à mão. | `sistemas/gwent.py`, `novo_estado()` e ramo `action == "relic"` | Equipamento e ativação não devem compartilhar a mesma identidade de ocorrência. O payload temporário precisa ser modelado como evento ou instância transitória. |
| `Esgar` filtra/remonta o descarte por `card_id`; os seletores de retorno usam IDs do modelo. | `sistemas/gwent.py`; revisão RSRX v0.1 | A retirada/ressurreição deve consumir exatamente a instância selecionada, nunca todas as cópias com mesmo `card_id`. |

### 2.1. Correção necessária em CI-004 e no exemplo anterior

A revisão cruzada rev. 5 recomendou unicidade de `(owner_player_id, exemplar_id)` e o exemplo v1 reutilizou `exemplar_id=501` para dois jogadores. Isso **não corresponde ao DDL do pacote atual**: `cartas_exemplares.id` é uma PK `AUTOINCREMENT` da tabela, portanto o identificador numérico é globalmente único no banco.

**Recomendação corrigida:** enquanto `exemplar_id` representar diretamente `cartas_exemplares.id`, exigir unicidade global do identificador e validar a associação `exemplar_id -> (user_id, card_id)`. Não aceitar o mesmo `exemplar_id` para dois proprietários. `owner_player_id` continua obrigatório e deve corresponder ao `user_id` da linha. Se no futuro o domínio quiser IDs locais por coleção, deverá introduzir outro identificador composto/versionado; não reinterpretar silenciosamente a PK atual.

Esta correção também significa que um exemplo de partida não pode reutilizar o mesmo `exemplar_id` para o lado adversário. O exemplo rev. 5 foi corrigido neste pacote: a ocorrência adversária usa outro exemplar globalmente distinto; a cópia adicional do mesmo modelo foi representada como token, sem exemplar de coleção.

## 3. Resoluções técnicas candidatas

### CI-001 — formato e geração de `instance_id`

**Recomendação:** UUIDv4 canônico em minúsculas, criado exclusivamente no servidor por gerador criptograficamente seguro no instante em que a ocorrência nasce (construção inicial do deck, criação do token ou materialização transitória aprovada). O cliente nunca escolhe nem fornece o identificador. O ID é imutável em todas as transições de zona e retorno do descarte.

**Rejeitar:** derivação de `card_id`, `exemplar_id`, índice do deck, posição de zona, nome do jogador ou timestamp. Esses valores podem repetir, mudar ou vazar semântica que não pertence à identidade.

**Validação exigida:** formato UUIDv4 canônico, versão/variant corretas, colisão detectada antes do commit e geração de novo UUID em caso de colisão.

### CI-002 — escopo de unicidade

**Recomendação:** unicidade global dentro da partida: os dois participantes, todas as quatro zonas e ocorrências temporárias materializadas. Cada `instance_id` aparece exatamente uma vez nas listas de zona e resolve uma única entrada no registry `instances`; toda entrada do registry é referenciada por exatamente uma zona no snapshot estável.

A validação deve verificar o estado completo, não apenas as chaves de `instances`. Isso detecta duplicatas em zonas, referências órfãs, instâncias órfãs, owner divergente e colisões entre campo/descarte.

### CI-003 — repetição de `card_id`

**Recomendação:** o modelo `CardInstance` permite várias instâncias com o mesmo `card_id`, desde que cada ocorrência tenha `instance_id` próprio. Isso é necessário para tokens, cópias geradas, efeitos de duplicação futuros e snapshots que representem ocorrências distintas.

**Separação obrigatória:** a regra atual de gravação do deck de jogador — exatamente 12 modelos diferentes — permanece intacta. CI-003 não aprova decks com cartas-modelo repetidas nem altera limites de composição. A rota de criação de partida deve rejeitar decks salvos que violem a política vigente, ainda que o modelo de instância aceite duplicatas em outros contextos.

### CI-004 — vínculo com `exemplar_id`

**Recomendação corrigida:** `exemplar_id` representa a PK global `cartas_exemplares.id` do banco atual. Quando `origin_type == "deck_exemplar"`, o campo é obrigatório e positivo; o servidor valida que a linha existe e que `user_id == owner_player_id` e `card_id` coincide com o modelo da instância. O identificador não pode ser reaproveitado por outra instância dentro da partida.

Para origens sem exemplar de coleção (por exemplo, token gerado ou ativação transitória modelada como carta), `exemplar_id` é `null`. Para `legacy_migration`, só preencher se o vínculo puder ser comprovado; não inferir pelo modelo, raridade ou posição do deck.

**Implicação para o construtor:** o caminho normal atual perde `exemplar_id` em `preparar_carta()`. O novo construtor deve receber um registro de origem interno contendo `card_id`, `owner_player_id`, `exemplar_id` validado e snapshot da definição; não deve reconstruir a proveniência a partir do payload de combate já preparado.

### CI-006 — tokens, relíquias e ocorrências transitórias

**Recomendação:** qualquer carta/token que seja materializado em uma zona ou tratado como alvo físico recebe seu próprio `instance_id`. Tokens com o mesmo `card_id` continuam sendo ocorrências distintas, normalmente com `exemplar_id=null` e `origin_type="generated_token"`.

A relíquia equipada é configuração/equipamento fora das quatro zonas; seu `card_id` não é um `instance_id`. Para a ativação, preferir um evento/ordem de uso identificado pelo `operation_id`, sem fabricar uma ocorrência de carta apenas para registrar o clique. **Exceção:** se o novo pipeline mantiver a ativação materializada como carta temporária na mão/resolvedor, essa ocorrência transitória recebe `instance_id` próprio, `origin_type="equipped_relic_activation"` e `exemplar_id=null`; sai do pipeline pela transição de zona/ação correspondente.

O baseline atual não guarda um `equipped_relic_exemplar_id`; guarda `equipped_relic_id` e verifica a posse de alguma cópia do modelo. Portanto, não declarar que a ativação pertence a um exemplar específico sem acrescentar e validar esse vínculo em decisão posterior.

### CI-010 — identidade de alvo

**Recomendação:** toda seleção de ocorrência física usa `target_instance_id`. O cliente pode enviar `card_id` para exibição ou filtro de modelo, mas o servidor resolve a ocorrência por `instance_id` e revalida em tempo de execução: participante/owner ou lado esperado, zona, tipo, fileira, métrica, estado e elegibilidade definidos pelo efeito.

IDs desatualizados, inexistentes, fora da zona esperada ou inelegíveis são rejeitados. O servidor nunca escolhe silenciosamente a primeira instância encontrada.

**Compatibilidade legada:** aceitar `target_id`/`card_id` só em adaptador de versão antiga e apenas depois de filtrar o conjunto elegível:

- zero correspondências: `target_not_eligible`;
- exatamente uma: resolver para aquela instância e registrar que o adaptador legado foi usado;
- duas ou mais: `ambiguous_legacy_target` e rejeitar a ação.

A compatibilidade não pode existir como fallback permanente do resolvedor novo. Efeitos de múltiplos alvos usarão uma lista de `target_instance_ids` única, sem repetição; quantidade mínima/máxima, ordem de aplicação e política parcial pertencem ao Grupo D/BUF-005.

### BUF-013 — ordem e desempate

**Recomendação:** listas de zona são ordenadas e sua ordem faz parte do estado persistido. Um efeito que diga `first`/`last` deve declarar que se refere à ordem da zona/field; isso preserva o comportamento atual em que `max()`, `min()` e `sorted()` estáveis desempataram pela ordem da lista.

Para seletores por métrica (`weakest`, `strongest`, maior bônus etc.), a definição do efeito deve declarar `tie_breaker`. Proposta padrão de compatibilidade: métrica principal → `zone_order` crescente (primeiro na zona) → `instance_id` lexicográfico crescente como último fallback técnico. Um efeito pode escolher `zone_order_desc` ou outra regra apenas se a regra estiver explícita no registry e no texto/telemetria correspondente. Nunca usar ordem acidental de serialização, ordem de hash-map ou identidade de objeto Python.

A proposta não acrescenta um novo contador de sequência ao schema neste grupo: a posição na lista ordenada já é persistida. Se uma mecânica futura precisar distinguir "ordem original de jogada" da ordem atual do tabuleiro, isso será um campo/evento versionado do Grupo B/C, não uma inferência feita a partir de `instance_id`.

### RSRX-09 — retirada, seleção e descarte por instância

**Recomendação:** toda seleção/retirada do descarte, sacrifício, remoção, recuperação à mão e ressurreição opera sobre exatamente um `instance_id`. `card_id` é identidade de modelo e não autoriza remoção física. Uma transição remove uma referência específica da zona de origem e insere a mesma instância na zona de destino, preservando sua identidade; a normalização de campos permanece sob policies do Grupo C.

O adaptador legado por `card_id` só pode prosseguir com correspondência elegível única. Esgar e qualquer efeito que hoje filtre todas as cópias por `card_id` não podem ser traduzidos como remoção em massa acidental.

## 4. Matriz de decisão para revisão do proprietário

| ID | Proposta deste grupo | Estado |
|---|---|---|
| CI-001 | UUIDv4 gerado no servidor, imutável, com colisão verificada | `OPEN_NOT_APPROVED` |
| CI-002 | Unicidade global por partida e exatamente uma zona por ocorrência | `OPEN_NOT_APPROVED` |
| CI-003 | Instâncias podem repetir `card_id`; regra dos 12 modelos distintos do deck permanece | `OPEN_NOT_APPROVED` |
| CI-004 | `exemplar_id` é PK global atual; validar dono/modelo; corrigir recomendação anterior de escopo local | `OPEN_NOT_APPROVED` |
| CI-006 | Tokens materializados recebem instância; relíquia equipada fica fora das zonas; ativação preferencialmente evento | `OPEN_NOT_APPROVED` |
| CI-010 | `target_instance_id`; adaptador legado só com correspondência elegível única | `OPEN_NOT_APPROVED` |
| BUF-013 | Ordem de zona persistida para first/last e desempate declarado por efeito | `OPEN_NOT_APPROVED` |
| RSRX-09 | Remover/retornar exatamente uma instância física | `OPEN_NOT_APPROVED` |

### Critérios para considerar o Grupo A fechado

O Grupo A só pode mudar para `APPROVED_BY_OWNER` depois de confirmação explícita das oito linhas acima ou de registro de alterações solicitadas. Após a aprovação, o próximo trabalho será uma revisão `CardInstance v0.2`/schema que incorpore as decisões; ainda não haverá integração no runtime nem migração de partidas.

## 5. Casos de validação do Grupo A

O harness `docs/scripts/validate-card-game-identity-group-A-v0.1.py` valida o modelo proposto em memória e verifica evidências estáticas dos caminhos atuais. Os cenários cobrem:

1. UUIDv4 canônico e rejeição de identificador inválido.
2. Unicidade de `instance_id` em todas as zonas dos dois participantes.
3. Uma referência por instância e nenhuma instância órfã.
4. Correspondência entre owner, zona e exemplar de coleção.
5. Unicidade global do `exemplar_id` de acordo com a PK atual do banco.
6. Repetição de `card_id` permitida no registry sem alterar a validação de deck.
7. Token repetindo modelo sem `exemplar_id`.
8. `deck_exemplar` sem exemplar, com exemplar desconhecido ou com dono/modelo divergente rejeitado.
9. Resolução exata por `target_instance_id` e rejeição de ID inexistente/inelegível.
10. Adaptador legado por modelo: zero, uma ou várias correspondências.
11. Desempate determinístico pela ordem persistida da zona e fallback de `instance_id`.
12. Verificação estática da perda de `exemplar_id` no caminho normal, da validação de 12 `card_id` distintos, do seletor `id` legado e da materialização atual da relíquia.

O resultado do harness não aprova estas regras e não testa partidas reais, banco em concorrência, HTTP, Discord, navegador ou produção.

## 6. Limitações e gates

- O banco inspecionado é o DDL e o código do pacote; nenhum banco de produção foi consultado.
- O contrato `CardInstance v0.1` não valida de ponta a ponta referências contra `cartas_exemplares`; essa validação está no harness do Grupo A e precisa entrar em schema/serviço na revisão posterior.
- A ativação de relíquia atual cria um payload temporário na mão. A recomendação baseada em evento altera o desenho do novo pipeline, não o legado.
- CI-010 não define a UX completa de multi-alvo, ausência/parcialidade ou consumo; isso pertence ao Grupo D.
- BUF-013 cobre ordem/desempate, não métricas e elegibilidade completas; esses campos permanecem BUF-006.
- CI-004 corrigido não autoriza inferir exemplares em snapshots antigos. Migração continua bloqueada por CI-012 e Grupo E.

**Guardrail:** nenhuma alteração em `sistemas/`, `bot.py`, `database.py`, catálogo ativo, resolvedores, API, frontend ou schema de produção. O motor antigo permanece preservado.
