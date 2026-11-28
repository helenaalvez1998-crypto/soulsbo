# Manifesto de mudanças — integração do site Card Engine v2 alpha v0.1 (rev. 29)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev28.zip`  
**Resultado:** `soulsbo-main-continuity-2026-11-28-rev29.zip`

## Arquivos de implementação/testes modificados (7)

- `cogs/card_engine_v2_ui.py` — edição/exclusão de decks na UI existente; atualização automática das views privadas a cada 12 s; paginação do histórico e rebind das views após ações/refresh.
- `sistemas/card_engine_v2/application.py` — superfície async para leitura de histórico paginado e operações associadas.
- `sistemas/card_engine_v2/discord_gateway.py` — fachada autenticada para histórico, deck CRUD, consulta e projeções de partida.
- `sistemas/card_engine_v2/repository.py` — histórico sanitizado e metadados de revisão nas consultas de partida.
- `site/index.html` — link para o Card Engine v2 Alpha no hub inicial.
- `site_hub.py` — registro das rotas privadas do Card Engine v2 no servidor existente.
- `tests/card_engine_v2/test_discord_gateway.py` — cobertura de histórico e versionamento de decks.

## Arquivos de implementação/testes novos (5)

- `site_card_engine_v2.py` — página privada e API HTTP autenticada.
- `site/card-engine-v2.html` — interface do jogador.
- `site/assets/card-engine-v2.css` — estilos responsivos.
- `site/assets/card-engine-v2.js` — deck builder, partidas, ações e polling web.
- `tests/card_engine_v2/test_site_http.py` — testes de sessão, CSRF, decks, partidas, ações e privacidade.

## Documentação adicionada/atualizada

- `docs/card-game-handoff.md` — promove a revisão 29 e registra limites, testes e próxima prioridade.
- `docs/card-engine-v2-site-alpha-v0.1.md` — contrato e operação da integração web.
- `docs/card-engine-v2-site-alpha-v0.1-validation.json` — relatório estruturado de validação.
- `docs/card-engine-v2-site-alpha-v0.1-change-manifest.md` — este manifesto.

No diff completo contra a rev. 28: **8 arquivos modificados, 8 adicionados e nenhum removido**. Os sete arquivos de implementação/testes modificados e cinco novos são discriminados acima; a diferença restante corresponde ao handoff e aos três documentos novos.

## Arquivos removidos

Nenhum arquivo-fonte foi removido. Caches `__pycache__`/`.pyc` transitórios são excluídos do ZIP final.

## Guardrails

Os seguintes arquivos foram comparados por SHA-256 com a baseline rev. 28 e permanecem byte a byte idênticos: `bot.py`, `database.py`, `sistemas/gwent.py`, `sistemas/cartas.py`, `site/app.js`.

Nenhuma escrita foi adicionada ao banco legado da coleção. Os decks e partidas continuam no armazenamento dedicado `DATA_DIR/card_engine_v2/`. Não houve migração de banco, publicação, deploy ou substituição do motor legado.

## Evidência

- `tests/card_engine_v2`: 209/209 PASS.
- `py_compile`: PASS.
- `node --check site/assets/card-engine-v2.js`: PASS.
- Registro do hub: 77 registros de método/caminho, incluindo `/card-engine-v2` e `/api/card-engine-v2/bootstrap`.
- Staging: 137 modelos históricos, 27 allowlisted, 110 bloqueados.
- Simulação Bo3: Player A 2–1 Player B, 97 eventos, SQLite íntegro.
- Demo combo/passiva/líder: 20–10, 49 eventos, SQLite íntegro.
- Runtime Discord real e deploy: não executados por ausência de `discord.py`, `aiosqlite`, credenciais e ambiente publicado.
