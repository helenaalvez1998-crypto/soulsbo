# Auditoria dos 28 ramos antigos de identidade — v0.1

> **STATUS: inventário estático e recomendações; nenhuma remoção foi aplicada.** Os handlers são resíduos/desconexões de catálogo, mas decisões finais devem ser registradas antes da limpeza funcional.

Baseline: `soulsbo-main(1).zip` — 27/11/2026.

## 1. Resultado consolidado

| Métrica | Quantidade |
|---|---:|
| Ramos literais em `_aplicar_habilidade_identidade()` | 50 |
| Efeitos com carta ativa em `CARD_IDENTITY_ABILITIES` | 22 |
| Ramos sem associação ativa | 28 |
| Cartas removidas da associação pelo V18 | 18 |
| IDs antigos presentes em campos de cartas sem handler de identidade ativo | 4 |
| Ramos antigos V75 sem identidade ativa | 6 |
| Cartas com hook oculto `gloria` | 3 |

A decomposição dos 28 ramos sem associação ativa é **18 + 4 + 6**. `gloria` e `sobrevivente` são problemas separados de ciclo de vida, não entram nessa contagem.

## 2. Dezoito identidades filtradas pelo V18

Os 18 IDs abaixo constam no dicionário-fonte original, mas seus card IDs estão em `CARTAS_SEM_EFEITO_IDS`; na carga runtime, a habilidade da carta fica vazia e a associação é filtrada. As tags de combo podem continuar produzindo efeitos, portanto “habilidade individual vazia” não equivale automaticamente a carta pura.

| Card ID | Carta | Efeito antigo | Tags ainda existentes | Pura estrita no runtime? |
|---|---|---|---|---|
| `chefe_cervo_sombrio` | Cavaleiro do Cão de Caça | `shadow_paths` — Passagem Sombria | veu_sombrio | Não |
| `chefe_cacador_sem_rosto` | Assassina da Faca Negra | `faceless_hunt` — Marca da Presa | — | Sim |
| `chefe_vigia_cinzento` | Cavaleiro de Leyndell | `grey_watch` — Vigília Cinzenta | — | Sim |
| `chefe_aparicao_veio` | Lâmina Negra Errante | `veil_shift` — Deslocamento Espectral | veu_sombrio | Não |
| `arma_lamina_peregrino` | Duelista da Casa Hoslow | `pilgrim_duel` — Duelo do Peregrino | peregrino | Não |
| `arma_martelo_fornalha` | Ferreiro de Volcano Manor | `forge_rhythm` — Martelo de Cadência | — | Sim |
| `arma_cajado_marulho` | Feiticeiro Cariano | `tide_resonance` — Ressonância das Marés | — | Sim |
| `arma_agulha_astro` | Leitora de Estrelas de Sellia | `astral_thread` — Fio Astral | astral, lua_cariana | Não |
| `arma_lanca_fornalha` | Lanceiro da Árvore Áurea | `furnace_charge` — Investida da Fornalha | — | Sim |
| `arma_arco_peregrino` | Batedor da Mansão Vulcânica | `covering_shot` — Tiro de Cobertura | peregrino | Não |
| `magia_brasa_errante` | Monge do Fogo | `wandering_ember` — Brasa Persistente | chama | Não |
| `magia_fagulha` | Aprendiz de Feitiçaria Cariana | `conductive_spark` — Faísca Condutora | — | Sim |
| `magia_orbe_eco` | Erudito da Academia | `echo_orb` — Orbe Refrator | eco | Não |
| `magia_chama_fria` | Feiticeira da Lua Gélida | `counterflame` — Contrafogo | chama | Não |
| `covenant_sentinelas` | Guardiões de Sellia | `shared_sentinel` — Sentinela Compartilhada | — | Sim |
| `covenant_ultimos` | Cavaleiros de sangue juramentados | `last_oath` — Último Juramento | — | Sim |
| `covenant_filhos_brasa` | Discípulos do Monge do Fogo | `ember_kin` — Herança da Brasa | — | Sim |
| `covenant_peregrinos_nevoa` | Peregrinos da Cidade Eterna | `mist_trail` — Rastro na Névoa | — | Sim |

**Recomendação:** preservar nome, descrição e efeito no arquivo de legado; remover os ramos e as entradas-fonte apenas depois da decisão `keep/merge/redesign/remove` de cada carta. Se a carta continuar pura, o handler deve sair da execução e as tags que ativam combos também precisam ser examinadas à luz da definição de pureza do usuário. Se o efeito for reativado, a reativação deve ocorrer pelo schema canônico, não por associação paralela oculta.

## 3. Quatro IDs antigos sem mapeamento ativo

Esses ramos existem dentro de `_aplicar_habilidade_identidade()`, mas nenhum ID de carta ativo os encaminha para lá. `habilidade` isoladamente não faz o resolvedor de identidade encontrá-los.

