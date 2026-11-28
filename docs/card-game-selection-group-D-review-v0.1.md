# Grupo D — seleção, fallback, resultados e custos: auditoria e proposta v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev11.zip`  
**Status:** `READ_ONLY_LEGACY_AUDIT; RESOLUTIONS_CANDIDATE_NOT_APPROVED`  
**Escopo de implementação:** documentação, schemas candidatos e harness de auditoria em `docs/` somente. Nenhuma alteração no runtime, API, banco, catálogo ativo ou frontend.

## 1. Resumo executivo

O Grupo D foi auditado em quatro dimensões que precisam permanecer separadas: (1) descoberta e seleção de alvos; (2) resultado por alvo e resultado agregado da ação; (3) custos da ação, da fonte e da proteção; (4) atomicidade lógica da resolução. O motor legado já possui comportamentos distintos para rejeição, bloqueio e ação consumida sem mudança no alvo. Reduzir tudo a `success/error` perderia regras importantes.

A auditoria reproduzível do Grupo D passou **23/23 casos**. As auditorias anteriores de escopo de fileira e paridade de UI também foram reexecutadas: **15/15** e **12/12**. O contrato CardInstance v0.4 passou novamente **72/72**. Esses resultados são de escopo diferente e não significam integração nem aprovação de design.

**Recomendação central:** o servidor deve produzir e validar um plano de seleção determinístico, apresentar as mesmas opções/métricas ao cliente, revalidar a submissão contra o estado atual e resolver a ação numa working copy. `applied`, `partial`, `blocked`, `consumed_no_effect` e `rejected` devem ser outcomes distintos. Custos de turno, fonte, ativação e carga de proteção devem ser declarados separadamente por efeito.

## 2. Evidências observadas no legado

### 2.1 Seleção de alvos

- A identidade física não está presente nas opções públicas do seletor: o resumo expõe `id`, nome, poder, bônus, fileira, escudo e estados, mas não `instance_id`/`exemplar_id`. Quando duas cópias compartilham o mesmo ID de modelo, a UI pode exibi-las separadamente, mas o backend resolve a primeira cópia elegível; a escolha da segunda não é inequívoca.
- O campo legado `target_id` é sobrecarregado: recebe ID de alvo e também escolha de modo em Noite/Chama. Isso deve ser separado em `target_instance_id` e `choice_id`.
- O servidor publica opções de relíquia, mas `site/app.js` reconstrói candidatos a partir do board do oponente e filtra fileira localmente, em vez de consumir a lista fornecida pelo servidor. O motor revalida a fileira na submissão, mas a origem de verdade da UI e do backend diverge.
- A Execução valida elegibilidade por poder efetivo, mas o seletor exibe poder-base + bônus. A Lágrima Sagrada valida por poder-base, mas também exibe poder-base + bônus. A interface deve exibir claramente a métrica real usada na regra.
- O motor possui fallbacks automáticos diferentes por efeito. Lágrima Sagrada usa o último candidato elegível na ordem do descarte; Réquiem seleciona maior poder-base; Execução seleciona menor poder efetivo na fileira escolhida; Égide seleciona maior poder efetivo entre aliados protegíveis; Passo seleciona menor poder efetivo, enquanto seu alvo secundário legado é obtido pela ordem original do board. Não existe regra universal `automático`.
- A seleção de múltiplos alvos mistura `manual + auto-fill` no legado: Égide e Passo solicitam um alvo manual e escolhem outro automaticamente. A interface não antecipa o segundo alvo.
- A raridade altera a cardinalidade de alvos da Égide e do Passo no legado. Isso é evidência de incompatibilidade com BUF-001 aprovado: no novo sistema, raridade não pode alterar quantidade de alvos. A quantidade precisa ser parâmetro explícito do efeito/release.
- Efeitos de até dois alvos podem funcionar com apenas um alvo disponível, como o caso de Morgott. Logo, `maximum_targets` não equivale a `minimum_targets`.

### 2.2 Escopo e ordenação

