# Revisão de remoção, execução, sacrifício e retorno do descarte — v0.1

**Data:** 2026-11-27  
**Status:** `CANDIDATE_FOR_REVIEW_NOT_APPROVED`  
**Runtime:** nenhuma integração desta proposta em `sistemas/gwent.py`. O módulo novo é um resolvedor de referência isolado.  
**Base consultada:** `sistemas/gwent.py`, `sistemas/cartas.py`, catálogo `CARTAS_POR_ID`, testes sintéticos de partida e os registros de efeitos/identidades.

## 1. Escopo e distinções obrigatórias

Esta revisão cobre três operações diferentes, que não devem ser colapsadas numa habilidade genérica:

1. **Remover/destruir/executar:** tira uma unidade do tabuleiro e pode ser bloqueada por escudo.
2. **Sacrificar:** tira uma unidade aliada do tabuleiro como custo de outra ação; no motor atual ignora escudo.
3. **Ressuscitar/recuperar:** tira uma unidade do descarte e a envia ao tabuleiro ou à mão. Retorno ao tabuleiro e retorno à mão possuem contratos diferentes.

`Lágrima Sagrada` (`gwent_medico`) é recuperação para a mão, não ressurreição. Não se deve classificá-la como retorno ao campo.

O inventário candidato contém nove atribuições: Chama Negra, Lâmina da Morte Destinada, Devorar, Preço em Sangue, Rykard, Ressurgir, Chamado dos Mortos, Esgar e Lágrima Sagrada.

## 2. Evidência do motor atual

### 2.1. Ponto central de remoção

Fonte: `sistemas/gwent.py:995-1021`, função `_remover_unidade()`.

O fluxo atual é:

1. Verifica `unit in side["board"]`.
2. Se `causa != "sacrificio"` e `escudo > 0`, consome um escudo e retorna sem remover.
3. Caso contrário, executa `side["board"].remove(unit)`.
4. Remove o escudo e zera `sangramento`, `geada`, `podrida` e `loucura`.
5. Anexa o objeto recebido ao descarte.
6. Incrementa `baixas`.
7. Se `unit.habilidade == "vinganca"`, concede +1 de bônus a cada aliado restante na mesma fileira.

**Semântica comprovada:** escudos bloqueiam remoção comum e execução, mas não sacrifício. Uma tentativa bloqueada consome uma carga de escudo, não vai ao descarte, não incrementa `baixas` e não dispara Vingança. Toda remoção bem-sucedida, inclusive sacrifício, incrementa `baixas` e pode ativar Vingança.

**Defeito adicional de identidade física:** membership e `list.remove()` usam igualdade de dicionários, não identidade de objeto. Com duas cópias físicas que tenham payloads iguais, `_remover_unidade(side, second, "sacrificio")` pode remover do tabuleiro o primeiro objeto igual, mas anexar o segundo objeto à pilha de descarte. O mesmo objeto pode então continuar no tabuleiro e aparecer no descarte, enquanto a primeira cópia desaparece. O resolvedor candidato usa busca por identidade (`is`) e `pop(index)` para evitar esse problema.

`baixas` não significa necessariamente “mortes”: inclui sacrifícios bem-sucedidos. Não foi encontrada nesta etapa uma normalização desse campo para um nome mais preciso.

### 2.2. Especiais de remoção

| Carta / ID | Fonte | Alvo e regra efetiva | Interação relevante |
|---|---|---|---|
| Chama Negra / `gwent_queima` | `sistemas/gwent.py:1616-1620` | Tenta remover a unidade de maior poder efetivo de cada lado; no empate, `max()` mantém o primeiro item da lista | Passa pelo ponto central de remoção; escudo bloqueia e é consumido. O especial ainda é resolvido/consumido mesmo quando um alvo resiste. |
| Lâmina da Morte Destinada / `gwent_execucao` | `1057-1060`, `1623-1638` | Exige escolher fileira; alvo é inimigo nela com poder efetivo até `min(6, 6 + potencia_raridade)`; target opcional, sem target escolhe o menor elegível | A expressão sempre vale 6 porque o orçamento de raridade atual é não negativo. Raridade não amplia o limite. Escudo bloqueia a execução, mas o especial continua consumido. |

A UI e a mensagem de erro repetem a fórmula com raridade, sugerindo uma escalabilidade que não ocorre. O teste da carta em raridade Singular confirmou que poder efetivo 7 continua inelegível, enquanto poder 6 é elegível; se o alvo tem escudo, a ativação é aceita, o escudo cai e a unidade permanece.

### 2.3. Sacrifícios

