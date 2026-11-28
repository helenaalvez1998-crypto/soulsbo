# Auditoria e proposta de consolidação dos estados — v0.1

**Data:** 2026-11-27  
**Estado:** auditoria do motor legado concluída; registry e resolvedor de referência são CANDIDATOS, NÃO APROVADOS e NÃO CONECTADOS AO RUNTIME.  
**Fonte principal:** `sistemas/gwent.py` e `sistemas/cartas.py` do pacote mestre desta revisão.

## 1. Objetivo e limite

Esta etapa cobre somente os quatro estados negativos que afetam diretamente unidades: **Geada**, **Podridão Escarlate**, **Sangramento** e **Loucura Frenética**. Ela também mapeia as habilidades de aplicação e purificação que usam esses estados.

O trabalho separa três coisas:

1. **Comportamento legado observado:** o que `sistemas/gwent.py` executa hoje.
2. **Proposta canônica:** a regra de referência para a nova base.
3. **Integração futura:** a ligação dos novos `effect_id` ao motor, APIs, descrições e renderizadores — ainda não feita.

Nenhuma habilidade legada foi apagada. Nenhuma regra foi alterada em `sistemas/gwent.py`.

## 2. Regra comum atual dos contadores

O motor mantém quatro campos inteiros diretamente no dicionário da unidade:

| Estado | Campo legado | Limite normal observado |
|---|---|---:|
| Geada | `geada` | 2 |
| Podridão Escarlate | `podrida` | 2 |
| Sangramento | `sangramento` | 2 |
| Loucura Frenética | `loucura` | 2 |

Não há atualmente um schema de estado da unidade separado que centralize esses quatro campos. As regras estão espalhadas pelo cálculo de poder, efeitos individuais, especiais, líderes, relíquias e limpeza de rodada.

### 2.1. Cálculo do poder efetivo

Em `sistemas/gwent.py::_poder_efetivo()` (linhas 987–992), o cálculo atual é:

`max(1, poder + bônus - penalidade_climática - penalidade_de_estados)`

Em detalhe:

- penalidade climática = `max(0, clima_da_fileira - resistência_climática)`;
- penalidade de estados = `min(3, geada + podrida + loucura)`;
- Sangramento **não** entra na penalidade direta de poder efetivo;
- o resultado nunca fica abaixo de 1.

Consequência importante: Geada, Podridão e Loucura compartilham um teto agregado de -3 pontos, embora cada contador possa chegar individualmente a duas marcas. Por exemplo, `geada=2`, `podrida=2`, `loucura=2` produz penalidade agregada 3, não 6. Sangramento é independente dessa soma.

### 2.2. Duração e limpeza atual

- Ao remover uma unidade por `_remover_unidade()` (linhas 995–1012), os quatro contadores são zerados antes de enviar a unidade ao descarte.
- Na transição para uma nova rodada, `_resolve_round()` zera os quatro estados tanto nas unidades arquivadas quanto na unidade mantida por `Glória` (linhas 1171–1193).
- A resolução terminal tem uma particularidade: `_resolve_round()` encerra a partida e retorna nas linhas 1146–1152 **antes** do bloco que limpa os estados para a próxima rodada. Portanto o snapshot final pode conservar os contadores no último campo mostrado. Isso não cria uma rodada extra, mas é uma divergência em relação a uma regra literal de “limpar no fechamento de qualquer rodada”.

**Proposta:** no novo motor, limpar os estados após calcular e registrar a pontuação da rodada, também na rodada final. A apresentação do resultado pode guardar o placar/highlights calculados, sem manter estados negativos ativos no snapshot terminal.

## 3. Semântica observada por estado

### 3.1. Geada

- Cada marca reduz 1 ponto de poder efetivo.
- Máximo de duas marcas por unidade.
- Não existe uma consequência secundária diferente da própria redução de poder ao alcançar a segunda marca.
- Geada expira no fechamento da rodada e é limpa ao remover/purificar a unidade.
- A redução combina com Podridão e Loucura, dentro do teto agregado de 3.

**Proposta canônica:** manter exatamente esse efeito, com `max_marks=2`, `power_reduction_per_mark=1`, `group=control_debuffs`, `group_cap=3` e sem ação adicional ao atingir duas marcas.

### 3.2. Podridão Escarlate

