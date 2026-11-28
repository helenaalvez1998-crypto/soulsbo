# Aprovação do Grupo A — identidade física v0.1

**Data do registro:** 2026-11-27  
**Baseline revisado:** `soulsbo-main-continuity-2026-11-27-rev6.zip`  
**Status:** `APPROVED_BY_OWNER`  
**Evidência de aprovação:** resposta do proprietário `ok, continue`, enviada imediatamente após a pergunta explícita: “Podemos seguir com a aprovação do Grupo A?”.

## 1. Escopo da aprovação

A aprovação cobre as oito propostas exatamente como apresentadas em `docs/card-game-identity-group-A-decision-review-v0.1.md`, incluindo a correção de CI-004 baseada no DDL atual de `cartas_exemplares`:

| ID | Decisão aprovada | Regra aprovada |
|---|---|---|
| CI-001 | Identidade por ocorrência | `instance_id` UUIDv4 canônico, gerado no servidor, imutável durante a vida da ocorrência. |
| CI-002 | Unicidade dentro da partida | Unicidade global entre participantes e zonas; cada ocorrência aparece em exatamente uma zona no snapshot estável. |
| CI-003 | Identidade de modelo separada | Várias instâncias podem compartilhar `card_id`; a regra atual do deck builder de 12 modelos distintos permanece inalterada. |
| CI-004 | Proveniência de coleção | `exemplar_id` referencia a PK global atual `cartas_exemplares.id`; validar existência, `user_id`/proprietário e `card_id`; não inferir nem reutilizar. |
| CI-006 | Tokens e relíquias | Tokens materializados recebem `instance_id`; relíquia equipada fica fora das zonas; ativação é preferencialmente evento/ordem. Se materializada como carta transitória, recebe instância própria e `exemplar_id=null`. |
| CI-010 | Seleção física | Selecionar por `target_instance_id`; seleção múltipla usa `target_instance_ids` sem repetição. Adaptador legado só resolve uma correspondência elegível única; zero ou múltiplas correspondências são rejeitadas. |
| BUF-013 | Ordem e desempate | Ordem persistida das zonas define first/last; seletores por métrica declaram desempate, com padrão compatível por ordem de zona e `instance_id` como fallback técnico. |
| RSRX-09 | Remoção e retorno | Remoção, recuperação, sacrifício e ressurreição operam sobre ocorrências físicas exatas, não sobre `card_id` em massa. |

## 2. Limites explícitos

A aprovação do Grupo A **não** aprova decisões dependentes ou grupos ainda abertos:

- CI-005/007/008/009/011/012/013/014 permanecem em revisão, conforme suas fontes.
- BUF-001…BUF-012 e BUF-014 permanecem pendentes; BUF-013 está aprovado somente nos limites acima.
- As demais decisões RSRX permanecem pendentes; RSRX-09 está aprovado somente nos limites acima.
- Não aprova políticas de duração/limpeza de bônus, escudos, estados ou resistência climática.
- Não aprova causalidade de eventos, amplificação por raridade, custos, fallback parcial ou regras de consumo.
- Não aprova alteração do banco, API, frontend, catálogo ativo, migrador ou runtime legado.
- Não altera a regra atual de composição dos decks.

## 3. Consequência documental

O Grupo A pode ser tratado como fechado para fins de identidade e como fundamento da revisão `CardInstance v0.2`. A especificação v0.2 continua **rascunho não congelado**, pois deve preservar marcadores provisórios para as decisões B/C/D/E/F ainda abertas.

A aprovação não foi inferida de um silêncio ou de um teste técnico: ela decorre da resposta afirmativa do proprietário à pergunta explícita de aprovação. Nenhuma regra fora das oito linhas acima foi incluída no escopo.

## 4. Guardrail permanente

O runtime legado continua intacto. Não iniciar migração de partidas nem integrar `CardInstance` ao motor em produção enquanto os contratos dependentes e os testes de persistência/atomicidade não estiverem fechados.
