# Revisão cruzada de decisões — CardInstance, buffs e ciclo de vida v0.1

> **Atualização rev. 9 — Grupo B aprovado:** o proprietário aprovou CI-005, CI-011, BUF-001 (Alternativa A), BUF-002, BUF-012, RSRX-03 (com causas finais no Grupo F) e RSRX-05 (separação causal, não valor agregado). Este parecer e sua matriz preservam as recomendações históricas; os estados atuais estão em `docs/card-game-snapshot-causality-group-B-approval-v0.1.md/.json` e `docs/card-game-card-instance-contract-v0.3.md`.

> **Atualização posterior:** após a publicação deste parecer, o proprietário aprovou o Grupo A (CI-001/002/003/004/006/010, BUF-013 e RSRX-09). Consulte `docs/card-game-identity-group-A-approval-v0.1.md` e `docs/card-game-card-instance-contract-v0.2.md`. O estado “nenhuma decisão aprovada” descrito abaixo registra o momento original deste parecer; as demais decisões continuam abertas.

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev4.zip`  
**Status:** `TECHNICAL_RECOMMENDATIONS_FOR_OWNER_REVIEW_NOT_APPROVED`  
**Integração:** nenhuma. Runtime, catálogo ativo, schemas de produção, banco, API e frontend não foram alterados.

> Este documento consolida CI-001…CI-014, BUF-001…BUF-014 e as decisões de remoção/sacrifício/ressurreição. Ele recomenda uma resolução técnica coerente, mas não aprova regras de jogo em nome do proprietário. Os fatos abaixo vêm dos documentos e do código do pacote rev. 4; recomendações e inferências estão identificadas como tais.

> > **Atualização rev. 8 — Grupo B auditado, não aprovado:** `docs/card-game-snapshot-causality-group-B-audit-v0.1.md` confirma que o runtime não congela manifestos de definição nem registra causalidade estruturada. A reprodução da Chama Negra evidencia amplificação indireta de Vingança; Rykard mantém Vingança +1 seguida de +2 do líder. Há conflito entre a BUF-001 deste parecer (amplificar somente outputs diretos) e `card-game-balance-spec-v0.1.md` (remover amplificação por raridade). O parecer do Grupo B recomenda remover o amplificador, mas exige aprovação explícita. CI-005/011, BUF-001/002/012 e RSRX-03/05 permanecem abertas.

**Errata rev. 6 — CI-004:** a revisão do DDL em `database.py` confirmou que `cartas_exemplares.id` é `INTEGER PRIMARY KEY AUTOINCREMENT` global. A recomendação anterior de unicidade somente por (`owner_player_id`, `exemplar_id`) e a permissão de reutilizar o mesmo inteiro entre jogadores não correspondem ao banco atual. A proposta corrigida exige unicidade global do `exemplar_id` e validação da relação `exemplar_id -> (user_id, card_id)`. Ver `docs/card-game-identity-group-A-decision-review-v0.1.md`. CI-004 continua aberta e não aprovada.


## 1. Conclusão executiva

A recomendação é **aprovar a arquitetura de identidade e transações em princípio, mas não congelar ainda o schema v1 nem iniciar o migrador**. O contrato atual resolve a separação entre modelo, exemplar e ocorrência física, mas precisa de uma revisão coordenada antes de ser usado como contrato definitivo.

As dependências mais importantes são:

1. **Identidade e seleção:** CI-001/002/003/004/010 precisam ser resolvidas em conjunto com BUF-006/013 e RSRX-09. O servidor tem de identificar uma ocorrência exata, não apenas o modelo da carta.
2. **Estado e ciclo de vida:** CI-008/009 precisam ser resolvidas em conjunto com BUF-008/009/010/011/014 e as regras RSRX de remoção e retorno. Uma transferência de zona não pode decidir limpeza implicitamente.
3. **Causalidade e raridade:** CI-005/008/011 precisam carregar contexto suficiente para separar o efeito que iniciou uma operação dos efeitos reativos disparados por ela. Isso resolve a amplificação indevida de Vingança por raridade (BUF-001/002) e preserva o encadeamento de Rykard (RSRX-05) sem acoplamento incidental.
4. **Atomicidade:** CI-011/014 precisam abranger a ação lógica completa, não somente uma movimentação de zona. Sacrifício + ganho, remoção + Vingança, ressurreição + saída do descarte e consumo de relíquia precisam ser confirmados ou rejeitados como uma única transação.
5. **Migração:** CI-012 deve ser posterior ao fechamento das regras acima. Migrar antes de saber quais campos são preservados, limpos ou temporários cria snapshots formalmente válidos, mas semanticamente ambíguos.

**Decisão operacional recomendada:** manter todos os registros CI/BUF/RSRX como `OPEN`; aceitar este relatório como análise de engenharia; pedir aprovação explícita das decisões de design em bloco, antes de alterar o schema ou implementar o migrador.

## 2. Fatos do pacote que condicionam a decisão

- O contrato `CardInstance v0.1` define UUIDv4, registry central `instances`, quatro zonas ordenadas, `target_instance_id`, `state_policy_id`, `operation_id` e `state_revision`. Seu harness isolado passou 30/30; não executa runtime, SQLite ou concorrência real.
- O runtime usa `_remover_unidade()` baseado em igualdade estrutural de dicionários; a auditoria reproduz o risco de remoção da cópia física errada.
- Esgar filtra o descarte por `card_id` e pode remover várias cópias do mesmo modelo ao retornar uma; precisa de seleção/remoção por instância.
- Remoção central limpa escudo e quatro estados, mas preserva bônus e resistência climática; sacrifício ignora escudo e também pode disparar Vingança.
- Ressurgir/Réquiem zeram bônus e escudo, mas não limpam explicitamente estados em snapshots residuais; Esgar preserva o bônus existente e soma +1, limpa escudo/estados e força a fileira escolhida.
- Lágrima Sagrada devolve a carta à mão sem normalização adicional. É recuperação à mão, não ressurreição ao campo.
- A unidade ressuscitada não volta a executar habilidade de entrada, passiva de facção ou combo da jogada de retorno; pode contribuir para combos de jogadas posteriores.
- BUF-011 recomenda distinguir resistência climática intrínseca de modificador temporário; o schema atual tem apenas `weather_resistance: integer`.
- BUF-005 reconhece políticas distintas para ausência/parcialidade de alvos; o ledger do contrato atual só define `result: applied`.
- `cartas_gwent_matches` possui `state_json`, mas não uma coluna de revisão nem uma tabela de operações/idempotência no DDL encontrado. CAS/serialização ainda precisará de implementação de persistência.

Esses fatos não demonstram que snapshots reais estejam corrompidos ou duplicados. Os casos de duplicidade/estado residual são fixtures controladas e riscos estruturais reproduzidos.

## 3. Recomendações para CI-001…CI-014

| ID | Resolução técnica recomendada | Cruzamentos | Prioridade | Situação |
|---|---|---|---|---|
| **CI-001** | UUIDv4 canônico, gerado no servidor por fonte segura; imutável durante toda a vida da ocorrência na partida. Nunca derivar de `card_id`, `exemplar_id` ou posição no deck. | CI-002/006/011; BUF-013; RSRX-09 | P0 | Aberta — recomendação clara |
| **CI-002** | Unicidade global por partida, cobrindo ambos os participantes, todas as zonas e instâncias temporárias materializadas. Validar colisões no snapshot inteiro, não apenas no dicionário `instances`. | CI-001/006/012/014; RSRX-09 | P0 | Aberta — recomendação clara |
| **CI-003** | O modelo de instâncias deve permitir várias ocorrências com o mesmo `card_id`. Isso **não** altera a regra separada do deck builder que hoje exige 12 modelos distintos. Tokens, relíquias materializadas e snapshots legados também podem originar ocorrências repetidas. | CI-001/002/006/012; BUF-013; RSRX-09 | P0 | Aberta — separar do deck builder |
| **CI-004** | Preservar `exemplar_id` apenas quando houver vínculo comprovado. Exigir para `origin_type=deck_exemplar`; aceitar `null` para catálogo/IA, token e ativação transitória. No DDL atual, `cartas_exemplares.id` é PK global; validar `user_id`/owner e `card_id`. | CI-003/006/012; origem de RSRX-09 | P1 | Aberta — recomendação corrigida no Grupo A |
| **CI-005** | Congelar `definition_snapshot` e versões imutáveis do catálogo/regras no início da partida. Recomenda-se acrescentar um digest canônico da definição para detectar divergência; estado de combate não deve ser copiado para o snapshot de definição. | BUF-001/002/012/014; RSRX-01/06/07 | P0 | Aberta — requer versão de catálogo/regras reproduzível |
| **CI-006** | Cada carta/token que entrar numa zona ou no pipeline de resolução como ocorrência de carta recebe `instance_id` próprio. A relíquia equipada permanece equipamento fora das quatro zonas; só a ativação recebe instância temporária se continuar sendo materializada como carta no pipeline. Se a ativação for modelada como evento/ordem, não inventar uma carta física. | CI-001/002/003/004/013; BUF-012; RSRX-09 | P1 | Aberta — distinção equipamento vs ativação |
| **CI-007** | Manter `owner_player_id` imutável e proibir transferência de controle na v1. Não adicionar `controller_player_id` sem uma mecânica ativa aprovada. Se surgir roubo/controle, revisar também a regra de qual jogador contém a referência da zona; proprietário e controlador não podem ser confundidos. | CI-002/013; arquitetura futura | P2 | Aberta — pode ser adiada |
| **CI-008** | Proibir limpeza implícita. Cada transição/evento declara política de estado para bônus, escudo, estados, resistência, combos e posição. A política de zona (`from_zone`/`to_zone`) não determina, por si só, a normalização. | BUF-008/009/010/011/014; RSRX-03/05/07/08/10 | P0 | Aberta — decisão-mãe de ciclo de vida |
| **CI-009** | Dividir resistência climática intrínseca (parte imutável da definição/atributo permanente) de modificadores temporários com origem, valor e expiração explícitos. O valor efetivo é calculado na resolução. A forma escalar atual deve ser tratada como agregada/legada, não como fonte de duração. | BUF-011; CI-005/008/012; RSRX-10 | P0 | Aberta — exige revisão do schema |
| **CI-010** | Usar `target_instance_id` em toda seleção física. `card_id`/`target_id` legado só pode funcionar em adaptador versionado quando houver exatamente um candidato elegível; ambiguidade rejeita a ação. O servidor revalida lado, zona, tipo, fileira, métrica e elegibilidade. | BUF-003/004/005/006/013; RSRX-06/08/09 | P0 | Aberta — recomendação clara |
| **CI-011** | UUIDv4 por operação lógica e ledger durável para replay idempotente. Fingerprint inclui revisão esperada e payload semântico. Mesma chave/mesmo payload retorna resultado anterior; mesma chave/payload diferente é conflito. O registro do resultado e as mutações da ação precisam ser atômicos. | CI-014; BUF-005/009/010; RSRX-02/03/05/09/10 | P0 | Aberta — ampliar além de `policy.identity_only` |
| **CI-012** | Migrar snapshot antigo uma única vez, com IDs criados e persistidos no mesmo commit da mudança de schema. Preservar contagem e ordem das ocorrências; nunca inferir `exemplar_id`; falha/ambiguidade aborta a ação e mantém snapshot original recuperável. Não executar até CI-008/009 e políticas RSRX/BUF estarem fechadas. | CI-001/002/004/005/008/009/010/014; BUF-011; RSRX-07/08/09/10 | P0 — bloqueado por dependências | Aberta — não iniciar migrador |
| **CI-013** | Manter `hand`, `draw_pile`, `board`, `discard` na v1. `board` só aceita unidade. Equipamento equipado permanece metadado fora das zonas; ativação materializada usa instância transitória. Exílio/banimento ou nova zona requer nova versão do schema. | CI-006/007/008/012; RSRX-09/10 | P1 | Aberta — recomendação clara |
| **CI-014** | Exigir revisão monotônica e CAS/serialização por partida, gravando snapshot e ledger na mesma transação. Para persistência real, a opção preferida é revisão versionada no registro da partida e ledger com chave única `(match_id, operation_id)`; ambos atualizados no mesmo commit. Testar duas ações concorrentes com a mesma revisão. | CI-011/012; todas as ações multi-alvo; RSRX-02/03/05/09 | P0 | Aberta — exige mudança de persistência e teste real |

### 3.1. Nota sobre CI-014 e banco

O contrato em JSON já contém `state_revision`, mas o DDL atual da tabela `cartas_gwent_matches` expõe `state_json` sem coluna `state_revision` e não foi encontrada uma tabela dedicada de operações. Recomendação de implementação futura: adicionar revisão persistida e ledger com restrição única por partida/operação, ou demonstrar mecanismo equivalente de serialização por partida. O snapshot, a revisão e o resultado idempotente da operação devem confirmar juntos. O harness em memória não prova isso.

## 4. Recomendações para BUF-001…BUF-014

| ID | Resolução técnica recomendada | Relação com CardInstance/RSRX | Situação |
|---|---|---|---|
| **BUF-001** | Amplificar somente deltas atribuídos ao efeito que está sendo resolvido. Outputs reativos recebem contexto causal próprio e só escalam se o efeito reativo declarar expressamente sua própria regra de raridade. | Exige `source_effect_id`/contexto de resolução; CI-005/008/011; RSRX-03/05. | Aberta |
| **BUF-002** | Vingança disparada por remoção não herda a raridade da carta que causou a remoção. Exceção somente se o próprio contrato de Vingança declarar amplificação explícita. | RSRX-03 define causas; CI-005 fixa a regra usada na partida; CI-011 registra a operação causal. | Aberta |
| **BUF-003** | Quantidade de alvos deve ser parâmetro explícito da carta/efeito, nunca uma consequência oculta do orçamento de raridade. Se a quantidade efetiva for 2, a UI deve informar e recolher as duas instâncias. | CI-010; RSRX-08/09; corrige divergência de Égide. | Aberta |
| **BUF-004** | Todos os alvos efetivamente afetados devem ser apresentados/selecionados, ou o efeito deve declarar no contrato um seletor secundário automático visível ao jogador. Não esconder a segunda unidade de Passo. Preferência: seleção explícita de todos os alvos quando houver escolha significativa. | CI-010/011; CI-014 para movimentação multi-instância. | Aberta |
| **BUF-005** | Política por efeito com `minimum_targets`, `on_no_target` e `on_partial_targets`. Distinguir `reject`, `consume_no_effect`, `fallback` e `partial_if_minimum_met`. `consume_no_effect` é uma ação consumida e deve ser registrada/confirmada atomicamente; `reject` não consome cartas, recursos ou alvos. | CI-010/011/014; RSRX-02 (Devorar sem alvo). | Aberta |
| **BUF-006** | Cada efeito declara lado, escopo de fileira, elegibilidade, métrica de ordenação, direção, quantidade, fallback e desempate. Pipeline: filtrar → calcular métrica → ordenar → cortar quantidade → resolver ausência/parcialidade → aplicar efeitos. Métrica exibida pela UI deve ser a mesma identificada pela API. | CI-010; CI-005 para snapshot de regra; BUF-013; RSRX-06/08/09. | Aberta |
| **BUF-007** | Não criar `transfer_bonus` genérico nesta etapa. Sacrifício com ganho, redução inimiga + ganho próprio e bônus de sobreviventes continuam efeitos compostos com causalidade explícita. Criar transferência estrita apenas quando existir regra que transfira exatamente o mesmo delta de origem para destino. | CI-008/011; RSRX-03/05 não são transferências de bônus. | Aberta |
| **BUF-008** | Separar `printed_row`/`base_row` imutável de `current_row` mutável. Guardar `last_unit_play_row` por jogador, não por instância; atualizar apenas quando uma unidade é realmente jogada; movimento, remoção, cartas especiais e retorno por ressurreição não alteram esse histórico. Fileiras de retorno são parâmetros por efeito. | CI-005/008; RSRX-08/10. | Aberta |
| **BUF-009** | Escudo protege categorias declaradas. Perfil-base compatível com o legado: bloqueia remoção comum/execução, consome uma carga quando bloqueia; sacrifício ignora. Estados, redução de bônus e purificação não consomem escudo, salvo configuração expressa. | CI-008; RSRX-03/10. | Aberta |
| **BUF-010** | Um serviço/resolvedor central avalia proteção por categoria; cada efeito declara `blockable_categories` e `consume_on_block`. O consumo da própria relíquia/carta é regra separada do consumo do escudo. | CI-008/011/014; RSRX-01/03; resolve diferenças de Lâmina Negra/Algemas. | Aberta |
| **BUF-011** | Modelar resistência intrínseca separada de modificadores temporários. Cada modificador registra fonte, magnitude e expiração (`round_end`, `leave_board`, duração em rodadas ou outro evento nomeado). Não inferir que um buff temporário persiste no descarte porque o escalar legado sobrevive ao reset. | CI-005/008/009/012; RSRX-10. Exige revisão do campo escalar no schema. | Aberta |
| **BUF-012** | Migrar somente atribuições ativas comprovadas no catálogo atual. Preservar aliases/branches sem binding como histórico/compatibilidade arquivada; não promovê-los a capacidades do novo registry sem reatribuição explícita. | CI-005/012; não tratar código órfão como carta ativa. | Aberta |
| **BUF-013** | Desempate determinístico e declarado. Para seletores semânticos `first`, usar ordem de zona/tabuleiro persistida, que é intencional; para empates de métrica sem regra de ordem, usar sequência estável de entrada/jogada e `instance_id` como último fallback. Nunca depender de ordem acidental de serialização. | CI-001/002/010/012; RSRX-06/09. | Aberta |
| **BUF-014** | Definir limites padrão e overrides por efeito dentro da versão de balanceamento. Não impor um piso/teto global implícito; cada efeito declara limites/escape quando necessário. O valor numérico do default depende da futura calibração 1–15 e permanece pendente. | CI-005/008; RSRX-06/07. | Aberta |

## 5. Recomendações para remoção, sacrifício e retorno (RSRX)

Os IDs RSRX-01…RSRX-10 abaixo são **chaves locais desta revisão cruzada** para organizar as decisões da seção 5 do documento de remoção/ressurreição; não alteram nem renomeiam o registro histórico original.

| ID local | Decisão original | Resolução técnica recomendada | Cruzamentos | Situação |
|---|---|---|---|---|
| **RSRX-01** | Limite da Execução | Não manter expressão de raridade que matematicamente permanece em 6. Declarar o limite como parâmetro explícito e alinhar texto/UI. O valor 6 é comportamento legado observado, não valor final aprovado para o sistema de poder 1–15. | BUF-006/014; CI-005/010. | Aberta |
| **RSRX-02** | Devorar sem aliado elegível | Rejeitar antes do consumo da carta e de qualquer mutação se o sacrifício for pré-condição; alternativa válida é fallback descrito no texto. Não permitir no-op silencioso. | BUF-005/006; CI-010/011/014. | Aberta |
| **RSRX-03** | Vingança no sacrifício | Tratar `sacrifice` como causa explícita. Recomendação candidata: Vingança dispara uma vez após sacrifício bem-sucedido, pois é o comportamento reproduzido; nunca dispara em tentativa bloqueada/não concluída. O registry lista as causas que disparam, sem inferência do tipo de operação. | BUF-001/002/009/010; CI-008/011/014. | Aberta |
| **RSRX-04** | Contador `baixas` | Não chamar todos os eventos de morte. Usar contador/evento `board_removals` ou `removed_units` para saídas totais e contador separado `sacrifices` quando a distinção for relevante. Manter adaptador para `baixas` legado durante migração. | CI-005/008/012; RSRX-03. | Aberta |
| **RSRX-05** | Vingança + Rykard | Preservar a soma (+1 de Vingança e +2 de Rykard = +3 por sobrevivente) como composição explícita, caso o design aprove acumulação. Eventos/deltas mantêm fontes separadas; nenhum bônus é reatribuído à carta jogada que iniciou a cadeia. | BUF-001/002/007/014; CI-005/008/011. | Aberta |
| **RSRX-06** | Limites de poder no descarte | Manter elegibilidade e limite declarados por efeito, não uma regra universal. Valores legados (Ressurgir/Esgar ≤5; Réquiem e Lágrima com fórmulas próprias) precisam ser reavaliados no balanceamento 1–15; não congelar fórmula de raridade sem aprovação. | BUF-006/014; CI-005/010. | Aberta |
| **RSRX-07** | Bônus na ressurreição | Declarar um `bonus_policy` por efeito: Ressurgir/Réquiem zeram; Esgar soma +1 ao bônus preservado. Esta é a recomendação de compatibilidade com o comportamento observado, não uma regra final de balanceamento. Não usar uma política genérica implícita para todo retorno. | BUF-014; CI-008/012; RSRX-10. | Aberta |
| **RSRX-08** | Fileira de retorno | Declarar `row_policy` por efeito: Ressurgir preserva fileira válida e usa a fileira da jogada atual como fallback; Réquiem preserva válida e usa fileira escolhida ou `melee`; Esgar força a fileira escolhida. Validar que o destino é uma fileira válida. | BUF-008; CI-008/010; RSRX-10. | Aberta |
| **RSRX-09** | Instância física | Toda seleção/retirada de descarte opera sobre `instance_id` e remove exatamente uma ocorrência. `card_id` serve para nome/arte e só pode funcionar como adaptador legado quando houver uma única ocorrência elegível. Corrige os riscos de remoção por igualdade e remoção em massa de cópias. | CI-001/002/003/004/006/010/012; BUF-013. | Aberta |
| **RSRX-10** | Estado após retorno ao campo | Remoção bem-sucedida limpa escudo e quatro estados; regra candidata de retorno ao campo também limpa escudo/estados para proteger contra snapshots antigos. Bônus e fileira seguem RSRX-07/08. Retorno não reexecuta habilidade de entrada/passiva/combo da jogada; a unidade pode contribuir para combos futuros. Resistência temporária segue BUF-011, não um escalar herdado. | CI-008/009/012; BUF-008/009/010/011/014; RSRX-07/08. | Aberta |

### 5.1. Dois contratos de ciclo de vida adicionais derivados da matriz

- **Recuperação à mão (Lágrima Sagrada):** manter separada da ressurreição ao campo. O legado move a ocorrência do descarte para a mão e preserva o payload; a política futura deve declarar campo a campo se esse comportamento é intencional. A ação deve selecionar uma instância exata e não executar gatilhos de entrada no tabuleiro.
- **Timing de retorno:** a unidade ressuscitada é anexada depois da verificação de combo e não recebe habilidade de entrada/passiva/combo pela jogada que a trouxe. Ela permanece elegível para interações futuras em campo. Tratar retorno como evento próprio, não como nova jogada de unidade.

## 6. Matriz de dependências e ordem de fechamento

| Grupo | Decisões que precisam ser fechadas juntas | Motivo | Bloqueia |
|---|---|---|---|
| **A — Identidade** | CI-001/002/003/004/006/010 + BUF-013 + RSRX-09 | Sem identidade física única, seleção manual, desempate, retirada de descarte e migração não são seguros. | Seletor novo, remoção/ressurreição e migrador |
| **B — Snapshot e causalidade** | CI-005/011 + BUF-001/002/012 + RSRX-03/05 | Raridade, Vingança e buffs de líder precisam distinguir fonte direta de evento reativo, usando definições congeladas. | Resolver de efeitos e eventos reativos |
| **C — Estado e expiração** | CI-008/009 + BUF-008/009/010/011/014 + RSRX-07/08/10 | Posição, proteção, bônus, status e resistência precisam de política em cada transição. | Schema CardInstance v0.2 e registry de ciclo de vida |
| **D — Seleção e custo de ação** | CI-010/011/014 + BUF-003/004/005/006 + RSRX-01/02/06 | UI, seletor, alvos secundários, ausência de alvo e consumo precisam ser uma única decisão atômica. | API/cliente, resolvedores multi-alvo e relíquias |
| **E — Persistência/migração** | CI-011/012/014 + CI-001/002/004/005/008/009 | Identificadores, versão, policies e resultados idempotentes têm de sobreviver ao processo e a concorrência. | Migrador e adaptação de banco |
| **F — Regras de remoção** | BUF-009/010 + RSRX-03/04/05/10 + CI-008/011/014 | Escudo, causa de remoção, Vingança, contador e buffs compostos têm ordem e atomicidade comuns. | Resolver de remoção/sacrifício |

**Ordem recomendada:** A → B → C → D → F → E. A migração (E) fica por último porque depende de identidade, snapshots e políticas de estado já aprovadas. O trabalho de persistência/protótipo pode ser desenhado antes, mas não migrar partidas.

## 7. Ajustes necessários antes de chamar o schema de CardInstance v1

O schema atual deve continuar sendo chamado de **candidato v0.1**. Antes de congelar uma versão, recomendo uma revisão do contrato com estes pontos:

1. **Resistência:** substituir o escalar sem proveniência por resistência intrínseca + modificadores temporários com `source_effect_id`, quantidade e expiração. O poder efetivo usa o total calculado na resolução.
2. **Políticas de estado:** manter `policy.identity_only` como operação neutra; adicionar policies nomeadas somente depois da aprovação do mapa RSRX/BUF. No mínimo separar movimento neutro, fim de rodada, remoção, recuperação à mão e ressurreição.
3. **Contexto de evento:** a execução de efeitos precisa ter `source_effect_id`, `source_instance_id` quando aplicável, causa/evento pai e alvos exatos. Isso impede que a raridade da carta inicial capture bônus reativos de Vingança.
4. **Resultado de operação:** além de `applied`, modelar outcomes semânticos como `blocked`, `rejected`, `consumed_no_effect` e `partial`, com distinção entre ação sem mutação, ação que consumiu recurso e ação que alterou apenas o escudo. O efeito exato no `state_revision` e no ledger deve ser definido antes da implementação.
5. **Operação multi-instância:** uma ação pode tocar várias ocorrências e recursos (vítima, sobreviventes, carta jogada, relíquia/escudo). A atomicidade precisa cobrir a ação inteira, não uma chamada isolada de transição de zona.
6. **Sequência determinística:** preservar ordem intencional das zonas; usar sequência estável de entrada/jogada para tie-breaks que tenham essa semântica e `instance_id` como fallback técnico. Não classificar a ordem do array como acidental onde o efeito define `first`.
7. **Estado de jogador:** `last_unit_play_row` pertence ao estado do participante, não a `CardInstance`; não alterar esse valor por movimento, remoção, especial ou retorno de ressurreição.
8. **Persistência:** desenhar revisão monotônica e idempotência para SQLite/DB com teste concorrente real. O protótipo em memória continua insuficiente para aprovar CI-014.

Esses itens exigem nova revisão/versionamento do schema e do exemplo. Não editar o schema atual silenciosamente nem tratar os campos candidatos como já implementados.

## 8. Plano de validação depois da aprovação

1. Testes de invariantes globais entre `instances` e zonas, incluindo duplicata, referência órfã, cópia física idêntica, ownership e tipo da zona.
2. Testes de cada `state_policy_id` com snapshots antes/depois: remoção comum, execução bloqueada, sacrifício, fim de rodada, recuperação à mão, Ressurgir, Réquiem e Esgar.
3. Testes de causalidade: raridade + Vingança; Vingança + Rykard; bônus de sobreviventes; output de efeito direto versus output reativo.
4. Testes de seletor e UI: cada métrica, `target_instance_id`, desempate, número de alvos, alvo secundário, ausência/parcialidade e valor mostrado ao usuário.
5. Testes de atomicidade multi-alvo: falha em qualquer etapa não pode deixar carta consumida, sacrifício feito ou escudo parcialmente alterado sem a política declarada.
6. Testes de replay e concorrência: mesma operação repetida, mesmo ID com payload diferente, revisão obsoleta, duas ações concorrentes, queda entre write e resposta, transação SQLite abortada.
7. Migração de fixtures legadas com cópias iguais, exemplar ausente, status residual, estado incoerente, ordem de descarte e falha/rollback.
8. Só depois, integração em branch isolada, primeiro no resolvedor candidato; não substituir o motor legado diretamente.

## 9. Validação executada nesta revisão

Foram reexecutados os harnesses presentes no pacote rev. 4:

| Artefato | Resultado |
|---|---:|
| Contrato candidato CardInstance | 30/30 |
| Resolvedor candidato + evidência do legado para RSRX | 49/49 |
| Auditoria base de buffs/proteção | 14/14 |
| Interações cruzadas de buffs | 9/9 |
| Sequência/`last_row` | 10/10 |
| Escopo e seleção de alvos | 15/15 |
| Paridade UI/alvo manual | 12/12 |
| Identidade/ciclo de vida | 17/17 |

As suítes têm escopos diferentes e **não** formam uma cobertura somável. Elas validam os contratos/auditorias anteriores; não testam o conteúdo deste parecer como implementação, persistência SQLite concorrente, HTTP, Discord, navegador ou produção.

## 10. Estado e próximo passo

- CI-001…CI-014: continuam `OPEN`.
- BUF-001…BUF-014: continuam `OPEN`.
- Decisões RSRX: continuam pendentes; os IDs RSRX-01…10 são apenas chaves locais deste parecer.
- Nenhuma recomendação foi aprovada pelo proprietário.
- Não há mudança funcional, migrador, integração, alteração de DB ou substituição de motor.

**Próximo passo recomendado:** revisar primeiro os grupos A, B e C em conjunto. Após aprovação explícita, preparar `CardInstance v0.2`/schema revisado e o contrato de evento/estado; depois fechar seleção e atomicidade (D/F). O migrador só entra no plano executável quando E estiver fechado.

## 11. Fontes internas consultadas

- `docs/card-game-card-instance-contract-v0.1.md` e `docs/card-game-card-instance-match.schema.v1.json`.
- `docs/card-game-buffs-decision-register-v0.1.md`.
- `docs/card-game-buffs-cross-interactions-v0.1.md` e `docs/card-game-buffs-movement-protection-audit-v0.1.md`.
- `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` e `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md`.
- `docs/card-game-identity-lifecycle-audit-v0.1.md`.
- `docs/card-game-manual-target-ui-parity-audit-v0.1.md` e `docs/card-game-target-selection-row-scope-audit-v0.1.md`.
- `docs/card-game-sequence-power-state-audit-v0.1.md`.
- `sistemas/gwent.py` e `database.py` (somente leitura).
