# Validação comportamental do motor de cartas — v0.2

> **STATUS: diagnóstico comportamental em fixtures sintéticos. Não é teste de produção, simulação competitiva, aprovação do EFP ou prova de equilíbrio.** Nenhuma regra funcional foi alterada durante esta etapa.

- Baseline: `soulsbo-main(1).zip`.
- Data do registro: 2026-11-27.
- Runner agregado: `docs/scripts/summarize-card-game-behavior-v0.2.py`.
- Relatório estruturado: `docs/card-game-behavior-validation-v0.2.json`.

## 1. Resultado agregado

**Resultado: 219/219 asserts aprovados em sete suites.**

| Suite | Asserts | Aprovados | Falhas | Cobertura declarada |
|---|---:|---:|---:|---|
| Efeitos representativos iniciais | 13 | 13 | 0 | Buff/debuff, compra, escudo, ressurreição, movimento, invocação, remoção, clima, sangramento, execução, buff de fileira e identidade. |
| Identidades ativas | 33 | 33 | 0 | As 22 identidades ativas em ao menos um cenário positivo, mais casos negativos/limite selecionados. |
| Habilidades genéricas de unidade | 39 | 39 | 0 | Condições de buffs/debuffs, fileiras, round, clima, aliados, descarte, escudo e habilidades condicionais. |
| Ciclo de vida | 7 | 7 | 0 | `vinganca`, `espolios`, `gloria` e ausência de handler para `sobrevivente`; vitória/derrota e bloqueios selecionados. |
| Especiais e relíquias | 18 | 18 | 0 | 11 handlers especiais adicionais, seis relíquias pelo caminho `action="relic"` e um caso de escudo/bloqueio. |
| Líderes | 22 | 22 | 0 | Os dez líderes ativos em cenário positivo e 12 rejeições/limites. |
| Combos e passiva de facção | 87 | 87 | 0 | Os 27 combos: ativação, ausência de parceiro e bloqueio de repetição do mesmo combo; quatro passivas de facção e exclusão de especiais. |
| **Total** | **219** | **219** | **0** | **Sete suites; os testes são cenários, não 219 habilidades distintas.** |

Os relatórios individuais preservam os casos, estado esperado/observado, nomes dos handlers e limitações:

- `card-game-effect-behavior-assertions-v0.1.json`
- `card-game-identity-behavior-assertions-v0.1.json`
- `card-game-generic-unit-assertions-v0.1.json`
- `card-game-lifecycle-assertions-v0.1.json`
- `card-game-special-relic-assertions-v0.1.json`
- `card-game-leader-assertions-v0.1.json`
- `card-game-combo-faction-assertions-v0.1.json`

## 2. Líderes testados

Todos os dez handlers de líder foram chamados por `sistemas.gwent.aplicar_jogada(..., action="leader")`:

| Líder | Efeito principal verificado |
|---|---|
| Godfrey | +2 a todos os aliados de Corpo a Corpo; demais fileiras não mudam. |
| Morgott | Escudo e +1 para os dois aliados mais fortes não protegidos na fileira escolhida. |
| Radagon | Remove os quatro tipos de estado negativo tratados pelo handler; cada unidade purificada recebe +1. |
| Mohg | Marca os dois inimigos mais fortes da fileira; segunda marca produz a redução de bônus e zera a marca. |
| Rykard | Sacrifica o aliado mais fraco da fileira e fortalece os sobreviventes; fixture também verificou a interação do sacrifício com escudo. |
| Esgar | Ressuscita a unidade elegível mais forte com poder até 5, na fileira escolhida, com +1. |
| Papa Esquecido | Fortalece apenas aliados de Os Esquecidos na fileira escolhida. |
| Rennala | Purifica Geada/Podridão e só fortalece aliados purificados de Cerco. |
| Astel | Aplica Geada aos três inimigos mais fortes da fileira escolhida, respeitando o limite de marcas. |
| Loretta | Fortalece os dois aliados mais fortes de Longa Distância; rejeita outra fileira. |

Os 12 casos negativos/limite verificam requisitos ausentes de alvo, fileira inválida para Loretta, fileira sem unidades relevantes, ausência de status para purificar e reutilização do líder. A chamada repetida teve o ponteiro de turno recolocado no jogador de teste para atingir especificamente a proteção `leader_used`, isolando a condição do bloqueio por turno.

## 3. Combos e passiva de facção — 87 asserts

O script `scripts/assert-combo-and-faction-passive-v0.1.py` chama o resolvedor real `_aplicar_combo_de_cartas()` e o caminho real `aplicar_jogada()`/`_resolve_round()` para os casos de facção. Resultado: **87/87**.

