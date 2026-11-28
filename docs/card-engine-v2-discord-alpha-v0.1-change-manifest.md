# Manifesto de mudanças — integração Discord Card Engine v2 alpha v0.1 (rev. 28)

**Baseline:** rev. 27.  
**Resultado:** primeira camada utilizável de UI/transport no comando `/jogo`, preservando o bot e o motor legado.

## Código novo

- `cogs/card_engine_v2_ui.py` — painel privado alpha, criação de deck por exemplares, seleção de líder, convites, escolha do deck do oponente, ações da partida, seleção/paginação de alvos e reabertura de partidas persistidas.
- `sistemas/card_engine_v2/discord_gateway.py` — fronteira de transporte com IDs de jogadores derivados da interação autenticada, leitura de inventário, revalidação, matchmaking, ações e view de participante.
- `tests/card_engine_v2/test_discord_gateway.py` — valida inventário, propriedade, matchmaking, privacidade, ações autenticadas, IDs compatíveis com JSON e listagem por participante.
- `tests/card_engine_v2/test_discord_ui_contract.py` — guardrails estáticos AST para projeção segura, ausência de acesso direto a SQLite na UI, identidade autenticada, entrada `/jogo`, reabertura, paginação e mensagens de erro sem detalhes internos.

## Código alterado

- `cogs/painel_jogo.py` — botão lazy-loaded **Partidas v2 · Alpha** na view já usada por `/jogo`; nenhum novo Cog/extensão precisa ser registrado. Falhas de inicialização são registradas no log e exibidas ao usuário com mensagem genérica.
- `sistemas/card_engine_v2/application.py` — adiciona operação mínima para listar metadados de partidas de um participante na fachada sync/async.
- `sistemas/card_engine_v2/repository.py` — consulta somente metadados de partidas do participante; não retorna snapshot completo nem mão.
- `sistemas/card_engine_v2/README.md` — documenta a nova fronteira de transporte e limites.
- `docs/card-game-handoff.md` — promove rev. 28 a baseline mais recente.

## Garantias mantidas

- UI usa `gateway.player_view()` e não chama `view_match()` privilegiado.
- UI não acessa ou escreve diretamente nos SQLite e não chama métodos de escrita do banco legado.
- Inventário legado é somente leitura e revalidado no save/matchmaking.
- Os cinco arquivos centrais legados (`bot.py`, `database.py`, `sistemas/gwent.py`, `sistemas/cartas.py`, `site/app.js`) não foram alterados.
- Sem liberação de cartas bloqueadas, mudança de regras, custos ou balanceamento.

## Evidência e limitações

- `py_compile` aprovado para UI, gateway, painel e pacote do motor.
- Suíte automatizada completa: 200/200 testes aprovados, incluindo guarda para não expor detalhes de exceção no painel `/jogo`.
- Staging de catálogo: 137 históricos, 27 allowlisted e 110 bloqueados.
- Simulações em SQLite descartável: Bo3 A 2–1 B (97 eventos); combo/passiva/líder 20–10 (49 eventos); ambas íntegras.
- `discord.py` e `aiosqlite` não estão instalados no ambiente de análise. Import real do bot, despacho de componentes, login Discord, teste end-to-end com duas contas e deploy não foram executados.
- Convites são temporários em memória; partidas e decks são persistidos. `Minhas partidas` permite reabertura pós-restart.

## Arquivos fora do escopo

Nenhuma alteração em `bot.py`, `database.py`, `sistemas/gwent.py`, `sistemas/cartas.py`, `site/app.js`, catálogo histórico bloqueado ou banco legado.

- Nenhum arquivo-fonte foi removido. Os 108 arquivos `.pyc`/diretórios `__pycache__` transitórios encontrados no ZIP de baseline foram excluídos do pacote para evitar distribuir cache de execução.
