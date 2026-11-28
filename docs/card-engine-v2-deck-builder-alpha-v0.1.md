# Card Engine v2 — Deck Builder e aplicação alpha v0.1

**Baseline:** revisão 25.  
**Release de regras:** `soulsbo-alpha-deck-rules-v0.1`.  
**Status:** implementado e testado como serviço isolado; não conectado a Discord, HTTP ou frontend.

## 1. Regra de deck adotada

A fonte normativa usada nesta implementação é `docs/CARD_GAME_REDESIGN.md`, seção **10. REGRAS OFICIAIS / Setup**:

- 30 cartas por deck;
- no máximo três cópias de cada `card_id`;
- mão inicial de quatro cartas.

A proposta exploratória de deck com 12 cartas, mínimo de oito unidades, máximo de quatro especiais e orçamento 32 que aparece em `docs/card-game-balance-spec-v0.1.md` permanece explicitamente não aprovada e não foi usada. O custo de energia por carta também não foi convertido em custo de construção do deck.

## 2. Validação autoritativa

`AlphaDeckBuilder` valida no servidor:

- tamanho exatamente igual a 30;
- no máximo três cópias por ID;
- todos os IDs na allowlist alpha ativa;
- modelos com tipo `unit` ou `special` reconhecido;
- facção selecionada pertencente ao conjunto canônico;
- compatibilidade entre facção do jogador e líder escolhido;
- inventário atual contendo a quantidade necessária de cada carta.

Não há restrição de deck monofação nem proporção mínima/máxima de unidades/especiais porque a fonte oficial consultada não define essas regras. A lista é embaralhada no servidor antes da distribuição. `shuffle_seed` e `starting_player_seed` existem apenas na entrada de baixo nível do controlador para simulações reproduzíveis; `AlphaGameApplication`, que será a fronteira dos transports, não expõe seed nem permite que cliente escolha o primeiro jogador.

A allowlist permanece em 27 modelos. Os outros 110 modelos históricos não podem entrar em decks alpha.

## 3. Partida competitiva estrita versus harness de testes

`AlphaMatchController.create_match()` continua disponível para fixtures determinísticas curtas dos testes. Esse método não é a entrada competitiva.

`AlphaMatchController.create_competitive_match()` exige inventário por jogador, valida os dois decks de 30 cartas, confirma líder/facção, embaralha cada lista no servidor, sorteia o primeiro jogador usando `random.SystemRandom` e cria a partida com mão inicial de quatro. O sorteio determina também quem inicia com a energia do primeiro turno; a aplicação de transporte não aceita que o cliente escolha o primeiro jogador. A view/runtime registra:

- `mode=competitive_alpha`;
- versão das regras de deck;
- tamanho e limite de cópias;
- mão inicial;
- confirmação de embaralhamento server-side;
- confirmação de que o inventário foi verificado;
- método `first_player_selection=server_random` e ID do jogador sorteado.

Deck inválido ou inventário insuficiente rejeita antes da criação da partida.

## 4. Persistência de decks

`SQLiteDeckRepository` grava decks salvos em SQLite próprio, diferente do banco de snapshots de partida e do banco legado.

- Chave: `(owner_player_id, deck_id)`.
- Nome, lista de modelos, facção, líder, versão das regras e timestamps persistidos.
- Atualização exige `expected_version`; versão divergente rejeita com `PersistenceConflict`.
- Exclusão também exige a versão esperada.
- Repositório recusa arquivo SQLite não vazio sem marcador próprio.
- `integrity_check` e `foreign_key_check` são expostos por `verify_integrity()`.

A gravação exige validação de propriedade; a criação da partida repete a validação com o inventário atual, portanto um deck salvo deixa de ser elegível caso a coleção tenha mudado.

## 5. Ponte de propriedade com a coleção antiga

