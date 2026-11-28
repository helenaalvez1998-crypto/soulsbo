# Validação stateful de partidas e snapshots — v0.1

> **STATUS: 12/12 cenários aprovados.** Esta etapa amplia os testes anteriores de funções isoladas para fluxos stateful do motor. Os testes executam `sistemas/gwent.py` com decks/fixtures em memória; não representam uma validação no servidor publicado.

- Data da execução: 2026-11-27.
- Script: `docs/scripts/assert-full-match-stateful-v0.1.py`.
- Relatório estruturado: `docs/card-game-match-snapshot-integration-v0.1.json`.
- Runtime de jogo alterado nesta etapa: **nenhum**.
- Fonte do schema SQLite: constantes `SCHEMA` e `SCHEMA_CARTAS` extraídas por AST de `database.py` e executadas em uma conexão SQLite `:memory:`.

## 1. Resultado agregado

**12/12 cenários aprovados; zero falhas.**

| Grupo | Cenários | Resultado |
|---|---:|---|
| Partidas completas de 3 rodadas, alternando as quatro facções | 4 | 4/4 |
| Preparação de payload de todo o catálogo | 1 | 1/1 — 137 modelos |
| Combo real ativado via jogadas normais e serializado | 1 | 1/1 |
| Líder + especial climático + reset de rodada | 1 | 1/1 |
| Relíquia: aplicação, consumo, persistência e bloqueio de segundo uso | 1 | 1/1 |
| Clima manual: persistência e bloqueio de segundo uso | 1 | 1/1 |
| Compatibilidade com snapshot legado e imutabilidade após ação rejeitada | 1 | 1/1 |
| SQLite: schema real, FK, insert/select/update de `state_json` | 1 | 1/1 |
| Contrato HTTP/frontend por inspeção estática | 1 | 1/1 |

## 2. Partidas completas

Foram executadas quatro partidas, cada uma com três rodadas e estado serializado em JSON após as ações e encerramentos de rodada. As combinações cobrem todas as facções em ambos os lados:

1. Ordem Áurea × Véu Carmesim.
2. Véu Carmesim × Lua Negra.
3. Lua Negra × Os Esquecidos.
4. Os Esquecidos × Ordem Áurea.

Cada jogo foi conduzido com sequência controlada de vitórias 1–1–1, encerrando com placar de coroas 2–1. Foram verificados: duas ações de `keep`, transição `mulligan` → `battle`, alternância de iniciativa, alternância de turno, jogada de unidade, passes, resolução da rodada, reset de clima, reset da passiva de facção, reset de `synergy_used`, preservação da mão entre rodadas, estado final `finished` e `winner_id`.

**Limite:** os 12 cards por jogador nesses quatro cenários são fixtures unitárias sintéticas com facção/linha/poder controlados. Isso verifica o fluxo do motor e não prova validade pelo endpoint de montagem de deck nem equilíbrio de decks reais.

## 3. Catálogo, combos e efeitos de partida

- `preparar_carta()` foi exercitada para os **137 modelos** de `CARTAS_POR_ID`; os payloads continham os campos esperados pela interface/renderizador, fileiras válidas e rotas de imagem. Unidades retornaram poder de 1 a 15; especiais retornaram poder visual 0.
- O combo `cinzas_fornalha` foi ativado por duas cartas do catálogo real em ações sequenciais do turno. O `combo_ativado`, o bônus individual e `synergy_used` sobreviveram ao ciclo JSON.
- Godfrey foi ativado através da ação de líder; em seguida, `gwent_especial_tempestade` aplicou clima à fileira; o passe encerrou a rodada, a tempestade foi removida e `leader_used` permaneceu consumido pela partida. A segunda ativação do líder foi rejeitada.
- A Grande Runa de Godrick foi ativada pela ação `relic`; o aliado recebeu +1, a carta temporária foi movida ao descarte, `relic_used` persistiu e uma segunda ativação foi rejeitada.
- A ação manual `weather` foi aplicada uma vez, persistiu no snapshot e a segunda ativação foi rejeitada.

