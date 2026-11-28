# Contrato candidato `CardInstance` e transições de zona v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev3.zip`  
**Status:** `CANDIDATE_FOR_REVIEW_NOT_APPROVED`  
**Integração:** nenhuma. Nenhum handler, runtime, catálogo ativo, banco, API ou frontend foi alterado.  
**Validação deste contrato:** harness isolado; não importa `sistemas.gwent` nem o resolvedor de remoção/ressurreição candidato.

## 1. Decisão de escopo desta versão

Esta especificação estabelece uma identidade por ocorrência de carta em uma partida, separada da identidade do modelo e do exemplar da coleção. Também estabelece a representação das zonas e o comportamento transacional mínimo para mover uma ocorrência entre elas.

O documento é uma proposta técnica, não uma aprovação de regras de jogo. O schema e o harness estão isolados dos módulos de produção. O motor legado permanece como baseline e não deve ser substituído nesta etapa.

### O que está dentro do escopo

- Identidade imutável de cada ocorrência de carta durante uma partida.
- Snapshot imutável da definição compilada usada na partida.
- Zonas `hand`, `draw_pile`, `board` e `discard`, espelhando os arrays presentes em `novo_estado()`.
- Unicidade global de `instance_id` dentro da partida.
- Resolução de alvo pela identidade física.
- Transição atômica, pré-condição de zona de origem e chave de idempotência.
- Regras de migração que impeçam a geração de IDs novos a cada carregamento de um snapshot antigo.

### O que fica fora do escopo

- Implementar ou importar `CardInstance` no motor atual.
- Mudar o endpoint de deck, a regra atual de 12 `card_id` distintos ou a UI.
- Aprovar as regras de limpeza/preservação de bônus, escudo, estados, resistência climática ou combos.
- Permitir mudança de controle entre jogadores.
- Alterar o esquema SQLite ou migrar partidas salvas reais.
- Definir a duração definitiva de `weather_resistance` ou a política de estados residuais.

## 2. Evidência do baseline que fundamenta a proposta

A inspeção do pacote rev. 3 confirma:

1. `novo_estado()` copia cada deck e divide suas cartas entre `hand` e `draw_pile`; não gera `instance_id`.
2. O snapshot padrão em `_gwent_deck_snapshots()` injeta `exemplar_id`, mas `preparar_carta()` não o devolve no payload normal. `preparar_carta_pessoal()` é um caminho distinto e preserva `exemplar_id`, além de compor o campo legado `id` com `card_id::exemplar_id`.
3. `_resumo_alvo()` publica `id`, sem `instance_id`; a API lê `target_id` e o encaminha para `aplicar_jogada()`.
4. `_remover_unidade()` usa `unit not in board` e `board.remove(unit)`, operações baseadas em igualdade, não numa chave física inequívoca.
5. As zonas de cada jogador em `novo_estado()` são `hand`, `draw_pile`, `board` e `discard`.
6. As relíquias ficam fora das 12 posições do deck em `equipped_relic_id`; ao ativar, o caminho legado cria um payload temporário e o acrescenta à mão para reutilizar o pipeline de jogada.
7. O snapshot de partida é persistido em `state_json` na tabela de partidas; as rotas de ação carregam, alteram e salvam esse snapshot.

A auditoria de ciclo de vida v0.1 já reproduziu a fragilidade de igualdade estrutural e as colisões de identidade no resolvedor candidato. Os resultados anteriores são evidência do legado/candidato isolado, não testes deste novo contrato.

## 3. Vocabulário e separação de identidades

