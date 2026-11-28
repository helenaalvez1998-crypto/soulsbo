# Auditoria de sobreposição, precedência e participação em combos — v0.1

**Status:** relatório histórico congelado do baseline pré-política. A política foi posteriormente aprovada e implementada; os resultados deste arquivo não descrevem o runtime atual.  \
**Baseline:** `soulsbo-main(1).zip`.  \
**Escopo:** comportamento observado antes da alteração funcional, sem mudança de runtime nesta auditoria.

> **Aviso de reprodução:** `docs/scripts/audit-combo-overlap-v0.1.py` usa o módulo `sistemas.gwent` do checkout em que for executado. Agora ele contém uma guarda que recusa a execução no runtime pós-política, para evitar sobrescrever o relatório histórico com números incompatíveis. Para o comportamento atual, execute somente `docs/scripts/audit-combo-overlap-v0.2.py`. O JSON/Markdown v0.1 são evidência histórica congelada; não os regenerar no checkout atual. Reproduzir o baseline exige checkout separado do código pré-política original.

## 1. Conclusão executiva

A execução de `_aplicar_combo_de_cartas()` possui duas regras implícitas que afetam a descrição e a atribuição do bônus:

1. Quando mais de um combo está elegível na mesma jogada, o motor ativa somente o primeiro na ordem de inserção de `SYNERGY_COMBOS` e retorna imediatamente. Os outros combos elegíveis ficam pendentes e podem disparar em jogadas posteriores.
2. Para uma jogada posterior disparar um combo pendente, o motor exige apenas que a carta atual tenha **alguma** tag de sinergia. Não exige que essa carta atual contribua com uma das tags exigidas pelo combo pendente. Se o tabuleiro já satisfaz as tags e o mínimo de participantes, uma carta não relacionada pode receber o bônus.

Também há três definições sem `minimum` explícito. Uma delas, `eco_convergente`, ativa atualmente com uma única carta (`gwent_unidade_eco`), embora sua descrição diga que o Erudito e outra unidade Astral amplificam a magia.

Esses resultados confirmam uma dessincronia entre **participação descrita** e **carta que recebe o efeito**. Não demonstram, por si só, desequilíbrio competitivo ou taxa de vitória. A intenção de design precisa ser definida antes de alterar o motor.

## 2. Origem exata no código

Arquivo: `sistemas/gwent.py`  
Função: `_aplicar_combo_de_cartas()`  
Trecho de referência no baseline: aproximadamente linhas 916–946.

| Linhas | Comportamento observado | Consequência |
|---|---|---|
| 918–920 | Carrega tags da carta atual e retorna apenas se o conjunto estiver vazio. | Qualquer carta com qualquer tag pode chegar à verificação dos combos; ainda não há vínculo com as tags requeridas pelo combo específico. |
| 921–925 | Une tags das unidades no campo e da carta atual. | Permite que o tabuleiro satisfaça antecipadamente a condição de um combo. |
| 926–931 | Itera `SYNERGY_COMBOS` em ordem de inserção e testa se todas as tags requeridas estão no conjunto total. | A ordem de declaração do dicionário determina precedência quando há sobreposição. |
| 932–936 | Só verifica quantidade mínima de participantes quando a chave `minimum` existe. | Combos sem `minimum` podem ser satisfeitos por uma única carta que carregue todas as tags. |
| 937–945 | Aplica o bônus à carta atual, aplica `team_bonus` aos aliados da fileira, marca o combo como usado e retorna imediatamente. | Apenas um combo é aplicado por chamada; demais combos elegíveis ficam para chamadas posteriores. O bônus individual vai para a carta atual, mesmo quando ela não forneceu as tags requeridas. |

O comportamento não é aleatório: é determinístico e decorre da ordem declarada de `SYNERGY_COMBOS` e do estado do tabuleiro.

## 3. Método reproduzível

Script: `docs/scripts/audit-combo-overlap-v0.1.py`.  
Saída estruturada: `docs/card-game-combo-overlap-v0.1.json`.

O script importa `sistemas.cartas` e `sistemas.gwent`, seleciona as unidades atuais que possuem tags em `CARD_SYNERGY_TAGS` e chama o resolvedor real `_aplicar_combo_de_cartas()`.

