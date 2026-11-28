# Matriz de rastreabilidade carta por carta — baseline atual

> Documento de auditoria estática gerado a partir do catálogo carregado em runtime. Não altera regras nem autoriza exclusão automática. Os valores representam o estado do ZIP original, em 2026-11-27.

> **Atualização de runtime (2026-11-28):** este relatório e suas tabelas são um snapshot histórico do ZIP de 2026-11-27. Para Malenia, não use os campos históricos de custo 4, habilidade `drenagem` ou texto antigo como estado atual. A definição autoritativa corrigida está em `data/card_game/malenia-runtime-current.v1.json`; o runtime atual usa custo 6, habilidade `scarlet_bloom` / Flor Escarlate, poder 9 e regra de corrosão sem repetição no limite.

## 1. Escopo e fontes

- Catálogo runtime: `sistemas/cartas.py` → `CARTAS_POR_ID` e `Carta.para_dict()`.
- Regras/associações: `sistemas/gwent.py` → `preparar_carta()`, `CARD_IDENTITY_ABILITIES`, `CARD_SYNERGY_TAGS`, `SYNERGY_COMBOS`, `aplicar_jogada()` e `_resolve_round()`.
- Camada visual: `sistemas/arte_gwent_efeitos.py` → `_AURAS` e `_EMBLEMAS`.
- Comparação de custo: `Carta.custo` vs. `CUSTO_RARIDADE[raridade]`.
- A identidade “definida mas filtrada” é extraída do dicionário antes da filtragem runtime em `sistemas/gwent.py`; não é efeito ativo no estado atual.

## 2. Resumo quantitativo

| Métrica | Resultado |
|---|---:|
| Modelos no catálogo | 137 |
| Unidades | 110 |
| Especiais | 27 |
| Habilidades declaradas em HABILIDADES | 59 |
| Identidades definidas antes do filtro | 40 |
| Identidades ativas em runtime | 22 |
| Identidades filtradas em runtime | 18 |
| Associações carta → tags | 72 |
| Combos | 27 |
| Cartas puras estritas (unidades) | 15 |
| Puras / unidades | 13.64% |
| Puras / catálogo total | 10.95% |
| Divergências de custo | 19 |
| Cartas com habilidade genérica + identidade ativa | 16 |
| Cartas com tags de combo | 67 |
| IDs de habilidade sem metadado | 9 |
| Unidades com habilidade nominal sem resolução genérica | 6 |
| Poder-base fora de 1–15 | 0 |
| Cartas alteradas pela transformação V18 em runtime | 43 |

## 3. Convenções para interpretar a matriz

- **Habilidade genérica:** valor do campo `Carta.habilidade`, usado pelo motor em ramos diretos de `aplicar_jogada()` ou no ciclo de rodada.
- **Identidade ativa:** regra obtida por `card_id` em `CARD_IDENTITY_ABILITIES`, chamada por `_aplicar_habilidade_identidade()`.
- **Identidade filtrada:** entrada presente no dicionário original, mas removida em runtime por `CARTAS_SEM_EFEITO_IDS`; não é executada hoje.
- **Tags/combos:** tags vêm de `CARD_SYNERGY_TAGS`; combos potenciais são aqueles cujo conjunto de tags intersecta as tags da carta. A ativação ainda exige as outras tags e/ou `minimum` no campo.
- **Pura estrita:** unidade sem `habilidade` runtime, sem identidade ativa e sem tags de combo. Passiva global de facção não é individual e não retira a classificação de pura.
- **Exibição vs. execução:** quando uma identidade ativa coexiste com o campo genérico preenchido, `preparar_carta()` retorna o ID genérico em `habilidade`, mas nome/texto da identidade; em `aplicar_jogada()`, o ID genérico é suprimido (`skill = ""`) e somente a identidade ativa é resolvida. É uma ambiguidade de payload, não dupla execução.
- **Custo:** a coluna “custo do modelo” vem de `Carta.custo`; “custo tabela raridade” vem de `CUSTO_RARIDADE`. Não é orçamento de deck.

## 4. Inconsistências de alta prioridade

1. **Contrato ambíguo, sem dupla execução:** 16 cartas têm o campo genérico preenchido e identidade ativa. `preparar_carta()` retorna o ID genérico em `habilidade`, mas nome/texto da identidade; `aplicar_jogada()` suprime o genérico e executa somente a identidade. IDs: `chefe_guardiao_cinzas`, `chefe_dama_vazio`, `chefe_rei_afogado`, `chefe_oraculo_ruina`, `chefe_malenia_lamina_miquella`, `chefe_radahn_flagelo_estrelas`, `chefe_maliketh_morte_destinada`, `chefe_messmer_impalador`, `chefe_placidusax_lorde_dragao`, `arma_duas_luas`, `arma_grande_sino`, `magia_selo_vigilia`, `magia_trovao_oco`, `magia_nevoa_antiga`, `magia_sol_negro`, `covenant_lua_velada`.
2. **IDs de habilidade sem metadado em HABILIDADES:** 9 cartas. IDs: `luterano_cruzado` (`sinergia_faccao`), `luterano_bispo` (`devoto`), `luterano_anjo` (`gloria`), `luterano_papa` (`sinergia_faccao`), `luterano_pastor` (`legado`), `luterano_mistico` (`devoto`), `luterano_profeta` (`sinergia_faccao`), `luterano_vigia` (`gloria`), `luterano_anjo2` (`gloria`).
3. **Identidades filtradas:** 18 cartas têm uma definição histórica de identidade que a filtragem runtime removeu. IDs: `chefe_cervo_sombrio`, `chefe_cacador_sem_rosto`, `chefe_vigia_cinzento`, `chefe_aparicao_veio`, `arma_lamina_peregrino`, `arma_martelo_fornalha`, `arma_cajado_marulho`, `arma_agulha_astro`, `arma_lanca_fornalha`, `arma_arco_peregrino`, `magia_brasa_errante`, `magia_fagulha`, `magia_orbe_eco`, `magia_chama_fria`, `covenant_sentinelas`, `covenant_ultimos`, `covenant_filhos_brasa`, `covenant_peregrinos_nevoa`.
4. **IDs de associação de tag sem carta no catálogo:** 5: `gwent_unidade_cruzado`, `gwent_unidade_evangelista`, `gwent_unidade_missionario`, `gwent_unidade_protetor`, `gwent_unidade_sacerdote`.
5. **Custo divergente:** 19 modelos. Lista resumida: `chefe_malenia_lamina_miquella` (4 vs 6), `chefe_radahn_flagelo_estrelas` (4 vs 6), `chefe_placidusax_lorde_dragao` (4 vs 6), `reliquia_grande_runa_godrick` (3 vs 4), `reliquia_runa_nao_nascidos` (3 vs 4), `reliquia_runa_morte` (4 vs 5), `reliquia_noite_chama` (3 vs 4), `reliquia_lamina_negra` (4 vs 5), `reliquia_algemas_margit` (2 vs 3), `luterano_bispo` (3 vs 4), `luterano_anjo` (2 vs 3), `luterano_papa` (4 vs 5), `luterano_profeta` (4 vs 5), `luterano_anjo2` (3 vs 4), `primordial_origem` (4 vs 6), `primordial_trono` (4 vs 6), `primordial_tempestade` (4 vs 6), `primordial_abismo` (4 vs 6), `primordial_eternidade` (4 vs 6).
6. **Puras estritas atuais:** 15 de 110 unidades (13.64%). IDs: `chefe_cacador_sem_rosto`, `chefe_vigia_cinzento`, `arma_martelo_fornalha`, `arma_cajado_marulho`, `arma_lanca_fornalha`, `magia_fagulha`, `covenant_sentinelas`, `covenant_ultimos`, `covenant_filhos_brasa`, `covenant_peregrinos_nevoa`, `gwent_unidade_lamina_sem_juramento`, `gwent_unidade_oraculo_clima`, `patente_2`, `patente_3`, `patente_4`.
7. **Divergência de facção a validar:** 6 IDs da família `luterano_*` têm facção diversa de `Os Esquecidos`: `luterano_apostolo`, `luterano_pastor`, `luterano_mistico`, `luterano_profeta`, `luterano_vigia`, `luterano_anjo2`.
8. **Poder-base:** todas as unidades do catálogo estático atual devem ser verificadas contra 1–15; as especiais usam poder 0 como regra histórica e não entram no critério de unidade. No baseline, fora da faixa: 0.


9. **Transformação V18:** 43 declarações de carta são alteradas durante o import: `habilidade` é zerada e `poder` recebe +1 quando não ultrapassa o teto da raridade. A matriz preserva os valores antes/depois por ID. IDs: `chefe_cervo_sombrio`, `chefe_cacador_sem_rosto`, `chefe_vigia_cinzento`, `chefe_aparicao_veio`, `arma_lamina_peregrino`, `arma_martelo_fornalha`, `arma_cajado_marulho`, `arma_agulha_astro`, `arma_lanca_fornalha`, `arma_arco_peregrino`, `magia_brasa_errante`, `magia_fagulha`, `magia_orbe_eco`, `magia_chama_fria`, `covenant_lobos_cinza`, `covenant_sentinelas`, `covenant_ultimos`, `covenant_filhos_brasa`, `covenant_peregrinos_nevoa`, `gwent_unidade_baluarte`, `gwent_unidade_lamina_sem_juramento`, `gwent_unidade_portaestandarte`, `gwent_unidade_oraculo_clima`, `gwent_unidade_eco`, `gwent_unidade_cavaleira`, `gwent_unidade_cartografa`, `gwent_unidade_mestre_forja`, `gwent_unidade_dupla_veu`, `gwent_unidade_circulo`, `gwent_unidade_sentinela_rubra`, `gwent_unidade_veterano_cercos`, `gwent_unidade_intendente`, `gwent_unidade_cacadora_fantasma`, `gwent_unidade_cantora_lamentos`, `gwent_unidade_saqueadora_veu`, `gwent_unidade_contrabandista`, `gwent_unidade_guardiao_runas`, `gwent_unidade_devorador_mana`, `gwent_unidade_bibliotecaria`, `luterano_missionario`, `luterano_sacerdote`, `luterano_irmao`, `luterano_diacon`.

## 5. Catálogo carta por carta

### Unidade (110)