| Origem | Fonte | Alvo / ganho | Falta ou particularidade |
|---|---|---|---|
| Devorar / `devorar` (`gwent_unidade_carniceiro_forja`) | `1871-1878` | Aliado mais fraco por poder efetivo na mesma fileira; ganho `min(4, max(1, poder_efetivo_do_alvo))` | Sem aliado: não sacrifica, não ganha bônus e a carta ainda entra. Não há erro nem fallback. |
| Preço em Sangue / `v75_blood_price` (`gwent_v75_veu_carrasco_preco`) | `sistemas/gwent.py:594-601`, em `_aplicar_habilidade_identidade()` | Aliado mais fraco na mesma fileira; ganho `min(3, max(1, poder_efetivo_do_alvo))` | Sem aliado: recebe +1. A identidade está ativa por ID, mesmo quando o campo genérico de habilidade está vazio. |
| Rykard / `rykard_devour` (`sombra_caminhante`) | `1427-1436` | Exige pelo menos duas unidades aliadas na fileira; sacrifica a mais fraca e dá +2 às unidades restantes na fileira | Se a vítima tem Vingança, a sequência do motor permite +1 por Vingança e depois +2 de Rykard aos mesmos sobreviventes (total +3). `victim_name` é variável local não utilizada. |

A seleção `min(..., key=_poder_efetivo)` desempata pela ordem atual do tabuleiro. O sacrifício ignora escudo e passa por `_remover_unidade()`, portanto também zera status, aumenta `baixas`, coloca a unidade no descarte e ativa Vingança quando a habilidade declarada é `vinganca`.

### 2.4. Ressurreição ao tabuleiro

| Origem | Fonte | Elegibilidade e seleção | Restauração atual |
|---|---|---|---|
| Ressurgir / `ressurgir` | `1879-1889`, append final em `1923-1924` | Não-especial, poder-base `<=5`; escolhe maior poder; empate pelo primeiro item do descarte | Remove um item por `list.remove`, faz `deepcopy`, zera bônus, remove escudo e preserva fileira se válida; caso contrário usa a fileira em que a carta nova foi jogada. Não limpa explicitamente os quatro status. |
| Chamado dos Mortos / `gwent_requiem` | opções `1065-1068`, resolução `1762-1779` | Não-especial, poder-base `<= min(10, 6 + orçamento_de_raridade)`; orçamento máximo atual 3, portanto limite efetivo máximo 9. Alvo pode ser escolhido; sem alvo escolhe maior poder | Remove um item, copia, zera bônus, remove escudo, preserva fileira válida; caso contrário usa a fileira escolhida ou `melee`. Não limpa explicitamente os quatro status. |
| Esgar / `esgar_blood_priest` | `1437-1448` | Não-especial, poder-base `<=5`; escolhe maior poder; empate pelo primeiro item do descarte | Faz cópia, força fileira escolhida, soma +1 ao bônus que já estava salvo, remove escudo, zera os quatro status e anexa ao tabuleiro. **Defeito:** reconstrói o descarte filtrando todos os registros com o mesmo `card_id`; pode apagar cópias que não foram ressuscitadas. |

As três vias inserem a unidade diretamente no campo. Não voltam a executar a habilidade de entrada da unidade, a passiva de facção ou um combo como efeito de chegada. O motor pode, contudo, considerar as tags dessa unidade em um combo posterior quando uma carta nova for jogada e o resolvedor verificar as cartas do campo.

O motor atual não tem um identificador físico universal `instance_id` no contrato de carta usado por estas funções. Os selectors de alvo geralmente usam `card.id`; esse ID identifica a definição da carta, não distingue com segurança duas cópias físicas.

### 2.5. Recuperação para a mão

Lágrima Sagrada / `gwent_medico`: `1061-1064` e `1604-1615`.

- Elegibilidade: não-especial e poder-base `<= min(8, 4 + orçamento_de_raridade)`; o orçamento máximo atual 3 limita o valor a 7.
- Alvo selecionado por ID quando informado; sem alvo, escolhe o último elegível na ordem do descarte.
- Move o mesmo objeto do descarte para a mão.
- Não zera bônus, escudo ou estados negativos.

É uma recuperação sem normalização, distinta da ressurreição. Os filtros antigos usam `not card.especial`; não validam simultaneamente um campo de tipo canônico. Um payload malformado com `categoria == "Especial"` e `especial` ausente/falso pode passar pelo filtro.

## 3. Defeitos comprovados e impacto

