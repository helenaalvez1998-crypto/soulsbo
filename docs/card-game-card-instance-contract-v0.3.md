# Contrato `CardInstance` v0.3 — Grupos A e B aprovados; envelope ainda aberto

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev8.zip`  
**Status:** `GROUP_A_AND_B_APPROVED; CONTRACT_DRAFT_NOT_FROZEN`  
**Integração:** nenhuma. Motor, DB, catálogo ativo, API, bot e frontend permanecem inalterados.

## 1. Escopo desta revisão

A v0.3 aplica as decisões aprovadas do Grupo A e do Grupo B. O Grupo A fecha identidade física; o Grupo B fecha manifesto imutável por partida, snapshot mecânico resolvido, separação entre operações e eventos, regra de raridade classificatória, fronteira dos efeitos reativos, binding ativo do registry e separação causal em remoção/Vingança e Rykard.

Continuam abertos os Grupos C (estado/duração), D (seleção/fallback/atomicidade e resultados completos), F (lista final de causas e políticas de remoção) e E (persistência concorrente/migração). A v0.3 é um contrato candidato, não um schema congelado nem uma autorização para integração.

## 2. Decisões incorporadas

### 2.1 Grupo A — identidade física (já aprovado)

- `card_id` identifica o modelo; pode repetir em instâncias diferentes.
- `exemplar_id` referencia a PK global `cartas_exemplares.id` quando a proveniência é comprovada.
- `instance_id` é UUIDv4 em minúsculas, gerado no servidor por ocorrência materializada e único globalmente na partida.
- Instâncias permanecem idênticas ao mudar de zona; seleção, remoção, retorno e ressurreição usam `instance_id`.
- Ordem dos arrays de zona é persistida; desempates são determinísticos e declarados.
- Tokens materializados têm instância própria; relíquia equipada, por si, é configuração e não instância de zona.

### 2.2 CI-005 — manifesto imutável de definição por partida

Cada partida contém `definition_manifest` com:

- `catalog_release_id`;
- `effect_registry_release_id`;
- `balance_rules_release_id`;
- `ruleset_release_id`;
- `canonicalization = RFC8785`;
- `artifact_sha256` para o conteúdo exato de cada um dos quatro artefatos;
- `definition_digest`, SHA-256 da representação canônica do manifesto sem o próprio campo digest.

Cada `CardInstance.definition_snapshot` guarda os quatro release IDs, os atributos mecânicos resolvidos da carta e seu próprio `definition_digest`. O digest por instância não substitui nem replica o manifesto: vincula a projeção mecânica daquela ocorrência aos releases fixados pela partida.

`schema_version` continua descrevendo a estrutura do envelope (v3). Nunca representa versão do catálogo, registry, balanceamento ou ruleset. Um release ID só é válido se o resolver de releases encontrar um artefato imutável e conferir seu SHA-256. A partida não pode consultar o catálogo corrente para reinterpretar uma definição antiga.

**Canonicalização:** JCS/RFC 8785, UTF-8, sem normalizações ad hoc. O hash do manifesto é calculado sobre todos os campos do manifesto exceto `definition_digest`. O digest por carta é calculado sobre todos os campos de `definition_snapshot` exceto seu próprio `definition_digest`. Implementação real deve usar biblioteca RFC 8785 conforme o padrão, não assumir que `json.dumps(sort_keys=True)` é universalmente equivalente.

### 2.3 CI-011 — operação lógica e eventos de domínio

`operation_id` e `event_id` são identidades distintas:

- Uma ação lógica tem um `operation_id` UUIDv4 e fingerprint semântico SHA-256.
- A resolução pode gerar zero, um ou vários eventos; cada evento tem `event_id` UUIDv4 próprio.
- O fingerprint cobre `match_id`, ator, `expected_revision`, ação/payload semanticamente normalizados e `definition_digest` da partida.
- Mesma chave + mesmo fingerprint: retornar resultado persistido sem reaplicar efeitos.
- Mesma chave + fingerprint diferente: rejeitar como conflito de idempotência.
- Uma revisão esperada obsoleta não pode aplicar a operação. A ordem entre replay idempotente e validação de revisão deve primeiro procurar a chave já concluída, para que um retry válido retorne o resultado original.
- Estado atualizado, `state_revision`, resultado da operação e eventos gerados são uma unidade de commit atômica.
- Cada evento tem sequência total crescente dentro da partida, `operation_id`, `caused_by_event_ids`, `kind`, `effect_scope`, `source_effect_id`, `source_instance_id`, `target_instance_ids` e `payload` tipado por convenção/handler.
- Causas precisam existir na mesma partida e anteceder o evento na sequência. O grafo é acíclico. O array de eventos é append-only.

A persistência real, CAS/serialização, restrições de unicidade no banco, lock por partida e transações concorrentes pertencem ao Grupo E. A v0.3 apenas fixa o contrato lógico.

### 2.4 BUF-001 — raridade é classificação, não multiplicador (Alternativa A aprovada)

No novo sistema, `rarity_id` pode permanecer na definição para classificação, apresentação e regras de obtenção fora da resolução mecânica. Não pode ser input do resolvedor de efeitos nem alterar:

- magnitude de bônus/penalidades;
- limiares de elegibilidade, incluindo Execução e retorno;
- quantidade de alvos ou escolha/ordenação de alvos;
- duração de buffs, escudos, estados ou resistência;
- qualquer outra saída mecânica.

`RARITY_EFFECT_BUDGET` não deve existir como dependência no novo catálogo/engine. Parâmetros mecânicos devem ser explícitos em `effect_id`/`effect_params` ou em regras versionadas, independentes de `rarity_id`.

Cartas do legado cujos limites atuais variam por raridade precisam de revisão individual: extrair o comportamento pretendido, fixar parâmetros explícitos e alinhar texto/UI antes de publicar um release do novo catálogo. Não presumir que o número de uma raridade específica é o correto. **Esta aprovação não congela fórmulas de cortes de raridade, EFP, custo de deck, orçamento 32 ou `leader_load`.**

### 2.5 BUF-002 — fronteira causal dos efeitos reativos

Cada reação tem seu próprio `source_effect_id` e evento causal separado, ligado ao evento que a provocou. A reação nunca herda raridade, parâmetros, limites ou identidade de fonte do efeito externo. Com BUF-001, não existe amplificação por raridade em outputs diretos nem reativos.

Exemplo: a remoção por Chama Negra pode causar um evento de remoção; se Vingança for permitida, ela gera evento reativo independente, originado em `unit.vengeance_on_removal`. O evento reativo não recebe `rarity_id` nem `RARITY_EFFECT_BUDGET` da Chama Negra.

### 2.6 BUF-012 — somente bindings ativos verificados

O novo registry só expõe como capacidade um `effect_id` com binding de catálogo ativo e verificado. Branches sem carta ativa, aliases inativos e handlers órfãos podem permanecer no baseline histórico/compatibilidade, mas não são capacidades executáveis do catálogo novo até reatribuição explícita e validação.

### 2.7 RSRX-03 — remoção e Vingança em eventos separados

Uma remoção/sacrifício bem-sucedido produz evento próprio. Se a unidade removida tiver Vingança e a causa estiver na lista permitida, a reação produz evento separado com `effect_scope=reactive`, fonte `unit.vengeance_on_removal`, `source_instance_id` da unidade removida e o evento de remoção como pai causal.

Uma tentativa bloqueada por escudo não é remoção e não dispara Vingança. A lista final de causas elegíveis (incluindo a decisão definitiva sobre sacrifício) permanece no Grupo F; esta aprovação não a antecipa.

### 2.8 RSRX-05 — Rykard com outputs separados

A reação de Vingança e o bônus direto do líder Rykard são eventos distintos, cada qual com fonte e relação causal próprias e ordenadas. O legado observado concede +1 reativo e +2 do líder, mas esta aprovação congela a separação e a atribuição, não o agregado +3 como valor final de balanceamento.

## 3. Estrutura do envelope v3

Arquivos normativos desta revisão:

- `schemas/card-game-card-instance-match.schema.v3.json` — envelope da partida com manifesto, instâncias, operações e stream de eventos;
- `schemas/card-game-definition-manifest.schema.v1.json` — forma do manifesto imutável;
- `schemas/card-game-domain-event.schema.v1.json` — forma de um evento causal;
- `examples/card-instance-match.example.v3.json` — fixture sintética Chama Negra → remoção → Vingança.

O objeto `operations` é indexado por `operation_id`. Cada registro guarda fingerprint, ator, revisão esperada/anterior/posterior, resultado persistido e IDs dos eventos emitidos. `events` é uma lista ordenada; `sequence` é única e estritamente crescente na partida.

O schema valida forma e tipos. Validação semântica adicional precisa garantir: igualdade entre chave e ID; unicidade global; eventos referenciando operação existente; relações causais existentes e anteriores; IDs de evento e operação diferentes; correspondência entre `event_ids` e eventos; digest de manifesto/instância; releases iguais entre manifesto e snapshot; e ownership/zona conforme Grupo A.

## 4. Exemplo causal: Chama Negra e Vingança

O exemplo v3 separa:

1. `unit_removed` (`effect_scope=direct`), cuja fonte é o efeito de remoção;
2. `vengeance_bonus_applied` (`effect_scope=reactive`), cuja fonte é `unit.vengeance_on_removal` e cujo pai é o evento de remoção.

A raridade épica da Chama Negra aparece apenas como classificação na definição da carta. Não é copiada ao evento de Vingança nem usada para calcular seu output. O `bonus_delta` ilustrativo vem dos parâmetros próprios do efeito reativo, não da raridade causadora.

No caso Rykard, o evento reativo de Vingança e o evento direto de Rykard são separados. A ordem causal registra primeiro a remoção, depois Vingança e então o output do líder. O total final depende dos parâmetros do release de regras aprovado.

## 5. Itens deliberadamente ainda abertos

- **Grupo C:** política de limpeza/preservação por transição; origem e duração de `weather_resistance`; duração/cargas dos buffs, escudos e estados. `weather_resistance` permanece deprecated/provisório na v3.
- **Grupo D:** política de alvo ausente/parcial, quantidade mínima/máxima, seleção de alvos secundários, resultado completo da operação e regras de consumo.
- **Grupo F:** conjunto de causas que dispara Vingança, incluindo sacrifício, e interação final com escudo/remoção.
- **Grupo E / CI-014:** DDL, ledger durável, idempotência no DB, transação atômica, CAS/lock por partida, migração e recuperação de snapshots.
- Releases reais de catálogo/registry/balance/ruleset ainda não foram publicados. IDs `example-only.*` do arquivo de exemplo não são releases operacionais.
- Fórmulas numéricas de EFP, custo, teto 32, carga de líder e faixas de raridade permanecem propostas não aprovadas.

## 6. Critérios de aceite da próxima integração (não executada)

1. Resolver quatro releases imutáveis da partida e conferir os quatro SHA-256 antes de iniciar.
2. Calcular e conferir o `definition_digest` do manifesto e o digest de cada snapshot mecânico.
3. Impedir consultas ao catálogo corrente durante replay/resolução de partida antiga.
4. Garantir retry idempotente por `operation_id` + fingerprint; colisão de fingerprint deve rejeitar.
5. Persistir estado/revisão/operação/eventos na mesma transação sob CAS/serialização por partida.
6. Rejeitar evento com operação inexistente, pai causal ausente, pai posterior, ciclo ou sequência repetida.
7. Garantir que `rarity_id` não entra no resolvedor nem muda qualquer saída mecânica.
8. Garantir que efeito reativo aponta para sua própria fonte e não herda raridade/parâmetros da causa.
9. Garantir que removal/Vingança e Rykard/Vingança/líder gerem eventos independentes e ordenados.
10. Garantir que bindings órfãos não sejam capacidades ativas.

## 7. Validação e limitações

O harness `scripts/validate-card-game-card-instance-v0.3.py` valida os schemas e o envelope sintético, além de UUID, ownership/zona, unicidade, digest de fixture, relação operação/evento, sequência causal, idempotência em memória e ausência de herança de raridade.

É validação documental/sintética. Não consulta DB real, catálogo publicado, serviço de release, partidas de produção, runtime novo, HTTP, Discord, browser ou transações concorrentes. O SHA-256 do exemplo valida o algoritmo aplicado à fixture; não comprova que existam releases operacionais publicados.

## 8. Estado após aprovação do Grupo B

**Aprovadas — Grupo A:** CI-001, CI-002, CI-003, CI-004, CI-006, CI-010, BUF-013 e RSRX-09.  
**Aprovadas — Grupo B:** CI-005, CI-011, BUF-001 (Alternativa A), BUF-002, BUF-012, RSRX-03 (causas finais no Grupo F) e RSRX-05 (separação causal, não valor agregado).  
**Abertas:** CI-007/008/009/012/013/014; BUF-003…BUF-011, BUF-014; RSRX-01/02/04/06/07/08/10; e grupos C/D/F/E conforme acima.

**Restrição:** o motor antigo não foi apagado nem substituído. A aprovação dos Grupos A e B fecha contratos documentais, não autoriza migração nem integração funcional.