| Campo | Escopo | Significado | Mutável durante a partida? |
|---|---|---|---|
| `card_id` | Catálogo | Identifica o modelo canônico da carta. | Não dentro do snapshot da partida. |
| `exemplar_id` | Coleção de um jogador | Identifica o exemplar físico/registro de coleção escolhido para o deck, quando existir. | Não. Pode ser `null` para tokens, cartas de catálogo/IA, relíquias ativadas e importações sem exemplar recuperável. |
| `instance_id` | Partida inteira | Identifica uma ocorrência individual de carta/unidade no estado de uma partida. | **Nunca.** É gerado pelo servidor e acompanha a ocorrência por todas as zonas. |
| `owner_player_id` | Partida | Participante ao qual a ocorrência pertence no momento de sua criação. | Imutável nesta versão. |
| `current_row` | Estado de combate | Posição atual da unidade. | Sim; é diferente da fileira impressa na definição. |

`exemplar_id` não substitui `instance_id`: o primeiro identifica um registro de exemplar da coleção; o segundo identifica uma ocorrência única entre os dois lados da partida. No DDL atual, `cartas_exemplares.id` é PK global (`INTEGER PRIMARY KEY AUTOINCREMENT`), portanto o ID do exemplar não é local/reutilizável entre proprietários. A relação com o proprietário deve ser validada por `user_id` e `card_id`. `card_id` não deve ser usado como chave de remoção ou seleção física. Ver errata do Grupo A ao final.

O contrato permite que duas instâncias tenham o mesmo `card_id`, desde que cada ocorrência tenha `instance_id` próprio. Isso é uma propriedade do modelo de instância, não uma mudança na regra atual do deck builder: `_api_gwent_deck_save()` continua exigindo 12 modelos distintos até decisão separada.

## 4. Contrato de `CardInstance`

O schema candidato está em `docs/card-game-card-instance-match.schema.v1.json`; um snapshot ilustrativo em `docs/examples/card-instance-match.example.v1.json`.

### 4.1 Campos obrigatórios

| Campo | Tipo | Regra candidata |
|---|---|---|
| `schema_version` | integer | `1`. |
| `instance_id` | string UUIDv4 | Gerado no servidor com fonte criptograficamente segura; minúsculo e canônico. Não derivar de `card_id`, `exemplar_id`, usuário ou índice do deck. |
| `card_id` | string | ID estável do modelo, repetível entre instâncias. |
| `exemplar_id` | integer positivo ou `null` | Preservar o vínculo de coleção quando disponível. Para `origin_type=deck_exemplar`, é obrigatório. |
| `owner_player_id` | string numérica | Deve corresponder ao participante dono das zonas desta ocorrência. A chave em `players` é a representação canônica atual do ID. |
| `origin_type` | enum | `deck_exemplar`, `catalog_deck`, `generated_token`, `equipped_relic_activation` ou `legacy_migration`. |
| `definition_snapshot` | object | Cópia imutável da definição compilada que foi usada ao iniciar/resolver a partida. |
| `state` | object | Estado mutável da ocorrência; não contém identidade nem dados de catálogo. |

### 4.2 `definition_snapshot` imutável

Campos: `catalog_version`, `balance_rules_version`, `card_id`, `kind`, `faction_id`, `printed_row`, `power_base`, `rarity_id`, `effect_id`, `effect_params` e `combo_tags`.

- `printed_row` e `power_base` são definidos pela carta de catálogo. Unidade exige fileira e poder-base; especial/relíquia exige `null` nesses dois campos.
- `current_row` fica em `state`, não em `definition_snapshot`.
- Os parâmetros e o identificador do efeito devem refletir a definição/compilação usada naquela partida. Uma atualização posterior do catálogo não pode reescrever silenciosamente uma partida em andamento.
- `catalog_version` e `balance_rules_version` precisam identificar versões imutáveis/reproduzíveis; o formato final de versionamento continua sujeito ao contrato canônico.

### 4.3 `state` de combate

O schema propõe:

- `current_row`: `melee`, `ranged`, `siege` ou `null` para especial/relíquia.
- `bonus`: inteiro.
- `shield_charges`: inteiro não negativo.
- `statuses`: contadores `status.bleeding`, `status.frost`, `status.scarlet_rot` e `status.madness`, cada um entre 0 e 2, alinhados aos IDs do registry candidato de estados.
- `weather_resistance`: inteiro não negativo. O schema não define duração, expiração ou se a resistência é atributo permanente; isso continua em aberto.
- `activated_combo_ids`: lista única de combos já ativados para a instância.
- `effect_state`: objeto tipado pelo registry do efeito individual. Nenhum estado arbitrário deve ser interpretado sem contrato do registry.

Para cartas especiais/relíquias, `current_row` é `null`; os campos numéricos podem ficar nos valores neutros definidos pelo exemplo. A representação de estados de carta não-unidade pode ser simplificada em revisão futura, mas não pode criar uma segunda identidade.

## 5. Envelope do estado da partida e zonas

A proposta usa um registry único `instances`, indexado por `instance_id`, e listas **ordenadas** de referências nas zonas de cada jogador. A ordem é preservada porque o topo/fundo da pilha, o último elegível do descarte, desempates do seletor e a ordem de tabuleiro podem afetar regras observadas no legado:

```json
{
  "schema_version": 1,
  "match_id": 123,
  "state_revision": 0,
  "status": "active",
  "players": {
    "1001": {
      "zones": {
        "hand": ["<instance_id>"],
        "draw_pile": [],
        "board": [],
        "discard": []
      }
    }
  },
  "instances": {
    "<instance_id>": {"instance_id": "<mesmo instance_id>"}
  },
  "operations": {}
}
```

O JSON acima é apenas um recorte estrutural; o exemplo completo está no arquivo de exemplo indicado no início desta seção.

### 5.1 Invariantes obrigatórios em todo snapshot estável

1. Cada `instance_id` aparece em **exatamente uma** lista de zona na partida inteira, somando os dois jogadores.
2. Cada referência de zona resolve exatamente uma entrada em `instances`.
3. Cada registro em `instances` é referenciado por uma zona; não existem instâncias órfãs nem duplicação silenciosa.
4. A chave do objeto em `instances` é igual ao campo `instance_id` do registro.
5. `owner_player_id` corresponde ao jogador que contém a referência. Troca de controle/propriedade não é permitida por este contrato v0.1.
6. `board` contém apenas instâncias cujo `definition_snapshot.kind` é `unit`.
7. UUIDs são únicos globalmente na partida. `card_id` pode repetir.
8. A ordem de cada lista de zona é significativa e deve ser preservada; mover uma instância remove apenas sua posição de origem e a anexa ao destino na ordem da operação.
9. Para instâncias `deck_exemplar`, o `exemplar_id` é globalmente único no banco atual e não pode ser reutilizado por outra instância na partida. A linha correspondente deve pertencer ao `owner_player_id` e seu `card_id` deve coincidir com o da instância.
10. O snapshot persistido representa um estado após uma transação completa. Não se serializa uma instância em duas zonas durante uma movimentação.
11. O número de zonas é deliberadamente fechado em quatro nesta versão. Uma futura zona (por exemplo, exílio) exige atualização explícita do schema e das invariantes; não se deve descartar a instância para simular uma zona inexistente.

### 5.2 Criação de identidade

No início da partida, o servidor deve:

1. carregar e validar os decks;
2. criar uma instância por ocorrência de carta, preservando `card_id` e `exemplar_id` quando disponível;
3. gerar todos os `instance_id` antes de distribuir cartas em `hand` e `draw_pile`;
4. inserir cada registro uma única vez em `instances`;
5. preencher as listas de zona com referências;
6. validar todas as invariantes antes de persistir o primeiro snapshot.

Tokens/unidades geradas devem receber seu próprio UUIDv4 no instante em que são criados. Uma ativação de relíquia, por ser materializada temporariamente pelo pipeline legado como payload em mão e não pertencer às 12 cartas do deck, deve receber uma instância de origem `equipped_relic_activation` caso o novo pipeline continue materializando-a como carta. O exemplar de coleção não deve ser inventado: `exemplar_id=null`.