| ID | Severidade | Evidência | Impacto |
|---|---|---|---|
| `RR-001` | Alta | `sistemas/gwent.py:1441-1443` | Esgar pode remover todas as cópias do mesmo ID do descarte ao ressuscitar apenas uma. |
| `RR-002` | Alta | `995-1009` | Remoção baseada em igualdade de dicionário pode retirar o objeto físico errado e deixar o objeto chamado simultaneamente no campo e no descarte. |
| `RR-003` | Média | `1058-1060`, `1629-1635` | Limite da Execução é sempre 6; UI/mensagem sugere scaling de raridade inexistente. |
| `RR-004` | Média | `1879-1888`, `1762-1779` | Ressurgir e Réquiem não limpam status explicitamente; entradas antigas/malformadas no descarte podem ressurgir afetadas. |
| `RR-005` | Média | `1871-1878` | Devorar sem aliado na fileira vira no-op silencioso e a carta continua jogada. |
| `RR-006` | Média | `1437-1448` | Esgar soma +1 a bônus já existente, enquanto Ressurgir e Réquiem zeram bônus; políticas de entrada divergentes. |
| `RR-007` | Média | `1061-1068`, `1605-1615`, `1762-1778`, `1879-1884` | Elegibilidade usa flag booleana `especial`, sem uma validação canônica de `kind == unit`. |
| `RR-008` | Média | seletores com `max/min` e listas em `1041-1078`, `1605-1615`, `1762-1779`, `1879-1884` | Empates dependem da ordem incidental de listas; não há contrato de desempate por cópia física. |
| `RR-009` | Média | `_remover_unidade` + Rykard `1427-1436` | Sacrifício de unidade com Vingança acumula +1 de Vingança e +2 do líder no mesmo grupo. É comportamento real, mas precisa ser escolha explícita de design. |

## 4. Proposta canônica executável (não aprovada)

Arquivos novos:

- `data/card_game/removal-resurrection-registry-candidate.v1.json`
- `data/card_game/removal-resurrection-registry.schema.v1.json`
- `sistemas/card_removal_resurrection_candidate.py`
- `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py`
- `docs/card-game-removal-resurrection-validation-v0.1.md/.json`

A proposta separa:

- Enum de causas: `normal_removal`, `execution`, `sacrifice`.
- Escudo: bloqueia remoção comum e execução; sacrifício ignora. Tentativa bloqueada consome uma carga e não dispara descarte, contador ou Vingança.
- Remoção bem-sucedida: remove o objeto físico correto por identidade, limpa escudo/status, envia uma única cópia ao descarte, incrementa o contador legado `baixas` e dispara Vingança uma vez para aliados restantes na mesma fileira.
- Cópia física: `instance_id` único é o identificador preferido. `card_id` legado só pode servir como alvo se houver exatamente uma cópia elegível com esse ID; caso contrário, é ambíguo.
- Ressurreição: aceita apenas `kind == "unit"`, remove exatamente uma entrada do descarte, limpa os quatro estados transitórios e escudo, não reexecuta habilidades de entrada/passiva/combo na chegada. A unidade pode participar de verificações de combo futuras.
- Recuperação à mão: fluxo separado, com preservação do objeto/campos conforme o legado até decisão explícita.
- Bônus e fileira de chegada são parâmetros por habilidade, nunca efeitos implícitos de raridade ou um comportamento universal presumido.

O módulo `sistemas/card_removal_resurrection_candidate.py` está isolado e **não é importado por `sistemas.gwent`**. Ele é uma prova executável de contrato, não o novo motor.


## 4.1. Interações cruzadas e ordem de resolução

A matriz completa está em `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md`. Os testes ampliados confirmaram que: (a) Vingança durante Devorar só atinge aliados que já estavam no tabuleiro; a carta que está entrando recebe seu ganho de sacrifício em seguida; (b) Rykard aplica +1 de Vingança e depois +2 do líder, resultando em +3 por aliado sobrevivente; (c) a unidade ressuscitada é anexada depois da verificação de combo e, portanto, só participa de combos futuros; (d) o caminho central de remoção já limpa status antes de enviar a unidade ao descarte, então os status residuais em Ressurgir/Réquiem são sobretudo risco de snapshots antigos ou fontes alternativas.

O novo contrato usa o campo canônico singular `effect_id == "effect.vengeance_on_removal"`; aliases `effect_ids` e `habilidade == \"vinganca\"` são aceitos apenas para compatibilidade no resolvedor de referência.

## 5. Decisões pendentes do proprietário