`legacy_collection_counts(database, user_id)` é um adaptador assíncrono somente de leitura que consulta `database.coliseu_listar_colecao(user_id)` e normaliza `card_id → quantidade`. Ele não escreve no banco legado nem migra decks.

Essa ponte valida quantidades por modelo, mas ainda não vincula cada posição de deck a um `cartas_exemplares.id`. `CardInstance.exemplar_id` permanece sem integração com exemplares evoluídos da coleção. Portanto, o deck builder já protege a quantidade possuída, mas **não está aprovado para partidas de produção com exemplares individualmente evoluídos** até que a proveniência do exemplar seja conectada de ponta a ponta.

## 6. Fronteira assíncrona

`AlphaGameApplication` oferece casos de uso para salvar/listar/validar decks, criar partidas a partir de decks salvos, consultar view, emitir ofertas e executar ações de partida.

`AsyncAlphaGameApplication` executa as chamadas síncronas do SQLite através de `asyncio.to_thread`, evitando bloquear o event loop do Discord/HTTP. A superfície de ações é allowlisted (`play_unit`, `play_special`, `sacrifice_unit`, `activate_leader`, `activate_card_ability`, `pass_turn`); nomes privados ou desconhecidos são rejeitados.

Exemplo de inicialização com arquivos novos e dedicados:

```python
from sistemas.card_engine_v2.application import (
    AlphaGameApplication,
    AsyncAlphaGameApplication,
    legacy_collection_counts,
)

app = AlphaGameApplication(
    match_database_path="data/card-engine-v2-matches.sqlite3",
    deck_database_path="data/card-engine-v2-decks.sqlite3",
)
async_app = AsyncAlphaGameApplication(app)

# Dentro de um callback Discord/HTTP:
owned = await legacy_collection_counts(bot.db, user_id)
report = await async_app.validate_deck(
    card_ids=deck_card_ids,
    faction_id="golden_order",
    leader_id="comandante_fornalha",
    owned_card_counts=owned,
)
```

O exemplo não substitui autenticação/autorização do transporte: o handler precisa obter `user_id` do principal autenticado, nunca do corpo enviado pelo cliente. O banco legado não deve ser passado como `match_database_path` ou `deck_database_path`.

## 7. Evidência desta revisão

Testes adicionados:

- 30 cartas exatas, máximo três cópias;
- rejeição de IDs fora da allowlist;
- rejeição de inventário insuficiente/inválido;
- compatibilidade líder/facção;
- shuffle reproduzível por seed e sem mutar a lista original;
- sorteio do primeiro jogador no caminho competitivo e consistência da energia inicial com o jogador sorteado;
- persistência, listagem, atualização CAS, exclusão CAS e integridade;
- rejeição de banco não marcado;
- criação competitiva usando decks salvos pertencentes aos jogadores;
- revalidação do inventário no matchmaking;
- mão inicial quatro e pilha de compra 26;
- fachada async e rejeição de nomes de ação não permitidos;
- ponte somente leitura para contagens da coleção antiga.

A suíte total após a implementação: **171/171** testes aprovados.

## 8. O que ainda bloqueia a integração real

- A allowlist do novo motor ainda tem 27 cartas, não o catálogo completo.
- Os 110 modelos históricos permanecem bloqueados e sem reconstrução/revisão de facção concluída.
- As 18 combinações sem tags-fonte continuam inativas.
- O registry de habilidades manuais permanece vazio.
- A ligação de `exemplar_id` aos exemplares evoluídos da coleção antiga não foi feita.
- A fachada async ainda não foi conectada a comandos Discord, rotas HTTP ou frontend.
- A autorização de convite/aceitação do oponente, UX de ações e reconexão continuam pendentes.
- Não há playtest humano nem aprovação final de balanceamento dos custos.

Não houve alteração de `bot.py`, `database.py`, `site/app.js`, `sistemas/gwent.py` ou `sistemas/cartas.py`. Não houve acesso ao banco publicado, migração ou cutover.
