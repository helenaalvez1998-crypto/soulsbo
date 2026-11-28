# Política oficial de resolução de combos — v0.1

**Status:** aprovada pelo usuário em 2026-11-27 e implementada no runtime desta revisão.  
**Arquivo funcional:** `sistemas/gwent.py`.  
**Resolvedor:** `_aplicar_combo_de_cartas()`.  
**Catálogo:** `SYNERGY_COMBOS`; tags por carta em `CARD_SYNERGY_TAGS`.  
**Regressões:** `docs/scripts/assert-combo-policy-v0.1.py`; resultado em `docs/card-game-combo-policy-assertions-v0.1.json`.

## 1. Regras aprovadas

1. **Participação obrigatória:** a carta recém-jogada só pode receber o bônus individual de um combo se possuir pelo menos uma das tags exigidas por aquele combo específico. Ter qualquer tag de sinergia não basta.
2. **Dois participantes distintos:** todos os combos exigem no mínimo duas instâncias distintas de unidades participantes. Uma unidade que possua duas ou mais tags exigidas conta como apenas um participante. Repetir a mesma referência de objeto não cria um segundo participante.
3. **Um combo por jogada:** uma chamada do resolvedor concede no máximo um combo. Os combos restantes que já estejam elegíveis continuam pendentes.
4. **Prioridade explícita:** cada definição possui `priority`, um inteiro único. O menor número tem precedência. A escolha não depende da ordem incidental de inserção do dicionário Python.
5. **Retomada de combo pendente:** uma jogada posterior pode ativar um combo pendente somente se a carta recém-jogada também contribuir com pelo menos uma tag requerida por esse combo. Uma carta sem relação com as tags específicas não pode recolher o bônus pendente.
6. **Destinatário do bônus individual:** o bônus individual é concedido à carta recém-jogada que participa do combo por tag. Essa regra também vale ao ativar um combo que havia ficado pendente após uma jogada anterior.
7. **Bônus de equipe preservado:** quando uma definição tem `team_bonus`, ele é aplicado aos aliados que já estavam no tabuleiro na mesma fileira da carta que ativa o combo. Aliados em outras fileiras não recebem esse bônus. A semântica existente foi preservada.
8. **Limite por rodada:** cada combo continua podendo ser usado uma vez por jogador por rodada, com controle em `player["synergy_used"]`; `_resolve_round()` reseta esse mapa no início da nova rodada.

## 2. Contrato de ativação

Para uma carta recém-jogada `C` e um combo `K`, a ativação exige simultaneamente:

- `tags(C) ∩ required_tags(K) != ∅`;
- `required_tags(K) ⊆ união das tags das unidades no tabuleiro + tags(C)`;
- quantidade de instâncias distintas, entre tabuleiro e `C`, que tenham ao menos uma tag requerida, maior ou igual a `K.minimum`;
- `K` ainda não estar marcado em `player.synergy_used`.

O resolver ordena os candidatos por `(priority ascendente, combo_id)` e aplica apenas o primeiro candidato válido. Os valores de prioridade são únicos, então o segundo item é apenas uma proteção determinística para catálogos futuros inválidos.

`C` é chamado antes de ser anexado ao tabuleiro pelo fluxo normal de `aplicar_jogada()`. A contagem inclui explicitamente o cartão atual e deduplica instâncias por identidade do objeto Python para não contar uma referência repetida duas vezes.

## 3. Prioridades oficiais do catálogo atual

As prioridades iniciais preservam a precedência que o dicionário tinha no baseline, mas agora são metadados explícitos e testados. Uma prioridade menor resolve primeiro.

