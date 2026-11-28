# Contrato `CardInstance` v0.4 — Grupos A, B e C aprovados; D/F/E abertos

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev10.zip`  
**Status:** `DRAFT_AFTER_GROUP_A_B_C_APPROVAL_NOT_FROZEN`  
**Integração:** nenhuma. Runtime, DB, catálogo ativo, API, bot e frontend permanecem inalterados.

## 1. Escopo desta revisão

A v0.4 incorpora somente as decisões aprovadas dos Grupos A, B e C. Mantém identidade por ocorrência, manifesto imutável, cadeia causal de eventos e regras explícitas de duração/transição. O contrato continua draft: Grupo D (seleção/fallback/atomicidade e outcomes completos), Grupo F (causas finais de remoção/Vingança) e Grupo E (persistência concorrente/migração real) ainda estão abertos.

Artefatos normativos deste draft:

- `docs/schemas/card-game-card-instance-match.schema.v4.json` — JSON Schema Draft 2020-12 do envelope v4;
- `docs/examples/card-instance-match.example.v4.json` — fixture estrutural compatível com o schema;
- `docs/card-game-card-instance-contract-validation-v0.4.json` — resultado do harness;
- `docs/scripts/validate-card-game-card-instance-v0.4.py` — validação estrutural e semântica isolada.

`schema_version=4` é versão estrutural do envelope. Não representa versão do catálogo, registry, balanceamento ou ruleset. O schema v4 não é schema de produção nem autorização para migração.

## 2. Decisões incorporadas

### 2.1 Grupo A — identidade física (aprovado)

- `card_id` identifica o modelo e pode repetir em instâncias diferentes.
- `exemplar_id` referencia a PK global `cartas_exemplares.id` quando a proveniência é comprovada; validar proprietário e `card_id`.
- `instance_id` é UUIDv4 minúsculo, gerado pelo servidor por ocorrência e único globalmente na partida.
- Uma instância mantém a mesma identidade ao mover, remover, recuperar ou ressuscitar.
- Zonas guardam referências; `instances` guarda o único registro de cada ocorrência.
- Tokens materializados recebem instância. Relíquia equipada não é instância de zona por si só.
- Seleção física usa `target_instance_id`/`target_instance_ids`. Adaptador legado por `card_id` só pode resolver uma ocorrência elegível única.
- Ordem das zonas é persistida; desempates devem ser determinísticos e declarados.
- A regra atual de deck builder (12 modelos distintos) permanece inalterada.

### 2.2 Grupo B — manifesto e causalidade (aprovado)

Cada partida contém `definition_manifest` imutável, com releases de catálogo, registry de efeitos, regras de balanceamento e ruleset; canonicalização RFC 8785; SHA-256 dos quatro artefatos; e `definition_digest`. Cada `definition_snapshot` fixa os mesmos release IDs, atributos mecânicos resolvidos e digest da definição.

Uma operação lógica usa `operation_id` UUIDv4 e fingerprint semântico. Cada evento usa `event_id` próprio; eventos são ordenados, append-only e ligados por `caused_by_event_ids`. Estado, `state_revision`, resultado e eventos pertencem ao mesmo commit lógico. A persistência concorrente real continua Grupo E.

BUF-001: `rarity_id` é classificatório e não pode participar de resolução, magnitude, elegibilidade, seleção, quantidade de alvos ou duração. `RARITY_EFFECT_BUDGET` não pertence ao novo motor. Efeitos reativos têm `source_effect_id` e evento próprios; não herdam parâmetros/raridade do evento externo. Somente bindings ativos verificados entram no novo registry. Remoção e Vingança, assim como Vingança e output direto de Rykard, são eventos separados. A lista final de causas de Vingança permanece Grupo F.

### 2.3 Grupo C — estado, duração e ciclo de vida (aprovado)

As dez decisões aprovadas estão registradas em `card-game-state-lifecycle-group-C-approval-v0.1.md` e `.json`. Seus efeitos estruturais são descritos abaixo.

#### 2.3.1 Fileiras e sequência

- `definition_snapshot.printed_row`: fileira impressa imutável.
- `state.current_row`: posição atual, obrigatoriamente `null` fora da zona `board`.
- `state.last_board_row`: projeção persistida da última fileira válida ocupada no campo; atualizada a cada movimento e saída do campo; pode sobreviver enquanto a instância está fora do board.
- `players[player_id].round_state.last_unit_play_row`: fileira da última unidade jogada com sucesso pelo participante na rodada. Movimento, carta especial, recuperação e ressurreição não atualizam esse campo. `round_close` o limpa.

`last_board_row` é uma projeção persistida, não precisa ser reconstruída a cada leitura a partir do log. O log continua sendo a fonte causal para auditoria/replay.

#### 2.3.2 Resistência climática

- `definition_snapshot.intrinsic_weather_resistance`: característica intrínseca imutável. Ausência no artefato de origem é materializada como `0` no snapshot.
- `state.weather_resistance_modifiers[]`: modificadores por instância, cada um com `modifier_id`, `amount`, `source_effect_id`, `source_instance_id`, `applied_event_id` e `expires_on`.
- Resistência efetiva = `max(0, intrinsic_weather_resistance + soma(modifiers ativos))`.
- O escalar legado `weather_resist` não é canônico e não aparece no schema v4.
- `vigil_seal` cria modificador `expires_on=board_exit`. A persistência do valor legado não pode ser usada para inferir duração permanente.
- O branch genérico `resistencia_climatica` sem binding ativo verificado permanece fora do catálogo novo, conforme BUF-012.

#### 2.3.3 Bônus

`state.bonus_grants[]` substitui o escalar canônico `bonus`. Cada grant registra:

- `grant_id` UUIDv4;
- `amount` assinado;
- `source_effect_id` e `source_instance_id` (quando houver uma instância-fonte);
- `applied_event_id`;
- `expires_on`;
- `clamp_policy_id` versionado.

O total de bônus é uma projeção calculada segundo a política explícita de cada efeito/release. Não existe piso/teto global implícito. `bonus` pode ser derivado para UI/compatibilidade, mas não é persistido como fonte canônica em v4. O ledger de eventos é append-only; o array de grants representa concessões ainda ativas.

#### 2.3.4 Proteção e escudos

`state.protection_grants[]` substitui `shield_charges` escalar e registra `grant_id`, `profile_id`, cargas restantes, fonte, evento de aplicação e expiração. Grant com `charges=0` pode permanecer para manter a identidade/proveniência da concessão; o consumo deve estar registrado em evento.

Política aprovada:

- Perfil padrão bloqueia `unit_removal` e `execution`.
- `sacrifice` faz bypass do perfil padrão.
- Aplicações de status e debuffs não são bloqueadas por padrão; somente uma interação explicitamente declarada no efeito pode consultar proteção.
- Noite/Chama e Lâmina Negra permanecem exceções específicas, não um princípio geral de imunidade.
- Um bloqueio compatível consome exatamente uma carga do grant de proteção correspondente.
- `action_cost_on_block` é propriedade separada do efeito recebido: Noite/Chama consome a ativação quando bloqueada; Lâmina Negra não consome/devolve a ativação quando bloqueada.
- A política de escolha entre vários grants compatíveis ainda depende do Grupo D; o v4 não inventa um desempate.

#### 2.3.5 Estados negativos

`state.status_applications[]` substitui os quatro contadores escalares. Cada registro representa uma marca/aplicação e registra `application_id`, `status_id`, fonte, `applied_event_id` e `expires_on`. Contadores são projeções por `status_id`; aplicações e expirações são rastreáveis. Se um efeito aplicar duas marcas, são duas aplicações identificáveis (ou dois registros criados pelo evento, conforme o handler).

A purificação remove somente os `status_id` declarados pelo efeito purificador. Não altera bônus, escudo ou resistência sem outputs separados explícitos.

**Fora do escopo aprovado:** os caps numéricos finais, o disparo de consequências por transição de limiar, a repetição de efeitos quando o alvo já está no limite e a diferença Malenia/Oráculo da Geada continuam dependentes da revisão específica do registry/ruleset. O schema não congela máximo de marcas nem regra de threshold.

#### 2.3.6 Expiração e transições

Todo grant/modificador/aplicação declara um dos seguintes `expires_on`:

- `board_exit`: expira quando a instância sai da zona `board` (remoção, sacrifício ou outra transição para fora do campo); movimento entre fileiras não é saída.
- `zone_exit`: expira em qualquer transição bem-sucedida entre zonas, inclusive `board`→`discard`, `discard`→`hand` e `discard`→`board`.
- `round_close`: expira no evento global de fechamento da rodada.
- `permanent_instance`: permanece durante a vida da instância na partida; não é removido por `round_close`.

Matriz aprovada:

| Transição | Política v0.4 |
|---|---|
| Movimento dentro de `board` | Atualiza `current_row` e `last_board_row`; preserva grants, proteções e status ainda válidos; não altera `last_unit_play_row`. |
| Remoção bloqueada | Consome uma carga compatível; não muda zona nem limpa estado. O custo da ação causadora segue `action_cost_on_block`. Não é remoção e não dispara Vingança. |
| Remoção/sacrifício bem-sucedido | Move a mesma instância para `discard`; `current_row=null`; atualiza/preserva `last_board_row`; limpa status e concessões de proteção; expira modificadores `board_exit` e `zone_exit`; mantém bônus ainda ativos até sua expiração declarada e preserva resistência intrínseca. Sacrifício ignora escudo. |
| Recuperação à mão (Lágrima Sagrada) | Move a mesma instância para `hand`; expira `zone_exit`; não é ressurreição; não executa hooks de entrada. Preserva somente grants/modificadores ainda válidos após as expirações já ocorridas. |
| Ressurreição ao campo (Ressurgir/Réquiem) | Expira `zone_exit`; limpa status e proteção; zera bônus; escolhe fileira por `last_board_row`, depois fileira solicitada válida, depois `melee`; preserva resistência intrínseca e grants `round_close`/`permanent_instance` ainda ativos; não repete on-play, passiva ou combo. |
| Retorno ao campo (Esgar) | Expira `zone_exit`; limpa status e proteção; mantém bônus anterior ainda ativo e adiciona +1 em grant/evento próprio; força a fileira solicitada válida, rejeitando ausência/valor inválido; não repete hooks de entrada. |
| Purificação | Remove somente as aplicações dos `status_id` declarados; demais tipos de grant permanecem. |
| Fechamento de rodada | Primeiro congela o snapshot imutável de pontuação/resultado; depois emite `round_close`; expira `round_close` em todas as instâncias e zonas, inclusive mão/pilha/descarte e rodada terminal; limpa marcadores de combo e `last_unit_play_row`; preserva `permanent_instance` e modificadores `board_exit` se a instância não saiu do board. |

Para representar o fechamento no ledger: o evento de pontuação deve preceder `round_close`; eventos de expiração/limpeza vêm depois e apontam causalmente para o evento de fechamento. O snapshot de pontuação não é recalculado após as expirações. A apresentação do último campo pode usar o snapshot de resultado sem manter os modificadores ativos no estado operacional.

### 2.4 Status e projeções

Em v4, os arrays de grants/aplicações são estado canônico ativo. Totais para cálculo/UI são projeções:

- `bonus_total`: soma dos grants segundo as respectivas `clamp_policy_id` e ordem/regra de agregação do release;
- `shield_charges`: soma das cargas disponíveis dos grants compatíveis com a consulta;
- `status_count[status_id]`: quantidade de aplicações ativas daquele status;
- `weather_resistance_effective`: resistência intrínseca + modificadores ativos, com piso zero.

A ordem/algoritmo exato de agregação de grants com clamp diferente precisa ser definido no ruleset/release. Não aplicar clamp global nem inventar um valor default silencioso.

## 3. O que o schema v4 valida e o que exige validador semântico

O JSON Schema v4 valida a forma dos registros, UUIDs, tipos, expiração, fontes e campos obrigatórios. Ele não consegue, sozinho, garantir invariantes que atravessam múltiplas árvores do documento. O validador semântico também verifica:

1. Cada `instance_id` aparece em exatamente uma zona de exatamente um proprietário.
2. Instância em `board` é unidade e tem `current_row` não nula.
3. Instância fora de `board` tem `current_row=null`; `last_board_row` pode permanecer.
4. Cada `applied_event_id` de grant/aplicação/modificador referencia evento existente; a origem do evento coincide com a origem declarada.
5. IDs de grants/aplicações/modificadores são únicos no escopo da instância.
6. `last_unit_play_row` é estado do participante/rodada, não propriedade da unidade.
7. Contagens, limiares e caps de status são validados pelo registry/ruleset versionado, não codificados como regra nova no schema v4.

## 4. Questões ainda abertas — Grupos D, F e E

- **D:** seleção e desempate entre múltiplos grants de proteção compatíveis; fallbacks para seleção parcial; outcomes completos (`applied`, `blocked`, `rejected`, `no_effect`, `conflict` etc.); consumo de custos para todas as famílias de efeito; contratos de alvo manual/automático.
- **F:** lista final de causas que disparam Vingança; relação exata entre sacrifício e Vingança; remoção forçada, execução, efeitos ambientais e outras causas elegíveis.
- **E:** CAS/serialização por partida; lock; constraints de unicidade no banco; armazenamento append-only do ledger; migração de snapshots antigos uma única vez; rollback e idempotência sob concorrência real.

Também permanecem fora do congelamento os números finais de balanceamento e a resolução de limites/thresholds dos estados negativos. A existência do `clamp_policy_id` não define ainda cada política numérica.

## 5. Guardrails

- Não alterar o motor legado, catálogo ativo, database schema de produção, API, bot ou frontend.
- Não executar migrador nem converter snapshots persistidos.
- Não promover handlers sem binding ativo verificado.
- Não inferir comportamento intencional a partir de persistência acidental do legado.
- Não tratar os testes de schema/harness como validação de integração.
- Preservar Grupos A/B/C aprovados e manter D/F/E explicitamente abertos.

## 6. Próximo gate

Avançar para o Grupo D: contrato de seleção, fallback, bloqueio, rejeição, ausência de efeito, alvo parcial, custo e resolução de grants compatíveis. O Grupo F deverá fechar causas de remoção/Vingança. O Grupo E só pode ser iniciado com testes reais de persistência transacional e concorrência. Até esses gates, `CardInstance v0.4` permanece draft documental.