| ID | Nome | Facção | Fileira | Poder | Raridade | Custo | Habilidade | Identidade ativa | Tags | Pura | Status de resolução |
|---|---|---|---|---:|---|---:|---|---|---|---|---|
| `chefe_guardiao_cinzas` | Cavaleiro da Árvore Áurea | Ordem Áurea | melee | 5 | Rara | 2 | `quebra_ritmo` | Égide das Cinzas (`ash_guardian`) | cinzas, ordem_dourada | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags |
| `chefe_dama_vazio` | Ranni, Bruxa da Lua | Lua Negra | siege | 6 | Épica | 3 | `ultimo_folego` | Fenda do Vazio (`void_rend`) | lua_cariana, vazio | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags |
| `chefe_cervo_sombrio` | Cavaleiro do Cão de Caça | Véu Carmesim | melee | 5 | Comum | 1 | — | FILTRADA: Passagem Sombria | veu_sombrio | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `chefe_rei_afogado` | Godfrey, Primeiro Lorde Prístino | Ordem Áurea | melee | 7 | Épica | 3 | `primeira_luz` | Dízimo do Abismo (`abyss_tithe`) | abismo, sangue_mohgwyn | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags |
| `chefe_oraculo_ruina` | Gurranq, Clérigo Bestial | Ordem Áurea | melee | 7 | Lendária | 4 | `impeto` | Presságio da Ruína (`ruin_omen`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `chefe_cacador_sem_rosto` | Assassina da Faca Negra | Véu Carmesim | melee | 6 | Rara | 2 | — | FILTRADA: Marca da Presa | — | Sim | identidade antiga filtrada/desativada em runtime |
| `chefe_vigia_cinzento` | Cavaleiro de Leyndell | Ordem Áurea | melee | 5 | Comum | 1 | — | FILTRADA: Vigília Cinzenta | — | Sim | identidade antiga filtrada/desativada em runtime |
| `chefe_aparicao_veio` | Lâmina Negra Errante | Véu Carmesim | melee | 4 | Comum | 1 | — | FILTRADA: Deslocamento Espectral | veu_sombrio | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `chefe_malenia_lamina_miquella` | Malenia, Lâmina de Miquella | Véu Carmesim | melee | 9 | Primordial | 4 | `drenagem` | Flor Escarlate (`scarlet_bloom`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `chefe_radahn_flagelo_estrelas` | Radahn, Flagelo das Estrelas | Ordem Áurea | siege | 9 | Primordial | 4 | `quebra_ritmo` | Gravidade do Flagelo (`star_gravity`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `chefe_maliketh_morte_destinada` | Maliketh, Lâmina Negra | Ordem Áurea | melee | 8 | Lendária | 4 | `cacador_arcano` | Morte Destinada (`destined_death`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `chefe_messmer_impalador` | Messmer, o Empalador | Ordem Áurea | melee | 8 | Lendária | 4 | `quebra_ritmo` | Lança do Impalador (`impaling_spear`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `chefe_placidusax_lorde_dragao` | Placidusax, Lorde Dragão | Lua Negra | siege | 9 | Primordial | 4 | `olho_tempestade` | Tempestade do Tempo (`time_storm`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `arma_lamina_peregrino` | Duelista da Casa Hoslow | Véu Carmesim | melee | 5 | Comum | 1 | — | FILTRADA: Duelo do Peregrino | peregrino | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `arma_martelo_fornalha` | Ferreiro de Volcano Manor | Véu Carmesim | melee | 6 | Rara | 2 | — | FILTRADA: Martelo de Cadência | — | Sim | identidade antiga filtrada/desativada em runtime |
| `arma_cajado_marulho` | Feiticeiro Cariano | Lua Negra | ranged | 6 | Rara | 2 | — | FILTRADA: Ressonância das Marés | — | Sim | identidade antiga filtrada/desativada em runtime |
| `arma_duas_luas` | Espadachim da Lua Negra | Lua Negra | melee | 7 | Épica | 3 | `precisao` | Dança Espelhada (`twin_dance`) | duas_luas, lua_cariana | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags |
| `arma_grande_sino` | Sentinela do Portão de Leyndell | Ordem Áurea | melee | 8 | Lendária | 4 | `instinto` | Sino do Último Bastião (`last_bell`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `arma_agulha_astro` | Leitora de Estrelas de Sellia | Lua Negra | ranged | 4 | Comum | 1 | — | FILTRADA: Fio Astral | astral, lua_cariana | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `arma_lanca_fornalha` | Lanceiro da Árvore Áurea | Ordem Áurea | melee | 5 | Comum | 1 | — | FILTRADA: Investida da Fornalha | — | Sim | identidade antiga filtrada/desativada em runtime |
| `arma_arco_peregrino` | Batedor da Mansão Vulcânica | Véu Carmesim | ranged | 5 | Comum | 1 | — | FILTRADA: Tiro de Cobertura | peregrino | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `magia_brasa_errante` | Monge do Fogo | Lua Negra | melee | 4 | Comum | 1 | — | FILTRADA: Brasa Persistente | chama | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `magia_selo_vigilia` | Confessora da Ordem Áurea | Ordem Áurea | melee | 5 | Rara | 2 | `adaptacao` | Selo de Vigília (`vigil_seal`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `magia_trovao_oco` | Dragoeiro Ancião | Ordem Áurea | ranged | 6 | Épica | 3 | `drenagem` | Descarga Oca (`hollow_thunder`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `magia_nevoa_antiga` | Astróloga de Liurnia | Lua Negra | siege | 7 | Épica | 3 | `encadeamento` | Névoa Ancestral (`ancient_mist`) | astral, lua_cariana | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags |
| `magia_sol_negro` | Apóstolo da Pele Divina | Véu Carmesim | melee | 8 | Lendária | 4 | `quebra_ritmo` | Eclipse Devorador (`devouring_eclipse`) | — | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id |
| `magia_fagulha` | Aprendiz de Feitiçaria Cariana | Lua Negra | ranged | 5 | Comum | 1 | — | FILTRADA: Faísca Condutora | — | Sim | identidade antiga filtrada/desativada em runtime |
| `magia_orbe_eco` | Erudito da Academia | Lua Negra | ranged | 5 | Comum | 1 | — | FILTRADA: Orbe Refrator | eco | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `magia_chama_fria` | Feiticeira da Lua Gélida | Lua Negra | ranged | 4 | Comum | 1 | — | FILTRADA: Contrafogo | chama | Não | identidade antiga filtrada/desativada em runtime; participa de combo por tags |
| `covenant_lobos_cinza` | Cavaleiros de Radahn | Ordem Áurea | melee | 6 | Rara | 2 | — | — | cinzas | Não | participa de combo por tags |
| `covenant_lua_velada` | Juramentada de Ranni | Lua Negra | ranged | 6 | Épica | 3 | `primeira_luz` | Aliança Lunar (`veiled_moon`) | duas_luas, lua_cariana | Não | habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags |
| `covenant_sentinelas` | Guardiões de Sellia | Lua Negra | melee | 5 | Comum | 1 | — | FILTRADA: Sentinela Compartilhada | — | Sim | identidade antiga filtrada/desativada em runtime |
| `covenant_coroa_abismo` | Cavaleiro da Dinastia Mohgwyn | Véu Carmesim | melee | 7 | Lendária | 4 | `drenagem` | — | abismo, sangue_mohgwyn | Não | habilidade genérica executada ao entrar em campo; participa de combo por tags |
| `covenant_ultimos` | Cavaleiros de sangue juramentados | Véu Carmesim | melee | 6 | Rara | 2 | — | FILTRADA: Último Juramento | — | Sim | identidade antiga filtrada/desativada em runtime |
| `covenant_filhos_brasa` | Discípulos do Monge do Fogo | Ordem Áurea | melee | 5 | Comum | 1 | — | FILTRADA: Herança da Brasa | — | Sim | identidade antiga filtrada/desativada em runtime |
| `covenant_peregrinos_nevoa` | Peregrinos da Cidade Eterna | Lua Negra | ranged | 5 | Comum | 1 | — | FILTRADA: Rastro na Névoa | — | Sim | identidade antiga filtrada/desativada em runtime |
| `covenant_irmandade_ferro` | Guardas da Árvore Áurea | Ordem Áurea | melee | 4 | Comum | 1 | `retaliacao` | — | estandarte | Não | habilidade genérica executada ao entrar em campo; participa de combo por tags |
| `gwent_unidade_baluarte` | Cavaleiro do Crisol | Ordem Áurea | melee | 6 | Rara | 2 | — | — | fornalha, ordem_dourada | Não | participa de combo por tags |
| `gwent_unidade_lamina_sem_juramento` | Caçador de Dedos | Véu Carmesim | melee | 6 | Rara | 2 | — | — | — | Sim | sem efeito individual/tag/identidade |
| `gwent_unidade_portaestandarte` | Porta-estandarte de Leyndell | Ordem Áurea | melee | 5 | Comum | 1 | — | — | estandarte, fornalha, ordem_dourada | Não | participa de combo por tags |
| `gwent_unidade_oraculo_clima` | Profeta de Liurnia | Lua Negra | siege | 6 | Rara | 2 | — | — | — | Sim | sem efeito individual/tag/identidade |
| `gwent_unidade_eco` | Erudito das Pedras Cintilantes | Lua Negra | siege | 6 | Rara | 2 | — | — | astral, eco | Não | participa de combo por tags |
| `gwent_unidade_cavaleira` | Cavaleira Cariana | Lua Negra | melee | 5 | Comum | 1 | — | — | veu_sombrio | Não | participa de combo por tags |
| `gwent_unidade_gigante` | Gigante de Fogo | Ordem Áurea | melee | 7 | Épica | 3 | `instinto` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `gwent_unidade_cartografa` | Exploradora da Cidade Eterna | Lua Negra | ranged | 5 | Comum | 1 | — | — | duas_luas | Não | participa de combo por tags |
| `gwent_unidade_invocador` | Apóstolo da Pele Divina Errante | Véu Carmesim | siege | 7 | Épica | 3 | `cacador_arcano` | — | astral | Não | habilidade genérica executada ao entrar em campo; participa de combo por tags |
| `gwent_unidade_mestre_forja` | Mestre Ferreiro de Volcano Manor | Véu Carmesim | melee | 6 | Rara | 2 | — | — | fornalha, ordem_dourada | Não | participa de combo por tags |
| `gwent_unidade_dupla_veu` | Gêmeas da Cidade Eterna | Lua Negra | melee | 6 | Rara | 2 | — | — | duas_luas, veu_sombrio | Não | participa de combo por tags |
| `gwent_unidade_circulo` | Discípulo da Academia | Lua Negra | siege | 6 | Rara | 2 | — | — | astral | Não | participa de combo por tags |
| `gwent_unidade_sentinela_rubra` | Cavaleiro de Radahn | Ordem Áurea | melee | 5 | Comum | 1 | — | — | muralha, ordem_dourada | Não | participa de combo por tags |
| `gwent_unidade_veterano_cercos` | Cavaleiro Draconiano | Ordem Áurea | melee | 6 | Rara | 2 | — | — | muralha | Não | participa de combo por tags |
| `gwent_unidade_herdeiro_portao` | Godwyn, o Dourado | Ordem Áurea | melee | 6 | Épica | 3 | `vinganca` | — | muralha, ordem_dourada | Não | efeito de ciclo de vida executado fora da entrada; participa de combo por tags |
| `gwent_unidade_carniceiro_forja` | Carrasco de Volcano Manor | Véu Carmesim | melee | 4 | Rara | 2 | `devorar` | — | banquete, sangue_mohgwyn | Não | habilidade genérica executada ao entrar em campo; participa de combo por tags |
| `gwent_unidade_intendente` | Mercador Nômade | Ordem Áurea | ranged | 4 | Comum | 1 | — | — | banquete | Não | participa de combo por tags |
| `gwent_unidade_cacadora_fantasma` | Assassina de Ravenmount | Véu Carmesim | melee | 6 | Rara | 2 | — | — | fantasmas | Não | participa de combo por tags |
| `gwent_unidade_cantora_lamentos` | Fia, Companheira do Leito de Morte | Véu Carmesim | ranged | 5 | Rara | 2 | — | — | fantasmas | Não | participa de combo por tags |
| `gwent_unidade_senhor_cacada` | Blaidd, o Meio-Lobo | Lua Negra | melee | 6 | Épica | 3 | `vinganca` | — | fantasmas | Não | efeito de ciclo de vida executado fora da entrada; participa de combo por tags |
| `gwent_unidade_saqueadora_veu` | Ladina da Cidade Eterna | Lua Negra | ranged | 5 | Comum | 1 | — | — | caravana | Não | participa de combo por tags |
| `gwent_unidade_contrabandista` | Recusante da Mansão Vulcânica | Véu Carmesim | ranged | 5 | Comum | 1 | — | — | caravana | Não | participa de combo por tags |
| `gwent_unidade_guardiao_runas` | Guardião da Ordem Áurea | Ordem Áurea | melee | 5 | Comum | 1 | — | — | runico | Não | participa de combo por tags |
| `gwent_unidade_necromante` | Servo dos que Vivem na Morte | Lua Negra | siege | 4 | Rara | 2 | `ressurgir` | — | runico | Não | habilidade genérica executada ao entrar em campo; participa de combo por tags |
| `gwent_unidade_detonador` | Guerreiro da Chama Frenética | Véu Carmesim | melee | 6 | Épica | 3 | `vinganca` | — | runico | Não | efeito de ciclo de vida executado fora da entrada; participa de combo por tags |
| `gwent_unidade_devorador_mana` | Cavaleiro de Sangue de Mohg | Véu Carmesim | melee | 6 | Rara | 2 | — | — | eclipse_voraz, sangue_mohgwyn | Não | participa de combo por tags |
| `gwent_unidade_bibliotecaria` | Bibliotecária de Raya Lucaria | Lua Negra | siege | 5 | Comum | 1 | — | — | eclipse_voraz | Não | participa de combo por tags |
| `gwent_mitica_coroa` | Cavaleiro Consagrado do Haligtree | Ordem Áurea | melee | 8 | Mítica | 5 | `estandarte` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `gwent_singular_primeiro` | Juramento Primordial do Crisol | Véu Carmesim | melee | 10 | Singular | 0 | `cacador_solitario` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `gwent_singular_intocavel` | Adaga da Faca Negra | Véu Carmesim | melee | 9 | Singular | 0 | `precisao` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `gwent_singular_nivel1` | Vontade de Marika | Ordem Áurea | melee | 10 | Singular | 0 | `ultimo_folego` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `gwent_singular_cacador_chefes` | Coroa do Lorde Prístino | Lua Negra | melee | 9 | Singular | 0 | `paradoxo_eterno` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `luterano_cruzado` | Cruzado Esquecido | Os Esquecidos | melee | 6 | Épica | 3 | `sinergia_faccao` | — | fe, gloria_divina | Não | ID de habilidade não catalogado em HABILIDADES; participa de combo por tags |
| `luterano_missionario` | Missionário Esquecido | Os Esquecidos | ranged | 5 | Rara | 2 | — | — | evangelho, fe | Não | participa de combo por tags |
| `luterano_bispo` | Bispo Esquecido | Os Esquecidos | siege | 5 | Lendária | 3 | `devoto` | — | devocao, fe | Não | ID de habilidade não catalogado em HABILIDADES; participa de combo por tags |
| `luterano_anjo` | Anjo Esquecido | Os Esquecidos | ranged | 3 | Épica | 2 | `gloria` | — | fe, gloria_divina | Não | efeito de ciclo de vida executado fora da entrada; participa de combo por tags |
| `luterano_papa` | Papa Esquecido | Os Esquecidos | siege | 7 | Mítica | 4 | `sinergia_faccao` | — | fe, soberania | Não | ID de habilidade não catalogado em HABILIDADES; participa de combo por tags |
| `luterano_sacerdote` | Sacerdote Esquecido | Os Esquecidos | ranged | 5 | Rara | 2 | — | — | fe, sacerdos | Não | participa de combo por tags |
| `luterano_irmao` | Irmão Esquecido | Os Esquecidos | melee | 4 | Comum | 1 | — | — | fe, irmandade | Não | participa de combo por tags |
| `luterano_diacon` | Diácono Esquecido | Os Esquecidos | ranged | 3 | Comum | 1 | — | — | diaconia, fe | Não | participa de combo por tags |
| `gwent_v75_ordem_veterano_juramento` | Veterano do Juramento Dourado | Ordem Áurea | melee | 4 | Rara | 2 | — | Juramento Dourado (`v75_golden_vow`) | v75_erdtree_oath | Não | identidade ativa executada por card_id; participa de combo por tags |
| `gwent_v75_ordem_guardiao_crisol` | Guardião do Crisol Menor | Ordem Áurea | melee | 4 | Rara | 2 | — | — | v75_crucible_guard | Não | participa de combo por tags |
| `gwent_v75_ordem_confessora_graca` | Confessora da Graça Serena | Ordem Áurea | siege | 5 | Épica | 3 | — | Regressão Serena (`v75_grace_mender`) | v75_erdtree_oath | Não | identidade ativa executada por card_id; participa de combo por tags |
| `gwent_v75_ordem_arauto_estandarte` | Arauto do Estandarte Áureo | Ordem Áurea | ranged | 5 | Épica | 3 | — | — | v75_crucible_guard | Não | participa de combo por tags |
| `gwent_v75_veu_acolito_sangue` | Acólito da Dinastia Sanguínea | Véu Carmesim | ranged | 4 | Rara | 2 | — | Marca da Dinastia (`v75_blood_mark`) | v75_blood_mark | Não | identidade ativa executada por card_id; participa de combo por tags |
| `gwent_v75_veu_devota_hemorragia` | Devota da Hemorragia | Véu Carmesim | siege | 4 | Rara | 2 | — | — | v75_blood_feast | Não | participa de combo por tags |
| `gwent_v75_veu_carrasco_preco` | Carrasco da Procissão Carmesim | Véu Carmesim | melee | 5 | Épica | 3 | — | Preço em Sangue (`v75_blood_price`) | v75_blood_feast | Não | identidade ativa executada por card_id; participa de combo por tags |
| `gwent_v75_veu_cacador_sangue` | Caçador das Catacumbas de Mohgwyn | Véu Carmesim | ranged | 5 | Épica | 3 | — | — | v75_blood_mark | Não | participa de combo por tags |
| `gwent_v75_lua_oraculo_geada` | Oráculo Gélido de Sellia | Lua Negra | siege | 4 | Rara | 2 | — | Presságio da Geada (`v75_frost_oracle`) | v75_frost_lore | Não | identidade ativa executada por card_id; participa de combo por tags |
| `gwent_v75_lua_cartografo_lunar` | Cartógrafo das Cidades Eternas | Lua Negra | ranged | 4 | Rara | 2 | — | — | v75_lunar_paths | Não | participa de combo por tags |
| `gwent_v75_lua_graviturgista` | Graviturgista de Nokron | Lua Negra | siege | 5 | Épica | 3 | — | Cisalhamento Gravitacional (`v75_gravity_shear`) | v75_frost_lore | Não | identidade ativa executada por card_id; participa de combo por tags |
| `gwent_v75_lua_guardia` | Guardiã do Juramento Lunar | Lua Negra | melee | 5 | Épica | 3 | — | — | v75_lunar_paths | Não | participa de combo por tags |
| `luterano_apostolo` | Apóstolo Esquecido | Ordem Áurea | melee | 5 | Épica | 3 | — | — | evangelho, fe | Não | participa de combo por tags |
| `luterano_pastor` | Pastor Esquecido | Véu Carmesim | ranged | 4 | Rara | 2 | `legado` | — | fe, irmandade | Não | ID de habilidade não catalogado em HABILIDADES; participa de combo por tags |
| `luterano_mistico` | Místico Esquecido | Lua Negra | siege | 5 | Rara | 2 | `devoto` | — | devocao, fe | Não | ID de habilidade não catalogado em HABILIDADES; participa de combo por tags |
| `luterano_profeta` | Profeta Esquecido | Ordem Áurea | melee | 6 | Mítica | 4 | `sinergia_faccao` | — | fe, soberania | Não | ID de habilidade não catalogado em HABILIDADES; participa de combo por tags |
| `luterano_vigia` | Vigia da Noite | Véu Carmesim | melee | 3 | Comum | 1 | `gloria` | — | fe, gloria_divina | Não | efeito de ciclo de vida executado fora da entrada; participa de combo por tags |
| `luterano_anjo2` | Anjo de Segunda Ordem | Lua Negra | siege | 5 | Lendária | 3 | `gloria` | — | fe, gloria_divina | Não | efeito de ciclo de vida executado fora da entrada; participa de combo por tags |
| `primordial_origem` | Besta Prístina, Arauto da Vontade Maior | Ordem Áurea | siege | 8 | Primordial | 4 | `lei_primeva` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `primordial_trono` | Marika, Rainha Eterna | Ordem Áurea | melee | 8 | Primordial | 4 | `decreto_soberano` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `primordial_tempestade` | Placidusax, Senhor Dragão | Lua Negra | siege | 8 | Primordial | 4 | `olho_tempestade` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `primordial_abismo` | Mãe Sem Forma | Véu Carmesim | siege | 8 | Primordial | 4 | `fome_abismo` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `primordial_eternidade` | Maliketh, Guardião da Morte Destinada | Ordem Áurea | melee | 8 | Primordial | 4 | `paradoxo_eterno` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `patente_1` | Novato de Raya Lucaria — Cinzas Novatas | Lua Negra | ranged | 3 | Comum | 1 | `cacador_arcano` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `patente_2` | Novato de Raya Lucaria — Guerreiro Caído | Lua Negra | siege | 3 | Comum | 1 | — | — | — | Sim | sem efeito individual/tag/identidade |
| `patente_3` | Aprendiz Cariano — Caçador de Almas | Lua Negra | siege | 6 | Rara | 2 | — | — | — | Sim | sem efeito individual/tag/identidade |
| `patente_4` | Escudeiro da Árvore Áurea — Cavaleiro do Abismo | Ordem Áurea | melee | 5 | Rara | 2 | — | — | — | Sim | sem efeito individual/tag/identidade |
| `patente_5` | Acólito Sanguíneo — Guardião das Cinzas | Véu Carmesim | ranged | 6 | Rara | 2 | `encadeamento` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `patente_6` | Veterano de Leyndell — Arauto da Ruína | Ordem Áurea | melee | 5 | Épica | 3 | `retaliacao` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `patente_7` | Feiticeiro Cariano — Executor Sombrio | Lua Negra | melee | 7 | Épica | 3 | `cacador_arcano` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `patente_8` | Veterano de Leyndell — Senhor das Almas | Ordem Áurea | ranged | 5 | Épica | 3 | `retaliacao` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `patente_9` | Lorde de Leyndell — Lenda do Coliseu | Ordem Áurea | siege | 8 | Lendária | 4 | `impeto` | — | — | Não | habilidade genérica executada ao entrar em campo |
| `patente_10` | Mestre Cariano — Sentinela Imortal | Lua Negra | siege | 6 | Lendária | 4 | `quebra_ritmo` | — | — | Não | habilidade genérica executada ao entrar em campo |

### Especial (27)

| ID | Nome | Facção | Fileira | Poder | Raridade | Custo | Habilidade | Identidade ativa | Tags | Pura | Status de resolução |
|---|---|---|---|---:|---|---:|---|---|---|---|---|
| `gwent_especial_tempestade` | Tempestade dos Picos | Lua Negra | melee | 0 | Rara | 2 | `gwent_clima` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_nevoa` | Miasma da Podridão | Lua Negra | melee | 0 | Rara | 2 | `gwent_nevoa` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_geada` | Geada dos Picos dos Gigantes | Lua Negra | melee | 0 | Rara | 2 | `gwent_geada` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_chuva` | Sangue Corrompido | Véu Carmesim | melee | 0 | Comum | 1 | `gwent_chuva` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_chifre` | Rugido de Godfrey | Ordem Áurea | melee | 0 | Épica | 3 | `gwent_chifre` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_medico` | Lágrima Sagrada | Véu Carmesim | melee | 0 | Rara | 2 | `gwent_medico` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_queima` | Chama Negra | Lua Negra | melee | 0 | Épica | 3 | `gwent_queima` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_purificar` | Lei da Regressão | Lua Negra | melee | 0 | Rara | 2 | `gwent_purificar` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_execucao` | Lâmina da Morte Destinada | Ordem Áurea | melee | 0 | Épica | 3 | `gwent_execucao` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_vinculo` | Juramento do Crisol | Ordem Áurea | melee | 0 | Rara | 2 | `gwent_vinculo` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_batedor` | Passo do Cão de Caça | Véu Carmesim | melee | 0 | Rara | 2 | `gwent_batedor` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_muralha` | Bastião de Leyndell | Ordem Áurea | melee | 0 | Comum | 1 | `gwent_muralha` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `elden_especial_sangramento` | Ritual de Sangue | Véu Carmesim | melee | 0 | Rara | 2 | `gwent_sangramento` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `elden_especial_geada` | Lua Cheia de Rennala | Lua Negra | melee | 0 | Rara | 2 | `gwent_geada_cariana` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `elden_especial_podrida` | Flor da Podridão Escarlate | Lua Negra | melee | 0 | Épica | 3 | `gwent_podrida` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `elden_especial_loucura` | Chama Frenética | Lua Negra | melee | 0 | Épica | 3 | `gwent_loucura` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `elden_especial_chama` | Chama do Gigante | Ordem Áurea | melee | 0 | Rara | 2 | `gwent_chama` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `elden_especial_invocacao` | Cinzas dos Lobos Solitários | Lua Negra | melee | 0 | Rara | 2 | `gwent_invocacao` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `reliquia_grande_runa_godrick` | Grande Runa de Godrick | Ordem Áurea | melee | 0 | Lendária | 3 | `reliquia_godrick` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `reliquia_runa_nao_nascidos` | Grande Runa dos Não Nascidos | Lua Negra | melee | 0 | Lendária | 3 | `reliquia_renala` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `reliquia_runa_morte` | Runa da Morte | Véu Carmesim | melee | 0 | Mítica | 4 | `reliquia_morte` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `reliquia_noite_chama` | Espada da Noite e da Chama | Lua Negra | melee | 0 | Lendária | 3 | `reliquia_noite_chama` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `reliquia_lamina_negra` | Lâmina Negra | Véu Carmesim | melee | 0 | Mítica | 4 | `reliquia_lamina_negra` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `reliquia_algemas_margit` | Algemas de Margit | Ordem Áurea | melee | 0 | Épica | 2 | `reliquia_algemas` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_egide` | Bênção da Árvore Áurea | Ordem Áurea | melee | 0 | Rara | 2 | `gwent_egide` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_requiem` | Chamado dos Mortos | Lua Negra | melee | 0 | Épica | 3 | `gwent_requiem` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |
| `gwent_especial_passo` | Passo do Lobo | Véu Carmesim | melee | 0 | Rara | 2 | `gwent_passo` | — | — | Não | Especial: possui ramo/ação no motor (requer ação especial). |

## 6. Detalhe individual dos efeitos, descrição e imagem

Esta seção preserva os textos atualmente efetivos e as ligações por carta para permitir comparação com os futuros textos mecânicos e artes.

### `chefe_guardiao_cinzas` — Cavaleiro da Árvore Áurea

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `quebra_ritmo` — Ruptura de Postura
- Habilidade declarada antes da transformação V18: `quebra_ritmo`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior.
- Identidade ativa: Égide das Cinzas; effect=`ash_guardian`
- Texto da identidade: Ao entrar em campo, dá +1 de bônus a um aliado da mesma fileira. Se já houver um aliado nessa fileira, esta carta também ganha +1.
- Identidade histórica filtrada: —
- Tags: cinzas, ordem_dourada
- Combos compatíveis por tag: Aliança da Árvore Áurea, Juramento da Árvore Áurea
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Ao entrar em campo, dá +1 de bônus a um aliado da mesma fileira. Se já houver um aliado nessa fileira, esta carta também ganha +1. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Um sentinela montado patrulha os caminhos que conduzem à Árvore Áurea, impondo a autoridade da capital.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_dama_vazio` — Ranni, Bruxa da Lua

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 6 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `ultimo_folego` — Último Suspiro
- Habilidade declarada antes da transformação V18: `ultimo_folego`; poder/custo declarados: 6 / 3
- Texto da habilidade no catálogo: Na terceira rodada, ganha +1 de poder ao entrar em campo.
- Identidade ativa: Fenda do Vazio; effect=`void_rend`
- Texto da identidade: Ao entrar em campo, tira 2 pontos de bônus da unidade inimiga mais forte. O bônus dela não pode ficar abaixo de -2.
- Identidade histórica filtrada: —
- Tags: lua_cariana, vazio
- Combos compatíveis por tag: Alinhamento Astral, Convergência da Lua Negra
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Ao entrar em campo, tira 2 pontos de bônus da unidade inimiga mais forte. O bônus dela não pode ficar abaixo de -2. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: A princesa lunar rompeu com os Dois Dedos e busca um destino independente da Vontade Maior.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_cervo_sombrio` — Cavaleiro do Cão de Caça

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `contragolpe`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Passagem Sombria
- Tags: veu_sombrio
- Combos compatíveis por tag: Caçada da Faca Negra
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um cavaleiro errante segue a trilha de presas pelas florestas enevoadas das Terras Intermédias.

### `chefe_rei_afogado` — Godfrey, Primeiro Lorde Prístino

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 7 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `primeira_luz` — Graça Dourada
- Habilidade declarada antes da transformação V18: `primeira_luz`; poder/custo declarados: 7 / 3
- Texto da habilidade no catálogo: Na primeira rodada, ganha +1 de poder ao entrar em campo.
- Identidade ativa: Dízimo do Abismo; effect=`abyss_tithe`
- Texto da identidade: Ganha +2 se você tiver uma unidade no descarte. Se não tiver, ganha +1 caso o adversário tenha mais unidades em campo.
- Identidade histórica filtrada: —
- Tags: abismo, sangue_mohgwyn
- Combos compatíveis por tag: Maré Abissal, Ritual do Véu Carmesim
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Ganha +2 se você tiver uma unidade no descarte. Se não tiver, ganha +1 caso o adversário tenha mais unidades em campo. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Primeiro Lorde Prístino e consorte de Marika, Godfrey liderou os guerreiros que conquistaram as Terras Intermédias.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_oraculo_ruina` — Gurranq, Clérigo Bestial

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 7 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `impeto` — Ímpeto do Lorde
- Habilidade declarada antes da transformação V18: `impeto`; poder/custo declarados: 7 / 4
- Texto da habilidade no catálogo: Ganha +1 de poder quando sua pontuação total é maior que a do adversário.
- Identidade ativa: Presságio da Ruína; effect=`ruin_omen`
- Texto da identidade: Tira 1 ponto de bônus da unidade inimiga mais forte. Também ganha +1 se o adversário estiver vencendo.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Tira 1 ponto de bônus da unidade inimiga mais forte. Também ganha +1 se o adversário estiver vencendo. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: O clérigo bestial consome Raiz da Morte e guarda um segredo ligado à própria Runa da Morte.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_cacador_sem_rosto` — Assassina da Faca Negra

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `retaliacao`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Marca da Presa
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Uma assassina Numen ligada à Noite das Facas Negras, quando um fragmento da Runa da Morte foi usado para matar Godwyn.

### `chefe_vigia_cinzento` — Cavaleiro de Leyndell

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `drenagem`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Vigília Cinzenta
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Um soldado da capital mantém a vigília entre as muralhas erguidas em nome da Ordem Áurea.

### `chefe_aparicao_veio` — Lâmina Negra Errante

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 4 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `adaptacao`; poder/custo declarados: 3 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Deslocamento Espectral
- Tags: veu_sombrio
- Combos compatíveis por tag: Caçada da Faca Negra
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Uma figura encapuzada atravessa as sombras, deixando apenas o rumor de uma lâmina silenciosa.

### `chefe_malenia_lamina_miquella` — Malenia, Lâmina de Miquella

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 9 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `drenagem` — Selo Enfraquecedor
- Habilidade declarada antes da transformação V18: `drenagem`; poder/custo declarados: 9 / 4
- Texto da habilidade no catálogo: Diminui em 1 o bônus dos inimigos, até o mínimo de -2.
- Identidade ativa: Flor Escarlate; effect=`scarlet_bloom`
- Texto da identidade: Ao entrar em campo, aplica Podridão Escarlate aos inimigos da fileira. Quem já estiver contaminado recebe uma segunda marca.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Ao entrar em campo, aplica Podridão Escarlate aos inimigos da fileira. Quem já estiver contaminado recebe uma segunda marca. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Espadachim lendária e irmã gêmea de Miquella, luta enquanto a Podridão Escarlate consome seu corpo.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_radahn_flagelo_estrelas` — Radahn, Flagelo das Estrelas

- Categoria/facção/fileira: Unidade / Ordem Áurea / siege
- Poder-base/raridade/custo: 9 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `quebra_ritmo` — Ruptura de Postura
- Habilidade declarada antes da transformação V18: `quebra_ritmo`; poder/custo declarados: 9 / 4
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior.
- Identidade ativa: Gravidade do Flagelo; effect=`star_gravity`
- Texto da identidade: Ao entrar em campo, move o inimigo mais forte para sua fileira e tira 2 pontos de bônus dele.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Ao entrar em campo, move o inimigo mais forte para sua fileira e tira 2 pontos de bônus dele. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: General temido da Fragmentação, dominou a gravidade para deter o curso das estrelas e permaneceu em Caelid após a Podridão.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_maliketh_morte_destinada` — Maliketh, Lâmina Negra

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 8 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `cacador_arcano` — Caçador de Feitiços
- Habilidade declarada antes da transformação V18: `cacador_arcano`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero.
- Identidade ativa: Morte Destinada; effect=`destined_death`
- Texto da identidade: Ao entrar em campo, tira até 2 pontos de bônus do inimigo mais forte.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Ao entrar em campo, tira até 2 pontos de bônus do inimigo mais forte. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Sombra leal de Marika e guardião da Runa da Morte, carrega a Morte Destinada selada em sua lâmina.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_messmer_impalador` — Messmer, o Empalador

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 8 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `quebra_ritmo` — Ruptura de Postura
- Habilidade declarada antes da transformação V18: `quebra_ritmo`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior.
- Identidade ativa: Lança do Impalador; effect=`impaling_spear`
- Texto da identidade: Ao entrar em campo, marca os inimigos da fileira com Sangramento. A segunda marca causa Hemorragia.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Ao entrar em campo, marca os inimigos da fileira com Sangramento. A segunda marca causa Hemorragia. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Filho de Marika e senhor da chama impura, comandou a purga que devastou o Reino das Sombras.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `chefe_placidusax_lorde_dragao` — Placidusax, Lorde Dragão

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 9 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `olho_tempestade` — Olho da Tempestade
- Habilidade declarada antes da transformação V18: `olho_tempestade`; poder/custo declarados: 9 / 4
- Texto da habilidade no catálogo: Recebe +2 quando sua fileira estiver sob efeito climático.
- Identidade ativa: Tempestade do Tempo; effect=`time_storm`
- Texto da identidade: Ao entrar em campo, aplica Geada aos inimigos da fileira e ganha +1 para cada inimigo atingido, até +3.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Ao entrar em campo, aplica Geada aos inimigos da fileira e ganha +1 para cada inimigo atingido, até +3. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Lorde Dragão ancestral que aguarda, em Farum Azula, o retorno de seu deus desaparecido.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `arma_lamina_peregrino` — Duelista da Casa Hoslow

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `primeira_luz`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Duelo do Peregrino
- Tags: peregrino
- Combos compatíveis por tag: Caminho do Maculado
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Herdeiro de uma casa de duelistas, transforma a elegância do aço em uma promessa de sangue.

### `arma_martelo_fornalha` — Ferreiro de Volcano Manor

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `encadeamento`; poder/custo declarados: 6 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Martelo de Cadência
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Entre fornalhas e juramentos de traição, um artesão molda armas para os recusantes do Monte Gelmir.

### `arma_cajado_marulho` — Feiticeiro Cariano

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `cacador_arcano`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Ressonância das Marés
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Discípulo da realeza cariana, conjura feitiçarias de pedra cintilante sob a proteção da lua.

### `arma_duas_luas` — Espadachim da Lua Negra

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 7 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `precisao` — Mira Cariana
- Habilidade declarada antes da transformação V18: `precisao`; poder/custo declarados: 7 / 3
- Texto da habilidade no catálogo: Ganha +1 de poder ao entrar na fileira de Longa Distância.
- Identidade ativa: Dança Espelhada; effect=`twin_dance`
- Texto da identidade: Ganha +1 se você tiver outro aliado em uma fileira diferente.
- Identidade histórica filtrada: —
- Tags: duas_luas, lua_cariana
- Combos compatíveis por tag: Dança da Lua Negra, Convergência da Lua Negra
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Ganha +1 se você tiver outro aliado em uma fileira diferente. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Um duelista das tradições carianas conduz a lâmina sob a luz fria da Lua Negra.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `arma_grande_sino` — Sentinela do Portão de Leyndell

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 8 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `instinto` — Instinto de Caçador
- Habilidade declarada antes da transformação V18: `instinto`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Ganha +2 de poder quando sua pontuação total é menor que a do adversário.
- Identidade ativa: Sino do Último Bastião; effect=`last_bell`
- Texto da identidade: Ganha +2 quando sua pontuação total for menor que a do adversário.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Ganha +2 quando sua pontuação total for menor que a do adversário. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Um guardião de elite protege os acessos da capital e enfrenta qualquer ameaça à ordem dourada.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `arma_agulha_astro` — Leitora de Estrelas de Sellia

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 4 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `primeira_luz`; poder/custo declarados: 3 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Fio Astral
- Tags: astral, lua_cariana
- Combos compatíveis por tag: Alinhamento Astral, Eco das Pedras Cintilantes, Convergência da Lua Negra
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Uma estudiosa de Sellia observa os astros e procura caminhos ocultos na feitiçaria noturna.

### `arma_lanca_fornalha` — Lanceiro da Árvore Áurea

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `primeira_luz`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Investida da Fornalha
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Treinado para defender os domínios da Árvore Áurea, avança com lança e disciplina militar.

### `arma_arco_peregrino` — Batedor da Mansão Vulcânica

- Categoria/facção/fileira: Unidade / Véu Carmesim / ranged
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `impeto`; poder/custo declarados: 5 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Tiro de Cobertura
- Tags: peregrino
- Combos compatíveis por tag: Caminho do Maculado
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um recusante percorre os caminhos do Monte Gelmir, atento às rotas e aos movimentos dos inimigos.

### `magia_brasa_errante` — Monge do Fogo

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 4 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `sangue_frio`; poder/custo declarados: 3 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Brasa Persistente
- Tags: chama
- Combos compatíveis por tag: Chamas do Monte Gelmir
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Devoto do fogo dos gigantes, preserva ritos antigos nas encostas geladas dos Picos dos Gigantes.

### `magia_selo_vigilia` — Confessora da Ordem Áurea

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `adaptacao` — Passo do Peregrino
- Habilidade declarada antes da transformação V18: `adaptacao`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: Ganha +1 de poder se for jogada em uma fileira diferente da sua última unidade.
- Identidade ativa: Selo de Vigília; effect=`vigil_seal`
- Texto da identidade: Reduz em 1 o dano do clima sofrido por esta carta e dá +1 de bônus a um aliado da mesma fileira.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Reduz em 1 o dano do clima sofrido por esta carta e dá +1 de bônus a um aliado da mesma fileira. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Treinada para agir discretamente, a Confessora combina devoção, infiltração e combate próximo.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `magia_trovao_oco` — Dragoeiro Ancião

- Categoria/facção/fileira: Unidade / Ordem Áurea / ranged
- Poder-base/raridade/custo: 6 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `drenagem` — Selo Enfraquecedor
- Habilidade declarada antes da transformação V18: `drenagem`; poder/custo declarados: 6 / 3
- Texto da habilidade no catálogo: Diminui em 1 o bônus dos inimigos, até o mínimo de -2.
- Identidade ativa: Descarga Oca; effect=`hollow_thunder`
- Texto da identidade: Tira 1 ponto de bônus de cada unidade inimiga na mesma fileira.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Tira 1 ponto de bônus de cada unidade inimiga na mesma fileira. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Um guerreiro ligado aos antigos dragões canaliza relâmpagos ancestrais em meio à batalha.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `magia_nevoa_antiga` — Astróloga de Liurnia

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 7 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `encadeamento` — Postura Encadeada
- Habilidade declarada antes da transformação V18: `encadeamento`; poder/custo declarados: 7 / 3
- Texto da habilidade no catálogo: Ganha +2 de poder se for jogada na mesma fileira que sua última unidade.
- Identidade ativa: Névoa Ancestral; effect=`ancient_mist`
- Texto da identidade: Ganha +2 se houver efeito climático em qualquer fileira.
- Identidade histórica filtrada: —
- Tags: astral, lua_cariana
- Combos compatíveis por tag: Alinhamento Astral, Eco das Pedras Cintilantes, Convergência da Lua Negra
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Ganha +2 se houver efeito climático em qualquer fileira. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Sob os céus de Liurnia, uma astróloga procura nas estrelas sinais de destinos ainda ocultos.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `magia_sol_negro` — Apóstolo da Pele Divina

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 8 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `quebra_ritmo` — Ruptura de Postura
- Habilidade declarada antes da transformação V18: `quebra_ritmo`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior.
- Identidade ativa: Eclipse Devorador; effect=`devouring_eclipse`
- Texto da identidade: Ganha +2 se algum inimigo tiver bônus acima de zero.
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id
- Texto exibido pela API principal: Ganha +2 se algum inimigo tiver bônus acima de zero. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Devoto da antiga ordem da Pele Divina, empunha a chama negra associada à morte dos deuses.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `magia_fagulha` — Aprendiz de Feitiçaria Cariana

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `cacador_arcano`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Faísca Condutora
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Um aprendiz da tradição cariana começa a dominar os projéteis de pedra cintilante.

### `magia_orbe_eco` — Erudito da Academia

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `precisao`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Orbe Refrator
- Tags: eco
- Combos compatíveis por tag: Eco das Pedras Cintilantes
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Pesquisador de Raya Lucaria, dedica a vida ao estudo dos segredos das pedras cintilantes.

### `magia_chama_fria` — Feiticeira da Lua Gélida

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 4 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `sangue_frio`; poder/custo declarados: 3 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Contrafogo
- Tags: chama
- Combos compatíveis por tag: Chamas do Monte Gelmir
- Efeito/resolução: identidade antiga filtrada/desativada em runtime; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Uma feiticeira errante combina o frio das antigas artes lunares com chamas de origem desconhecida.

### `covenant_lobos_cinza` — Cavaleiros de Radahn

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `instinto`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: cinzas
- Combos compatíveis por tag: Aliança da Árvore Áurea
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Veteranos da hoste do Flagelo das Estrelas, marcham sob o estandarte do general de Caelid.

### `covenant_lua_velada` — Juramentada de Ranni

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 6 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `primeira_luz` — Graça Dourada
- Habilidade declarada antes da transformação V18: `primeira_luz`; poder/custo declarados: 6 / 3
- Texto da habilidade no catálogo: Na primeira rodada, ganha +1 de poder ao entrar em campo.
- Identidade ativa: Aliança Lunar; effect=`veiled_moon`
- Texto da identidade: Esta carta ganha +1 e dá +1 de bônus a um aliado em outra fileira.
- Identidade histórica filtrada: —
- Tags: duas_luas, lua_cariana
- Combos compatíveis por tag: Dança da Lua Negra, Convergência da Lua Negra
- Efeito/resolução: habilidade genérica declarada, mas suprimida pela identidade ativa; identidade executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Esta carta ganha +1 e dá +1 de bônus a um aliado em outra fileira. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: AMBIGUIDADE DE PAYLOAD: campo habilidade mantém ID genérico; nome/texto usam identidade; o motor suprime o genérico e executa somente a identidade.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Uma aliada juramentada à princesa lunar acompanha sua busca por um caminho além da Ordem Áurea.
- **Alerta de contrato:** a habilidade genérica fica preenchida no campo `habilidade`, mas é suprimida quando há identidade ativa; a preparação exibe nome/texto da identidade. Não há dupla execução.

### `covenant_sentinelas` — Guardiões de Sellia

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `adaptacao`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Sentinela Compartilhada
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Vigias da cidade oculta de Sellia protegem seus segredos e as passagens de feitiçaria.

### `covenant_coroa_abismo` — Cavaleiro da Dinastia Mohgwyn

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 7 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `drenagem` — Selo Enfraquecedor
- Habilidade declarada antes da transformação V18: `drenagem`; poder/custo declarados: 7 / 4
- Texto da habilidade no catálogo: Diminui em 1 o bônus dos inimigos, até o mínimo de -2.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: abismo, sangue_mohgwyn
- Combos compatíveis por tag: Maré Abissal, Ritual do Véu Carmesim
- Efeito/resolução: habilidade genérica executada ao entrar em campo; participa de combo por tags
- Texto exibido pela API principal: Diminui em 1 o bônus dos inimigos, até o mínimo de -2. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um guerreiro jurado à dinastia sanguínea guarda os domínios ocultos de Mohg.

### `covenant_ultimos` — Cavaleiros de sangue juramentados

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `ultimo_folego`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Último Juramento
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Combatentes unidos por juramentos de sangue permanecem ao lado de seu senhor até o último fôlego.

### `covenant_filhos_brasa` — Discípulos do Monge do Fogo

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `contragolpe`; poder/custo declarados: 5 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Herança da Brasa
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Seguidores dos antigos monges preservam a chama dos gigantes e seus rituais esquecidos.

### `covenant_peregrinos_nevoa` — Peregrinos da Cidade Eterna

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `primeira_luz`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: Rastro na Névoa
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: identidade antiga filtrada/desativada em runtime
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Viajantes das cidades subterrâneas cruzam a escuridão em busca de uma nova estrela.

### `covenant_irmandade_ferro` — Guardas da Árvore Áurea

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 4 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `retaliacao` — Retaliação dos Semideuses
- Habilidade declarada antes da transformação V18: `retaliacao`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: Ganha +1 de poder quando sua pontuação total é menor que a do adversário.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: estandarte
- Combos compatíveis por tag: Juramento de Leyndell
- Efeito/resolução: habilidade genérica executada ao entrar em campo; participa de combo por tags
- Texto exibido pela API principal: Ganha +1 de poder quando sua pontuação total é menor que a do adversário.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Defensores juramentados protegem os caminhos e santuários consagrados à Árvore Áurea.

### `gwent_especial_tempestade` — Tempestade dos Picos

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_clima` — Tempestade dos Picos
- Habilidade declarada antes da transformação V18: `gwent_clima`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Escolha uma fileira. A tempestade reduz em 1 o poder efetivo de todas as unidades dos dois lados nessa fileira enquanto o clima estiver ativo.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Escolha uma fileira. A tempestade reduz em 1 o poder efetivo de todas as unidades dos dois lados nessa fileira enquanto o clima estiver ativo. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Nuvens pesadas cobrem uma fileira. A chuva atravessa as defesas e enfraquece todas as unidades expostas enquanto o clima durar.

### `gwent_especial_nevoa` — Miasma da Podridão

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_nevoa` — Névoa de Sellia
- Habilidade declarada antes da transformação V18: `gwent_nevoa`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Aplica 1 marca de Podridão Escarlate a todas as unidades inimigas da fileira escolhida; raridades Lendárias ou superiores aplicam uma segunda marca.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Aplica 1 marca de Podridão Escarlate a todas as unidades inimigas da fileira escolhida; raridades Lendárias ou superiores aplicam uma segunda marca.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_nevoa
- Lore/descrição atual: Uma nuvem pútrida se espalha pelo campo, lembrando os pântanos corrompidos de Caelid.

### `gwent_especial_geada` — Geada dos Picos dos Gigantes

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_geada` — Lua Gélida
- Habilidade declarada antes da transformação V18: `gwent_geada`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Aplica 1 marca de Geada a todas as unidades inimigas em campo; raridades Lendárias ou superiores aplicam uma segunda marca.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Aplica 1 marca de Geada a todas as unidades inimigas em campo; raridades Lendárias ou superiores aplicam uma segunda marca.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_geada
- Lore/descrição atual: O frio dos Picos dos Gigantes avança sobre o campo e silencia o vigor dos combatentes.

### `gwent_especial_chuva` — Sangue Corrompido

- Categoria/facção/fileira: Especial / Véu Carmesim / melee
- Poder-base/raridade/custo: 0 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `gwent_chuva` — Sangue Corrompido
- Habilidade declarada antes da transformação V18: `gwent_chuva`; poder/custo declarados: — / 1
- Texto da habilidade no catálogo: Aplica uma marca de Sangramento a todas as unidades inimigas na fileira de Cerco; a segunda marca reduz 2 de bônus (mínimo -2) e consome as marcas.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Aplica uma marca de Sangramento a todas as unidades inimigas na fileira de Cerco; a segunda marca reduz 2 de bônus (mínimo -2) e consome as marcas.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_chuva
- Lore/descrição atual: Um rito sanguíneo mancha o campo de batalha com a promessa de uma dívida ainda não paga.

### `gwent_especial_chifre` — Rugido de Godfrey

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `gwent_chifre` — Rugido de Godfrey
- Habilidade declarada antes da transformação V18: `gwent_chifre`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Concede +2 às suas unidades na fileira escolhida até o fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Concede +2 às suas unidades na fileira escolhida até o fim da rodada. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_chifre
- Lore/descrição atual: O rugido do Primeiro Lorde Prístino ecoa entre as fileiras e reacende a coragem dos guerreiros.

### `gwent_especial_medico` — Lágrima Sagrada

- Categoria/facção/fileira: Especial / Véu Carmesim / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_medico` — Lágrima Sagrada
- Habilidade declarada antes da transformação V18: `gwent_medico`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Devolve à sua mão uma unidade do seu descarte com poder-base 4 ou menos; você pode escolher o alvo.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Devolve à sua mão uma unidade do seu descarte com poder-base 4 ou menos; você pode escolher o alvo. Raridade Rara: recupera unidade com poder-base até 5.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_medico
- Lore/descrição atual: Uma lágrima consagrada guarda a memória dos que tombaram e ainda podem retornar à jornada.

### `gwent_especial_queima` — Chama Negra

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `gwent_queima` — Chama Negra
- Habilidade declarada antes da transformação V18: `gwent_queima`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Tenta remover a unidade de maior poder efetivo de cada lado; um escudo pode bloquear cada remoção.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Tenta remover a unidade de maior poder efetivo de cada lado; um escudo pode bloquear cada remoção.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_queima
- Lore/descrição atual: A chama negra, temida até pelos deuses, consome tudo o que toca.

### `gwent_especial_purificar` — Lei da Regressão

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_purificar` — Lei da Regressão
- Habilidade declarada antes da transformação V18: `gwent_purificar`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Remove todos os efeitos climáticos.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Remove todos os efeitos climáticos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_purificar
- Lore/descrição atual: A Lei da Regressão revela a verdade por trás das ilusões e desfaz os véus que encobrem o mundo.

### `gwent_especial_execucao` — Lâmina da Morte Destinada

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `gwent_execucao` — Lâmina da Morte Destinada
- Habilidade declarada antes da transformação V18: `gwent_execucao`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Remove uma unidade inimiga escolhida da fileira selecionada se ela tiver poder efetivo 6 ou menos; um escudo pode bloquear a remoção.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Remove uma unidade inimiga escolhida da fileira selecionada se ela tiver poder efetivo 6 ou menos; um escudo pode bloquear a remoção. Raridade Épica: alcança poder efetivo até 6.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_execucao
- Lore/descrição atual: A lâmina da Morte Destinada carrega o fragmento de um poder que deveria permanecer selado.

### `gwent_especial_vinculo` — Juramento do Crisol

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_vinculo` — Juramento do Crisol
- Habilidade declarada antes da transformação V18: `gwent_vinculo`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Se houver ao menos duas unidades aliadas na fileira escolhida, concede +2 a todas elas até o fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Se houver ao menos duas unidades aliadas na fileira escolhida, concede +2 a todas elas até o fim da rodada. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_vinculo
- Lore/descrição atual: Um juramento ancestral une os guerreiros às formas primordiais que precederam a Erdtree.

### `gwent_especial_batedor` — Passo do Cão de Caça

- Categoria/facção/fileira: Especial / Véu Carmesim / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_batedor` — Passo do Cão de Caça
- Habilidade declarada antes da transformação V18: `gwent_batedor`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Compra uma carta da reserva, se disponível.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Compra uma carta da reserva, se disponível. Raridade Rara: compra até 2 cartas.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_batedor
- Lore/descrição atual: O passo do cão de caça atravessa o campo antes que o inimigo perceba sua aproximação.

### `gwent_especial_muralha` — Bastião de Leyndell

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `gwent_muralha` — Bastião de Leyndell
- Habilidade declarada antes da transformação V18: `gwent_muralha`; poder/custo declarados: — / 1
- Texto da habilidade no catálogo: Concede +1 às suas unidades na fileira escolhida até o fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Concede +1 às suas unidades na fileira escolhida até o fim da rodada.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_muralha
- Lore/descrição atual: As muralhas douradas de Leyndell erguem-se como símbolo da resistência da capital.

### `elden_especial_sangramento` — Ritual de Sangue

- Categoria/facção/fileira: Especial / Véu Carmesim / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_sangramento` — Sangramento
- Habilidade declarada antes da transformação V18: `gwent_sangramento`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Marca as unidades inimigas da fileira; a segunda marca reduz o bônus em 2 (mínimo -2) e consome as marcas. Marcas expiram no fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Marca as unidades inimigas da fileira; a segunda marca reduz o bônus em 2 (mínimo -2) e consome as marcas. Marcas expiram no fim da rodada. Raridade Rara: aplica uma marca extra a até 1 alvo(s), podendo ativar hemorragia imediatamente.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: O ritual desperta o poder do sangue e transforma cada ferida em um presságio de ruína.

### `elden_especial_geada` — Lua Cheia de Rennala

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_geada_cariana` — Geada Cariana
- Habilidade declarada antes da transformação V18: `gwent_geada_cariana`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Aplica até duas marcas às unidades inimigas da fileira escolhida; cada marca reduz 1 de poder efetivo até o fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Aplica até duas marcas às unidades inimigas da fileira escolhida; cada marca reduz 1 de poder efetivo até o fim da rodada. Raridade Rara: aplica uma segunda marca a até 1 alvo(s).
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A lua cheia de Rennala ilumina o campo com a frieza ancestral da realeza cariana.

### `elden_especial_podrida` — Flor da Podridão Escarlate

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `gwent_podrida` — Podridão Escarlate
- Habilidade declarada antes da transformação V18: `gwent_podrida`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Cada marca reduz 1 de poder efetivo; a segunda também corrói 1 ponto de bônus positivo, se houver. Marcas expiram no fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Cada marca reduz 1 de poder efetivo; a segunda também corrói 1 ponto de bônus positivo, se houver. Marcas expiram no fim da rodada. Raridade Épica: pode aplicar a segunda marca imediatamente a até 1 alvo(s).
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A flor escarlate floresce onde a podridão encontra carne, pedra e memória.

### `elden_especial_loucura` — Chama Frenética

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `gwent_loucura` — Loucura Frenética
- Habilidade declarada antes da transformação V18: `gwent_loucura`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Cada marca reduz 1 de poder efetivo; a segunda remove todos os bônus positivos da unidade. Marcas expiram no fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Cada marca reduz 1 de poder efetivo; a segunda remove todos os bônus positivos da unidade. Marcas expiram no fim da rodada. Raridade Épica: pode aplicar a segunda marca imediatamente a até 1 alvo(s).
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A chama frenética consome razão e identidade, deixando apenas o caos da Chama Frenética.

### `elden_especial_chama` — Chama do Gigante

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_chama` — Chama do Gigante
- Habilidade declarada antes da transformação V18: `gwent_chama`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Remove Geada de todas as suas unidades; cada unidade purificada recebe +1 de poder até o fim da rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Remove Geada de todas as suas unidades; cada unidade purificada recebe +1 de poder até o fim da rodada. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A chama dos gigantes arde contra o frio que tenta aprisionar os vivos.

### `elden_especial_invocacao` — Cinzas dos Lobos Solitários

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_invocacao` — Cinzas dos Lobos Solitários
- Habilidade declarada antes da transformação V18: `gwent_invocacao`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Invoca Lobos Espirituais com 3 de poder na fileira escolhida.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Invoca Lobos Espirituais com 3 de poder na fileira escolhida. Raridade Rara: invoca lobos com 4 de poder.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Cinzas antigas despertam os espíritos de lobos que outrora caçaram ao lado de seus mestres.

### `reliquia_grande_runa_godrick` — Grande Runa de Godrick

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Lendária / 3 (tabela por raridade: 4)
- Habilidade nominal runtime: `reliquia_godrick` — Grande Runa de Godrick
- Habilidade declarada antes da transformação V18: `reliquia_godrick`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Exige ao menos uma unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Exige ao menos uma unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Fragmento do Anel Prístino reivindicado por Godrick, o Enxertado, que buscava poder por meio do enxerto.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `reliquia_runa_nao_nascidos` — Grande Runa dos Não Nascidos

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Lendária / 3 (tabela por raridade: 4)
- Habilidade nominal runtime: `reliquia_renala` — Grande Runa dos Não Nascidos
- Habilidade declarada antes da transformação V18: `reliquia_renala`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Remove Geada e Podridão das unidades aliadas afetadas; cada unidade purificada recebe +1 de bônus.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Remove Geada e Podridão das unidades aliadas afetadas; cada unidade purificada recebe +1 de bônus.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A Grande Runa guardada por Rennala conserva o poder do renascimento e da perfeição inacabada.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `reliquia_runa_morte` — Runa da Morte

- Categoria/facção/fileira: Especial / Véu Carmesim / melee
- Poder-base/raridade/custo: 0 / Mítica / 4 (tabela por raridade: 5)
- Habilidade nominal runtime: `reliquia_morte` — Runa da Morte
- Habilidade declarada antes da transformação V18: `reliquia_morte`; poder/custo declarados: — / 4
- Texto da habilidade no catálogo: Em cada fileira, reduz em até 2 o bônus positivo da unidade inimiga que tiver o maior bônus naquela fileira.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Em cada fileira, reduz em até 2 o bônus positivo da unidade inimiga que tiver o maior bônus naquela fileira.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: O fragmento da Morte Destinada recorda o poder que Maliketh recebeu para manter selado.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `reliquia_noite_chama` — Espada da Noite e da Chama

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Lendária / 3 (tabela por raridade: 4)
- Habilidade nominal runtime: `reliquia_noite_chama` — Espada da Noite e da Chama
- Habilidade declarada antes da transformação V18: `reliquia_noite_chama`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Na postura da Noite, aplica Geada a todas as unidades inimigas da fileira escolhida. Na postura da Chama, atinge a unidade de maior poder efetivo: reduz 1 de poder-base e 2 de bônus; Escudo bloqueia o golpe.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Na postura da Noite, aplica Geada a todas as unidades inimigas da fileira escolhida. Na postura da Chama, atinge a unidade de maior poder efetivo: reduz 1 de poder-base e 2 de bônus; Escudo bloqueia o golpe.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Arma lendária da Mansão Cariana. Sua postura especial libera um ataque mágico ou uma onda de fogo.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `reliquia_lamina_negra` — Lâmina Negra

- Categoria/facção/fileira: Especial / Véu Carmesim / melee
- Poder-base/raridade/custo: 0 / Mítica / 4 (tabela por raridade: 5)
- Habilidade nominal runtime: `reliquia_lamina_negra` — Lâmina Negra
- Habilidade declarada antes da transformação V18: `reliquia_lamina_negra`; poder/custo declarados: — / 4
- Texto da habilidade no catálogo: Na fileira escolhida, reduz em 3 o bônus de uma unidade inimiga (a escolhida ou a de maior poder efetivo). Escudo bloqueia o efeito sem consumir a Relíquia.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Na fileira escolhida, reduz em 3 o bônus de uma unidade inimiga (a escolhida ou a de maior poder efetivo). Escudo bloqueia o efeito sem consumir a Relíquia.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A arma de Maliketh, que guarda a Morte Destinada selada em sua lâmina. Não é uma das adagas usadas pelas Assassinas da Faca Negra.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `reliquia_algemas_margit` — Algemas de Margit

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Épica / 2 (tabela por raridade: 3)
- Habilidade nominal runtime: `reliquia_algemas` — Algemas de Margit
- Habilidade declarada antes da transformação V18: `reliquia_algemas`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Na fileira escolhida, zera o bônus positivo de uma unidade inimiga (a escolhida ou a de maior bônus); bônus negativos permanecem inalterados.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Na fileira escolhida, zera o bônus positivo de uma unidade inimiga (a escolhida ou a de maior bônus); bônus negativos permanecem inalterados.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Correntes forjadas para conter o Agouro caído, capazes de subjugar até mesmo um inimigo temível.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `gwent_unidade_baluarte` — Cavaleiro do Crisol

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `guardiao_fileira`; poder/custo declarados: 6 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fornalha, ordem_dourada
- Combos compatíveis por tag: Aliança da Árvore Áurea, Juramento da Árvore Áurea
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um cavaleiro do Crisol, marcado pelas antigas formas que antecederam a Árvore Áurea, guarda a formação com disciplina.

### `gwent_unidade_lamina_sem_juramento` — Caçador de Dedos

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `cacador_solitario`; poder/custo declarados: 6 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: sem efeito individual/tag/identidade
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Caçador de Dedos, um duelista errante que prefere trilhas solitárias e confrontos sem testemunhas.

### `gwent_unidade_portaestandarte` — Porta-estandarte de Leyndell

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `estandarte`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: estandarte, fornalha, ordem_dourada
- Combos compatíveis por tag: Aliança da Árvore Áurea, Juramento de Leyndell, Juramento da Árvore Áurea
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: O estandarte de Leyndell reúne soldados dispersos sob o símbolo dourado da capital.

### `gwent_unidade_oraculo_clima` — Profeta de Liurnia

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `resistencia_climatica`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: sem efeito individual/tag/identidade
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: O profeta de Liurnia observa as mudanças do céu e interpreta os sinais trazidos por tempestades e geadas.

### `gwent_unidade_eco` — Erudito das Pedras Cintilantes

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `eco_arcano`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: astral, eco
- Combos compatíveis por tag: Alinhamento Astral, Eco das Pedras Cintilantes
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um estudioso das pedras cintilantes investiga as ressonâncias deixadas por feitiçarias antigas.

### `gwent_unidade_cavaleira` — Cavaleira Cariana

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `quebra_ritmo`; poder/custo declarados: 5 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: veu_sombrio
- Combos compatíveis por tag: Caçada da Faca Negra
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Uma duelista cariana, treinada nas tradições de combate da realeza lunar.

### `gwent_unidade_gigante` — Gigante de Fogo

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 7 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `instinto` — Instinto de Caçador
- Habilidade declarada antes da transformação V18: `instinto`; poder/custo declarados: 7 / 3
- Texto da habilidade no catálogo: Ganha +2 de poder quando sua pontuação total é menor que a do adversário.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +2 de poder quando sua pontuação total é menor que a do adversário. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Uma presença colossal na linha de frente.

### `gwent_unidade_cartografa` — Exploradora da Cidade Eterna

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `adaptacao`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: duas_luas
- Combos compatíveis por tag: Dança da Lua Negra
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Encontra rotas onde os outros veem obstáculos.

### `gwent_unidade_invocador` — Apóstolo da Pele Divina Errante

- Categoria/facção/fileira: Unidade / Véu Carmesim / siege
- Poder-base/raridade/custo: 7 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `cacador_arcano` — Caçador de Feitiços
- Habilidade declarada antes da transformação V18: `cacador_arcano`; poder/custo declarados: 7 / 3
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: astral
- Combos compatíveis por tag: Alinhamento Astral, Eco das Pedras Cintilantes
- Efeito/resolução: habilidade genérica executada ao entrar em campo; participa de combo por tags
- Texto exibido pela API principal: Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Converte conhecimento arcano em força de combate.

### `gwent_unidade_mestre_forja` — Mestre Ferreiro de Volcano Manor

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `dupla_fornalha`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fornalha, ordem_dourada
- Combos compatíveis por tag: Aliança da Árvore Áurea, Juramento da Árvore Áurea
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um mestre ferreiro de Volcano Manor trabalha entre brasas, aço e os juramentos dos recusantes.

### `gwent_unidade_dupla_veu` — Gêmeas da Cidade Eterna

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `irmandade_veu`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: duas_luas, veu_sombrio
- Combos compatíveis por tag: Caçada da Faca Negra, Dança da Lua Negra
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Duas irmãs das Cidades Eternas percorrem caminhos subterrâneos que raramente aparecem nos mapas.

### `gwent_unidade_circulo` — Discípulo da Academia

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `circulo_arcano`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: astral
- Combos compatíveis por tag: Alinhamento Astral, Eco das Pedras Cintilantes
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Discípulo de Raya Lucaria, dedica-se ao estudo dos círculos arcanos e dos resíduos de feitiçaria.

### `gwent_unidade_sentinela_rubra` — Cavaleiro de Radahn

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `escudo_ferro`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: muralha, ordem_dourada
- Combos compatíveis por tag: Defesa de Leyndell, Juramento da Árvore Áurea
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um cavaleiro da hoste de Radahn mantém sua posição sob o estandarte vermelho de Caelid.

### `gwent_unidade_veterano_cercos` — Cavaleiro Draconiano

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `sobrevivente`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: muralha
- Combos compatíveis por tag: Defesa de Leyndell
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Já viu mais muralhas caírem do que rostos conhecidos.

### `gwent_unidade_herdeiro_portao` — Godwyn, o Dourado

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 6 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `vinganca` — Vingança
- Habilidade declarada antes da transformação V18: `vinganca`; poder/custo declarados: 6 / 3
- Texto da habilidade no catálogo: Ao cair, concede +1 às unidades aliadas da mesma fileira.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: muralha, ordem_dourada
- Combos compatíveis por tag: Defesa de Leyndell, Juramento da Árvore Áurea
- Efeito/resolução: efeito de ciclo de vida executado fora da entrada; participa de combo por tags
- Texto exibido pela API principal: Ao cair, concede +1 às unidades aliadas da mesma fileira. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: aura:vinganca
- Lore/descrição atual: Quando cai, a formação inteira jura vingá-lo.

### `gwent_unidade_carniceiro_forja` — Carrasco de Volcano Manor

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `devorar` — Devorar
- Habilidade declarada antes da transformação V18: `devorar`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: Ao entrar, consome a unidade aliada de menor poder efetivo na mesma fileira e recebe bônus igual ao poder dela, até +4.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: banquete, sangue_mohgwyn
- Combos compatíveis por tag: Banquete de Sangue, Ritual do Véu Carmesim
- Efeito/resolução: habilidade genérica executada ao entrar em campo; participa de combo por tags
- Texto exibido pela API principal: Ao entrar, consome a unidade aliada de menor poder efetivo na mesma fileira e recebe bônus igual ao poder dela, até +4. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: aura:devorar
- Lore/descrição atual: Consome os restos da batalha para ampliar a própria força.

### `gwent_unidade_intendente` — Mercador Nômade

- Categoria/facção/fileira: Unidade / Ordem Áurea / ranged
- Poder-base/raridade/custo: 4 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `espolios`; poder/custo declarados: 3 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: banquete
- Combos compatíveis por tag: Banquete de Sangue
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um mercador nômade percorre as Terras Intermédias levando provisões e notícias entre assentamentos.

### `gwent_unidade_cacadora_fantasma` — Assassina de Ravenmount

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `sobrevivente`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fantasmas
- Combos compatíveis por tag: Procissão dos que Vivem na Morte
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Uma assassina de Ravenmount atravessa a névoa sem deixar rastros fáceis de seguir.

### `gwent_unidade_cantora_lamentos` — Fia, Companheira do Leito de Morte

- Categoria/facção/fileira: Unidade / Véu Carmesim / ranged
- Poder-base/raridade/custo: 5 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `ressurgir`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fantasmas
- Combos compatíveis por tag: Procissão dos que Vivem na Morte
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Fia, Companheira do Leito de Morte, entoa lamentos pelos que encontraram repouso entre os mortos.

### `gwent_unidade_senhor_cacada` — Blaidd, o Meio-Lobo

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 6 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `vinganca` — Vingança
- Habilidade declarada antes da transformação V18: `vinganca`; poder/custo declarados: 6 / 3
- Texto da habilidade no catálogo: Ao cair, concede +1 às unidades aliadas da mesma fileira.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fantasmas
- Combos compatíveis por tag: Procissão dos que Vivem na Morte
- Efeito/resolução: efeito de ciclo de vida executado fora da entrada; participa de combo por tags
- Texto exibido pela API principal: Ao cair, concede +1 às unidades aliadas da mesma fileira. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: aura:vinganca
- Lore/descrição atual: A presa que o derruba desperta a matilha inteira.

### `gwent_unidade_saqueadora_veu` — Ladina da Cidade Eterna

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `espolios`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: caravana
- Combos compatíveis por tag: Saque da Cidade Eterna
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Nenhuma rota é cara demais para quem leva o butim.

### `gwent_unidade_contrabandista` — Recusante da Mansão Vulcânica

- Categoria/facção/fileira: Unidade / Véu Carmesim / ranged
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `escudo_ferro`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: caravana
- Combos compatíveis por tag: Saque da Cidade Eterna
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um recusante de Volcano Manor, acostumado a negociar favores e segredos nas encostas do Monte Gelmir.

### `gwent_unidade_guardiao_runas` — Guardião da Ordem Áurea

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `escudo_ferro`; poder/custo declarados: 5 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: runico
- Combos compatíveis por tag: Ritual das Runas
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um guardião da Ordem Áurea carrega inscrições rúnicas ligadas aos ensinamentos da capital.

### `gwent_unidade_necromante` — Servo dos que Vivem na Morte

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `ressurgir` — Ressurgir
- Habilidade declarada antes da transformação V18: `ressurgir`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: Se houver uma unidade elegível, traz do descarte a mais forte com poder base 5 ou menos diretamente ao campo.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: runico
- Combos compatíveis por tag: Ritual das Runas
- Efeito/resolução: habilidade genérica executada ao entrar em campo; participa de combo por tags
- Texto exibido pela API principal: Se houver uma unidade elegível, traz do descarte a mais forte com poder base 5 ou menos diretamente ao campo. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: aura:ressurgir
- Lore/descrição atual: Desperta no campo os que o descarte ainda guarda.

### `gwent_unidade_detonador` — Guerreiro da Chama Frenética

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `vinganca` — Vingança
- Habilidade declarada antes da transformação V18: `vinganca`; poder/custo declarados: 6 / 3
- Texto da habilidade no catálogo: Ao cair, concede +1 às unidades aliadas da mesma fileira.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: runico
- Combos compatíveis por tag: Ritual das Runas
- Efeito/resolução: efeito de ciclo de vida executado fora da entrada; participa de combo por tags
- Texto exibido pela API principal: Ao cair, concede +1 às unidades aliadas da mesma fileira. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: aura:vinganca
- Lore/descrição atual: Sua queda libera a energia que ele guardava.

### `gwent_unidade_devorador_mana` — Cavaleiro de Sangue de Mohg

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `devorar`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: eclipse_voraz, sangue_mohgwyn
- Combos compatíveis por tag: Eclipse Sanguíneo, Ritual do Véu Carmesim
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um cavaleiro ligado ao sangue de Mohg participa dos rituais sombrios da dinastia subterrânea.

### `gwent_unidade_bibliotecaria` — Bibliotecária de Raya Lucaria

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 5 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `espolios`; poder/custo declarados: 4 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: eclipse_voraz
- Combos compatíveis por tag: Eclipse Sanguíneo
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: O conhecimento reunido na guerra vale mais que ouro.

### `gwent_especial_egide` — Bênção da Árvore Áurea

- Categoria/facção/fileira: Especial / Ordem Áurea / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_egide` — Bênção da Árvore Áurea
- Habilidade declarada antes da transformação V18: `gwent_egide`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Concede escudo a uma unidade sua.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Concede escudo a uma unidade sua. Raridade Rara: protege até 2 unidades.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_egide
- Lore/descrição atual: Concede escudo a uma unidade sua (a escolhida, ou a mais forte sem escudo).

### `gwent_especial_requiem` — Chamado dos Mortos

- Categoria/facção/fileira: Especial / Lua Negra / melee
- Poder-base/raridade/custo: 0 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `gwent_requiem` — Chamado dos Mortos
- Habilidade declarada antes da transformação V18: `gwent_requiem`; poder/custo declarados: — / 3
- Texto da habilidade no catálogo: Traz do descarte diretamente ao campo uma unidade com poder base 6 ou menos.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Traz do descarte diretamente ao campo uma unidade com poder base 6 ou menos. Raridade Épica: recupera unidade com poder-base até 7.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_requiem
- Lore/descrição atual: Traz direto ao campo uma unidade com poder base 6 ou menos do seu descarte (a escolhida, ou a mais forte).

### `gwent_especial_passo` — Passo do Lobo

- Categoria/facção/fileira: Especial / Véu Carmesim / melee
- Poder-base/raridade/custo: 0 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `gwent_passo` — Passo do Lobo
- Habilidade declarada antes da transformação V18: `gwent_passo`; poder/custo declarados: — / 2
- Texto da habilidade no catálogo: Move uma unidade sua para a fileira escolhida.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: Especial: possui ramo/ação no motor (requer ação especial).
- Texto exibido pela API principal: Move uma unidade sua para a fileira escolhida. Raridade Rara: move até 2 unidades.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: emblema:gwent_passo
- Lore/descrição atual: Move uma unidade sua para a fileira escolhida (a escolhida, ou a mais fraca fora dela).

### `gwent_mitica_coroa` — Cavaleiro Consagrado do Haligtree

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 8 / Mítica / 5 (tabela por raridade: 5)
- Habilidade nominal runtime: `estandarte` — Estandarte
- Habilidade declarada antes da transformação V18: `estandarte`; poder/custo declarados: 8 / 5
- Texto da habilidade no catálogo: Concede +1 às outras unidades aliadas da mesma fileira.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Concede +1 às outras unidades aliadas da mesma fileira. Raridade Mítica: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Uma presença mítica que fortalece a formação aliada.

### `gwent_singular_primeiro` — Juramento Primordial do Crisol

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 10 / Singular / 0 (tabela por raridade: 0)
- Habilidade nominal runtime: `cacador_solitario` — Caçador Solitário
- Habilidade declarada antes da transformação V18: `cacador_solitario`; poder/custo declarados: 10 / —
- Texto da habilidade no catálogo: +2 se não houver outra unidade sua na fileira.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: +2 se não houver outra unidade sua na fileira. Raridade Singular: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Exemplar singular conquistado por um feito extraordinário.

### `gwent_singular_intocavel` — Adaga da Faca Negra

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 9 / Singular / 0 (tabela por raridade: 0)
- Habilidade nominal runtime: `precisao` — Mira Cariana
- Habilidade declarada antes da transformação V18: `precisao`; poder/custo declarados: 9 / —
- Texto da habilidade no catálogo: Ganha +1 de poder ao entrar na fileira de Longa Distância.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +1 de poder ao entrar na fileira de Longa Distância. Raridade Singular: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Conquistada ao concluir um desafio sem sofrer dano.

### `gwent_singular_nivel1` — Vontade de Marika

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 10 / Singular / 0 (tabela por raridade: 0)
- Habilidade nominal runtime: `ultimo_folego` — Último Suspiro
- Habilidade declarada antes da transformação V18: `ultimo_folego`; poder/custo declarados: 10 / —
- Texto da habilidade no catálogo: Na terceira rodada, ganha +1 de poder ao entrar em campo.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Na terceira rodada, ganha +1 de poder ao entrar em campo. Raridade Singular: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Conquistada ao vencer um desafio no nível um.

### `gwent_singular_cacador_chefes` — Coroa do Lorde Prístino

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 9 / Singular / 0 (tabela por raridade: 0)
- Habilidade nominal runtime: `paradoxo_eterno` — Paradoxo Eterno
- Habilidade declarada antes da transformação V18: `paradoxo_eterno`; poder/custo declarados: 9 / —
- Texto da habilidade no catálogo: Recebe +2 na terceira rodada se o adversário venceu a segunda.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Recebe +2 na terceira rodada se o adversário venceu a segunda. Raridade Singular: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Conquistada ao derrotar todos os chefes de um desafio.

### `luterano_cruzado` — Cruzado Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / melee
- Poder-base/raridade/custo: 6 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `sinergia_faccao` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `sinergia_faccao`; poder/custo declarados: 6 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, gloria_divina
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: ID de habilidade não catalogado em HABILIDADES; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um guerreiro sagrado que luta pela fé, mesmo após ser esquecido pelo mundo. Ganha força com aliados da mesma facção.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_missionario` — Missionário Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / ranged
- Poder-base/raridade/custo: 5 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `legado`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: evangelho, fe
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Espalha a palavra divina. Se venceu a rodada anterior, entra com +2 de poder.

### `luterano_bispo` — Bispo Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / siege
- Poder-base/raridade/custo: 5 / Lendária / 3 (tabela por raridade: 4)
- Habilidade nominal runtime: `devoto` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `devoto`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: devocao, fe
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: ID de habilidade não catalogado em HABILIDADES; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Líder espiritual que fortalece aliados da mesma facção.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_anjo` — Anjo Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / ranged
- Poder-base/raridade/custo: 3 / Épica / 2 (tabela por raridade: 3)
- Habilidade nominal runtime: `gloria` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `gloria`; poder/custo declarados: 3 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, gloria_divina
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: efeito de ciclo de vida executado fora da entrada; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Mensageiro divino que permanece no campo se vencer a rodada.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_papa` — Papa Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / siege
- Poder-base/raridade/custo: 7 / Mítica / 4 (tabela por raridade: 5)
- Habilidade nominal runtime: `sinergia_faccao` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `sinergia_faccao`; poder/custo declarados: 7 / 4
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, soberania
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: ID de habilidade não catalogado em HABILIDADES; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Mítica: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Sumo sacerdote esquecido. Sua presença fortalece todos os aliados da fé.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_sacerdote` — Sacerdote Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / ranged
- Poder-base/raridade/custo: 5 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `devoto`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, sacerdos
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Cura e fortalece aliados da mesma facção.

### `luterano_irmao` — Irmão Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / melee
- Poder-base/raridade/custo: 4 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `legado`; poder/custo declarados: 3 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, irmandade
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Um irmão de fé que ganha força ao vencer.

### `luterano_diacon` — Diácono Esquecido

- Categoria/facção/fileira: Unidade / Os Esquecidos / ranged
- Poder-base/raridade/custo: 3 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `escolha_ritmo`; poder/custo declarados: 2 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: diaconia, fe
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Auxilia nos rituais e escolhe o melhor momento para agir.

### `gwent_v75_ordem_veterano_juramento` — Veterano do Juramento Dourado

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: Juramento Dourado; effect=`v75_golden_vow`
- Texto da identidade: Ao entrar, recebe +1; se houver aliado na mesma fileira, o aliado mais fraco também recebe +1.
- Identidade histórica filtrada: —
- Tags: v75_erdtree_oath
- Combos compatíveis por tag: Juramento do Crisol e da Graça
- Efeito/resolução: identidade ativa executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Ao entrar, recebe +1; se houver aliado na mesma fileira, o aliado mais fraco também recebe +1. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Identidade exibida e executada.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Veterano de Leyndell que mantém a formação unida: ao entrar, fortalece a si e o aliado mais fraco da mesma fileira.

### `gwent_v75_ordem_guardiao_crisol` — Guardião do Crisol Menor

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: v75_crucible_guard
- Combos compatíveis por tag: Juramento do Crisol e da Graça
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Não possui habilidade individual. Pode completar combos da Ordem Áurea quando estiver em campo com a unidade compatível.

### `gwent_v75_ordem_confessora_graca` — Confessora da Graça Serena

- Categoria/facção/fileira: Unidade / Ordem Áurea / siege
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: Regressão Serena; effect=`v75_grace_mender`
- Texto da identidade: Purifica até dois aliados da mesma fileira de estados negativos; cada aliado purificado recebe +1. Se ninguém precisar de purificação, fortalece o aliado mais fraco em +1.
- Identidade histórica filtrada: —
- Tags: v75_erdtree_oath
- Combos compatíveis por tag: Juramento do Crisol e da Graça
- Efeito/resolução: identidade ativa executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Purifica até dois aliados da mesma fileira de estados negativos; cada aliado purificado recebe +1. Se ninguém precisar de purificação, fortalece o aliado mais fraco em +1. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Identidade exibida e executada.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Uma Confessora treinada na Lei da Regressão remove condições negativas de até dois aliados na fileira de Cerco e os fortalece.

### `gwent_v75_ordem_arauto_estandarte` — Arauto do Estandarte Áureo

- Categoria/facção/fileira: Unidade / Ordem Áurea / ranged
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: v75_crucible_guard
- Combos compatíveis por tag: Juramento do Crisol e da Graça
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Épica: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Não possui habilidade individual. Pode completar combos de formação da Ordem Áurea com a unidade compatível.

### `gwent_v75_veu_acolito_sangue` — Acólito da Dinastia Sanguínea

- Categoria/facção/fileira: Unidade / Véu Carmesim / ranged
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: Marca da Dinastia; effect=`v75_blood_mark`
- Texto da identidade: Aplica uma marca de Sangramento ao inimigo mais forte da fileira; a segunda marca provoca Hemorragia e reduz 2 de bônus.
- Identidade histórica filtrada: —
- Tags: v75_blood_mark
- Combos compatíveis por tag: Banquete da Hemorragia
- Efeito/resolução: identidade ativa executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Aplica uma marca de Sangramento ao inimigo mais forte da fileira; a segunda marca provoca Hemorragia e reduz 2 de bônus. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Identidade exibida e executada.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Servo do Palácio de Mohgwyn que marca o inimigo mais forte da fileira; a segunda marca provoca Hemorragia.

### `gwent_v75_veu_devota_hemorragia` — Devota da Hemorragia

- Categoria/facção/fileira: Unidade / Véu Carmesim / siege
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: v75_blood_feast
- Combos compatíveis por tag: Banquete da Hemorragia
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Não possui habilidade individual. Pode completar o combo Banquete da Hemorragia com a unidade compatível.

### `gwent_v75_veu_carrasco_preco` — Carrasco da Procissão Carmesim

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: Preço em Sangue; effect=`v75_blood_price`
- Texto da identidade: Sacrifica o aliado mais fraco da mesma fileira e recebe bônus igual ao seu poder efetivo, até +3; sem aliado, recebe +1.
- Identidade histórica filtrada: —
- Tags: v75_blood_feast
- Combos compatíveis por tag: Banquete da Hemorragia
- Efeito/resolução: identidade ativa executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Sacrifica o aliado mais fraco da mesma fileira e recebe bônus igual ao seu poder efetivo, até +3; sem aliado, recebe +1. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Identidade exibida e executada.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: O carrasco sacrifica o aliado mais fraco da mesma fileira para absorver parte de seu poder, com ganho limitado.

### `gwent_v75_veu_cacador_sangue` — Caçador das Catacumbas de Mohgwyn

- Categoria/facção/fileira: Unidade / Véu Carmesim / ranged
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: v75_blood_mark
- Combos compatíveis por tag: Banquete da Hemorragia
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Épica: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Não possui habilidade individual. Pode completar combos de marca de Sangramento com a unidade compatível.

### `gwent_v75_lua_oraculo_geada` — Oráculo Gélido de Sellia

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: Presságio da Geada; effect=`v75_frost_oracle`
- Texto da identidade: Aplica uma marca de Geada ao inimigo mais forte da fileira; se já tinha uma marca, completa a segunda e recebe +1.
- Identidade histórica filtrada: —
- Tags: v75_frost_lore
- Combos compatíveis por tag: Convergência da Geada Lunar
- Efeito/resolução: identidade ativa executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Aplica uma marca de Geada ao inimigo mais forte da fileira; se já tinha uma marca, completa a segunda e recebe +1. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Identidade exibida e executada.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Uma astróloga de Sellia aplica Geada ao inimigo mais forte da fileira; completar a segunda marca fortalece o oráculo.

### `gwent_v75_lua_cartografo_lunar` — Cartógrafo das Cidades Eternas

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: v75_lunar_paths
- Combos compatíveis por tag: Convergência da Geada Lunar
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.

### `gwent_v75_lua_graviturgista` — Graviturgista de Nokron

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: Cisalhamento Gravitacional; effect=`v75_gravity_shear`
- Texto da identidade: Reduz em 1 o bônus de até dois inimigos com bônus positivo na fileira; se atingir dois, recebe +1.
- Identidade histórica filtrada: —
- Tags: v75_frost_lore
- Combos compatíveis por tag: Convergência da Geada Lunar
- Efeito/resolução: identidade ativa executada por card_id; participa de combo por tags
- Texto exibido pela API principal: Reduz em 1 o bônus de até dois inimigos com bônus positivo na fileira; se atingir dois, recebe +1. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Identidade exibida e executada.
- Arte: identidade ativa sem aura específica por ID
- Lore/descrição atual: Dobra a gravidade sobre até dois inimigos fortalecidos na fileira escolhida; se atingir dois, recebe poder adicional.

### `gwent_v75_lua_guardia` — Guardiã do Juramento Lunar

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: v75_lunar_paths
- Combos compatíveis por tag: Convergência da Geada Lunar
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Épica: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.

### `luterano_apostolo` — Apóstolo Esquecido

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: evangelho, fe
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Épica: ao completar combo compatível, reforça até 1 bônus já alterados: +1 nos positivos ou -1 nos negativos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Espalha a verdade divina; ao entrar em campo com aliado da mesma facção, ambos ganham +1 de poder.
- **Alerta de facção:** ID da expansão dos Esquecidos, mas facção atual Ordem Áurea; confirmar/corrigir.

### `luterano_pastor` — Pastor Esquecido

- Categoria/facção/fileira: Unidade / Véu Carmesim / ranged
- Poder-base/raridade/custo: 4 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `legado` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `legado`; poder/custo declarados: 4 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, irmandade
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: ID de habilidade não catalogado em HABILIDADES; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Guia o rebanho fiel. Se venceu a rodada anterior, entra em campo com +2 de poder.
- **Alerta de facção:** ID da expansão dos Esquecidos, mas facção atual Véu Carmesim; confirmar/corrigir.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_mistico` — Místico Esquecido

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 5 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `devoto` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `devoto`; poder/custo declarados: 5 / 2
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: devocao, fe
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: ID de habilidade não catalogado em HABILIDADES; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Conecta-se ao sagrado; cada aliada da mesma facção em campo concede +1 de bônus adicional.
- **Alerta de facção:** ID da expansão dos Esquecidos, mas facção atual Lua Negra; confirmar/corrigir.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_profeta` — Profeta Esquecido

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 6 / Mítica / 4 (tabela por raridade: 5)
- Habilidade nominal runtime: `sinergia_faccao` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `sinergia_faccao`; poder/custo declarados: 6 / 4
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, soberania
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: ID de habilidade não catalogado em HABILIDADES; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Mítica: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Líder espiritual que une o rebanho. Ganha +1 de poder para cada aliada da Fé em campo.
- **Alerta de facção:** ID da expansão dos Esquecidos, mas facção atual Ordem Áurea; confirmar/corrigir.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_vigia` — Vigia da Noite

- Categoria/facção/fileira: Unidade / Véu Carmesim / melee
- Poder-base/raridade/custo: 3 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `gloria` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `gloria`; poder/custo declarados: 3 / 1
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, gloria_divina
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: efeito de ciclo de vida executado fora da entrada; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Mantém a vigilância durante a noite. Permanece no campo ao vencer a rodada.
- **Alerta de facção:** ID da expansão dos Esquecidos, mas facção atual Véu Carmesim; confirmar/corrigir.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `luterano_anjo2` — Anjo de Segunda Ordem

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 5 / Lendária / 3 (tabela por raridade: 4)
- Habilidade nominal runtime: `gloria` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `gloria`; poder/custo declarados: 5 / 3
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: fe, gloria_divina
- Combos compatíveis por tag: Glória Divina, Devoção, Evangelho, Irmandade Esquecida, Soberania Divina, Sacerdócio
- Efeito/resolução: efeito de ciclo de vida executado fora da entrada; participa de combo por tags
- Texto exibido pela API principal: Sem habilidade especial. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: DIVERGÊNCIA: campo habilidade não corresponde a metadado/resolução unitária; conferir descrição/lore.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Brilho do sagrado. Ao vencer rodada, permanece no campo para o início da próxima.
- **Alerta de facção:** ID da expansão dos Esquecidos, mas facção atual Lua Negra; confirmar/corrigir.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.
- **Alerta crítico:** `habilidade` não tem metadado em `HABILIDADES`; conferir se a carta depende de identidade não ligada ou se o campo é legado.

### `primordial_origem` — Besta Prístina, Arauto da Vontade Maior

- Categoria/facção/fileira: Unidade / Ordem Áurea / siege
- Poder-base/raridade/custo: 8 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `lei_primeva` — Lei Primeva
- Habilidade declarada antes da transformação V18: `lei_primeva`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Recebe +2 de poder ao entrar na primeira rodada.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Recebe +2 de poder ao entrar na primeira rodada. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A Besta Prístina manifesta a vontade que veio além das estrelas e deu forma à ordem dourada.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `primordial_trono` — Marika, Rainha Eterna

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 8 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `decreto_soberano` — Decreto Soberano
- Habilidade declarada antes da transformação V18: `decreto_soberano`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Reduz em 2 o bônus de todas as unidades inimigas, até o limite de -2.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Reduz em 2 o bônus de todas as unidades inimigas, até o limite de -2. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Marika, a Rainha Eterna, ergueu a ordem dourada e rompeu o Anel Prístino, mudando para sempre as Terras Intermédias.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `primordial_tempestade` — Placidusax, Senhor Dragão

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 8 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `olho_tempestade` — Olho da Tempestade
- Habilidade declarada antes da transformação V18: `olho_tempestade`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Recebe +2 quando sua fileira estiver sob efeito climático.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Recebe +2 quando sua fileira estiver sob efeito climático. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Placidusax, antigo lorde dos dragões, permanece suspenso no tempo em Farum Azula.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `primordial_abismo` — Mãe Sem Forma

- Categoria/facção/fileira: Unidade / Véu Carmesim / siege
- Poder-base/raridade/custo: 8 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `fome_abismo` — Fome do Abismo
- Habilidade declarada antes da transformação V18: `fome_abismo`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Ganha +2 de poder quando sua pontuação total é menor que a do adversário.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +2 de poder quando sua pontuação total é menor que a do adversário. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: A Mãe Sem Forma é venerada pelos seguidores de Mohg como origem do poder sanguíneo.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `primordial_eternidade` — Maliketh, Guardião da Morte Destinada

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 8 / Primordial / 4 (tabela por raridade: 6)
- Habilidade nominal runtime: `paradoxo_eterno` — Paradoxo Eterno
- Habilidade declarada antes da transformação V18: `paradoxo_eterno`; poder/custo declarados: 8 / 4
- Texto da habilidade no catálogo: Recebe +2 na terceira rodada se o adversário venceu a segunda.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Recebe +2 na terceira rodada se o adversário venceu a segunda. Raridade Primordial: reforça até 3 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Maliketh guarda a Morte Destinada, o poder cuja ausência sustenta a ordem sem morte de Marika.
- **Alerta de custo:** custo cadastrado diverge do custo tabelado por raridade.

### `patente_1` — Novato de Raya Lucaria — Cinzas Novatas

- Categoria/facção/fileira: Unidade / Lua Negra / ranged
- Poder-base/raridade/custo: 3 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `cacador_arcano` — Caçador de Feitiços
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Recompensa por alcançar o nível 1. Papel tático: Longa distância. Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero.

### `patente_2` — Novato de Raya Lucaria — Guerreiro Caído

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 3 / Comum / 1 (tabela por raridade: 1)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: sem efeito individual/tag/identidade
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Recompensa por alcançar o nível 5. Papel tático: Cerco. Esta carta não tem habilidade especial; seu efeito vem do poder e dos bônus recebidos em combate.

### `patente_3` — Aprendiz Cariano — Caçador de Almas

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: sem efeito individual/tag/identidade
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Recompensa por alcançar o nível 10. Papel tático: Cerco. Esta carta não tem habilidade especial; seu efeito vem do poder e dos bônus recebidos em combate.

### `patente_4` — Escudeiro da Árvore Áurea — Cavaleiro do Abismo

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `nenhuma` — sem nome no catálogo
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: —
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: sem efeito individual/tag/identidade
- Texto exibido pela API principal: Sem habilidade especial.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema (esperado para carta pura)
- Lore/descrição atual: Recompensa por alcançar o nível 15. Papel tático: Corpo a corpo. Esta carta não tem habilidade especial; seu efeito vem do poder e dos bônus recebidos em combate.

### `patente_5` — Acólito Sanguíneo — Guardião das Cinzas

- Categoria/facção/fileira: Unidade / Véu Carmesim / ranged
- Poder-base/raridade/custo: 6 / Rara / 2 (tabela por raridade: 2)
- Habilidade nominal runtime: `encadeamento` — Postura Encadeada
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: Ganha +2 de poder se for jogada na mesma fileira que sua última unidade.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +2 de poder se for jogada na mesma fileira que sua última unidade. Raridade Rara: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Recompensa por alcançar o nível 20. Papel tático: Longa distância. Ganha +2 de poder se for jogada na mesma fileira que sua última unidade.

### `patente_6` — Veterano de Leyndell — Arauto da Ruína

- Categoria/facção/fileira: Unidade / Ordem Áurea / melee
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `retaliacao` — Retaliação dos Semideuses
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: Ganha +1 de poder quando sua pontuação total é menor que a do adversário.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +1 de poder quando sua pontuação total é menor que a do adversário. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Recompensa por alcançar o nível 30. Papel tático: Corpo a corpo. Ganha +1 de poder quando sua pontuação total é menor que a do adversário.

### `patente_7` — Feiticeiro Cariano — Executor Sombrio

- Categoria/facção/fileira: Unidade / Lua Negra / melee
- Poder-base/raridade/custo: 7 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `cacador_arcano` — Caçador de Feitiços
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Recompensa por alcançar o nível 40. Papel tático: Corpo a corpo. Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero.

### `patente_8` — Veterano de Leyndell — Senhor das Almas

- Categoria/facção/fileira: Unidade / Ordem Áurea / ranged
- Poder-base/raridade/custo: 5 / Épica / 3 (tabela por raridade: 3)
- Habilidade nominal runtime: `retaliacao` — Retaliação dos Semideuses
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: Ganha +1 de poder quando sua pontuação total é menor que a do adversário.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +1 de poder quando sua pontuação total é menor que a do adversário. Raridade Épica: reforça até 1 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Recompensa por alcançar o nível 50. Papel tático: Longa distância. Ganha +1 de poder quando sua pontuação total é menor que a do adversário.

### `patente_9` — Lorde de Leyndell — Lenda do Coliseu

- Categoria/facção/fileira: Unidade / Ordem Áurea / siege
- Poder-base/raridade/custo: 8 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `impeto` — Ímpeto do Lorde
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: Ganha +1 de poder quando sua pontuação total é maior que a do adversário.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +1 de poder quando sua pontuação total é maior que a do adversário. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Recompensa por alcançar o nível 75. Papel tático: Cerco. Ganha +1 de poder quando sua pontuação total é maior que a do adversário.

### `patente_10` — Mestre Cariano — Sentinela Imortal

- Categoria/facção/fileira: Unidade / Lua Negra / siege
- Poder-base/raridade/custo: 6 / Lendária / 4 (tabela por raridade: 4)
- Habilidade nominal runtime: `quebra_ritmo` — Ruptura de Postura
- Habilidade declarada antes da transformação V18: `nenhuma/sem declaração literal`; poder/custo declarados: — / —
- Texto da habilidade no catálogo: Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior.
- Identidade ativa: nenhuma; effect=`—`
- Texto da identidade: —
- Identidade histórica filtrada: —
- Tags: —
- Combos compatíveis por tag: —
- Efeito/resolução: habilidade genérica executada ao entrar em campo
- Texto exibido pela API principal: Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior. Raridade Lendária: reforça até 2 bônus já alterados pela habilidade: +1 nos positivos ou -1 nos negativos. Não muda o poder inicial nem os escudos.
- Exibição × execução: Sem conflito detectado pela matriz estática; requer teste de execução.
- Arte: sem aura/emblema específico
- Lore/descrição atual: Recompensa por alcançar o nível 100. Papel tático: Cerco. Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior.

## 7. Contratos técnicos que devem ser validados na reconstrução

1. O campo mecânico canônico deve apontar para um único `effect_id` que seja simultaneamente executado e descrito. Se houver efeito secundário, ele deve aparecer como efeito separado e explicitamente listado.
2. O texto exibido em catálogo, deck, detalhe, Discord e arte deve derivar do mesmo payload preparado, sem reconstrução independente a partir de `HABILIDADES`.
3. Carta pura significa ausência de efeito genérico, identidade, tags/combos e trigger individual; passivas globais devem ser identificadas separadamente.
4. O custo exibido, persistido e validado deve ser o mesmo valor canônico; custo por raridade não pode recalcular silenciosamente um valor diferente.
5. A definição visual precisa consumir a versão atual da definição mecânica ou sinalizar que a arte integral é antiga e exige regeneração/aprovação.
6. Toda carta deve ter teste: descrição esperada, precondição, ação, alterações exatas de estado e resultado observado.

## 8. Arquivos machine-readable

- `card-game-card-traceability.csv`: planilha CSV UTF-8 com uma linha por modelo de carta; listas/objetos estão codificados em JSON nas respectivas células.
- `card-game-card-traceability.json`: mesmo conteúdo estruturado, com metadados e tipos preservados.

## 9. Limitações

- Auditoria estática; não executa partida real nem carrega DB de produção.
- O catálogo em `CARTAS_POR_ID` inclui os modelos existentes no código e as patentes materializadas durante import. Cartas procedurais de jogadores gravadas no banco não são enumeradas por este documento.
- Compatibilidade por tag significa potencial de combo, não que o combo se ativa sozinho; outras cartas/condições são necessárias.
- Cobertura de aura/emblema é apenas a camada específica de `_AURAS` / `_EMBLEMAS`; não afirma ausência de outros símbolos, molduras ou textos visuais.
- As cartas podem ter snapshots antigos em partidas e dados de exemplares não incluídos no ZIP.


## 6. Correção de auditoria: habilidade genérica + identidade ativa

A leitura direta de `sistemas/gwent.py` (ramo `action == "play"` dentro de `aplicar_jogada()`) confirma que, se `card_id` pertence a `CARD_IDENTITY_ABILITIES`, o motor define `skill = ""` antes de qualquer ramo genérico. Em seguida chama `_aplicar_habilidade_identidade()`. Portanto, as 16 cartas listadas no item 4.1 **não executam dois efeitos individuais**. O defeito é de contrato: `preparar_carta()` devolve `"habilidade": skill` com o ID genérico histórico, enquanto `habilidade_nome` e `habilidade_texto` são construídos a partir da identidade. A API deve futuramente substituir esse ID por `null`/`""` e expor `effect_id` canônico único. A matriz JSON/CSV marca `habilidade_generica_suprimida_por_identidade=true`.