| Prioridade | ID | Nome | Tags requeridas | Mínimo | Bônus individual | Bônus de equipe |
|---:|---|---|---|---:|---:|---:|
| 10 | `cinzas_fornalha` | Aliança da Árvore Áurea | `cinzas`, `fornalha` | 2 | +2 | 0 |
| 20 | `veu_sombrio` | Caçada da Faca Negra | `veu_sombrio` | 2 | +2 | 0 |
| 30 | `vazio_astral` | Alinhamento Astral | `astral`, `vazio` | 2 | +2 | 0 |
| 40 | `mare_abissal` | Maré Abissal | `abismo` | 2 | +2 | 0 |
| 50 | `juramento_estandarte` | Juramento de Leyndell | `estandarte` | 2 | +1 | +1 |
| 60 | `passos_duas_luas` | Dança da Lua Negra | `duas_luas` | 2 | +2 | 0 |
| 70 | `eco_convergente` | Eco das Pedras Cintilantes | `astral`, `eco` | 2 | +2 | 0 |
| 80 | `chama_dupla` | Chamas do Monte Gelmir | `chama` | 2 | +2 | 0 |
| 90 | `muralha_inabalavel` | Defesa de Leyndell | `muralha` | 2 | +2 | +1 |
| 100 | `banquete_guerra` | Banquete de Sangue | `banquete` | 2 | +3 | 0 |
| 110 | `procissao_fantasma` | Procissão dos que Vivem na Morte | `fantasmas` | 2 | +2 | +1 |
| 120 | `caravana_saqueadora` | Saque da Cidade Eterna | `caravana` | 2 | +2 | 0 |
| 130 | `ritual_runico` | Ritual das Runas | `runico` | 2 | +2 | +1 |
| 140 | `eclipse_voraz` | Eclipse Sanguíneo | `eclipse_voraz` | 2 | +3 | 0 |
| 150 | `rota_peregrina` | Caminho do Maculado | `peregrino` | 2 | +1 | 0 |
| 160 | `juramento_erdtree` | Juramento da Árvore Áurea | `ordem_dourada` | 2 | +2 | +1 |
| 170 | `convergencia_lunar` | Convergência da Lua Negra | `lua_cariana` | 2 | +2 | 0 |
| 180 | `ritual_dinastia` | Ritual do Véu Carmesim | `sangue_mohgwyn` | 2 | +2 | +1 |
| 190 | `v75_juramento_dois_crisol` | Juramento do Crisol e da Graça | `v75_erdtree_oath`, `v75_crucible_guard` | 2 | +2 | 0 |
| 200 | `v75_banquete_hemorragia` | Banquete da Hemorragia | `v75_blood_mark`, `v75_blood_feast` | 2 | +2 | 0 |
| 210 | `v75_convergencia_gelida` | Convergência da Geada Lunar | `v75_frost_lore`, `v75_lunar_paths` | 2 | +2 | 0 |
| 220 | `fe_gloria` | Glória Divina | `fe`, `gloria_divina` | 2 | +2 | 0 |
| 230 | `fe_devocao` | Devoção | `fe`, `devocao` | 2 | +2 | 0 |
| 240 | `fe_evangelho` | Evangelho | `fe`, `evangelho` | 2 | +2 | 0 |
| 250 | `fe_irmandade` | Irmandade Esquecida | `fe`, `irmandade` | 2 | +2 | 0 |
| 260 | `fe_soberania` | Soberania Divina | `fe`, `soberania` | 2 | +2 | 0 |
| 270 | `fe_sacerdos` | Sacerdócio | `fe`, `sacerdos` | 2 | +2 | 0 |

## 4. Correções aplicadas aos dados

- `cinzas_fornalha`, `vazio_astral` e `eco_convergente` receberam `minimum: 2` explícito. Os outros 24 já tinham esse valor; agora os 27 são explícitos.
- Todas as 27 definições receberam uma prioridade única, de 10 a 270, seguindo a precedência anterior do dicionário.
- Descrições que atribuíam o bônus a “quem completa” foram atualizadas para dizer “carta participante que ativa o combo”, refletindo também o caso de um combo pendente.
- As descrições de Aliança da Árvore Áurea, Alinhamento Astral e Eco das Pedras Cintilantes explicitam cartas/unidades distintas.

## 5. Exemplo de sobreposição e combo pendente

1. `chefe_guardiao_cinzas` e `gwent_unidade_baluarte` tornam elegíveis `cinzas_fornalha` e `juramento_erdtree`.
2. `cinzas_fornalha` vence por prioridade 10 contra 160 e é marcado em `synergy_used`.
3. `covenant_irmandade_ferro` tem tag `estandarte`, mas não tem `ordem_dourada`; ele não pode recolher `juramento_erdtree` pendente.
4. Uma futura carta participante que tenha `ordem_dourada` poderá ativar o combo pendente e receber o bônus individual.
5. Se o combo conceder bônus de equipe, os aliados já presentes na mesma fileira da carta ativadora recebem o `team_bonus`.

Apenas um combo é ativado em cada chamada. A regra de prioridade, não a ordem do dicionário, decide o vencedor.

## 6. Validação executada

Script: `docs/scripts/assert-combo-policy-v0.1.py`.  
Relatório: `docs/card-game-combo-policy-assertions-v0.1.json`.

**32/32 assertions passaram**, cobrindo:

