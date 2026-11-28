# Conquistas do Soulsbo — alpha v0.1

## Fonte de verdade

O navegador não envia progresso. O servidor calcula métricas a partir de `cartas_exemplares`, `cartas_movimentacoes`, `cartas_gwent_rankings` e do repositório de partidas do Card Engine v2. O resultado é persistido em `cartas_conquistas` dentro de uma transação `BEGIN IMMEDIATE`; o desbloqueio é monotônico e não é removido se o jogador posteriormente perder um exemplar.

## Metas rastreadas

| Chave | Meta | Fonte |
|---|---|---|
| `first_blood` | 1 vitória | Ranking legado + resultados finalizados do Card Engine v2 |
| `collector` | 50 exemplares físicos | `cartas_exemplares` |
| `forger` | 10 exemplares distintos com ascensão de raridade | `cartas_movimentacoes.action='evolucao'` |
| `legend` | 1 exemplar Singular | `cartas_exemplares.rarity` |
| `perfectionist` | Todos os modelos comuns do catálogo estático | Interseção de `CARTAS_POR_ID` comuns com IDs possuídos |
| `dedicado` | 100 partidas concluídas | Ranking legado + repositório Card Engine v2 |

As metas “Apostador” (cinco cartas no nível máximo) e “Sobrevivente” (três falhas de evolução) são exibidas como **rastreamento pendente**. O inventário atual não guarda nível individual de evolução, e a evolução com risco não possui trilha real de tentativas/falhas. Elas não aparecem como 0/100 nem podem ser desbloqueadas por payload do cliente.

## Interface e API

- Página: `/conquistas`.
- Endpoint autenticado: `GET /api/gwent/conquistas/list`.
- `POST /api/gwent/conquistas/registrar` aceita somente objeto vazio e recalcula o progresso no servidor; payload com progresso enviado pelo cliente é rejeitado. O GET é somente leitura e não persiste progresso.
- IDs são obtidos da sessão Discord assinada.
- Resposta usa `Cache-Control: no-store`.

## Limitações

- As conquistas não concedem Denários, itens ou recompensas cosméticas nesta versão; as recompensas precisam de um catálogo definido e de um ledger transacional.
- A contagem de partidas combina ranking histórico legado e partidas finalizadas no Card Engine v2. Se houver migração manual de resultados entre os sistemas, deve-se evitar contar a mesma partida duas vezes.
- “Perfeccionista” usa os modelos marcados como `Comum` no catálogo estático atual. Cartas procedurais não entram nessa meta.
