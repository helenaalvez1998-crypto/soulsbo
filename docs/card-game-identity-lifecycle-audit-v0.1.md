# Auditoria de identidade física e ciclo de vida de unidades v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev2.zip`  
**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`  
**Resultado direcionado:** 17/17 assertions aprovadas; zero falhas.  
**Integração:** nenhuma. O motor legado, o catálogo ativo, persistência, API e frontend não foram alterados.

## 1. Objetivo e limites

Esta etapa verifica como uma unidade é identificada e transportada entre mão, campo e descarte, especialmente em remoção, recuperação para a mão e retorno ao campo. O foco é separar identidade do modelo, exemplar da coleção e instância física da partida.

A evidência vem de leitura estática das funções do runtime e fixtures sintéticas que exercitam o motor legado e o resolvedor candidato isolado. Não houve acesso a SQLite real, HTTP, Discord, navegador, R2 ou partidas de produção. Não se afirma que existam atualmente decks persistidos com IDs duplicados.

**Interpretação dos testes:** um caso aprovado significa que a afirmação comportamental foi reproduzida. Alguns casos aprovam deliberadamente ao confirmar uma lacuna ou um risco; isso não significa que o comportamento observado seja desejável ou aprovado como regra de design.

## 2. Identidade: três níveis distintos

| Campo | Papel correto na modelagem | Situação observada |
|---|---|---|
| `card_id` / `id` de catálogo | Identifica o modelo/definição da carta | É a chave usada pela maioria dos seletores do runtime legado. |
| `exemplar_id` | Identifica um exemplar pertencente à coleção do jogador | O deck salva esse vínculo, mas o caminho padrão de preparação descarta o campo do payload de partida. Cartas pessoais geradas preservam `exemplar_id` e montam um `id` composto. |
| `instance_id` | Identifica uma ocorrência física única dentro de uma partida | O runtime legado não o gera nem o exige. `novo_estado()` copia o deck recebido sem atribuir identidade de partida. |

### 2.1 Caminho de cartas padrão

`_api_gwent_deck_save()` exige exatamente 12 entradas e 12 `card_id` distintos. O endpoint também resolve o exemplar escolhido e persiste `card_ids_json` e `exemplar_ids_json` alinhados.

`_gwent_deck_snapshots()` reconstitui o exemplar correspondente e injeta `payload["exemplar_id"]`, mas chama `preparar_carta()`. O retorno de `preparar_carta()` inclui `id` do modelo, mas não inclui `exemplar_id` nem `instance_id`. Portanto, o vínculo com o exemplar deixa de estar presente no objeto padrão que segue para a partida.

O carregador do snapshot valida que o resultado contenha 12 cartas, mas não repete `len(set(ids)) == 12`. Assim, um deck antigo ou malformado com modelos repetidos pode passar pela verificação de contagem. Isso é um risco de compatibilidade demonstrado por inspeção da função; não é evidência de que algum registro real esteja assim. A rota atual de gravação continua bloqueando novos decks desse tipo.

### 2.2 Caminho de cartas pessoais

`preparar_carta_pessoal()` preserva `card_id` e `exemplar_id` e define `id` de runtime no formato `card_id::exemplar_id`. Esse composto diferencia exemplares da carta pessoal neste caminho, mas ainda não é um identificador universal de instância por partida: não é criado para todas as cartas e não substitui `instance_id`.

### 2.3 Seleção e transporte pela interface

`_resumo_alvo()` serializa `id`, nome, poder, bônus, fileira, escudo e estados; não expõe `exemplar_id` ou `instance_id`. O frontend envia `target_id` com o `id` selecionado. Quando mais de uma ocorrência tiver o mesmo `id`, o protocolo não permite ao usuário distinguir fisicamente as cópias. O relatório anterior de paridade UI/alvo já demonstrou a colisão na seleção.

## 3. Comportamento legado do ciclo de vida

| Operação | Destino | Campos observados | Risco / ressalva |
|---|---|---|---|
| Remoção bem-sucedida via `_remover_unidade()` | Descarte, mesmo objeto em memória | Remove escudo; zera Sangramento, Geada, Podridão e Loucura; preserva `bonus`, `weather_resist` e `combo_ativado`. | `board.remove(unit)` usa igualdade estrutural de dicionários. Com cópias iguais, pode retirar outro objeto e depois anexar o objeto pedido ao descarte, deixando a mesma referência simultaneamente no campo e no descarte. |
| Remoção bloqueada por escudo | Continua no campo | Consome uma carga e retorna sem descartar. | Não é uma mudança de zona; não deve gerar uma nova identidade. |
| Fim de rodada — unidade arquivada | Descarte via `deepcopy` | Zera bônus, escudo e os quatro estados; remove `combo_ativado`; preserva `weather_resist` e quaisquer identificadores presentes no dicionário. | A unidade no descarte é uma cópia; o runtime não valida unicidade de identidade ao arquivar. |
| Glória — unidade que permanece | Continua no campo via `deepcopy` | Zera bônus, escudo e os quatro estados; remove `combo_ativado`; preserva `weather_resist`. | Mesmo comportamento de normalização temporária do fim de rodada, mas permanece em campo. |
| Lágrima Sagrada (`gwent_medico`) | Mão | Remove a carta elegível do descarte e anexa o mesmo objeto à mão; preserva o bônus e os demais campos que chegaram ao descarte. | No fluxo normal de remoção, escudo/estados já foram limpos pela remoção central, enquanto o bônus permanece. O efeito não faz normalização adicional. A carta especial usada vai para o descarte; por isso, a validação deve procurar a unidade recuperada, não esperar que o descarte fique vazio. |
| Réquiem (`gwent_requiem`) | Campo | Remove uma carta elegível, copia-a, zera `bonus`, remove escudo e preserva `row` se válida; caso contrário usa a fileira escolhida. | Não zera explicitamente os quatro estados nem `weather_resist`. Estados residuais foram reproduzidos apenas com fixture deliberadamente obsoleta; a remoção central e o fim de rodada limpam os quatro estados nos caminhos normais conhecidos. |
| Ressurgir (`ressurgir`) | Campo, como entrada adicional da jogada | Escolhe maior poder-base elegível; copia; zera `bonus`; remove escudo; mantém `row` válida ou usa a fileira escolhida. | Também não zera explicitamente os quatro estados nem `weather_resist`. A limpeza ausente só foi demonstrada com registro obsoleto sintético. A unidade ressuscitada é adicionada após a resolução principal de combo/on-play daquela jogada. |
| Esgar (`voz_caidos`) | Campo | Escolhe a unidade elegível mais forte até poder-base 5; força a fileira escolhida; soma +1 ao bônus preexistente; remove escudo e zera os quatro estados. | Remove do descarte **todas** as entradas cujo `id` seja igual ao da escolhida, em vez de retirar um exemplar exato. `weather_resist` é preservado. |

### 3.1 Risco reproduzido em `_remover_unidade()`

O teste cria dois dicionários distintos com conteúdo inicialmente igual. Ao solicitar a remoção do segundo, a operação `list.remove()` encontra o primeiro dicionário estruturalmente igual, pois a seleção não usa identidade de objeto nem uma chave física. Em seguida, a função anexa o segundo objeto ao descarte. O resultado é que o objeto solicitado continua no campo e passa a aparecer também no descarte, enquanto o primeiro objeto igual é removido.

Isso não prova que decks válidos atuais gerem esse caso: a rota atual exige modelos distintos. Demonstra, porém, que o contrato de remoção é frágil diante de snapshots antigos/malformados, duplicações criadas por outros fluxos ou futuros efeitos que permitam cópias do mesmo modelo.

## 4. Resolvedor candidato: acertos e lacunas

O módulo isolado `sistemas/card_removal_resurrection_candidate.py` melhora parte da semântica:

- `attempt_removal()` localiza a unidade por identidade de objeto (`is`) e remove o índice exato; não depende da igualdade estrutural do dicionário.
- `resurrect_from_discard()` pode resolver `target_instance_id`; exige que esse identificador corresponda a exatamente uma unidade elegível no descarte.
- `resurrect_from_discard()` torna explícitos o modo de bônus (`reset_to_zero`, `add_one_to_existing_bonus`, `preserve`) e a política de fileira (`preserve_if_valid_else_fallback`, `force_selected_row`). Também normaliza escudo e os quatro estados.
- `recover_unit_to_hand()` seleciona e move uma unidade para a mão sem normalização, preservando a semântica do legado.

Lacunas restantes reproduzidas:

1. `attempt_removal()` não verifica colisões globais de `instance_id`. Foi possível deixar a mesma identidade no campo e no descarte.
2. `resurrect_from_discard()` verifica ambiguidade de `instance_id` apenas entre as unidades elegíveis do descarte. Não verifica se o mesmo `instance_id` já existe na mão, campo, pilha ou zona do oponente; foi possível ressuscitar uma segunda ocorrência do mesmo identificador.
3. O candidato não exige `instance_id` em todas as entradas. A identidade auxiliar `_card_identifier()` ainda pode recorrer a `id` do modelo.
4. A unicidade do identificador físico ainda não faz parte de um envelope global de estado da partida nem de uma validação de zonas.

O resolvedor candidato permanece isolado e não é importado pelo runtime legado.

## 5. Requisitos candidatos para a especificação futura

As recomendações abaixo são requisitos propostos para revisão, não decisões aprovadas:

1. **Separar modelo, exemplar e instância.** Manter `card_id` como modelo; manter `exemplar_id` como vínculo de coleção; criar `instance_id` novo, opaco e imutável para cada ocorrência da partida.
2. **Atribuir antes da primeira zona.** Criar o `instance_id` durante a construção do snapshot de partida, antes de distribuir cartas entre mão e pilha. O identificador deve sobreviver a movimento, descarte, retorno à mão, ressurreição e cópia de estado.
3. **Validar unicidade global.** Em cada transição, garantir que um `instance_id` apareça em exatamente uma zona, dentre mão, pilha, campo e descarte de ambos os jogadores. Exceções temporárias devem ser representadas explicitamente, não por duplicação silenciosa.
4. **Selecionar por identidade física.** A UI deve enviar `target_instance_id`; servidor deve resolver uma ocorrência única e rejeitar ausência/ambiguidade. `target_id` pode permanecer apenas como compatibilidade temporária quando houver uma única ocorrência elegível.
5. **Remover por índice/identidade.** Não usar `list.remove()` sobre dicionários de carta como mecanismo de seleção física. O resolvedor deve localizar a instância e alterar uma zona de forma atômica.
6. **Declarar política de entrada por destino.** Retorno à mão, ressurreição e recuperação de líder devem declarar, por efeito, quais campos preservam, zeram ou recalculam. A política não deve ficar implícita em cópias rasas/profundas ou no fato de uma unidade ter sido removida por um caminho específico.
7. **Definir duração de `weather_resist`.** A auditoria confirma que sobrevive à remoção e ao fim da rodada. A duração correta permanece decisão de design e deve ser registrada junto aos demais efeitos temporários/permanentes.
8. **Manter a semântica de ausência/duplicidade visível.** Nenhum seletor automático deve silenciosamente escolher uma cópia arbitrária quando o payload manual é ambíguo; o fallback precisa ser declarado por efeito.

### Proposta de envelope de instância (ilustrativa, ainda não aprovada)

```json
{
  "instance_id": "match-opaque-unique-id",
  "card_id": "modelo_canonico",
  "exemplar_id": 123456,
  "owner_id": "player-id",
  "zone": "hand",
  "state": {
    "row": "melee",
    "bonus": 0,
    "shield": 0,
    "statuses": {}
  }
}
```

O envelope serve apenas para mostrar a separação de identidade. Não é uma proposta de schema final: os nomes, estados, fronteiras de persistência e política de proprietário ainda precisam ser decididos em conjunto com o contrato canônico.

## 6. Evidência e regressões reexecutadas

### Auditoria direcionada — 17/17

- Seis verificações de gravação/carregamento de deck, preparação de cartas, inicialização e resumo de alvo.
- Sete verificações do ciclo de vida legado: igualdade estrutural na remoção, limpeza parcial, fim de rodada, Lágrima Sagrada, Réquiem, Ressurgir e Esgar.
- Quatro verificações do resolvedor candidato: remoção exata, colisão no campo/descarte, colisão entre zonas na ressurreição e rejeição de identificador ambíguo no descarte.

Script reproduzível: `docs/scripts/audit-card-identity-lifecycle-v0.1.py`  
Resultado estruturado: `docs/card-game-identity-lifecycle-audit-v0.1.json`  
Execução: `python docs/scripts/audit-card-identity-lifecycle-v0.1.py` a partir da raiz do repositório.

### Regressões direcionadas executadas nesta etapa

| Suite | Resultado |
|---|---:|
| Identidade e ciclo de vida | 17/17 |
| Paridade de seleção manual/UI/alvo | 12/12 |
| Seleção de alvos e escopo de fileira | 15/15 |
| Buffs, movimentação e proteção | 14/14 |
| Sequência (`last_row`) | 10/10 |
| Remoção/ressurreição candidato + evidência legada | 49/49 |
| Mapeamento de identidade | 33/33 |
| Efeitos de ciclo de vida | 7/7 |
| Estados negativos candidato | 41/41 |
| Catálogo de efeitos candidato | 23/23 |

As suítes possuem escopos diferentes e não devem ser somadas como uma única cobertura. Todos os testes direcionados usam fixtures sintéticas ou validações estáticas; nenhum resultado afirma que um estado equivalente exista em banco/produção.

## 7. Arquivos e integridade

Arquivos novos:

- `docs/card-game-identity-lifecycle-audit-v0.1.md`
- `docs/card-game-identity-lifecycle-audit-v0.1.json`
- `docs/scripts/audit-card-identity-lifecycle-v0.1.py`

Arquivos de continuidade atualizados:

- `docs/README-PACOTE-CONTINUIDADE.md`
- `docs/card-game-handoff.md`
- `docs/PACOTE-MANIFESTO.md`

Nenhum arquivo de runtime, catálogo, schema, banco, API ou frontend foi modificado. A auditoria não aprova o resolvedor candidato, não fecha as decisões BUF-001…BUF-014 nem as decisões de remoção/ressurreição, e não autoriza substituição do motor antigo.

## 8. Continuidade após esta auditoria

A especificação candidata de `CardInstance` e as transições de zona foi produzida em `docs/card-game-card-instance-contract-v0.1.md`. A etapa seguinte é revisar CI-001…CI-013 antes de qualquer implementação. A auditoria original recomendava consolidar os seguintes pontos: matriz de zonas, invariantes de unicidade, regras de criação e persistência do `instance_id`, payload de seleção, idempotência das transições e política de limpeza/preservação de cada campo em Lágrima Sagrada, Réquiem, Ressurgir, Esgar, Glória, remoção e fim de rodada.

Em paralelo, revisar as decisões pendentes BUF e RSRX que dependem da duração de bônus, escudos, estados e resistência climática. Só depois de aprovação explícita dessas regras faz sentido adaptar o resolvedor candidato e planejar sua integração gradual. O motor antigo permanece preservado.