| Decisão | Evidência antiga | Recomendação para debate | Não decidido |
|---|---|---|---|
| Limite da Lâmina da Morte Destinada | Poder efetivo máximo 6 em todas as raridades | Não manter expressão de raridade enganosa; aprovar explicitamente um valor fixo ou fórmula após balanceamento 1–15 | **Pendente** |
| Devorar sem aliado | Carta é jogada e não faz nada | Exigir precondição e rejeitar a ação antes de consumir a carta, ou atribuir fallback descrito | **Pendente** |
| Vingança no sacrifício | Vingança dispara para qualquer remoção bem-sucedida, inclusive sacrifício | Preservar se sacrifício significa queda real; caso contrário, declarar causas que disparam | **Pendente** |
| Contador `baixas` | Inclui sacrifícios | Renomear no novo modelo para `removed_units`/`board_removals`, ou conservar sem chamar de mortes | **Pendente** |
| Acúmulo Vingança + Rykard | +1 da Vingança seguido de +2 do líder | Tornar acumulação intencional e documentada ou impedir uma das camadas | **Pendente** |
| Limites de poder no descarte | Ressurgir/Esgar 5; Réquiem min(10, 6+raridade); Lágrima min(8,4+raridade) | Manter limites por função de carta somente se forem parte deliberada do design; de outra forma reequilibrar como novo sistema | **Pendente** |
| Bônus na ressurreição | Ressurgir/Réquiem = 0; Esgar = bônus anterior +1 | Definir cada modo explicitamente; discutir se Esgar deve entrar com exatamente +1 ou somar +1 | **Pendente** |
| Fileira de retorno | Ressurgir preserva válida/fallback; Réquiem preserva válida/fallback escolhido/melee; Esgar força fileira escolhida | Manter política por efeito se for parte do identity; caso contrário padronizar fallback | **Pendente** |
| Instância física | IDs de carta são usados em ações; Esgar filtra cópias por ID | `instance_id` único em cada exemplar e alvo; `card_id` fica como ID do modelo | **Pendente para o schema/exemplar** |
| Estado após retorno | Esgar limpa estado; Ressurgir/Réquiem não | Limpar escudo e todos os quatro estados em todo retorno ao campo; mão permanece recuperação separada | **Proposta, não aprovada** |

## 6. Validação executada

`docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` passou **49/49 testes** na execução registrada, incluindo:

- Validação Draft 2020-12 do schema e instância.
- Nove atribuições e sete IDs de cartas existentes no catálogo legado.
- Causas, escudos, descarte, contador, Vingança, limpeza de estados e remoção por identidade física.
- Seleção de unidade elegível, cópias duplicadas, IDs ambíguos, tipo unidade/especial, bônus, fileira, limpeza, retorno à mão e contador.
- Reprodução de comportamentos legados: execução com limite fixo, sacrifício do Preço em Sangue que ignora escudo, Devorar sem alvo, remoção incorreta por igualdade, descarte em massa de cópias pelo Esgar e estados inconsistentes de retorno.

Comando reproduzível na raiz do projeto:

```bash
python docs/scripts/test-card-removal-resurrection-candidate-v0.1.py
```

Validação estática adicional:

```bash
python -m py_compile sistemas/card_removal_resurrection_candidate.py
python -m py_compile docs/scripts/test-card-removal-resurrection-candidate-v0.1.py
```

O relatório JSON registra 49 testes, 49 aprovados, zero falhas. O script deve ser executado novamente caso registry, módulo, teste ou runtime seja alterado.

## 7. Limitações

- O resolvedor candidato não participa de partidas reais do runtime; resultados da parte candidata são testes puros e da parte legada são cenários em memória.
- Não houve teste HTTP, Discord, DB de produção, browser, R2 ou partidas competitivas completas nesta etapa.
- `instance_id` ainda não foi integrado ao schema de exemplares/coleção nem às ações serializadas. O protótipo exige `kind == "unit"`; a conversão de dados legados precisa mapear `especial/categoria` explicitamente.
- Os limites 5/9/7 e o valor 6 da execução são dados observados, não recomendação de balanceamento para poder-base 1–15.
- Nenhuma limpeza, migração ou exclusão de habilidades antigas ocorreu.

## 8. Próximos passos

1. Obter decisões sobre os itens pendentes da seção 5.
2. Auditar as interações de efeitos de remoção/sacrifício com escudo, Vingança, bônus de líder, clima, estados, baixa e combo.
3. Definir `instance_id` no schema de exemplares e nos snapshots/ações antes de codificar qualquer ressurreição real.
4. Integrar remoção e retorno ao novo motor quando as decisões forem aprovadas.
5. Depois revisar buffs, movimento e efeitos de fileira antes de calibrar EFP/custo/raridade.

**Regra para novo chat:** leia este documento, o `data/card_game/removal-resurrection-registry-candidate.v1.json`, o módulo candidato, o relatório JSON e o handoff. Não trate nenhum item desta proposta como aprovado ou conectado ao runtime.