- 67 IDs de unidades atuais com tags foram considerados.
- Cinco IDs do mapa de tags sem carta no catálogo foram excluídos e permanecem documentados como referências órfãs.
- Foram enumeradas 4.422 ordens de duas cartas distintas (67 × 66).
- Foram enumeradas 287.430 sequências ordenadas de três cartas distintas (67 × 66 × 65).
- Os testes não repetem modelos de carta dentro de cada par/trinca, respeitando a regra de unicidade por modelo observada no salvamento de deck.
- As trincas não constituem uma validação completa de um deck de 12 cartas: não validam posse, líder, relíquia, todas as restrições de composição, oponente, clima ou partidas completas.
- A execução não mede vitória, EV, força EFP ou equilíbrio.

Para reproduzir:

```bash
python docs/scripts/audit-combo-overlap-v0.1.py
```

## 4. Resultados quantitativos

| Medida | Resultado | Interpretação |
|---|---:|---|
| Unidades atuais com tags | 67 | Universo usado nas enumerações. |
| Definições de combo | 27 | Catálogo atual do motor. |
| Combos sem `minimum` | 3 | `cinzas_fornalha`, `vazio_astral`, `eco_convergente`. |
| Ativações solo no catálogo atual | 1 | `gwent_unidade_eco` ativa `eco_convergente`. |
| Ordens de dois modelos distintas examinadas | 4.422 | Todas as permutações de pares. |
| Ordens de dois modelos com mais de um combo elegível | 154 (3,4826%) | 77 pares não ordenados; precedência adia ao menos um combo. |
| Combos diferentes acionados em sequências de três modelos distintos | 11.780 de 287.430 (4,0984%) | A sequência pode ativar pelo menos dois combos distintos em jogadas sucessivas. |
| Sequências triplas multi-combo da mesma facção | 1.088 | Exemplos podem ser incorporados a um deck monofacção; não equivale a validar o deck completo. |
| Transições ordenadas distintas entre primeiro e combo posterior | 102 | Há muitas combinações de precedência, não um único caso isolado. |
| Eventos de acionamento de combo posterior analisados | 11.784 | Eventos subsequentes ao primeiro combo da sequência. |
| Carta que acionou o combo posterior sem contribuir tag exigida | 8.096 (68,7033%) | Evidência direta da regra de participação insuficiente. |
| Carta que acionou o combo posterior e contribuiu com tag exigida | 3.688 (31,2967%) | Casos em que a carta atual participa da condição por tag. |

O percentual de 68,7033% tem como denominador os 11.784 **eventos posteriores** encontrados nas sequências examinadas, não todas as jogadas do jogo.

## 5. Exemplos concretos

### 5.1. Combo pendente concedido a uma carta sem a tag requerida

As três cartas abaixo têm IDs distintos e pertencem à Ordem Áurea:

| Ordem | ID | Nome | Tags |
|---:|---|---|---|
| 1 | `chefe_guardiao_cinzas` | Cavaleiro da Árvore Áurea | `cinzas`, `ordem_dourada` |
| 2 | `gwent_unidade_baluarte` | Cavaleiro do Crisol | `fornalha`, `ordem_dourada` |
| 3 | `covenant_irmandade_ferro` | Guardas da Árvore Áurea | `estandarte` |

**Primeira jogada:** ao entrar o Cavaleiro do Crisol, as tags `cinzas` e `fornalha` completam `cinzas_fornalha` (`Aliança da Árvore Áurea`). Ao mesmo tempo, as duas primeiras unidades satisfazem as tags e o mínimo 2 do `juramento_erdtree`, mas o resolvedor retorna depois de ativar o primeiro combo, deixando o segundo pendente.

**Terceira jogada:** Guardas da Árvore Áurea possui apenas a tag `estandarte`. Mesmo assim, o resolvedor ativa `juramento_erdtree`, porque as duas unidades anteriores já satisfazem `ordem_dourada` e o mínimo de participantes. O bônus individual do combo é aplicado à carta atual — Guardas da Árvore Áurea — embora ela não contribua com `ordem_dourada`.

Isso é comportamento observado do código atual. Pode ser considerado defeito de vínculo entre participantes e recompensa, a menos que a regra intencional seja “qualquer unidade com alguma tag pode recolher um combo que ficou pendente”. Essa regra alternativa não está expressa na descrição do combo nem documentada no catálogo.

### 5.2. Ativação solo de `eco_convergente`