- Cada marca reduz 1 ponto de poder efetivo (pela soma agregada em `_poder_efetivo`).
- Na segunda marca, o alvo perde 1 ponto de bônus positivo, se possuir; o valor não cai abaixo de 0 por essa consequência.
- A segunda marca não é consumida: o contador permanece em 2 até a limpeza da rodada.
- O especial `gwent_podrida` ignora alvos que já estejam em 2 marcas.
- Há uma exceção problemática na identidade de Malenia (`scarlet_bloom`): ela tenta somar duas marcas quando o alvo já está contaminado e executa a corrosão de bônus mesmo quando o contador já estava no limite 2. Assim, novas ativações podem repetir a corrosão sem nova transição para duas marcas.

**Proposta canônica:** uma marca por ativação; a corrosão ocorre somente na transição de 1 para 2; o contador permanece em 2; aplicações posteriores não repetem a consequência até o estado ser removido ou reiniciado.

### 3.3. Sangramento

- Uma marca isolada não reduz diretamente o poder efetivo.
- Ao atingir duas marcas, o bônus é reduzido em 2, com piso de -2.
- A Hemorragia consome/reset as marcas para 0, permitindo iniciar outro ciclo na mesma rodada.
- A segunda marca pode ser alcançada em ações diferentes ou imediatamente por um especial que aplique duas marcas na mesma resolução devido à raridade legada.

**Proposta canônica:** preservar a natureza cíclica: cada transição para duas marcas causa `bonus = max(-2, bonus - 2)` e consome as marcas.

### 3.4. Loucura Frenética

- Cada marca reduz 1 ponto de poder efetivo via a soma agregada dos estados de controle.
- Na segunda marca, todo bônus positivo é definido como 0; bônus que já sejam zero ou negativos não são alterados.
- As marcas permanecem em 2 até a limpeza da rodada.

**Proposta canônica:** manter a remoção de bônus positivos na transição para duas marcas; não repetir enquanto o alvo permanecer no limite 2.

## 4. Aplicadores legados mapeados

O mapa detalhado, com IDs, parâmetros de alvo, referências de linha e notas de raridade, está em `data/card_game/status-registry-candidate.v1.json`.

| Origem | ID legado / carta | Estado | Alvo e comportamento principal |
|---|---|---|---|
| Especial | `gwent_nevoa` / `gwent_especial_nevoa` | Podridão | Todas as unidades inimigas na fileira escolhida. |
| Especial | `gwent_geada` / `gwent_especial_geada` | Geada | Todas as unidades inimigas no campo. |
| Especial | `gwent_chuva` / `gwent_especial_chuva` | Sangramento | Todas as unidades inimigas em Cerco. |
| Especial | `gwent_sangramento` / `elden_especial_sangramento` | Sangramento | Todas as unidades inimigas na fileira escolhida. |
| Especial | `gwent_geada_cariana` / `elden_especial_geada` | Geada | Todas as unidades inimigas na fileira escolhida. |
| Especial | `gwent_podrida` / `elden_especial_podrida` | Podridão | Todas as unidades inimigas na fileira escolhida. |
| Especial | `gwent_loucura` / `elden_especial_loucura` | Loucura | Todas as unidades inimigas na fileira escolhida. |
| Identidade | `scarlet_bloom` / Malenia | Podridão | Todas as unidades inimigas na fileira em que Malenia entra; variante com repetição de corrosão no limite. |
| Identidade | `impaling_spear` / Messmer | Sangramento | Todas as unidades inimigas na fileira em que Messmer entra. |
| Identidade | `time_storm` / Placidusax | Geada | Todas as unidades inimigas na fileira; Placidusax ganha +1 por inimigo na fileira, até +3. A contagem inclui inimigos que já estejam no limite de Geada. |
| Identidade | `v75_frost_oracle` / Oráculo da Geada | Geada | Inimigo mais forte da fileira; o bônus próprio legado pode repetir quando o alvo já está em 2 marcas. |
| Identidade | `v75_blood_mark` / Acólito do Sangue | Sangramento | Inimigo mais forte da fileira; Hemorragia também concede +1 à carta que ativou. |
| Líder | `mohg_blood_rite` / Mohg | Sangramento | Até os dois inimigos mais fortes da fileira escolhida. Uma utilização por partida. |
| Líder | `astel_gravity` / Astel | Geada | Até os três inimigos mais fortes da fileira escolhida. Uma utilização por partida. |
| Relíquia | `reliquia_noite_chama` — modo Noite | Geada | Todas as unidades inimigas da fileira escolhida; modo alternativo Chama não aplica estado. |

## 5. Efeitos de purificação mapeados

Purificação não é um efeito único. Os caminhos atuais removem conjuntos diferentes de estados e concedem bônus em condições diferentes.