## 6. Transições de zona: contrato transacional

Uma operação de zona recebe no mínimo:

```text
operation_id
instance_id
player_id
expected_from_zone
to_zone
state_policy_id
```

### 6.1 Política de movimento nesta versão

O harness de referência implementa apenas `state_policy_id = "policy.identity_only"`:

- confirma que a instância existe e está exatamente na zona de origem esperada;
- confirma que a zona de destino existe e é compatível com o tipo;
- remove a referência da origem e a adiciona ao destino numa única cópia transacional do estado;
- preserva `instance_id`, `card_id`, `exemplar_id`, `owner_player_id`, `definition_snapshot` e `state` integralmente;
- valida todas as invariantes novamente antes do commit;
- se qualquer validação falhar, o estado original não é modificado.

A movimentação não cria uma nova instância, não faz `deepcopy` lógico de uma carta para duplicar sua ocorrência e não normaliza bônus/escudo/estados implicitamente. Ações que precisam limpar ou alterar campos devem aplicar uma política de estado nomeada e aprovada, no mesmo commit transacional.

### 6.2 Idempotência e concorrência

- O envelope contém `state_revision`, inteiro monotônico não negativo, incrementado uma vez a cada mutação confirmada.
- A ação apresenta `expected_revision`; uma ação nova só é aceita quando esse valor coincide com a revisão carregada. Revisão divergente rejeita a ação sem alteração parcial.
- `operation_id` é UUIDv4 criado no servidor por ação lógica.
- O snapshot guarda `operations[operation_id]` com fingerprint SHA-256 dos argumentos recebidos, inclusive `expected_revision`. O ledger também persiste `expected_revision`, `revision_before`, `revision_after` e o resultado `applied` para auditoria; `revision_before` deve coincidir com `expected_revision`.
- Repetir o mesmo `operation_id` com os mesmos argumentos retorna o resultado anterior sem executar de novo e sem incrementar `state_revision`. O replay idempotente é reconhecido antes da comparação com a revisão atual.
- Reutilizar o mesmo `operation_id` com argumentos diferentes é conflito e deve falhar.
- `expected_from_zone` atua como precondição adicional: uma ação atrasada não pode mover a unidade a partir de uma zona diferente da esperada.
- A persistência deve gravar o snapshot e o registro da operação no mesmo commit de banco. A implementação precisa oferecer compare-and-swap por `state_revision` ou serialização equivalente por partida; a escolha do mecanismo de banco continua aberta.

O protótipo de transição no script valida essas regras em memória. `expected_revision` fica explícito no ledger, e a validação exige igualdade com `revision_before`. Não é uma implementação de produção nem testa concorrência real no SQLite.

### 6.3 Mudança de jogador/controlador

Nesta versão, uma instância só pode transitar entre zonas do seu `owner_player_id`. O baseline não demonstrou mecânica ativa de roubo/troca de controle que exija mover uma unidade para a zona do oponente. Caso exista ou seja aprovada uma mecânica assim, deve-se decidir separadamente entre `owner_player_id` imutável e `controller_player_id` mutável; não reutilizar `owner_player_id` silenciosamente.

## 7. Seleção de alvos e protocolo

- O servidor serializa `instance_id` em cada opção de alvo.
- O cliente envia `target_instance_id`, nunca `card_id` como identidade física.
- O servidor resolve o ID dentro do estado da partida, confirma proprietário/lado, zona, tipo, elegibilidade, fileira, poder e condições do efeito; o ID sozinho não autoriza a ação.
- `card_id` permanece disponível para exibir o nome/arte e identificar o modelo.
- Durante migração de snapshots antigos, `target_id` pode ser aceito apenas em uma rota de compatibilidade versionada e somente quando resolver exatamente uma opção elegível. Se houver ambiguidade, rejeitar; nunca selecionar a primeira cópia silenciosamente.
- `exemplar_id` não precisa ser exposto ao navegador. É metadado da coleção e não substitui autorização no servidor.