- 27 tentativas solo, uma por combo/tag provider;
- contrato do catálogo: 27 mínimos explícitos iguais a 2 e 27 prioridades únicas;
- sobreposição com o dicionário deliberadamente invertido, provando precedência por prioridade explícita e um combo por jogada;
- sequência pendente conhecida, rejeição de carta sem tag requerida e recompensa a uma carta posterior participante;
- deduplicação de uma mesma instância de unidade;
- uma jogada real por `aplicar_jogada(action="play")`, demonstrando que o fluxo principal do motor invoca a política e concede o combo à carta participante.

Também foram reexecutadas as sete suites anteriores (219/219), totalizando 251/251 assertions distribuídas em oito suites. A varredura enumerativa pós-correção está em `card-game-combo-overlap-v0.2.md/.json`.

## 7. Impacto, compatibilidade e limites

- **Runtime alterado:** apenas `sistemas/gwent.py` nesta correção funcional. O campo `priority` e os mínimos ficam no catálogo em memória; não há mudança de schema de banco, API ou formato persistido.
- **Decks salvos:** não precisam de migração: continuam armazenando IDs de carta e exemplar. O validador de deck não foi modificado.
- **Partidas persistidas:** `state_json` guarda bônus já aplicados e `synergy_used`. Não há retroatividade: bônus de combos já concedidos em uma partida ativa não são removidos automaticamente. A política nova vale para jogadas resolvidas após a atualização do processo. Para partidas em andamento, o operador deve decidir entre deixá-las terminar sob estado misto ou encerrá-las/reiniciá-las em uma janela controlada; o ZIP não contém o DB de produção para executar essa decisão.
- **Apresentação:** descrições de combos preparadas pelo motor agora refletem a nova regra. Arte integral já aprovada não é regenerada automaticamente; não houve alteração de imagens.
- **Balanceamento:** nenhum valor de bônus, EFP, custo de carta, raridade ou orçamento de deck foi calibrado nesta mudança. A prioridade define precedência, não força competitiva.
- **Limites:** os testes usam estados sintéticos em memória. A enumeração de pares/trincas não equivale a uma partida completa de 12 cartas, nem testa API, frontend, Discord, DB de produção, IA ou R2.

## 8. Histórico da alteração

| Arquivo | Trecho/função/campo | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `sistemas/gwent.py` | `SYNERGY_COMBOS` | 27 combos; 3 sem `minimum`; sem prioridade explícita | 27 combos com `minimum: 2` e `priority` único | Formalizar participantes distintos e precedência aprovada | Combos solo deixam de ativar; conflitos têm ordem declarada | Catálogo assertado; 27 tentativas solo bloqueadas |
| `sistemas/gwent.py` | `_aplicar_combo_de_cartas()` | Qualquer tag permitia avaliar qualquer combo; mínimo condicional; ordem do dicionário decidia precedência | Exige contribuição de tag requerida; conta instâncias distintas; ordena por prioridade; um por jogada | Corrigir recompensa para carta não participante e dependência de ordem incidental | Muda bônus futuros em partidas; preserva `synergy_used` e `team_bonus` | 32 testes da política; 87 testes combo/facção; auditoria pós-correção |
| `sistemas/gwent.py` | descrições dos combos | “carta que completa” e descrição solo possível | “carta participante que ativa”; duas cartas explícitas onde aplicável | Alinhar texto com regra de combo pendente e mínimo | Texto preparado em catálogo/API passa a refletir a regra | Comparação estática; não foram regeneradas artes integrais |
| `docs/scripts/assert-combo-policy-v0.1.py` e `docs/card-game-combo-policy-assertions-v0.1.json` | Nova suite | Inexistente | 32 regressões específicas, incluindo chamada pelo ponto de entrada público | Travar a política aprovada contra regressão | Diagnóstico apenas | 32/32 |
| `docs/scripts/audit-combo-overlap-v0.2.py`, `docs/card-game-combo-overlap-v0.2.json/.md` | Nova auditoria pós-correção | Relatório antigo media defeitos do baseline | Nova varredura no runtime corrigido | Comparar antes/depois | Evidência de comportamento pós-patch | 4.422 pares e 287.430 trincas reavaliados |

## 9. Próximos passos

1. Rodar testes de integração de `aplicar_jogada()` com snapshots de partida serializados e desserializados.
2. Testar pelo menos quatro sequências de cartas por facção em partidas completas, incluindo múltiplas sobreposições e reset de rodada.
3. Fazer teste de contrato da API `/api/gwent/cards` e das descrições de combos exibidas no site.
4. Definir política operacional para partidas que já estejam em andamento na produção.
5. Só depois retomar simulação de facções e calibração EFP/custo/raridade.