- Os predicados consultam a fileira atual (`current_row`), não a fileira impressa/original, quando a política é limitada à fileira.
- O motor usa métricas distintas: poder efetivo, poder-base e bônus bruto. Exemplo: Cisalhamento Gravitacional filtra bônus positivo e ordena por bônus bruto; não deve ser convertido para maior poder efetivo.
- Exemplos de seleção global versus fileira: Fenda do Vazio e Gravidade do Flagelo buscam globalmente; Juramento Dourado, Marca da Dinastia, Morgott, Mohg, Astel e Loretta têm escopos de fileira específicos.
- `max()`, `min()` e ordenações estáveis preservam atualmente a primeira ocorrência na ordem do array quando há empate. Essa ordem incidental precisa ser convertida em desempate versionado, respeitando BUF-013 já aprovado: ordem explícita de zona para semântica `first/last`; para métricas, sequência estável de entrada/jogada e `instance_id` como último desempate.
- A ordem de pipeline deve ser explícita: formar candidatos → filtrar lado/zona/fileira/elegibilidade → calcular métrica → ordenar/desempatar → aplicar cardinalidade → tratar ausência/parcialidade → resolver efeitos/custos.

### 2.3 Outcomes e custos

- Alvo inválido, seleção fora de fileira ou ausência de alvo obrigatório pode produzir erro/rejeição sem mutação da entrada, sem consumir a carta-fonte e sem custo de turno.
- Morgott sem alvo elegível é rejeitado e não marca `leader_used`.
- Existem ações aceitas que consomem fonte e turno sem alterar alvos: Chama sem aliado com Geada; Muralha em fileira vazia; Algemas de Margit em alvo com bônus zero. Esses exemplos são `consumed_no_effect`, não `rejected`.
- Bloqueio por proteção é um resultado aceito, diferente de rejeição. Execução bloqueada consome a carta especial e o turno e consome uma carga de escudo, mas mantém o alvo no campo.
- Lâmina Negra bloqueada consome a carga do escudo e o turno, mas não consome a ativação de uso único da relíquia (`relic_used` permanece falso).
- Noite/Chama bloqueada consome a carga do escudo, a ativação da relíquia e o turno. Essa diferença deve permanecer como configuração específica do efeito, alinhada à regra C aprovada.
- Uma ação em área pode produzir resultados mistos: um alvo bloqueado e outro afetado. Resultado agregado deve ser `partial`, com resultado individual por alvo.
- O endpoint atual executa o resolver dentro de `Database.transaction()` (`BEGIN IMMEDIATE`) e só grava o novo `state_json` quando o resolver não retorna erro. Isso demonstra atomicidade local naquele caminho, não idempotência durável, replay seguro ou CAS entre processos.
- A API não recebe `operation_id` nem `expected_revision`; o bloqueio de clique no browser é apenas proteção local. Idempotência persistente, revisão, conflito e serialização concorrente continuam pertencendo ao Grupo E.

### 2.4 Proteção com múltiplas concessões

O contrato v0.4 já representa `protection_grants[]`, mas não define como escolher entre vários grants compatíveis. A proposta abaixo recomenda seleção determinística baseada no evento de aplicação, e não na ordem incidental do array JSON. Só grants ativos, com carga positiva e perfil compatível podem ser candidatos.

## 3. Modelo proposto para aprovação

### 3.1 Request de ação

O novo request separa:

- `operation_id`: ação lógica idempotente (Grupo B aprovado);
- `expected_revision`: revisão do estado que fundamentou a oferta/seleção (enforcement transacional real continua Grupo E);
- `source_instance_id`: instância-fonte quando houver;
- `selection.mode`: `none`, `manual_single`, `manual_set`, `automatic` ou `manual_primary_auto_fill`;
- `target_instance_id`/`target_instance_ids`: identidade física dos alvos;
- `choice_id`: escolha de modo/variante, nunca reutilizada para identidade de alvo;
- `target_row`: fileira solicitada quando a política exigir.

O cliente não escolhe `target_policy_id` nem define a métrica: a política vem do snapshot de definições imutável da partida.

### 3.2 Política declarativa por efeito

Cada efeito com seleção deve declarar, no release versionado:

- lado e zona dos alvos;
- escopo de fileira e base (`current_row` quando aplicável);
- predicados de elegibilidade parametrizados;
- métrica de elegibilidade/exibição e métrica de ordenação, que podem ser diferentes;
- direção e desempate;
- modo de seleção e cardinalidade (`exact`, `up_to`, `all_matching`, com mínimo e máximo separados);
- fallback e comportamento sem alvo;
- política para conjunto parcial;
- política de proteção e custos.

