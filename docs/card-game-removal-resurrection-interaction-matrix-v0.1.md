# Matriz de interações — remoção, sacrifício e retorno do descarte v0.1

**Data:** 2026-11-27  
**Status:** auditoria comportamental do runtime legado + proposta isolada; nenhuma regra nova foi integrada.  
**Base:** `sistemas/gwent.py`, registry candidato de remoção/ressurreição e 49 testes controlados.

## 1. Objetivo e limites

Esta matriz investiga o que acontece quando remoção, sacrifício ou retorno ao campo se combina com escudo, Vingança, fileira, combos, status e ordem de efeitos de entrada. Ela não aprova balanceamento nem substitui testes HTTP/Discord/DB/produção.

## 2. Interações reproduzidas

| Caso | Sequência / condição | Resultado comprovado no legado ou candidato | Consequência de design |
|---|---|---|---|
| IR-01 | Remoção comum ou execução contra alvo com escudo | Consome uma carga, mantém a unidade no campo, não envia ao descarte, não incrementa `baixas` e não dispara Vingança | Bloqueio é uma tentativa frustrada, não uma remoção parcial |
| IR-02 | Sacrifício de alvo com escudo e estados negativos | Ignora escudo; ao remover, limpa escudo e os quatro status, descarta, incrementa `baixas` e pode disparar Vingança | Sacrifício é uma causa distinta e deve continuar explicitamente tipada |
| IR-03 | Devorar sacrifica uma unidade com Vingança | O alvo é removido antes de a carta Devorar ser anexada ao tabuleiro. Vingança concede +1 somente aos aliados pré-existentes na mesma fileira; depois Devorar recebe seu ganho próprio com base no poder efetivo da vítima | O bônus de Vingança não alcança a unidade que está entrando por Devorar nessa mesma resolução |
| IR-04 | Rykard sacrifica vítima com Vingança e existem outros aliados na fileira | `_remover_unidade()` aplica Vingança (+1); em seguida o handler de Rykard concede +2 aos sobreviventes. O resultado observado é +3 por sobrevivente | A acumulação é comportamento efetivo, mas precisa ser uma escolha explícita na regra nova |
| IR-05 | Uma carta entra com `ressurgir` e uma unidade ressuscitada tem tags de combo | A ordem do fluxo é: resolver habilidade/identidade; calcular combo da carta jogada; anexar a carta jogada ao campo; anexar a unidade ressuscitada | A unidade ressuscitada não participa da verificação de combo da mesma jogada de retorno |
| IR-06 | Uma unidade ressuscitada já está no campo e uma carta participante é jogada depois | A chamada posterior de `_aplicar_combo_de_cartas()` considera as tags de todas as unidades atualmente no campo; uma unidade ressuscitada pode completar o conjunto de tags com a carta nova | Não reexecutar combo na chegada não significa excluir a unidade ressuscitada de combos futuros |
| IR-07 | O alvo de remoção tem Vingança, mas a remoção comum é bloqueada por escudo | O escudo é consumido e a Vingança não dispara | O hook depende de remoção bem-sucedida, não da tentativa |
| IR-08 | Duas cópias físicas têm dicionários iguais | O motor legado usa `in`/`list.remove` por igualdade; pode remover a primeira cópia igual e descartar o objeto que foi passado, deixando uma referência física duplicada | O runtime novo precisa localizar e remover por `instance_id` ou identidade de instância, não por igualdade estrutural |
| IR-09 | Duas cópias de mesmo `card_id` estão no descarte e Esgar retorna uma | O handler legado filtra o descarte inteiro pelo `card_id` da escolhida; as cópias adicionais somem do descarte | O retorno precisa retirar apenas o item/`instance_id` selecionado |
| IR-10 | `Ressurgir` ou `Réquiem` retorna um registro de descarte com status residual | Os handlers não limpam explicitamente os quatro status na chegada; o resolvedor candidato normaliza status e escudo | A normalização no retorno é uma proposta, particularmente útil para snapshots antigos ou fontes alternativas de descarte |
| IR-11 | Uma unidade é removida pelo caminho central e depois ressuscitada | O caminho central já zera status antes de anexar ao descarte; portanto, o problema de estado residual em Ressurgir/Réquiem depende de snapshots antigos, objetos malformados ou outras origens de descarte | Não exagerar o risco: a maioria das remoções atuais já limpa os campos antes do descarte |
| IR-12 | Uma unidade retorna à mão por `gwent_medico` | É movido o objeto do descarte à mão; não é colocado no tabuleiro nem passa pela política de normalização de ressurreição | Recuperação à mão deve permanecer operação distinta |