| Subconjunto | Casos | O que foi verificado |
|---|---:|---|
| Combos positivos | 27 | Um par concreto de cartas por combo ativa a definição exata; bônus da carta e `team_bonus` para aliado da mesma fileira conferidos. |
| Requisito incompleto | 27 | Sem o conjunto parceiro, o combo alvo não ativa. Os demais combos são marcados como usados para isolar a condição. |
| Repetição na rodada | 27 | O mesmo `combo_id` não ativa novamente na mesma rodada. O resolvedor pode ativar outro combo distinto se as tags também o satisfizerem; isso é registrado, não tratado como falha. |
| Carta sem tags | 1 | Uma unidade sem tags não ativa combo. |
| Passivas de facção | 4 | Para cada uma das quatro facções: unidade estrangeira não consome o bônus; primeira unidade da facção recebe +1; segunda não recebe outro +1; reset ocorre no encerramento da rodada. |
| Especial não consome passiva | 1 | `gwent_especial_chifre` não consome a passiva exclusiva de unidades. |

Limitações específicas: cada combo usa apenas um par atual que ativa a combinação; não foram exauridas outras combinações de provedores, permutações com tags sobrepostas nem precedência completa entre vários combos que possam ser válidos ao mesmo tempo. As passivas foram testadas em fixtures sintéticos, sem todas as identidades de cada facção ou modificadores de raridade.

## 4. Ramos antigos de identidade — classificação estática

O inventário AST e de associação runtime mantém **28 ramos sem associação ativa**, sem os remover:

| Grupo | Quantidade | Situação |
|---|---:|---|
| Identidades filtradas pela transformação V18 | 18 | O ID de carta foi colocado em `CARTAS_SEM_EFEITO_IDS`; o catálogo runtime limpa a habilidade e remove a associação. Algumas cartas conservam tags de combo, portanto não são necessariamente puras. |
| Campos legados sem associação ativa | 4 | `devoto`, `legado`, `escolha_ritmo` e `sinergia_faccao`; seis cartas atuais ainda carregam três desses campos, e `escolha_ritmo` não tem carta runtime associada. |
| Ramos V75 obsoletos | 6 | Código de resolução legado de uma expansão; as cartas atuais declaram ausência de habilidade individual e algumas ainda participam de combos por tags. |

A decomposição, os IDs de carta, as tags, a recomendação de destino e os trechos de referência estão em:

- `card-game-stale-identity-disposition-v0.1.md`
- `card-game-stale-identity-disposition-v0.1.json`
- `scripts/audit-stale-identity-branches-v0.1.py`

Não apagar esses ramos antes de decidir carta a carta `keep`, `merge`, `redesign` ou `remove`, além de revisar tags/combos e dados persistidos.

Dois problemas de ciclo de vida são separados desta contagem:

- `gloria`: hook oculto em `_resolve_round()` e ausente de `HABILIDADES`; três cartas possuem esse campo atualmente.
- `sobrevivente`: declarado em `HABILIDADES`, mas não foi identificado handler correspondente de fim de rodada.

## 5. Cobertura estrutural do baseline após os testes

- 59 IDs no catálogo genérico.
- 56 valores de habilidade encontrados no handler direto de jogada.
- Dois hooks de ciclo de vida declarados: `vinganca` e `espolios`.
- Um ID declarado sem handler identificado: `sobrevivente`.
- Um hook adicional fora do catálogo: `gloria`.
- 22 identidades ativas, todas ligadas a ramos reconhecidos pelo smoke/source-map.
- 28 ramos de identidade sem associação ativa.
- 27 combos, sem combo estruturalmente impossível no cruzamento das tags exigidas; cinco IDs de carta órfãos continuam na tabela de tags.

O smoke executou as 56 rotas diretas sem exceção nas fixtures, tratou os hooks em separado e reconheceu as 22 identidades. Isso é cobertura de chamada controlada, não cobertura exaustiva de branch.

## 6. Como reproduzir

A partir da raiz do projeto:

```bash
python docs/scripts/audit-effect-handler-coverage-v0.1.py
python docs/scripts/audit-stale-identity-branches-v0.1.py
python docs/scripts/validate-card-effect-smoke-v0.1.py
python docs/scripts/assert-card-effect-behavior-v0.1.py
python docs/scripts/assert-card-identity-behavior-v0.1.py
python docs/scripts/assert-generic-unit-effects-v0.1.py
python docs/scripts/assert-card-lifecycle-effects-v0.1.py
python docs/scripts/assert-special-and-relic-effects-v0.1.py
python docs/scripts/assert-leader-effects-v0.1.py
python docs/scripts/assert-combo-and-faction-passive-v0.1.py
python docs/scripts/summarize-card-game-behavior-v0.2.py
```

O runner agregado lê os sete relatórios JSON e falha se a contagem estiver inconsistente ou existir qualquer caso que não tenha passado.

## 7. Limitações e o que não foi provado

1. Os testes usam `aplicar_jogada()` e funções do motor em memória com estados sintéticos. Não testam DB de produção, rotas HTTP, interface web, handlers Discord, Cloudflare R2 ou imagens publicadas.
2. Os casos cobrem caminhos positivos, negativos e limites selecionados, não todas as combinações de estado, raridade, ordem de jogada, IA ou interações de todos os efeitos.
3. As suites não representam 219 efeitos únicos; há repetição intencional de famílias e cenários.
4. Aprovação dos asserts não calcula valor esperado, vantagem, win rate, duração, paridade de facções nem força relativa de decks.
5. Os 28 ramos antigos foram classificados, mas não removidos. Seus destinos exigem decisão explícita e conferência de tags/combos/dados persistidos.
6. `sobrevivente` e `gloria` continuam problemas de contrato/evento a resolver.
7. EFP v0.2 e balanceamento v0.1 continuam propostas sem aprovação. Não alterar custo, raridade, poder, composição do deck ou regras do motor com base apenas nestes asserts.

