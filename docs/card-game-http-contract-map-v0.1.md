# Mapa estático de contratos HTTP Gwent — v0.1

> Auditoria por AST/inspeção de fonte. Não importa `bot.py`, não instancia `aiohttp`, não executa handlers, Discord nem o wrapper `Database`.

## Rotas principais

| Método | Rota | Handler | Linhas do handler | Autenticação | Checagem de origem | Uso pelo frontend |
|---|---|---|---:|---|---|---|
| GET | `/api/gwent/cards` | `_api_gwent_cards` | 2114–2207 | sim | não detectada | /api/gwent/cards |
| GET | `/api/gwent/cards/{card_id}/image` | `_api_gwent_card_image` | 3342–3639 | sim | não detectada | /api/gwent/cards/, image |
| GET | `/api/gwent/deck` | `_api_gwent_deck` | 1093–1232 | sim | não detectada | /api/gwent/deck |
| POST | `/api/gwent/deck` | `_api_gwent_deck_save` | 1234–1349 | sim | sim | /api/gwent/deck |
| POST | `/api/gwent/deck/reset` | `_api_gwent_deck_reset` | 1351–1365 | sim | sim | /api/gwent/deck/reset |
| GET | `/api/gwent/matches` | `_api_gwent_matches` | 1414–1429 | sim | não detectada | /api/gwent/matches |
| POST | `/api/gwent/matches` | `_api_gwent_match_create` | 1431–1517 | sim | sim | /api/gwent/matches |
| POST | `/api/gwent/matches/solo` | `_api_gwent_match_create_solo` | 1519–1613 | sim | sim | /api/gwent/matches/solo |
| GET | `/api/gwent/matches/{match_id}` | `_api_gwent_match_detail` | 1706–1829 | sim | não detectada | /api/gwent/matches/${matchId} |
| POST | `/api/gwent/matches/{match_id}/action` | `_api_gwent_match_action` | 1831–1995 | sim | sim | /action |
| POST | `/api/gwent/matches/{match_id}/respond` | `_api_gwent_match_respond` | 1615–1704 | sim | sim | /respond |
| GET | `/api/gwent/public-cards/{card_id}/image` | `_api_gwent_public_card_image` | 3012–3339 | não detectada | não detectada | card.image_url, /api/gwent/public-cards/ |

## Contrato de deck e custo

O frontend envia `cards: [{card_id, exemplar_id}]`, `faction`, `leader_id` e `relic_id` em `POST /api/gwent/deck`. O handler exige 12 modelos únicos, facção válida/predominante, líder da facção, relíquia permitida e possuída, mínimo de oito unidades e máximo de quatro especiais. O estado da implementação não contém soma de custo nem teto de orçamento.

A função `preparar_carta()` retorna estas chaves: `arquetipo_descricao, arquetipo_faccao, categoria, combos_compativeis, descricao, especial, faccao, fileira, habilidade, habilidade_identidade, habilidade_nome, habilidade_texto, id, image_url, nome, papel_gwent, poder, potencia_raridade, raridade, row, row_label, sinergias, tipo_combate`. **`custo` não está na lista.** As rotas `/api/gwent/cards` e `/api/gwent/deck` atribuem `payload['custo']` antes de chamar `preparar_carta()`, mas a preparação explícita descarta esse campo. Assim, o custo pode existir no modelo/base payload e ainda não chegar ao consumidor final desse contrato.

## Contrato de partidas

- `GET /api/gwent/matches`: lista partidas/ranking/leaderboard do usuário autenticado.
- `POST /api/gwent/matches`: recebe `opponent_id`; valida guild/decks, limite de três partidas pendentes/ativas e posse de relíquias; salva snapshot de deck/config em `state_json` com status `pending`.
- `POST /api/gwent/matches/{match_id}/respond`: recebe `action` (`accept`, `decline`, `cancel`); somente o convidado aceita/recusa e somente o criador cancela. Na aceitação, revalida relíquias, embaralha snapshots e cria `novo_estado()`.
- `POST /api/gwent/matches/solo`: cria partida contra NARA com cópia do deck/config do usuário; a API informa `rewards: false`.
- `GET /api/gwent/matches/{match_id}`: para `pending`, retorna somente `match_id/status`; para `active/finished`, retorna estado público, mão, placar, alvos, clima, líder, relíquia, histórico e recompensa.
- `POST /api/gwent/matches/{match_id}/action`: recebe `action`, `card_id`, `row`, `card_ids`, `target_id`; aplica `aplicar_jogada()` dentro de transação e executa turno NARA no servidor quando necessário. Retorna `{ok: true}`; o frontend busca novamente o detalhe para obter o estado novo.

## Achados relevantes para a reconstrução

1. **Custo não é uma regra de deck.** O handler de gravação não calcula soma de custo nem compara com orçamento.
2. **Custo não chega no payload preparado.** `preparar_carta()` não inclui `custo` no dicionário retornado, mesmo quando rotas anteriores calcularam `payload['custo']`.
3. **Ações são refetch-based.** O POST de ação devolve apenas sucesso; o frontend chama `refreshGwentMatch()` e `GET /api/gwent/matches/{id}`.
4. **Convite é snapshot-based.** O deck/config enviado é guardado no convite; a aceitação revalida posse de relíquia, depois embaralha e inicializa a partida.
5. **NARA atua no servidor.** A ação humana pode ser seguida por `executar_turno_ia()` no mesmo handler; em exceção, o backend tenta `pass` como fallback.

## Limites e próximo passo

Todas as conclusões são estáticas. Não foi possível executar HTTP porque `discord.py` e `aiosqlite` não estão instalados; tentativa de instalação temporária foi bloqueada por DNS. Não usar esta auditoria como prova de respostas reais, autenticação, transações, race conditions, integração do browser ou DB.

Próxima execução: em ambiente com as dependências de `requirements.txt`, construir testes `aiohttp.TestClient` para cada rota de leitura/escrita, autenticação (401), origem (403), ownership, status (400/403/404/409), transação/rollback e refetch da UI. Em seguida, corrigir o contrato do custo junto da especificação aprovada — não antes de definir o schema/custo oficial.

## Reprodução

```bash
python docs/scripts/audit-gwent-http-contracts-v0.1.py
```
