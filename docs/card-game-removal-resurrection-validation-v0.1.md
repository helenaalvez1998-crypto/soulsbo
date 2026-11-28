# Validação — remoção, sacrifício e ressurreição candidata v0.1

**Status:** `CANDIDATE_FOR_REVIEW_NOT_APPROVED`; módulo independente, não integrado ao motor.  
**Data:** 2026-11-27.

## Resultado

| Métrica | Resultado |
|---|---:|
| Testes executados | 49 |
| Aprovados | 49 |
| Falhas | 0 |
| Atribuições no registry | 9 |
| IDs de cartas legadas mapeados no catálogo | 7/7 |

A execução gravou os contadores, os caminhos de fonte, limitações e SHA-256 dos arquivos principais em `docs/card-game-removal-resurrection-validation-v0.1.json`.

## Escopo dos 49 testes

- Schema Draft 2020-12 e validação do JSON candidato.
- Unicidade dos nove `assignment_id` e existência das sete cartas legadas mapeadas.
- Enum de causa, objeto ausente, escudo e consumo de carga, sacrifício que ignora escudo, descarte, contador e Vingança.
- Remoção da cópia correta por identidade de objeto, inclusive caso de dicionários iguais.
- Ressurreição de uma unidade, seleção mais forte, limite, desempate legado, `instance_id`, IDs legados ambíguos, filtro de especiais, limpeza de escudo/estados, bônus e fileira.
- Recuperação para a mão como fluxo separado e preservação dos campos antigos.
- Reprodução no motor legado de: igualdade de dicionários em `_remover_unidade`, limite da Execução em Singular, shield/sacrifício, Vingança, identidade Preço em Sangue, Devorar sem alvo, bug de cópias do Esgar, diferença de bônus/estado entre Esgar/Ressurgir/Réquiem, limite de poder do Réquiem, interação Devorar+Vingança, acúmulo Vingança+Rykard e ordem de combo/ressurreição.

## Interações cruzadas adicionadas nesta revisão

- O registry e o resolvedor reconhecem o `effect_id` canônico singular `effect.vengeance_on_removal`; `effect_ids` e `habilidade="vinganca"` permanecem somente como compatibilidade de teste/legado.
- Remoção seguida de ressurreição comprova que a instância volta com escudo/status limpos e não decrementa o contador de remoções.
- Devorar com vítima Vingança comprova a ordem: Vingança fortalece os aliados já no campo; a carta Devorar recebe seu ganho de sacrifício em seguida, mas não recebe a Vingança da vítima.
- Rykard com vítima Vingança concede +3 aos aliados sobreviventes (+1 Vingança e +2 líder).
- O código resolve combo antes de anexar a unidade ressuscitada; ela pode contribuir para uma jogada posterior.
- Consulte `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` para a matriz de 12 interações.

## Comando de reprodução

Na raiz do repositório:

```bash
python docs/scripts/test-card-removal-resurrection-candidate-v0.1.py
```

Verificação de sintaxe:

```bash
python -m py_compile sistemas/card_removal_resurrection_candidate.py
python -m py_compile docs/scripts/test-card-removal-resurrection-candidate-v0.1.py
```

## Limitações

- Os casos legados usam estados sintéticos em memória. Não são testes HTTP, Discord, banco de produção, navegador, R2 ou partidas competitivas completas.
- Os testes candidatos validam o contrato isolado; `sistemas/card_removal_resurrection_candidate.py` não é importado por `sistemas.gwent`.
- `instance_id` ainda não está ligado ao schema de exemplares, coleção, seleção de alvo, deck ou snapshot.
- Os limites de poder, comportamento sem alvo e bônus/fileira de entrada ainda dependem de decisão de design.
- Passar nos testes não significa aprovação de balanceamento ou autorização para remover as implementações antigas.

## Integridade do runtime preservado nesta etapa

Os cinco arquivos funcionais centrais foram comparados com as entradas equivalentes do ZIP mestre recebido no início desta etapa. Os hashes coincidem:

| Arquivo | SHA-256 (entrada e saída) |
|---|---|
| `sistemas/gwent.py` | `f69e8865759862ddc5bef9ff26ee2ddb43bcfbe33d3e61c985d4b118c6e42383` |
| `sistemas/cartas.py` | `3bed48cbd496de431d92b76653518bda54a59ae5ee7ec8586b448b9fd19a0192` |
| `bot.py` | `a735b2380176a5871f45770d99489825c587033d4a0d760b48b108a6e2a885ff` |
| `database.py` | `ead936a2813335e5a98b31276a9e08ea6dc3a6121543300dd24decc7d69a3ed2` |
| `site/app.js` | `9aafa6ba1ef2641fce9ab169192b27d28b92d2b92ee15881ca5db9984b39386b` |

A comparação direta confirma que estes arquivos não foram modificados nesta etapa. A suíte histórica do motor (251/251) e a stateful (12/12) também foram reexecutadas; permanecem separadas dos 49 testes candidatos desta revisão.

## Regressões independentes reexecutadas nesta entrega

Além dos 49 testes específicos, os conjuntos já existentes foram reexecutados após criar o candidato. Mantêm escopos distintos:

| Conjunto | Resultado |
|---|---:|
| Comportamento agregado do motor legado (`summarize-card-game-behavior-v0.3.py`) | 251/251 em 8 suites |
| Partidas stateful/snapshots | 12/12 |
| Contrato e schemas de carta | 35/35 |
| Estados negativos candidatos | 41/41 |
| Catálogo candidato de efeitos | 23/23 |
| Auditoria semântica | 11/11 |
| Ferramentas de auditoria de produção em fixtures | 7/7 |

Não somar os resultados como “testes únicos de habilidades”: existem sobreposições e as suites cobrem escopos diferentes. As verificações são sintéticas e locais; não substituem integração real do bot, banco, site, Discord ou R2.