## 8. Próximos passos

1. Expandir a cobertura de combos para pares alternativos, tags sobrepostas e precedência quando múltiplos combos forem elegíveis; testar clima, transições de rodada, IA e interações entre efeitos.
2. Produzir uma decisão explícita para cada um dos 28 ramos antigos e para os hooks `gloria`/`sobrevivente`; não deletar até revisar os IDs, dados e combos dependentes.
3. Construir um simulador determinístico de partidas completas com políticas documentadas, seeds, espelhos e confrontos entre as quatro facções.
4. Medir win rate, pontos por rodada, duração, frequência de ativação e valor marginal dos efeitos.
5. Só então calibrar EFP, custo, raridade e teto do deck para apresentar uma proposta revisada ao usuário.

## 9. Histórico desta etapa

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/assert-leader-effects-v0.1.py` | Novo script; `state_for()`, `activate()`, dez `test_*()` e casos negativos | Adicionadas 22 asserções para dez líderes e doze condições negativas/limite. | Cobrir o caminho de ação de líder que faltava nas suites anteriores. | Diagnóstico em `docs/scripts/`; não é importado pelo runtime. | 22/22 passaram; todas as dez ramificações positivas foram acionadas. |
| `docs/scripts/assert-combo-and-faction-passive-v0.1.py`, `docs/card-game-combo-faction-assertions-v0.1.json` | Nova suite de combos e passiva de facção | 87 cenários: 27 positivos, 27 incompletos, 27 bloqueios de repetição, carta sem tags, quatro facções e exclusão de especial. | Testar cada combo e o comportamento/reset da passiva no resolver real. | Apenas ferramenta e relatório sintético; nenhum impacto no runtime. | 87/87 passaram; um par concreto por combo, sem exaurir pares alternativos/precedência múltipla. |
| `docs/card-game-leader-assertions-v0.1.json` | Novo relatório estruturado | Guarda os casos, status e limitações da suite de líderes. | Evidência reproduzível para a continuidade. | Apenas documentação/dados de diagnóstico. | Gerado pelo script; 22/22. |
| `docs/scripts/summarize-card-game-behavior-v0.2.py` | Agregador atualizado | Valida sete relatórios JSON e soma contagens/cobertura estática. | Evitar somas manuais e detectar saídas ausentes/falhas. | Diagnóstico apenas. | 219 asserts, 219 aprovados, 0 falhas. |
| `docs/card-game-behavior-validation-v0.2.json` e `.md` | Novos relatórios agregados | Consolidadas suites, cobertura estática, 28 ramos antigos, limitações e próximos passos. | Dar ao handoff um ponto único de consulta. | Nenhum impacto funcional. | Runner agregado e leitura dos relatórios individuais. |
| `docs/card-game-handoff.md`, `README-PACOTE-CONTINUIDADE.md`, `PACOTE-MANIFESTO.md`, `card-game-efp-methodology-v0.2.md`, `card-game-mapping-audit.md`, `card-game-balance-validation-v0.1.md` | Estado e histórico da revisão anterior (supersedida) | Na revisão intermediária, o relatório tinha seis suites e 132 asserts; essa contagem foi substituída pela suite de combos/facção e total de 219 nesta revisão. | Preservar a sequência histórica sem deixar um número antigo parecer atual. | Apenas documentação e harnesses. | Revisão atual: sete suites, 219/219; ver a linha seguinte e o handoff atualizado. |
| `docs/card-game-handoff.md`, `README-PACOTE-CONTINUIDADE.md`, `PACOTE-MANIFESTO.md`, `card-game-efp-methodology-v0.2.md`, `card-game-mapping-audit.md`, `card-game-balance-validation-v0.1.md` | Atualização da revisão atual | Documentos/índice/manifeste atualizados para sete suites, 219 asserts e pendências residuais de pares alternativos, precedência de combos, clima, IA e partidas completas. | Manter o pacote de continuidade coerente com os testes executados. | Somente documentação e testes em `docs/`; sem runtime. | Agregador confirmou 219/219, sete relatórios JSON. |


### Diagnóstico complementar posterior — sobreposição de combos (não integra a contagem de asserts)

A enumeração adicional do resolvedor real está documentada em `card-game-combo-overlap-v0.1.md/.json`. Ela encontrou 154/4.422 ordens de pares com múltiplos combos elegíveis, 11.780/287.430 trincas com dois ou mais combos, e 8.096/11.784 acionamentos posteriores cuja carta atual não fornece nenhuma tag exigida pelo combo acionado. Também detectou `eco_convergente` ativável sozinho por `gwent_unidade_eco`. Esses achados não mudam o resultado **219/219**: são uma auditoria enumerativa separada, não uma nova suite de asserts e não partidas completas. A política de participação, mínimos, precedência e alvo ainda precisa de aprovação; o motor permanece sem alterações.
