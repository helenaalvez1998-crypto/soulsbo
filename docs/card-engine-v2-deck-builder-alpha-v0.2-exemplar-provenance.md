# Deck Builder alpha v0.2 — proveniência física de exemplares

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev26.zip`  
**Revisão resultante:** rev. 27  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Escopo:** serviço isolado do Card Engine v2; nenhuma integração Discord/HTTP/frontend ou escrita no banco legado.

## Contrato de identidade

Os três identificadores têm papéis distintos e não são intercambiáveis:

- `card_id`: modelo/definição da carta no catálogo.
- `exemplar_id`: ID global da cópia física em `cartas_exemplares.id`.
- `instance_id`: UUIDv4 gerado pelo servidor para a ocorrência da cópia dentro de uma partida.

Cada slot de um deck competitivo de 30 cartas agora persiste um `card_id` e um `exemplar_id` alinhados. Um mesmo exemplar físico não pode ocupar dois slots nem ser selecionado para os dois participantes. O máximo continua sendo três cópias por `card_id`; IDs fora da allowlist permanecem bloqueados.

## Validação de coleção

`legacy_collection_exemplars(database, user_id)` chama somente `Database.coliseu_listar_exemplares(user_id)`, cuja projeção retorna `id`, `user_id`, `card_id`, `rarity`, `power`, origem e metadados do exemplar. O adapter transforma `id` em chave global e conserva dono, modelo, poder e classificação. O helper é somente leitura: não atualiza, migra nem grava em `database.py` ou nas tabelas legadas.

No `save_deck`, o serviço valida que cada ID existe no inventário recebido, pertence ao jogador, corresponde ao `card_id` do slot e não se repete. No matchmaking, o mesmo vínculo é verificado novamente com o inventário vivo, porque a coleção pode mudar depois que o deck foi salvo. A verificação global entre os dois decks rejeita qualquer `exemplar_id` duplicado antes da criação das instâncias.

## Snapshot do exemplar na partida

No matchmaking, slots `(card_id, exemplar_id)` são embaralhados como pares. O servidor gera um UUIDv4 `instance_id` por carta e cria `origin_type="deck_exemplar"` com:

- `exemplar_id`: referência da cópia física selecionada;
- `exemplar_snapshot.power_base`: poder individual atual do exemplar, lido no momento de criação da partida;
- `exemplar_snapshot.rarity_id`: classificação visual congelada para apresentação/auditoria.

O poder individual congelado passa a ser a base mecânica daquela ocorrência durante a partida. `effective_power`, métrica `base_power`, filtros de targeting e seleção de líder consultam a função comum `base_power(instance)`. A definição estática do catálogo continua imutável e separada do estado de evolução/aprimoramento da cópia. Alterações posteriores na coleção não reescrevem a instância já criada.

**Raridade é exclusivamente classificação.** Não altera poder, custo energético, elegibilidade, seleção de alvo ou efeitos. A ponte agora reconhece também `Primordial`, que já existe no vocabulário do banco legado e na progressão de raridade. O suporte não cria bônus mecânico.

## Persistência de decks

O marcador do `SQLiteDeckRepository` evolui para schema 2. A migration v1→v2 adiciona `exemplar_ids_json` com lista vazia para linhas antigas. Não inventa IDs a partir de quantidades agregadas. Linhas antigas sem proveniência física continuam consultáveis, mas são recusadas no matchmaking até que o proprietário salve novamente o deck com IDs reais obtidos da coleção.

A ordem e o tamanho de `card_ids_json` e `exemplar_ids_json` devem coincidir. O repositório rejeita IDs inválidos e repetidos; o serviço de aplicação valida a posse e o alinhamento com o modelo antes de persistir.

## Projeção de partida por jogador

`AlphaMatchController.view(match_id, viewer_player_id=...)` e `AlphaGameApplication.view_match_for_player(match_id, authenticated_player_id)` geram uma projeção destinada a um participante:

- a mão própria exibe `instance_id`, `card_id`, `exemplar_id`, poder congelado e raridade de exibição;
- a mão adversária retorna `hand_count` e `hand_hidden=true`, sem conteúdo nem IDs físicos;
- IDs físicos de cartas do adversário no campo também são omitidos;
- informações públicas do campo, poder efetivo, energia, vida e estado de rodada continuam disponíveis.

A view sem `viewer_player_id` é privilegiada e existe para simulação, diagnóstico e testes. Não deve ser enviada a jogadores. Um futuro handler Discord/HTTP precisa obter o `authenticated_player_id` da sessão/principal autenticado e nunca de um campo controlado pelo cliente. Esta revisão não cria o sistema de autenticação nem o handler de transporte. A API síncrona e a fachada assíncrona de aplicação não aceitam seeds de embaralhamento fornecidas pelo cliente; o matchmaking usa aleatoriedade do sistema. Seeds reproduzíveis permanecem restritas ao controlador de baixo nível para simulações e testes internos.

## Compatibilidade e limites

- As regras de deck permanecem 30 cartas, até três cópias por modelo e mão inicial de quatro.
- A allowlist continua em 27 cartas; os outros 110 modelos históricos permanecem bloqueados.
- O `CardInstance` continua no schema 7 draft. `exemplar_snapshot` é opcional no schema para preservar snapshots antigos; instâncias competitivas novas com `origin_type="deck_exemplar"` exigem `exemplar_id` e snapshot válido.
- Nenhum arquivo central do motor legado foi alterado. `database.py` é chamado somente através do adapter de leitura existente.
- Não existe transação distribuída entre o banco legado de coleção e os dois SQLite do Card Engine v2. A leitura viva é validada antes da criação da partida; a ocorrência é então congelada no snapshot v2.
- Não há UI, integração bot/API, autenticação de produção, playtests humanos, migração de jogadores ou cutover.

## Validação desta tranche

- Suíte oficial `docs/scripts/test-card-engine-v2-playable-alpha-v0.5.py`: 188/188 testes, zero falhas, zero ignorados.
- Inclui posse individual, correspondência `card_id`/exemplar, duplicidade dentro do deck, duplicidade global entre jogadores, inventário removido após salvar, migração de deck schema v1 sem IDs inventados, congelamento de poder, raridade Primordial, adapter legado somente leitura, projeção sem mão adversária e rejeição de seeds fornecidas à API sync/async de aplicação.
- `py_compile` aprovado para motor, scripts e testes.
- Staging histórico: 137 modelos, 27 alpha-only, 110 bloqueados; checks e hashes aprovados.
- Simulação Bo3: Player A venceu por 2–1, 97 eventos, SQLite `integrity_check=ok` e zero violações de chaves estrangeiras.
- Simulação de combos/passivas/líder: Player A venceu por 20–10, 49 eventos, SQLite `integrity_check=ok` e zero violações de chaves estrangeiras.
- Nenhum banco publicado foi aberto; simulações usam bancos temporários descartáveis.

## Próxima etapa

Construir handlers de interface/Discord usando `AsyncAlphaGameApplication`, obter o principal autenticado no adapter e nunca aceitar `owner_player_id`, deck de terceiro, IDs de alvo ou starter vindos diretamente do cliente. Depois disso, criar o fluxo visual de coleção/deck builder e partida. Reconstrução dos 110 modelos, ampliação dos combos e playtests seguem pendentes.