## 4. Snapshots legados e persistência

- `aplicar_jogada()` recebeu um snapshot legado sem `phase`, `weather`, `event_log` e diversos defaults por jogador; os campos compatíveis foram reconstruídos sem exceção.
- A tentativa de jogar uma carta ausente retornou erro e não alterou o objeto de estado fornecido ao motor.
- O script extraiu as constantes `SCHEMA` e `SCHEMA_CARTAS` diretamente de `database.py` usando AST, executou ambas em SQLite `:memory:` com `PRAGMA foreign_keys=ON`, criou usuários, gravou `cartas_gwent_matches.state_json`, leu e atualizou o snapshot e conferiu novamente o conteúdo. Isso verifica o DDL e o envelope JSON, mas não usa a classe `Database`/`aiosqlite` nem o arquivo DB de produção.

## 5. Contrato da interface e verificação sintática

Verificação estática confirmou no `bot.py` as rotas/handlers de catálogo, deck, detalhe de partida e ação; e no `site/app.js` o consumo de `/api/gwent/cards`, `catalog`, `cards`, `habilidade_texto`, `combos_compativeis`, `image_url` e envio de `card_id`, `row`, `card_ids`, `target_id` para a rota de ação.

Também passaram:

- `python -m compileall -q bot.py database.py sistemas/gwent.py sistemas/cartas.py site_portal.py site_hub.py`
- `node --check site/app.js`

**Limite importante de execução HTTP:** a importação de `bot.py` falhou nesta sessão porque o ambiente de análise não tem o pacote `discord` (`ModuleNotFoundError: No module named 'discord'`). A importação de `database.py` também não está disponível porque `aiosqlite` não está instalado. Ambos são requisitos fixados no `requirements.txt` (`discord.py==2.7.1`, `aiosqlite==0.22.1`). Tentei instalá-los no ambiente temporário com `pip`, mas a resolução DNS não estava disponível e o índice de pacotes não pôde ser alcançado. Não alterei `requirements.txt` nem vendorei stubs. Portanto, não foi executado `aiohttp.TestClient`, handler real, gateway Discord, transação assíncrona real nem endpoint contra DB. O script registra dinamicamente a presença desses módulos em cada execução, sem fingir que fez dispatch HTTP.

## 6. Limitações que continuam abertas

1. Ainda falta integração HTTP efetiva (`/api/gwent/cards`, `/api/gwent/matches/{id}` e `/action`) com `NaraBot`, `aiohttp.TestClient`, DB assíncrono e fixtures de autenticação.
2. Ainda falta fluxo real de criação/aceitação de convite, criação solo com NARA/IA, fallback da IA e recompensa de partida.
3. Ainda falta validação do frontend com resposta de API real em browser, bem como inspeção de imagens retornadas pelo serviço de arte/R2.
4. Os testes de partidas completas usam unidades sintéticas; são testes de transição, não simulação competitiva nem teste com doze cartas reais escolhidas pelo deck builder.
5. Não há DB de produção, credenciais, configuração de deploy, arte aprovada no R2 ou estado de partidas reais no ZIP.
6. As regras de EFP, custo, orçamento de deck e raridade continuam propostas não aprovadas.
7. A instalação temporária de `discord.py==2.7.1` e `aiosqlite==0.22.1` foi tentada, mas bloqueada por falha de DNS/rede do ambiente; a próxima execução precisa de um ambiente com esses pacotes previamente instalados ou acesso a wheels locais.

## 7. Reprodução

A partir da raiz `soulsbo-main/`:

```bash
python docs/scripts/assert-full-match-stateful-v0.1.py
python docs/scripts/summarize-card-game-behavior-v0.3.py
python -m compileall -q bot.py database.py sistemas/gwent.py sistemas/cartas.py site_portal.py site_hub.py
node --check site/app.js
```

O script stateful grava novamente seu resultado no JSON associado. A suíte v0.3 preserva o relatório anterior de 251 assertions isoladas; não some cenários com assertions como se fossem a mesma unidade de contagem.