A mudança de payload HTTP/UI não faz parte desta entrega.

## 8. Políticas de ciclo de vida ainda não aprovadas

O contrato separa **movimentação** de **normalização de estado**. A observação do legado não basta para aprovar as políticas novas. O que foi observado na auditoria anterior:

| Operação legada | Observação reproduzida | Decisão nova ainda necessária |
|---|---|---|
| Remoção comum/execução/sacrifício | Remoção central limpa escudo e quatro estados; preserva bônus, `weather_resist` e `combo_ativado`. Escudo bloqueia algumas causas, sacrifício ignora. | Definir políticas por causa, gatilhos, limpeza e transferência a descarte. |
| Fim de rodada | Cópia arquivada zera bônus, escudo e estados e remove `combo_ativado`; preserva `weather_resist`. | Definir campos temporários, efeitos persistentes e comportamento na rodada final. |
| Lágrima Sagrada | Retorna a ocorrência do descarte à mão sem normalização adicional; o estado já pode ter sido limpo na remoção anterior. | Decidir preservação de cada campo sem herdar incidentalmente a condição de entrada. |
| Réquiem | Retorno ao campo zera bônus e escudo, preserva fileira válida; não zera explicitamente estados em registros obsoletos. | Definir limpeza completa e se retorno dispara efeitos de entrada. |
| Ressurgir | Retorno ao campo como entrada adicional; zera bônus e escudo, preserva fileira válida; não zera explicitamente estados em registros obsoletos. | Definir limpeza, timing e interação com combos/passivas/on-play. |
| Esgar | Força fileira escolhida, soma +1 ao bônus preexistente e limpa escudo e quatro estados; remove entradas do descarte por `id`. | Definir política de identidade exata, bônus inicial e normalização. |

Nenhuma dessas linhas vira `state_policy_id` final sem decisão explícita. Os nomes possíveis (`policy.remove_unit`, `policy.round_close`, `policy.recover_to_hand`, `policy.resurrect_to_board`) são apenas placeholders de trabalho, não IDs congelados.

## 9. Migração de snapshots antigos

Partidas legadas não têm `instance_id`. O novo carregador não deve gerar UUIDs novamente em cada leitura, pois isso quebraria referências e idempotência. Proposta:

1. detectar `schema_version`/marcador de identidade ausente;
2. executar um migrador determinístico por snapshot, sem mutação parcial;
3. gerar UUIDs para cada ocorrência física, mesmo quando os `card_id` forem iguais;
4. preencher `exemplar_id` apenas quando houver vínculo comprovável; não inferir ou inventar exemplar;
5. construir `instances` e zonas, validar unicidade e contagem;
6. persistir o snapshot migrado e a versão de schema atomicamente antes de aceitar uma ação;
7. em falha/ambiguidade, interromper a ação e preservar o snapshot original para recuperação — não criar identidade parcial em memória e seguir o jogo.

Um seed determinístico derivado do antigo snapshot só seria apropriado depois de avaliar privacidade, colisões, cópias do snapshot e requisitos de auditoria. A recomendação atual é UUIDv4 aleatório criado uma única vez e persistido na migração transacional.

## 10. Decisões pendentes para aprovação

