# Baseline legado do catálogo — fotografia v0.1

**Propósito:** preservar de forma reprodutível o que o runtime atual define antes da reconstrução. Este arquivo não é o novo catálogo oficial e não deve ser importado pelo runtime como fonte de verdade.

Dados estruturados completos: `data/card_game/catalog-legacy-baseline-v0.1.json`.

## Contagem conferida em runtime

| Tipo normalizado | Quantidade | Regra de slot futura |
|---|---:|---|
| Unidades | 110 | Deck de 12; fileira e poder-base. |
| Especiais táticas | 21 | Deck de 12; sem poder-base. |
| Relíquias | 6 | Slot separado; não contam nas 12 posições. |
| **Total** | **137** | Modelos legados com ID no catálogo. |

Os dez registros `patente_1` a `patente_10` são gerados deterministicamente a partir de `levels.PATENTES` e entram no `CARTAS_POR_ID`. Recompensas dinâmicas de jogos (`carta_jogo`) não são parte deste conjunto fixo porque surgem por nome de jogo/marco.

## Inventário de mecânicas preservadas

| Catálogo | Quantidade |
|---|---:|
| Definições genéricas em `HABILIDADES` | 59 |
| Identidades ativas em `CARD_IDENTITY_ABILITIES` | 22 |
| Combos | 27 |
| Líderes | 10 |
| Associações carta-tag (medição histórica) | 72 |

As seis relíquias possuem IDs de efeito em `HABILIDADES` e são mantidas como kind separado no snapshot.

## Pureza do baseline

- Unidades estritamente puras no estado antigo: 15.
- Denominador de modelos: 137.
- Percentual atual em relação a todos os modelos: 10,95%.
- Meta confirmada para a reconstrução: pelo menos `ceil(30% × N)`; para N=137, 42 cartas puras.
- Déficit mínimo aritmético em relação ao baseline fixo: 27 unidades a redesenhar como puras, antes de qualquer expansão/alteração de denominador.

Critério: unidade sem habilidade individual, sem identidade ativa e sem tag ligada a combo ativo. A passiva global de facção não conta como habilidade individual.

## Alertas preservados, não corrigidos nesta fotografia

1. Seis cartas `luterano_*` estão alocadas atualmente às facções Ordem Áurea, Véu Carmesim ou Lua Negra, embora façam parte da expansão dos Esquecidos e tenham narrativa de fé. A nova versão revisará nomes, facção e lore em conjunto.
2. Há divergências entre `Carta.custo` e a tabela `CUSTO_RARIDADE`; os custos deste arquivo são apenas valores legados.
3. O modelo antigo mistura especiais táticas e relíquias em `categoria=Especial`. O snapshot separa `special` e `relic` sem alterar o runtime.
4. A transformação V18 apaga habilidade e aumenta poder em um subconjunto de cartas no import do módulo. O snapshot guarda também valores pre-V18 quando disponíveis na matriz antiga.
5. Habilidades por identidade e habilidades genéricas são dois mecanismos legados diferentes. O snapshot registra ambas as camadas sem as somar nem decidir sua sobrevivência.
6. Textos em `descricao` podem misturar lore e regra. São preservados literalmente apenas para comparação.

## Como reproduzir

```bash
python docs/scripts/build-card-catalog-baseline-v0.1.py
python docs/scripts/test-card-contract-v1.py
```

A construção importa o catálogo runtime atual e a matriz de rastreabilidade antiga. O script registra SHA-256 de `sistemas/cartas.py`, `sistemas/gwent.py`, `levels.py` e `docs/card-game-card-traceability.json`. Se qualquer uma dessas fontes mudar, o snapshot reproduzido terá hashes diferentes.