| Origem | ID legado | Estados removidos | Alvos | Bônus/condição |
|---|---|---|---|---|
| Líder Radagon | `radagon_purification` | Os quatro | Todos os aliados | +1 a cada aliado que tinha pelo menos um estado. |
| Líder Rennala | `rennala_full_moon` | Geada e Podridão | Todos os aliados | +1 somente aos aliados purificados em Cerco. Não remove Sangramento ou Loucura. |
| Identidade — Regressão Serena | `v75_grace_mender` | Os quatro | Até dois aliados mais fracos na mesma fileira | +1 a cada purificado; sem alvos afetados, fortalece o aliado mais fraco da fileira; sem aliado, a própria carta recebe +1. |
| Especial Chama do Gigante | `gwent_chama` | Geada | Todos os aliados | +1 por aliado que tinha Geada. |
| Relíquia Grande Runa dos Não Nascidos | `reliquia_renala` | Geada e Podridão | Todos os aliados | +1 por aliado purificado. |

A Lei da Regressão (`gwent_purificar`) limpa clima, não os quatro estados; por isso não foi classificada como purificador de estado.

## 6. Amplificação de raridade legada — risco de descrição e balanceamento

O motor atual não tem uma única regra de escala para estados:

1. `potencia_raridade` é carregada da tabela `RARITY_EFFECT_BUDGET` em `aplicar_jogada()` (linha 1512).
2. `gwent_nevoa` e `gwent_geada` aplicam uma segunda marca a todos os alvos quando o budget chega a 2 (linhas 1575–1597).
3. `gwent_sangramento`, `gwent_geada_cariana`, `gwent_podrida` e `gwent_loucura` podem aplicar marca extra aos primeiros alvos da lista de tabuleiro, condicionados ao budget e ao alvo ainda não ter marca (linhas 1680–1747). A seleção depende da ordem da lista do tabuleiro, não de uma ordenação explícita por poder.
4. Após resolver especiais, `_aplicar_potencia_raridade()` pode modificar novamente deltas de bônus (linhas 1801–1807). O mesmo amplificador é chamado após efeitos de unidades/identidades/combos (linhas 1907–1915). Assim, uma Hemorragia ou corrosão de Podridão pode sofrer uma perda extra de bônus conforme raridade; bônus próprios de identidade também podem ser ampliados.
5. Relíquias estão explicitamente excluídas desse amplificador (linhas 1801–1804). Líderes são resolvidos em outro ramo e não passam por esse helper.

A descrição de `preparar_carta()` acrescenta textos específicos para algumas habilidades e um aviso genérico de potência para outras (linhas 731–763), mas essa camada de raridade cria múltiplas variáveis mecânicas e dificulta comparar EFP entre efeitos.

**Proposta para o novo jogo:** `rarity_scaling=false` para estados. Raridade será derivada de poder, efeito e custo; não aumentará marcas, número de alvos, consequências, duração ou modificadores de bônus de forma oculta. Qualquer potência adicional futura precisará ser um parâmetro explícito no efeito e no texto, não uma segunda camada automática.

## 7. Discrepâncias que a nova regra corrige

| Achado | Evidência legada | Regra proposta |
|---|---|---|
| Malenia repete corrosão quando alvo já está em 2 de Podridão | `scarlet_bloom`, linhas 527–532 | Consequência ocorre só ao cruzar para 2. |
| Oráculo da Geada recebe +1 quando alvo já está em 2 marcas | `v75_frost_oracle`, linhas 608–614 (`old_marks >= 1`) | +1 somente quando a aplicação efetivamente cruza para 2. |
| Especial pode dar marcas extras conforme raridade e ordem do tabuleiro | `aplicar_jogada()`, linhas 1512, 1575–1597 e 1680–1747 | Uma marca por aplicação; alvos explícitos; sem escala oculta. |
| Amplificador geral altera bônus após aplicação de estado | `_aplicar_potencia_raridade()`, linhas 659–692, 1801–1807 e 1907–1915 | Resolução do estado aplica exatamente a consequência descrita, sem pós-amplificação por raridade. |
| Snapshot da última rodada pode manter contadores depois do término | `_resolve_round()`, linhas 1146–1152 retorna antes da limpeza 1154–1193 | Expirar estados no fechamento inclusive da rodada final, preservando placar calculado. |
| `effect.row_status_pressure` atual não inclui Loucura no enum e não cobre todos os efeitos de purificação | `data/card_game/effect-registry-candidate.v1.json` | Revisar o registry de efeitos para usar perfis de estado e operações de limpeza tipadas. |

## 8. Proposta canônica v0.1

