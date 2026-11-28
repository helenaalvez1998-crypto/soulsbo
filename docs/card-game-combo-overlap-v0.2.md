# Auditoria de sobreposição de combos — runtime V76

**Status:** auditoria pós-política, executada sobre o catálogo V76.  
**Política:** mínimo de participantes explícito, prioridade única e contribuição de tag pela carta que recebe o combo.  
**Script:** `docs/scripts/audit-combo-overlap-v0.2.py`.  
**Dados completos:** `docs/card-game-combo-overlap-v0.2.json`.

## 1. Resultado atual

A enumeração percorreu as 92 unidades do catálogo atual que possuem tags de sinergia e os 27 combos registrados. Foram examinados todos os pares ordenados e trincas ordenadas de IDs de unidade distintos.

| Medida | Resultado V76 |
|---|---:|
| IDs de unidade com tags | 92 |
| IDs órfãos excluídos | 5 |
| Combos registrados | 27 |
| Combos sem mínimo explícito | 0 |
| Prioridades duplicadas | 0 |
| Ativações com uma única carta | 0 |
| Pares ordenados examinados | 8.372 |
| Pares ordenados com mais de um combo elegível | 720 (8,6001%) |
| Pares não ordenados distintos com sobreposição | 360 |
| Combos envolvidos em sobreposição de pares | 17 |
| Trincas ordenadas examinadas | 753.480 |
| Trincas com dois ou mais combos em jogadas sucessivas | 24.886 (3,3028%) |
| Trincas multi-combo da mesma facção | 24.516 |
| Gatilhos posteriores que contribuíram com uma tag exigida | 24.886/24.886 (100%) |
| Transições ordenadas distintas entre combos | 58 |

**Interpretação:** sobreposições continuam existindo no universo enumerado, mas o resolvedor aplica a prioridade declarada e ativa no máximo um combo por jogada. Um combo posterior só pode ser recolhido por uma carta que contribua com ao menos uma das tags exigidas por ele. Cada instância de unidade conta uma única vez para o mínimo de participantes.

## 2. Relação com Os Esquecidos

A expansão V76 elevou a facção a 30 unidades sem aumentar o número de combos globais. As novas cartas reutilizam as seis sinergias de fé já existentes (`fe_gloria`, `fe_devocao`, `fe_evangelho`, `fe_irmandade`, `fe_soberania` e `fe_sacerdos`). Isso preserva a política de 27 combos e evita criar uma regra de sinergia paralela apenas para a facção nova.

## 3. Reproduzir

```bash
python docs/scripts/audit-combo-overlap-v0.2.py
```

O script gera o JSON completo, incluindo pares elegíveis, transições e exemplos. A enumeração usa o resolvedor real em estados sintéticos em memória e não modifica o runtime persistido.

## 4. Limitações

- A varredura usa IDs de unidade catalogados e não constrói todas as combinações possíveis de decks legais de 12 cartas.
- Não valida posse, líderes, relíquias, mãos reais, clima, IA, histórico completo de partidas, API hospedada, Discord ou estado do banco de produção.
- Percentuais representam somente o universo de pares/trincas enumerados; não são taxa real de ativação, win rate, EV nem prova estatística de equilíbrio entre facções.
- Cinco IDs órfãos no mapa de tags continuam documentados e foram excluídos da enumeração porque não pertencem ao catálogo atual.