## 3. Ordem exata do turno de unidade

No caminho de jogada de unidade em `aplicar_jogada()`, a ordem observada no trecho de `sistemas/gwent.py` é:

1. Habilidades genéricas de entrada são resolvidas, incluindo Devorar/Ressurgir.
2. Habilidade de identidade (se houver) é resolvida.
3. A carta jogada verifica e ativa, no máximo, um combo.
4. O modificador de raridade é aplicado.
5. A passiva de facção é aplicada à carta jogada, se elegível.
6. A carta jogada é anexada ao tabuleiro.
7. Se houver unidade ressuscitada, ela é anexada depois da carta jogada.

Consequências: a unidade ressuscitada não recebe a passiva de facção da jogada atual, não executa sua habilidade de entrada novamente e não participa do cálculo de combo dessa jogada. Em jogadas futuras, se permanecer em campo, suas tags são consideradas pelo resolver de combos. Esta é a ordem efetiva atual, não uma recomendação obrigatória para o novo motor.

## 4. Semântica de Vingança e sacrifício

- Vingança usa atualmente o campo legado `habilidade == "vinganca"`.
- O contrato canônico define `effect_id == "effect.vengeance_on_removal"`; o resolvedor de referência foi ajustado para reconhecer esse campo singular e aceitar aliases legados somente como compatibilidade.
- A Vingança é resolvida depois da remoção bem-sucedida e antes que o handler externo continue seus próprios bônus (caso de Rykard).
- O alvo removido já não pertence ao tabuleiro durante a seleção dos aliados afetados.
- Só aliados na mesma fileira recebem +1.
- O campo legado `baixas` inclui sacrifícios e não deve ser interpretado como contagem exclusiva de mortes.

## 5. Resultados da bateria ampliada

O script `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` passou **49/49 testes**, sem falhas. Em relação à bateria anterior (43), foram adicionados seis testes:

1. `effect_id` canônico singular ativa Vingança no resolvedor candidato.
2. Remoção seguida de ressurreição entrega uma unidade limpa e mantém o contador de remoções.
3. Unidade ressuscitada pode contribuir para um combo disparado por carta posterior.
4. Vingança em Devorar só fortalece os aliados pré-existentes; o novo Devorador recebe seu ganho separadamente.
5. Rykard acumula +1 de Vingança e +2 do próprio líder.
6. A ordem do código prova que o combo da jogada é calculado antes de anexar a carta jogada e a unidade ressuscitada.

As três verificações do runtime são cenários sintéticos em memória, com chamada ao motor ou conferência do fluxo-fonte. Os três testes do resolvedor são isolados e não significam integração do módulo candidato.

## 6. Recomendação candidata (não aprovada)

1. Preservar a distinção entre remoção comum, execução e sacrifício.
2. Preservar escudo contra remoção comum/execução e bypass pelo sacrifício, salvo mudança deliberada da regra.
3. Disparar Vingança apenas após remoção bem-sucedida; aprovar separadamente se sacrifício continua sendo causa válida.
4. Decidir de forma explícita se efeitos de sacrifício podem acumular com buffs do líder (o legado de Rykard resulta em +3).
5. Usar `effect_id` singular no catálogo canônico e `instance_id` por exemplar físico.
6. Retirar exatamente uma instância do descarte; `card_id` só identifica o modelo e não uma cópia física.
7. Ao retornar ao campo, limpar escudo e os quatro estados temporários; não repetir efeito de entrada, passiva de facção ou combo da jogada de retorno; permitir participação em combos futuros.
8. Manter `gwent_medico` como recuperação para mão, com política separada.
9. Não aprovar ainda o limite de Execução, limites de poder dos retornos, bônus inicial de Esgar ou comportamento de Devorar sem alvo. Esses valores precisam de decisão e balanço no sistema 1–15.

## 7. Reproduzir

```bash
python docs/scripts/test-card-removal-resurrection-candidate-v0.1.py
```

O relatório atualizado está em `docs/card-game-removal-resurrection-validation-v0.1.md/.json`.

**Estado:** nenhuma alteração em `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, banco, API ou imagens. A auditoria e o resolvedor candidato permanecem independentes do runtime. As decisões da seção 6 não foram aprovadas pelo proprietário.
