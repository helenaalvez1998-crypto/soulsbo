# Contrato `CardInstance` v0.2 — identidade física aprovada, envelope ainda em revisão

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev6.zip`  
**Status:** `GROUP_A_APPROVED; CONTRACT_DRAFT_NOT_FROZEN`  
**Aprovação do Grupo A:** `docs/card-game-identity-group-A-approval-v0.1.md`  
**Integração:** nenhuma. Runtime, catálogo ativo, DB, API e frontend permanecem inalterados.

## 1. Objetivo e escopo

Esta revisão aplica ao envelope de partida as decisões aprovadas do Grupo A: CI-001, CI-002, CI-003, CI-004, CI-006, CI-010, BUF-013 e RSRX-09. Corrige o vínculo de `exemplar_id`, define seleção física e explicita invariantes que o JSON Schema sozinho não consegue expressar.

**Não é um contrato final congelado.** Os grupos B (snapshot/causalidade), C (estado/duração), D (seleção/custo/atomicidade), F (remoção) e E (persistência/migração) continuam abertos. Os campos `weather_resistance`, `policy.identity_only` e `result=applied` permanecem placeholders provisórios herdados do v0.1 e estão marcados como deprecated no schema v2; não são decisões aprovadas por esta versão.

## 2. Decisões aprovadas e invariantes

### 2.1 Identidades distintas

| Campo | Escopo | Regra aprovada |
|---|---|---|
| `card_id` | Catálogo | Identifica o modelo. Pode repetir entre instâncias. |
| `exemplar_id` | Banco/coleção | PK global atual `cartas_exemplares.id`; representa proveniência de coleção quando comprovada. |
| `instance_id` | Partida | UUIDv4 canônico em minúsculas, gerado no servidor para cada ocorrência física/virtual materializada; imutável. |
| `owner_player_id` | Partida | Participante dono da ocorrência. Deve corresponder à zona que a contém. Transferência de controle não está aprovada. |

`card_id` nunca substitui `instance_id` em seleção, remoção ou retorno. Duas instâncias podem compartilhar o mesmo modelo, inclusive quando uma é token.

### 2.2 `instance_id` e unicidade

1. O servidor gera UUIDv4 com fonte criptograficamente segura quando a ocorrência nasce.
2. A colisão deve ser detectada no registry antes do commit; não derivar o ID de modelo, exemplar, posição ou timestamp.
3. O ID permanece o mesmo ao mover entre mão, pilha, campo e descarte, ao recuperar ou ressuscitar, e durante serialização/reload.
4. O ID é globalmente único dentro da partida, considerando os dois participantes e todas as zonas.
5. Em todo snapshot estável, cada instância do registry aparece em exatamente uma lista de zona, e cada referência de zona resolve uma única entrada do registry. Não pode haver duplicatas nem órfãos.

O JSON Schema valida forma UUIDv4 e os tipos. A unicidade entre listas, igualdade entre chave/valor e totalidade do registry exigem validação semântica no serviço.

### 2.3 Proveniência de `exemplar_id`

No DDL atual, `cartas_exemplares.id` é `INTEGER PRIMARY KEY AUTOINCREMENT`, uma PK global da tabela. A linha também contém `user_id` e `card_id`.

- `origin_type=deck_exemplar`: `exemplar_id` deve ser positivo e existir; a linha deve corresponder a `owner_player_id` por `user_id` e ao mesmo `card_id`.
- `catalog_deck`, `generated_token` e `equipped_relic_activation`: `exemplar_id=null`; não inventar proveniência.
- `legacy_migration`: preencher somente quando a relação puder ser provada; caso contrário manter `null` e registrar a lacuna fora do objeto.
- Um `exemplar_id` não pode ser reutilizado por duas instâncias da mesma partida. Por ser PK global, também não pode representar duas linhas diferentes no banco.

O caminho atual `preparar_carta()` perde o exemplar no payload padrão. O futuro construtor precisa receber DTO de origem validado antes da projeção para payload de combate. Não modificar esse caminho legado nesta etapa.

### 2.4 Tokens, relíquias e objetos transitórios

Todo token/carta virtual materializado em uma zona recebe seu próprio `instance_id`, mesmo quando compartilha `card_id` com outra ocorrência. A relíquia equipada é configuração fora das quatro zonas e não é, por si só, uma instância de partida.

A ativação da relíquia deve ser representada preferencialmente por evento/ordem de uso com `operation_id`. Se o futuro pipeline precisar materializar uma carta transitória, ela recebe um `instance_id` próprio, `origin_type=equipped_relic_activation` e `exemplar_id=null`. O baseline não guarda `equipped_relic_exemplar_id`; portanto, não atribuir a ativação a um exemplar específico sem uma decisão posterior.

### 2.5 Zonas e ordem

O envelope mantém listas ordenadas por participante: `hand`, `draw_pile`, `board` e `discard`. A ordem dos arrays é estado persistido e possui semântica:

- `first`/`last` referem-se à ordem da zona/field declarada pelo efeito;
- seletores por métrica precisam declarar um `tie_breaker` no catálogo/registry;
- fallback compatível aprovado: métrica principal → posição na lista candidata (ordem da zona) → `instance_id` lexicográfico crescente como fallback técnico;
- nunca depender de ordem de hash-map, serialização incidental ou identidade de objeto Python.

Não criar `play_sequence` neste grupo. Caso uma regra precise de ordem original de jogada, essa informação pertence ao estado/evento de jogador e será fechada em B/C, não inferida do `instance_id` nem da posição atual.

### 2.6 Seleção por identidade física

- Alvo único: `target_instance_id`.
- Alvos múltiplos: `target_instance_ids`, array não vazio e sem repetição.
- O cliente pode carregar `card_id` para texto/arte/filtro, mas o servidor resolve a ocorrência por `instance_id` e revalida owner/lado, zona, tipo, fileira, métrica, estado e elegibilidade do efeito.
- ID inexistente, obsoleto, fora do escopo ou inelegível é rejeitado; o servidor não seleciona silenciosamente a primeira ocorrência.
- Adaptador legado de `target_id`/`card_id` é temporário e fora do protocolo novo: zero correspondências elegíveis → `target_not_eligible`; uma → resolver e registrar uso do adaptador; duas ou mais → `ambiguous_legacy_target` e rejeitar.
- Quantidade mínima/máxima, alvo secundário, ordem de aplicação, fallback parcial e consumo de recurso pertencem ao Grupo D e não são decididos aqui.

O schema separado `schemas/card-game-target-selection.schema.v1.json` valida somente a forma do seletor. Não substitui validação semântica no servidor.

### 2.7 Remoção, sacrifício e retorno

Cada operação de remoção, sacrifício, recuperação à mão ou ressurreição atua sobre uma ocorrência exata identificada por `instance_id`. A transição retira uma única referência da zona de origem e move a mesma instância para a zona de destino; nunca remove todas as cartas que compartilham `card_id`.

A identidade preservada não determina automaticamente quais campos do estado persistem. Limpeza/preservação de bônus, escudo, estados, resistência, fileira e gatilhos continua sob Grupo C/RSRX-07/08/10.

## 3. Envelope e schema v2

- `schemas/card-game-card-instance-match.schema.v2.json`: schema Draft 2020-12 do snapshot de partida e das instâncias.
- `examples/card-instance-match.example.v2.json`: exemplo com duas instâncias do mesmo `card_id`, IDs de exemplar distintos e token sem exemplar.
- `schemas/card-game-target-selection.schema.v1.json`: fragmento de requisição de seleção física.

Versões `schema_version=2` identificam esta revisão documental do envelope. O schema não consegue, sozinho, validar igualdade entre chave de registry e `instance_id`, referência exatamente uma vez, correspondência com participante, unicidade global de `exemplar_id` ou existência/owner/modelo no banco. Essas regras são verificadas pelo harness e deverão ser implementadas no serviço novo.

### 3.1 Campos provisórios herdados

Para não resolver silenciosamente o Grupo C/D/F:

- `weather_resistance` permanece no estado somente como campo provisório/deprecated; não define origem, duração ou expiração aprovada.
- `state_policy_id=policy.identity_only` é placeholder do protótipo de transição, não policy de ciclo de vida aprovada.
- `result=applied` é placeholder e não cobre blocked/rejected/consumed_no_effect/partial.
- `state_revision`/ledger continuam desenho de contrato; persistência real e concorrência continuam CI-014/Grupo E.

Antes de congelar uma futura versão, o schema deverá substituir esses placeholders com as decisões aprovadas dos grupos dependentes.

## 4. Requisitos do serviço futuro (não implementados)

1. Gerar o UUIDv4 no servidor antes de distribuir ocorrências entre zonas.
2. Construir as instâncias a partir de origem validada, preservando `exemplar_id` sem inferência.
3. Validar todas as invariantes do snapshot como uma unidade.
4. Resolver alvos exclusivamente por identidade física e revalidar elegibilidade no servidor.
5. Fazer transições/removal por uma única instância, nunca igualdade estrutural do payload nem filtro amplo por `card_id`.
6. Preservar a ordem dos arrays em persistência e replay.
7. Não mudar ainda endpoint de deck, regra de 12 modelos, catálogo, DB, API ou frontend.

## 5. Validação e limitações

O harness `scripts/validate-card-game-card-instance-v0.2.py` valida o exemplo contra os dois schemas, UUIDv4, igualdade key/value, unicidade e ownership em zonas, proveniência de exemplar, repetição de `card_id`, ordem, seletor singular/múltiplo e rejeições negativas.

Ele usa fixtures sintéticas e leitura estática do DDL; não acessa DB real, partidas de produção, HTTP, Discord, navegador, transações concorrentes ou runtime novo. Passar não comprova integração nem balanceamento.

## 6. Estado de decisões após esta revisão

**Aprovadas:** CI-001, CI-002, CI-003, CI-004, CI-006, CI-010, BUF-013 e RSRX-09.

**Continuam abertas:** CI-005/007/008/009/011/012/013/014; BUF-001…BUF-012 e BUF-014; RSRX-01…08 e RSRX-10. As chaves RSRX são locais ao parecer cruzado, não IDs oficiais previamente existentes no projeto.

**Bloqueios de implementação:** causalidade/versionamento do snapshot (B); policies e duração do estado (C); custos, alvos múltiplos e atomicidade da ação (D); causas e efeitos de remoção (F); persistência/idempotência/migração real (E).

**Próximo passo:** avançar ao Grupo B — snapshot e causalidade — sem migrador, sem alteração funcional e sem congelar o schema definitivo.
