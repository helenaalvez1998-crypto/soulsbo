# Auditoria de combos após aplicação da política — v0.2

**Status:** auditoria pós-correção executada no runtime atualizado.  
**Política:** `card-game-combo-policy-v0.1.md` (aprovada pelo usuário e implementada).  
**Script:** `docs/scripts/audit-combo-overlap-v0.2.py`.  
**Dados:** `docs/card-game-combo-overlap-v0.2.json`.

## 1. Resultado

A enumeração foi repetida contra o resolvedor corrigido, usando as mesmas 67 unidades atuais com tags, 27 combos, todos os pares ordenados e todas as trincas ordenadas de IDs distintos.

| Medida | Baseline anterior | Após a política | Interpretação |
|---|---:|---:|---|
| Combos sem `minimum` explícito | 3 | 0 | Todos exigem dois participantes distintos. |
| Ativações solo | 1 | 0 | `eco_convergente` não ativa mais com apenas o Erudito híbrido. |
| Pares ordenados com mais de um combo elegível | 154/4.422 (3,4826%) | 152/4.422 (3,4374%) | Ainda existem sobreposições; agora têm prioridade explícita. |
| Combos envolvidos em sobreposição de pares | 15 | 14 | O catálogo pós-patch foi reavaliado. |
| Trincas que ativam dois ou mais combos em jogadas sucessivas | 11.780/287.430 (4,0984%) | 2.582/287.430 (0,8983%) | A regra de contribuição reduz as transições legítimas/persistentes no universo enumerado. |
| Trincas multi-combo da mesma facção | 1.088 | 666 | Ainda existem sequências multi-combo da mesma facção. |
| Eventos posteriores cuja carta fornece tag requerida | 3.688/11.784 (31,2967%) no baseline; 8.096 sem tag | 2.582/2.582 (100%) | Todos os acionamentos posteriores observados respeitam participação por tag. |
| Transições ordenadas distintas entre combos | 102 | 54 | Ainda há diversidade de sequências de combos pendentes. |

**Nota:** os valores percentuais são condicionados ao universo de pares/trincas enumerados. Não são taxa de ativação em partidas reais, EV, win rate ou prova de balanceamento.

## 2. O que mudou

- O resolvedor agora filtra combos pelo cruzamento entre tags da carta atual e tags exigidas pelo combo.
- O mínimo de dois participantes é obrigatório em todos os 27 combos.
- A ordem é controlada por `priority` exclusivo (menor primeiro), e não pela inserção do dicionário.
- No máximo um combo ativa por jogada. Combos adiados permanecem disponíveis, mas uma jogada posterior precisa contribuir com tag requerida.
- A auditoria pós-correção encontrou zero ativações solo e zero acionamentos posteriores por carta sem tag requerida.

## 3. Reproduzir

```bash
python docs/scripts/audit-combo-overlap-v0.2.py
```

O relatório JSON inclui pares e exemplos de transições; o script faz chamadas ao resolvedor real em estados sintéticos em memória. Não modifica o runtime.

## 4. Limitações

- A enumeração cobre 4.422 pares e 287.430 trincas de três IDs distintos entre as 67 unidades com tags.
- Não valida deck completo de 12 cartas, posse, líder, relíquia, mão, clima, IA, snapshots reais, DB, API, site, Discord ou R2.
- A sobreposição ainda existe e a regra resolve-a por prioridade, mas não foram testadas todas as sequências de 12 cartas em partidas completas.
- A nova política não calibra bônus, EFP, custo, raridade ou equilíbrio de facções.
- Partidas ativas persistidas preservam bônus já concedidos pelo comportamento anterior; não há DB de produção neste pacote para inspecionar ou migrar.