| ID | Decisão | Recomendação técnica candidata | Situação |
|---|---|---|---|
| CI-001 | Formato de `instance_id` | UUIDv4 canônico, gerado no servidor. | Aberta |
| CI-002 | Escopo de unicidade | Global por partida, entre os dois participantes e todas as zonas. | Aberta |
| CI-003 | Cópias do mesmo `card_id` | Suportar múltiplas instâncias distintas no modelo; manter a regra do deck atual separada. | Aberta |
| CI-004 | `exemplar_id` | Preservar quando comprovado; usar a PK global atual e validar owner/card_id. | Aberta |
| CI-005 | Snapshot imutável | Congelar versão de catálogo/balanceamento e dados mecânicos no início da partida. | Aberta |
| CI-006 | Identidade de tokens/relíquias temporárias | Atribuir instância própria a toda ocorrência que entrar no pipeline/zona. | Aberta |
| CI-007 | Controle entre jogadores | Manter transferência bloqueada até existir regra explícita e estado `controller_player_id`. | Aberta |
| CI-008 | Política de limpeza | Nenhuma limpeza implícita; políticas nomeadas por evento/efeito. | Aberta |
| CI-009 | `weather_resistance` | Persistir como campo distinto; duração/expiração pendente. | Aberta |
| CI-010 | Seleção de alvo | `target_instance_id`, com compatibilidade antiga apenas se houver correspondência única. | Aberta |
| CI-011 | Idempotência | `operation_id` UUIDv4 e ledger persistido no mesmo commit da mutação. | Aberta |
| CI-012 | Migração de partidas ativas | Migrar e persistir uma única vez antes de permitir novas ações; falha aborta a ação. | Aberta |
| CI-013 | Zonas suportadas | As quatro zonas atuais; qualquer zona nova exige nova versão do schema. | Aberta |
| CI-014 | Concorrência na persistência | Exigir `state_revision` + compare-and-swap (ou serialização equivalente por partida) no mesmo commit do snapshot e ledger. | Aberta |

As recomendações são técnicas; todas as decisões permanecem abertas até aprovação do proprietário. Nenhuma aprovação foi inferida pelo pedido de execução desta auditoria.

## 11. Testes e limitações

Harness: `docs/scripts/test-card-instance-contract-v0.1.py`. Resultado estruturado: `docs/card-game-card-instance-contract-validation-v0.1.json`.

O script testa invariantes de identidade e zonas, duplicação de chaves JSON, validação de tipos/estados, preservação durante transição, ordenação de zonas, precondição de origem, revisão monotônica, idempotência e atomicidade do protótipo em memória. Ele não importa runtime legado, não executa handlers reais, não acessa SQLite, não testa HTTP/JavaScript/Discord/R2 e não demonstra carga concorrente.

O schema JSON descreve a estrutura local. Unicidade global, integridade referencial, propriedade das zonas, instâncias órfãs e atomicidade dependem de validação semântica adicional; JSON Schema não substitui essas verificações cruzadas.

**Resultado do harness:** 30/30 assertions aprovadas; zero falhas. O schema passou pela meta-validação Draft 2020-12 e o exemplo foi validado sem erros. A aprovação dos testes valida o protótipo do contrato, não aprova o design nem autoriza integração.

## 12. Próximo passo

Revisar CI-001…CI-014 e, em paralelo, fechar as políticas de ciclo de vida de remoção/retorno (RSRX) e duração de bônus/escudo/estados/resistência (BUF). Só após as decisões aprovadas deve-se adaptar o resolvedor candidato, criar um migrador de snapshots e planejar integração gradual. Até lá, preservar o motor antigo como baseline.


## Errata técnica — Grupo A (rev. 6, não aprovada)

A revisão do DDL confirmou que `cartas_exemplares.id` é uma chave primária global da tabela. A formulação anterior de unicidade apenas por (`owner_player_id`, `exemplar_id`) e a permissão de repetir o mesmo inteiro para jogadores diferentes não correspondem ao banco atual. A recomendação corrigida é unicidade global de `exemplar_id` e validação conjunta de `exemplar_id`, `user_id`/`owner_player_id` e `card_id`. O exemplo foi ajustado: a instância transitória de token não inventa exemplar e o exemplar do segundo participante usa outro ID global.

A errata é uma proposta de revisão para CardInstance v0.2; não representa aprovação nem altera DB, schema de produção ou runtime. Consulte `docs/card-game-identity-group-A-decision-review-v0.1.md`.
