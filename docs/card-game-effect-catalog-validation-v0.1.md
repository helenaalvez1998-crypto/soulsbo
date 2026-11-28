# Validação do catálogo de efeitos candidato v0.1

**Estado:** candidato para revisão; não aprovado e não conectado ao runtime.

## Resultado

- JSON Schema Draft 2020-12: APROVADO.
- Validador `validate_effect_registry()`: APROVADO.
- Suite estrutural: **23/23** testes aprovados.
- Auditoria semântica AST: APROVADA; suite de regressão semântica: **11/11**.
- Resultado global: **APROVADO** para integridade estrutural do candidato.

## Inventário consolidado

| Registro | Quantidade |
|---|---:|
| Famílias de efeito canônicas candidatas | 54 |
| Famílias de unidades | 36 |
| Famílias de especiais | 12 |
| Famílias de relíquias | 6 |
| IDs de `HABILIDADES` cobertos por alias | 59 |
| Habilidades genéricas de unidade | 32 |
| Especiais táticas | 21 |
| Relíquias | 6 |
| Aliases parametrizados | 30 |
| Aliases diretos | 29 |
| Identidades ativas mapeadas | 22 |
| Cartas com habilidade genérica suprimida por identidade | 16 |
| Combos com prova de par de IDs distintos | 27 |
| Líderes | 10 |
| Passivas de facção separadas | 4 |
| Famílias com prioridade alta/média/baixa de revisão | 18/6/30 |
| Habilidades genéricas com handler direto / hook / sem handler | 56/2/1 |
| IDs órfãos de cartas associados a tags | 5 |

## Habilidades unitárias sem atribuição atual

Há **11** definições de unidade no catálogo antigo sem carta atualmente atribuída: `circulo_arcano`, `contragolpe`, `dupla_fornalha`, `eco_arcano`, `escudo_ferro`, `espolios`, `guardiao_fileira`, `irmandade_veu`, `resistencia_climatica`, `sangue_frio`, `sobrevivente`. Elas foram preservadas como aliases de migração, mas não serão atribuídas automaticamente a cartas novas.

## Disposições de migração propostas (não aprovadas)

| Origem | Disposição | Quantidade |
|---|---|---:|
| HABILIDADES | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` | 29 |
| HABILIDADES | `MERGE_AS_PARAMETERIZED_FAMILY` | 29 |
| HABILIDADES | `REDESIGN_AS_EXPLICIT_ROUND_END_EFFECT; NEW_HANDLER_REQUIRED` | 1 |
| Identidades ativas | `KEEP_AS_SINGLE_CARD_EFFECT_CANDIDATE` | 5 |
| Identidades ativas | `MERGE_AS_PARAMETERIZED_FAMILY` | 8 |
| Identidades ativas | `REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW` | 9 |
| Ramos sem associação | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` | 9 |
| Ramos sem associação | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` | 15 |
| Ramos sem associação | `REMOVE_UNREGISTERED_FIELD_EFFECT_FROM_NEW_RUNTIME` | 4 |

As disposições significam manter como candidato, fundir por parâmetros, redesenhar/dividir após revisão ou remover do novo runtime. Não são autorização para apagar imediatamente o código legado.

## Limites e decisões pendentes

- Os 54 `resolution_handler` são nomes propostos; nenhum novo handler foi implementado nesta etapa.
- Os parâmetros default são traduções estruturais das regras legadas, não valores balanceados.
- Os efeitos compostos (`ruin_omen`, `time_storm`, `gravity_reposition`, `row_status_pressure` e sacrifícios) precisam de testes detalhados antes de aprovação.
- Os grupos de status compartilham um modelo, mas Geada, Podridão, Sangramento e Loucura não devem ser tratados como idênticos: limiar, consequência, reset e duração são parâmetros distintos.
- Os 27 combos foram preservados da política atual aprovada; precisam ser reavaliados depois de reescrever as facções e o catálogo de tags.
- EFP, custo, raridade e orçamento de deck seguem não aprovados. Não atribuir efeitos às 137 cartas novas com base apenas neste candidato.
- O código legado e os seus dados não foram apagados ou alterados.

## Reproduzir

```bash
python docs/scripts/build-effect-catalog-candidate-v0.1.py
python docs/scripts/test-effect-catalog-candidate-v0.1.py
python docs/scripts/audit-effect-semantic-groups-v0.1.py
python docs/scripts/test-effect-semantic-audit-v0.1.py
python docs/scripts/summarize-effect-catalog-candidate-v0.1.py
```

O JSON desta validação inclui hashes SHA-256 dos artefatos principais, a suite estrutural e a auditoria semântica. A prioridade alta/média/baixa é heurística de revisão, não decisão automática de equivalência ou aprovação.

Consulte `docs/card-game-effect-semantic-audit-v0.1.md/.json` para evidências AST por família, localização de handlers, ganchos de ciclo de vida, ramos não mapeados e revisão semântica manual.