Predicados devem ser identificadores versionados de regras, não expressões arbitrárias fornecidas pelo cliente. O servidor gera as ofertas, prévia de alvos secundários e valores explicativos; o cliente só apresenta. Na submissão, o servidor revalida a revisão, a identidade, a zona, a fileira, a elegibilidade e o limite.

### 3.3 Cardinalidade e seleção manual

- `exact`: exige exatamente o número definido.
- `up_to`: exige no mínimo `minimum_targets` e aceita qualquer quantidade até `maximum_targets`.
- `all_matching`: seleciona todos os candidatos que passam nos predicados; qualquer cap adicional precisa ser explícito.
- `maximum_targets` não implica mínimo igual ao máximo. Um efeito `up_to 2` com mínimo 1 pode ser aplicado a um único alvo.
- `manual_set` é preferível quando a escolha dos alvos múltiplos é uma decisão relevante do jogador.
- Se o design mantiver `manual_primary_auto_fill`, a prévia dos alvos secundários automáticos deve ser mostrada antes da confirmação. Não deve existir alvo secundário oculto.
- A quantidade de alvos deve vir de parâmetro explícito; jamais de raridade (BUF-001 aprovado).

### 3.4 Fallback, ausência de alvo e parcialidade

Não existe fallback universal. Cada efeito escolhe uma política:

- `reject`: tentativa inválida; não há commit, custo, evento de domínio nem consumo de fonte/turno.
- `consume_no_effect`: tentativa válida conforme o contrato do efeito; consome somente os custos declarados e grava evento/outcome mesmo sem alteração de alvo.
- `fallback`: executa fallback nomeado no próprio efeito, com critérios também declarados.

Recomendação para revisão das cartas: efeitos com vítima obrigatória, como Execução e Réquiem sem alvo válido, devem rejeitar; Algemas deve exigir bônus positivo e rejeitar quando não houver vítima qualificada; Noite/Chama e Muralha devem declarar explicitamente se o no-op é intencional ou se devem rejeitar. Fallbacks explícitos como Regressão Serena permanecem definidos pelo contrato específico, não por regra global. RSRX-02 (Devorar) precisa definir a ausência de sacrifício elegível antes de congelar a política.

Para seleção múltipla, o plano deve satisfazer o mínimo antes da aplicação. `up_to` com um de dois disponíveis e mínimo 1 é `applied`, não `partial`. `partial` é apropriado quando o mesmo plano válido gera outcomes mistos por alvo (por exemplo, um bloqueado e outro aplicado), ou quando o contrato permite aplicação parcial acima do mínimo. Abaixo do mínimo, aplica-se fallback ou rejeita-se a operação conforme o efeito.

### 3.5 Outcomes e custo multidimensional

Outcomes agregados propostos:

- `applied`: todos os alvos planejados foram afetados conforme a regra;
- `partial`: resultados mistos/parte dos alvos aplicada conforme política permitida;
- `blocked`: todos os alvos relevantes foram bloqueados por proteção compatível;
- `consumed_no_effect`: operação aceita e seus custos declarados foram consumidos, mas nenhum alvo mudou;
- `rejected`: validação falhou; não há commit de gameplay.

Cada alvo registra `applied`, `blocked` ou `skipped`. `rejected` é outcome da operação, não de um alvo individual. `conflict` por revisão obsoleta/idempotência pertence à camada transacional Grupo E e não é outcome de regra de jogo.

Custos independentes:

1. custo de turno;
2. consumo da carta/unidade-fonte;
3. consumo da ativação do líder/relíquia;
4. carga(s) de proteção consumida(s);
5. outros custos explicitamente nomeados.

Rejeição não consome custos. Bloqueio e no-op podem consumir custos conforme a política do efeito. Manter as exceções aprovadas do Grupo C: Noite/Chama consome ativação quando bloqueada; Lâmina Negra não; ambas consomem turno e carga de proteção no caso auditado.

### 3.6 Escolha de grants de proteção

Proposta: selecionar entre grants compatíveis com o perfil/categoria do evento, ativos e com `charges_remaining > 0`, por `applied_event.sequence` ascendente (mais antigo primeiro); em empate, `grant_id` lexicográfico ascendente. O consumo altera exatamente um grant e gera evento próprio. A ordem do array não participa da decisão. Se o balanceamento precisar de prioridade por perfil, ela deverá estar no release versionado do perfil, não implícita na implementação.

### 3.7 Plano atômico

A resolução lógica deve seguir duas fases:

1. **Planejar:** validar fase/turno/fonte, revisão, escolha, todos os alvos, cardinalidade, predicados, desempates, grants de proteção e custos. Produzir um plano imutável sem mutação.
2. **Resolver/commit:** executar o plano numa working copy, registrar eventos e custos, validar invariantes e então publicar o novo estado como um único resultado aceito.

Se ocorrer falha inesperada durante a resolução, descartar a working copy inteira. `blocked` e `consumed_no_effect` são outcomes aceitos e fazem commit quando houver custo/evento declarado. A transação persistente, CAS, idempotência em retry e concorrência entre processos não são resolvidas neste Grupo D; permanecem Grupo E.

## 4. Decisões propostas e dependências

As decisões estruturadas estão em `docs/card-game-selection-group-D-decisions-v0.1.json`. Todas permanecem `PENDING_OWNER_APPROVAL`.

| ID | Tema | Dependências |
|---|---|---|
| DSEL-DEC-001 | Separar identidade de alvo e escolha de modo | CI-010, Grupo A |
| DSEL-DEC-002 | Oferta server-authoritative e revalidação | CI-010, CI-011 |
| DSEL-DEC-003 | Política declarativa por efeito | BUF-003/004/005/006 |
| DSEL-DEC-004 | Cardinalidade explícita, sem raridade | BUF-001 aprovado, BUF-013 aprovado |
| DSEL-DEC-005 | Seleção manual/múltipla e prévia de secundários | CI-010, BUF-013 |
| DSEL-DEC-006 | Fallback e ausência de alvo por efeito | RSRX-01/02/06; revisão de cartas |
| DSEL-DEC-007 | Outcomes por alvo e por operação | CI-011 |
| DSEL-DEC-008 | Custos independentes por dimensão | Grupo C aprovado; BUF/RSRX |
| DSEL-DEC-009 | Desempate de grants de proteção | CI-008/009, BUF-009/010 |
| DSEL-DEC-010 | Planejamento e commit lógico atômico | CI-011; persistência real no Grupo E |
| DSEL-DEC-011 | Revisão/idempotência no request | CI-014/Grupo E; request candidato apenas |
| DSEL-DEC-012 | Métrica exibida e prévia da UI derivadas do servidor | CI-010, CI-011 |

**Importante:** BUF-013 já está aprovado no Grupo A. DSEL-DEC-004 e DSEL-DEC-005 o aplicam, não o reabrem. CI-014 não é encerrado aqui; apenas se define o contrato candidato que o Grupo E deverá persistir.

## 5. Limites e não decisões

- Não se alterou código funcional para fazer desaparecer comportamentos legados dependentes de raridade; a proibição aplica-se ao novo sistema por BUF-001 aprovado.
- Não foram congelados parâmetros finais de quantidade para Égide/Passo nem todas as regras de target count de cartas; isso pertence ao balanceamento/release do efeito.
- Não foram aprovadas globalmente as políticas `reject` versus `consume_no_effect`; cada efeito precisa de decisão no registry/carta.
- Não foi fechada a ausência de alvo para Devorar (RSRX-02), as causas de Vingança (Grupo F) nem a semântica final de custos de todas as cartas.
- Não foi implementada idempotência, CAS, controle de revisão ou concorrência real; Grupo E.
- Os schemas/request/result são candidatos para revisão, não contrato congelado nem API implementada.

## 6. Validações e integridade

- Auditoria Grupo D: 23/23;
- seleção/alvos por escopo e fileira: 15/15;
- paridade manual/UI: 12/12;
- CardInstance v0.4: 72/72.

As fixtures chamam funções reais do legado e fazem algumas verificações estáticas em API/frontend/DB/schema. Não são teste de browser real, rede, persistência concorrente, replay, integração ou produção. A validação de schemas/fixtures candidatos é separada da auditoria comportamental.

**Runtime:** nenhuma alteração em `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, catálogo ativo ou resolvedores. Todos os artefatos desta revisão ficam em `docs/`.

## 7. Próximo gate

Solicitar aprovação/ajuste das 12 propostas DSEL-DEC-001..012. Após aceite, elaborar `CardInstance v0.5` draft integrando request, políticas, outcomes e custos. Grupo F (causas de remoção/Vingança) e Grupo E (persistência concorrente/migração) permanecem gates próprios. Não integrar o runtime nem iniciar migrador antes de fechar esses grupos e testar persistência real.