| Efeito | Cartas que ainda carregam o campo | Implementação encontrada | Recomendação |
|---|---|---|---|
| `devoto` | `luterano_bispo` (Bispo Esquecido), `luterano_mistico` (Místico Esquecido) | +1 when at least two allied units of the same faction are already on board. | REWRITE_AS_CANONICAL_EFFECT_OR_CLEAR_CARD_FIELDS |
| `legado` | `luterano_pastor` (Pastor Esquecido) | +2 if the player won the immediately previous round. | REWRITE_AS_CANONICAL_EFFECT_OR_CLEAR_CARD_FIELDS |
| `escolha_ritmo` | Nenhuma carta runtime | Current branch grants +1 unconditionally; comment describes a row choice and persistence that are not implemented here. | REMOVE_OR_REDESIGN; CURRENT_BRANCH_DOES_NOT_IMPLEMENT_THE_TEXTUAL_CHOICE_OR_RETENTION |
| `sinergia_faccao` | `luterano_cruzado` (Cruzado Esquecido), `luterano_papa` (Papa Esquecido), `luterano_profeta` (Profeta Esquecido) | +1 for each allied unit of the same faction. | REWRITE_AS_CANONICAL_EFFECT_OR_CLEAR_CARD_FIELDS |

Observações:
- `devoto`, `legado` e `sinergia_faccao` continuam em seis cartas atuais e não têm metadados em `HABILIDADES` nem mapeamento de identidade ativo; portanto os campos parecem prometer efeitos que não são despachados.
- `escolha_ritmo` não possui referência de campo em carta runtime, não está em `HABILIDADES` e o comentário do ramo descreve escolha/retensão que a implementação não executa.
- Para essas cartas, não basta apagar o código do ramo: é necessário substituir ou limpar o campo `habilidade` e revisar a descrição textual.

## 4. Seis ramos antigos da expansão V75

| Ramo | Card ID atual associado | Carta atual | Texto atual sobre habilidade | Tags |
|---|---|---|---|---|
| `v75_crucible_guard` | `gwent_v75_ordem_guardiao_crisol` | Guardião do Crisol Menor | Não possui habilidade individual. Pode completar combos da Ordem Áurea quando estiver em campo com a unidade compatível. | v75_crucible_guard |
| `v75_golden_standard` | `gwent_v75_ordem_arauto_estandarte` | Arauto do Estandarte Áureo | Não possui habilidade individual. Pode completar combos de formação da Ordem Áurea com a unidade compatível. | v75_crucible_guard |
| `v75_blood_feast` | `gwent_v75_veu_devota_hemorragia` | Devota da Hemorragia | Não possui habilidade individual. Pode completar o combo Banquete da Hemorragia com a unidade compatível. | v75_blood_feast |
| `v75_blood_pursuit` | `gwent_v75_veu_cacador_sangue` | Caçador das Catacumbas de Mohgwyn | Não possui habilidade individual. Pode completar combos de marca de Sangramento com a unidade compatível. | v75_blood_mark |
| `v75_lunar_cartography` | `gwent_v75_lua_cartografo_lunar` | Cartógrafo das Cidades Eternas | Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível. | v75_lunar_paths |
| `v75_moon_ward` | `gwent_v75_lua_guardia` | Guardiã do Juramento Lunar | Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível. | v75_lunar_paths |

**Recomendação:** arquivar e remover os seis ramos antigos após validar os combos/tags correspondentes. As cartas atuais declaram ausência de habilidade individual, mas algumas ainda participam de combos; não remover tags sem recalcular o efeito de deck.

## 5. Hooks de ciclo de vida separados

### `gloria`

`gloria` não é uma entrada de `HABILIDADES` e não é uma identidade. É um hook direto em `_resolve_round()`: quando o jogador vence, a unidade `gloria` mais forte permanece em campo; se perder, vai ao descarte. Há três cartas com esse valor:

- `luterano_anjo` — Anjo Esquecido (Os Esquecidos, Épica)
- `luterano_vigia` — Vigia da Noite (Véu Carmesim, Comum)
- `luterano_anjo2` — Anjo de Segunda Ordem (Lua Negra, Lendária)

**Recomendação:** formalizar como `trigger=round_end`, incluir no schema e descrição canônicos, testar o ramo vitória/derrota e só então decidir se mantém.

### `sobrevivente`

`sobrevivente` existe em `HABILIDADES` com texto “Ao fim da rodada, permanece no campo (a mais forte, se houver várias)”, mas não foi localizado em `_resolve_round()` nem em outro hook. A recomendação é implementar o evento corretamente ou retirar a definição e qualquer referência de carta antes do novo catálogo.

## 6. Decisões recomendadas antes da limpeza

1. Confirmar quais das 18 identidades V18 continuam puras e quais devem voltar como efeito individual.
2. Para `devoto`, `legado` e `sinergia_faccao`, decidir se viram efeitos canônicos reais ou se as cartas ficam puras; não manter campos enganosos.
3. Remover/recriar `escolha_ritmo`, pois o ramo atual não cumpre o texto comentado.
4. Arquivar e retirar os seis ramos V75 antigos depois de revalidar tags e combos.
5. Resolver `gloria` e `sobrevivente` como eventos de fim de rodada, com descrição alinhada à execução.
6. Rodar auditoria AST, testes positivos/negativos e comparação de estados antes/depois da remoção.

## 7. Reprodutibilidade

Gerador: `docs/scripts/audit-stale-identity-branches-v0.1.py`.
Saída estruturada: `docs/card-game-stale-identity-disposition-v0.1.json`.

O script lê o AST de `sistemas/gwent.py`, compara o dicionário original com o mapa filtrado em runtime, cruza os card IDs com `CARTAS_POR_ID`, `CARTAS_SEM_EFEITO_IDS` e `CARD_SYNERGY_TAGS`, e registra a associação e recomendação. Não altera módulos funcionais.