`gwent_unidade_eco` — **Erudito das Pedras Cintilantes**, da Lua Negra — possui simultaneamente as tags `astral` e `eco`. A definição `eco_convergente` exige ambas, mas não declara `minimum: 2`. Assim, o próprio Erudito ativa sozinho o combo `Eco das Pedras Cintilantes`.

A descrição atual diz: “O Erudito das Pedras Cintilantes e uma unidade Astral amplificam a mesma magia (+2).” O texto descreve dois participantes, enquanto a definição permite um.

`cinzas_fornalha` e `vazio_astral` também não declaram `minimum`; na varredura atual, nenhuma unidade isolada do catálogo conseguiu ativá-los sozinha. A ausência do mínimo continua sendo uma ambiguidade de regra.

## 6. Decisões de design necessárias antes da correção

Não alterar o runtime até aprovar estas decisões:

1. **Contribuição obrigatória:** a carta que recebe o bônus de um combo deve obrigatoriamente fornecer pelo menos uma das tags requeridas? A recomendação técnica é **sim**, para alinhar participação, recompensa e descrição. Uma regra mais estrita poderia exigir que a carta atual introduza uma tag requerida que ainda faltava no campo.
2. **Mínimo de participantes:** `cinzas_fornalha`, `vazio_astral` e `eco_convergente` devem exigir dois modelos distintos, pois suas descrições nomeiam dois participantes? A recomendação é **sim**, salvo redesign explícito da descrição/efeito.
3. **Sobreposição e precedência:** quando dois ou mais combos se tornam elegíveis na mesma jogada, devem todos aplicar-se, apenas um aplicar-se, ou haver prioridades por carta/facção? O comportamento atual — primeiro item do dicionário, retorno imediato e combos restantes adiados — não está explicitado como regra de jogo. A recomendação é declarar uma política determinística no manifesto de combos, não depender acidentalmente da ordem do dicionário.
4. **Alvo do bônus:** se os requisitos já estavam completos antes da jogada atual, quem deve receber o bônus: a carta que completou os requisitos, todos os participantes, ou uma recompensa de equipe? O motor atual sempre aplica o bônus individual à carta atual.

Uma opção consistente e simples para uma primeira correção seria: (a) exigir que a carta atual compartilhe ao menos uma tag requerida; (b) exigir dois participantes distintos nos três combos de descrição conjunta; (c) manter no máximo um combo por jogada, mas dar prioridade explícita via campo `priority`; (d) só acionar o combo na carta que completa seus requisitos. Isso é uma recomendação técnica para discussão, não uma regra aprovada.

## 7. Impacto esperado e superfícies afetadas

Se a política for corrigida, os efeitos podem alterar poder de unidades, bônus de fileira, pontuação e descrições do catálogo. Os pontos a validar são:

- `_aplicar_combo_de_cartas()` em `sistemas/gwent.py`.
- `SYNERGY_COMBOS` e `CARD_SYNERGY_TAGS` em `sistemas/gwent.py`.
- `preparar_carta()` e os campos `combos_compativeis`/descrição em `sistemas/gwent.py` e `sistemas/cartas.py`.
- snapshots persistidos das partidas (`state_json`): partidas em andamento podem conservar estado antigo e não devem ser reescritas implicitamente.
- renderização de texto/indicadores em `sistemas/arte_cartas.py`, `sistemas/arte_gwent_efeitos.py` e frontend, se a decisão mudar o texto apresentado.

Antes de alterar a função, acrescentar testes negativos específicos para: carta atual sem tag requerida; combo de duas participações com uma única carta; pares alternativos de tags; múltiplos combos elegíveis; carta que completa o requisito; combo já usado; reset entre rodadas; e efeitos de time em fileiras diferentes.

## 8. Estado desta auditoria

- **Concluído:** diagnóstico reproduzível do comportamento atual com 67 unidades, 27 combos, pares e trincas de IDs distintos.
- **Achados confirmados:** primeira correspondência por ordem de dicionário; combos elegíveis podem ser adiados; carta posterior sem tag requerida pode receber o bônus; `eco_convergente` é ativável por uma única carta; três definições não têm mínimo explícito.
- **Pendente:** decisão de design para os quatro pontos da seção 6; extensão dos testes para todos os pares alternativos de ativação dentro de partidas completas; simulação de pontuação e equilíbrio.
- **Alterações funcionais:** nenhuma.