1. Quatro estados com perfil explícito: `status.frost`, `status.scarlet_rot`, `status.bleeding`, `status.madness`.
2. Cada contador tem máximo de duas marcas.
3. Geada, Podridão e Loucura reduzem 1 de poder efetivo por marca; a soma desses três estados tem teto 3.
4. Sangramento não reduz poder efetivo por marca; a segunda marca reduz 2 do bônus (piso -2) e consome as marcas.
5. Podridão na segunda marca corrói 1 bônus positivo (piso 0); Loucura na segunda marca zera bônus positivo; esses estados permanecem em duas marcas.
6. Consequência de limiar é ativada somente na transição para duas marcas. Não se repete enquanto o estado fica no cap.
7. Todos os estados expiram no fechamento da rodada; também são limpos quando a unidade sai do campo ou é purificada.
8. Raridade não multiplica os estados nem suas consequências.
9. Escopos/alvos dos aplicadores continuam parâmetros individuais: todas as unidades, fileira escolhida, Cerco fixo, inimigo mais forte, top 2/top 3 etc.
10. Purificadores são definições distintas com lista explícita de estados, escopo e bônus de purificação.

## 9. Arquivos novos desta etapa

- `data/card_game/status-registry-candidate.v1.json` — perfis dos quatro estados, regras agregadas, aplicações e purificadores legados.
- `data/card_game/status-registry.schema.v1.json` — JSON Schema Draft 2020-12 para o registry candidato.
- `sistemas/card_status_candidate.py` — resolvedor de referência independente; não é importado por `sistemas.gwent`.
- `docs/scripts/test-card-status-candidate-v0.1.py` — testes da especificação candidata e regressões que demonstram dois comportamentos legados repetitivos.

## 10. Validação e reprodução

Executar na raiz do projeto:

```bash
python docs/scripts/test-card-status-candidate-v0.1.py
python docs/scripts/test-card-contract-v1.py
python docs/scripts/test-effect-catalog-candidate-v0.1.py
python docs/scripts/test-effect-semantic-audit-v0.1.py
```

Resultado desta revisão:

- Estados candidatos: 4/4.
- Aplicadores mapeados: 15 (7 especiais, 5 identidades, 2 líderes, 1 relíquia).
- Purificadores mapeados: 5.
- Testes novos de estado: 41/41 (`docs/scripts/test-card-status-candidate-v0.1.py`).
- Relatório de validação: `docs/card-game-status-effects-validation-v0.1.md/.json`; hashes dos cinco arquivos funcionais comparados com as entradas do ZIP mestre desta revisão e todos coincidiram.
- Contrato canônico: 35/35.
- Catálogo candidato: 23/23.
- Auditoria semântica: 11/11.
- As suítes legadas de comportamento continuam em 251/251 asserts e 12/12 cenários stateful; são testes sintéticos do motor antigo, não prova de integração de produção nem de balanceamento.

## 11. Escopo exato do resolvedor candidato

`sistemas/card_status_candidate.py` implementa apenas a infraestrutura comum de transição de marcas, consequência de limiar, cálculo de poder efetivo, purificação seletiva/total e limpeza no fechamento da rodada. O mapa `applications` descreve origens/escopos/metadados, mas o módulo ainda **não** implementa seletores completos de alvos para cada especial/identidade/líder/relíquia, nem os efeitos colaterais próprios de Placidusax, Oráculo da Geada ou Acólito do Sangue. Esses handlers precisam ser construídos e testados individualmente após aprovação.

A suite de 41 testes inclui validação do schema e das referências de aplicações/purificadores, testes unitários do resolvedor novo e testes que chamam funções do motor antigo para demonstrar três defeitos conhecidos. Os 251 asserts legados e 12 cenários stateful são suites separadas; não provam equilíbrio competitivo e não tornam a regra antiga recomendada.

## 12. Pendências antes de conectar ao runtime

- Aprovar ou alterar os perfis e o modelo de consequência de limiar.
- Decidir se a consequência de Podridão e Loucura fica no contador/registry do estado ou em resolução callback do efeito (a proposta atual centraliza no status registry).
- Atualizar o registry canônico de efeitos para representar `status_profile_ref`, `loucura` e todos os cleansers sem duplicar regras.
- Implementar integração com `aplicar_jogada`, líderes, relíquias e `preparar_carta()` somente após aprovação.
- Adicionar testes ponta a ponta de status + clima + escudos + purificação + remoção + fim da rodada.
- Atualizar descrições e auras para refletir parâmetros reais.
- Calibrar EFP após estimar valor esperado por alvo/condição; esta auditoria não define custos, raridades finais nem força competitiva.

**Conclusão:** os quatro estados podem compartilhar uma infraestrutura de contadores e resolução, mas não uma consequência genérica idêntica. A implementação nova deve unificar aplicação/expiração e manter regras específicas de limiar por estado.
