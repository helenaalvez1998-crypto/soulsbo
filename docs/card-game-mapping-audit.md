# Auditoria de mapeamento do jogo de cartas — baseline e estado pós-política de combos

> **Documento histórico + atualização de estado.** As seções 1–6 e a matriz de cartas preservam o baseline recebido (`soulsbo-main(1).zip`); a seção 7 foi atualizada com o catálogo de combos atualmente carregado, a seção 21 registra a política implementada e a seção 22 registra a validação stateful/snapshot. Os resultados v0.1 das seções 19–20 são históricos pré-patch, não o estado atual. A seção 22 é a referência mais recente para limites de integração de partidas.

- **Data da auditoria:** 2026-11-27.
- **Fonte analisada:** `soulsbo-main(1).zip`.
- **SHA-256 do ZIP recebido:** `02126ba16148b004608f38bde1103cb9d446772be2913976cef5c3c3fd5dfe37`.
- **Pasta-base no ZIP:** `soulsbo-main/`.
- **Alteração funcional posterior ao baseline:** política de combos aprovada e implementada em `sistemas/gwent.py` (`SYNERGY_COMBOS` e `_aplicar_combo_de_cartas()`).
- **Limitação:** o ZIP não contém o banco de produção nem segredos/configurações do ambiente. A análise foi estática, complementada por import dos módulos Python do catálogo e do motor; não foi executada uma partida real com dados de produção.

## 1. Sumário executivo do estado encontrado


| Métrica | Valor do código-fonte |
| --- | --- |
| Modelos em `CARTAS_POR_ID` | 137 |
| Unidades | 110 |
| Especiais (inclui relíquias) | 27 |
| Habilidades declaradas em `HABILIDADES` | 59 |
| Habilidades individuais de identidade ativas após filtro | 22 |
| Definições de identidade antes do filtro | 40 |
| Definições de identidade filtradas em runtime | 18 |
| Associações carta → tags de combo | 72 |
| Combos declarados | 27 |
| Líderes | 10 |
| Relíquias no catálogo | 6 |
| Cartas puras estritas entre unidades | 15 / 110 (13.64%) |
| Cartas puras estritas no catálogo total | 15 / 137 (10.95%) |
| Cartas cujo custo cadastrado difere de `CUSTO_RARIDADE` | 19 |

### Interpretação da contagem de cartas puras

Para esta auditoria, “pura” foi contado estritamente como unidade que: (1) tem `habilidade` vazia; (2) não possui identidade ativa em `CARD_IDENTITY_ABILITIES`; e (3) não possui tags em `CARD_SYNERGY_TAGS`. Essa regra trata participação em combo como efeito, coerente com a exigência de ausência de qualquer habilidade/efeito. A passiva global da facção (`FACTION_BOOST`) foi separada por ser uma regra externa à carta. O resultado de 15 unidades é uma fotografia do catálogo de modelos, não da coleção/exemplares do banco.

Se a meta de 30% for calculada sobre os 137 modelos do catálogo, são necessárias pelo menos **42 cartas puras**. Se o denominador for somente as 110 unidades, são necessárias pelo menos **33**. A especificação final precisa declarar qual denominador é oficial; a interpretação literal “cartas do jogo” favorece o total de modelos e, portanto, 42.

## 2. Mapa do repositório e responsabilidades

### Arquivos centrais


| Arquivo | Responsabilidade e vínculos |
| --- | --- |
| `sistemas/cartas.py` | Modelo `Carta`; serialização `para_dict()`; catálogo base; `HABILIDADES`; categorias, facções, fileiras, raridade, faixas de poder e custo; seleção de cartas de pacote; geração determinística de cartas de jogos e patentes; listas de IDs V18 e V75. |
| `sistemas/gwent.py` | Motor autoritativo da partida; normalização de facção/fileira; validação de predominância; conjuntos de cobertura; passivas e líderes; tags/combos; identidades; preparação de cartas; estado da partida; resolução de jogadas, efeitos, rodada, clima, IA, pontuação, MMR e XP. |
| `database.py` | Schema e persistência de coleção, exemplares individuais, decks, partidas, rankings, recompensas, Ateliê, artes, transmutação/cartas geradas e migrações auxiliares. |
| `bot.py` | Registra endpoints do núcleo Gwent; monta payloads de coleção/catálogo/deck; valida e salva decks; cria e consulta partidas; despacha ação para `aplicar_jogada`; gera/serve imagem pública e imagem de exemplar; conecta rotas `site_hub` e `site_portal`. |
| `site_hub.py` | Rotas da biblioteca pública e outros módulos web. Implementa `/api/gwent/catalogo-cartas` independentemente de `/api/gwent/cards`. |
| `site_portal.py` | Rotas do portal do site e integração da aplicação web; é registrado no servidor pelo bootstrap de `bot.py`. |
| `site/app.js` | Frontend principal do Coliseu: busca coleção/modelos, modal de carta, custo/descrição, deck builder, líder/relíquia, lista/ações/estado da partida e chamadas de imagem. |
| `site/catalogo-cartas.html` | Biblioteca pública; busca `/api/gwent/catalogo-cartas` e desenha textos próprios do payload dessa API. |
| `cogs/painel_jogo.py` | Comando Discord `/jogo`; abre painel de acesso ao sistema de cartas/site. |
| `sistemas/arte_cartas.py` | Prepara payload visual canônico com `preparar_carta()` e renderiza cartas-base; calcula fingerprint/ETag e cache; pode usar arte oficial completa. |
| `sistemas/arte_gwent_efeitos.py` | Desenha auras de unidade e emblemas especiais por ID de habilidade visual. |
| `sistemas/molduras_cartas.py` | Normalização de facção, estilos, molduras e efeitos de raridade. |
| `sistemas/templates_cartas.py` | Layouts/templates usados na renderização de carta completa. |
| `sistemas/arte_cartas_geradas.py` | Arte de cartas pessoais/geradas; integra com o fluxo de transmutação. |
| `sistemas/gerador_cartas.py` | Geração procedural de definições; compatibilidade de habilidade por função; balanceamento cumulativo 50/50; validação da definição/lote. |
| `sistemas/afinidades.py` | Taxonomia de facções, raridades de gerador, afinidades e análise/classificação de ingredientes. |
| `sistemas/atelie_coliseu.py` | Fluxo de submissão/aprovação e recuperação de arte oficial. |
| `sistemas/direcao_arte_prompts.py` e `sistemas/prompt_arte_criador.py` | Direção textual de arte e preparação de prompts. |
| `sistemas/storage_r2.py` | Integração de armazenamento externo R2 para assets. |
| `sistemas/recompensas_gwent.py` | Recompensas vinculadas à partida e sua conclusão. |
| `sistemas/decks_base.py` e `sistemas/starter_deck.py` | Módulos auxiliares de deck inicial/base; confirmar uso operacional antes de classificá-los como mortos. |
| `sistemas/auditoria_efeitos.py` | Relatório estático de cobertura por nome; não executa testes de partida. |
| `sistemas/arte_upload_criador.py`, `sistemas/atelie_coliseu.py`, `sistemas/atelier_pdf.py` | Fluxos auxiliares de arte, upload, aprovação e documentação de criação. |

### Arquivos auxiliares/documentação já existentes

- `docs/CARD_GAME_REDESIGN.md`: proposta de redesign anterior. Não deve ser tratado como regra oficial sem reconciliação: descreve, por exemplo, deck de 30 cartas e energia/vida, enquanto o motor atual salva deck de 12 cartas e disputa por três rodadas/coroas.
- `docs/MAPEAMENTO_BOT_VS_SITE.md`: visão geral de paridade entre bot e site; útil como contexto, mas não contém o fluxo técnico completo do Gwent.
- `docs/ATELIE_CARTA_COMPLETA.md`: registra requisitos de arte integral e informa que artes aprovadas são imagens completas e antigas não são reescritas automaticamente.
- `docs/CLOUDFLARE_R2.md`: configuração do armazenamento externo; deve ser consultado antes de alterar armazenamento.

### Fluxo funcional ponta a ponta

```text
CATÁLOGO PYTHON
  sistemas/cartas.py: Carta / CARTAS_POR_ID / HABILIDADES
        │
        ├── DB: database.py
        │     ├── cartas_colecao (propriedade agregada por card_id)
        │     ├── cartas_exemplares (exemplar_id, raridade, poder, origem)
        │     ├── cartas_gwent_decks (card_ids_json, exemplar_ids_json, facção, líder, relíquia)
        │     └── cartas_gwent_matches (state_json / snapshots da partida)
        │
        ├── API principal em bot.py
        │     ├── GET /api/gwent/cards
        │     ├── GET/POST /api/gwent/deck
        │     └── GET/POST /api/gwent/matches + /action
        │             │
        │             └── sistemas/gwent.py
        │                   preparar_carta() / novo_estado()
        │                   aplicar_jogada() / _resolve_round()
        │                   identidade / habilidade / combo / passiva / clima
        │
        ├── API pública alternativa em site_hub.py
        │     └── GET /api/gwent/catalogo-cartas
        │             └── Carta.para_dict() + HABILIDADES (não passa por preparar_carta)
        │
        └── Imagem
              bot.py image endpoints
                ├── arte oficial por card_id + exemplar_id (se existente)
                └── sistemas/arte_cartas.py
                      preparar_payload_carta_base()
                      preparar_carta() → texto → renderização/cache
                      sistemas/arte_gwent_efeitos.py → auras/emblemas
```

### APIs relevantes do jogo


| Método e rota | Arquivo/função | Uso |
| --- | --- | --- |
| GET `/api/gwent/cards` | `bot.py` · `_api_gwent_cards` | Devolve catálogo e exemplares da coleção; o catálogo global é preparado com `preparar_carta()`. |
| GET `/api/gwent/exemplars` | `bot.py` | Lista/consulta exemplares. |
| GET `/api/gwent/deck` | `bot.py` · `_api_gwent_deck` | Recupera IDs de cartas/exemplares, facção, líder e relíquia e prepara payload do deck. |
| POST `/api/gwent/deck` | `bot.py` · `_api_gwent_deck_save` | Valida propriedade, 12 IDs distintos, quantidade de unidades/especiais, facção predominante, líder e relíquia; persiste os IDs/configuração. |
| POST `/api/gwent/deck/reset` | `bot.py` · `_api_gwent_deck_reset` | Limpa a configuração do deck sem apagar a coleção. |
| GET `/api/gwent/matches` | `bot.py` · `_api_gwent_matches` | Lista partidas. |
| POST `/api/gwent/matches` | `bot.py` · `_api_gwent_match_create` | Cria convite/partida usando snapshots de deck. |
| POST `/api/gwent/matches/solo` | `bot.py` · `_api_gwent_match_create_solo` | Cria partida contra a IA. |
| GET `/api/gwent/matches/{match_id}` | `bot.py` · `_api_gwent_match_detail` | Obtém estado serializado da partida. |
| POST `/api/gwent/matches/{match_id}/action` | `bot.py` · `_api_gwent_match_action` | Valida jogador/estado e despacha ação de jogo para `aplicar_jogada()`. |
| GET `/api/gwent/public-cards/{card_id}/image` | `bot.py` · `_api_gwent_public_card_image` | Serve thumbnail/arte pública, incluindo renderização base e arte oficial. |
| GET `/api/gwent/cards/{card_id}/image` | `bot.py` · `_api_gwent_card_image` | Serve imagem contextual/privada do exemplar. |
| GET `/api/gwent/catalogo-cartas` | `site_hub.py` · `catalogo_cartas_api` | Biblioteca pública independente; usa metadados do catálogo e `HABILIDADES`. |

### Frontend, Discord e eventos

- `cogs/painel_jogo.py`: comando slash `/jogo` (linha 451 na cópia auditada). É a entrada Discord/painel, não o motor de batalha.
- `bot.py`: registra handlers HTTP na região das linhas 830–861; depois chama `site_hub.registrar_rotas` e `site_portal.registrar_rotas` no bootstrap do servidor.
- `site/app.js`: inicializa coleção via `GET /api/gwent/cards`; deck builder via `GET/POST /api/gwent/deck`; partidas via `/api/gwent/matches`, `/solo`, `/{id}`, `/{id}/respond` e `/{id}/action`. Também usa `image_url` e os endpoints de arte do Ateliê.
- `site/catalogo-cartas.html`: executa `fetch('/api/gwent/catalogo-cartas')` na inicialização.
- A API de ação do jogo encaminha ações como jogar carta, passar, mulligan, usar líder, clima e relíquia ao motor. As ações e elegibilidade precisam continuar sendo validadas no backend; o frontend apenas apresenta as opções.

## 3. Estrutura de dados atual

### Modelo Python `Carta`

Em `sistemas/cartas.py`, `Carta` é um `@dataclass(frozen=True, slots=True)` com os campos:


| Campo | Tipo observado | Significado |
| --- | --- | --- |
| `id` | str | ID estável do modelo; usado em tags, identidades, imagens e persistência. |
| `nome` | str | Nome exibido. |
| `categoria` | str | `Unidade` ou `Especial`. |
| `faccao` | str | Ordem Áurea, Véu Carmesim, Lua Negra ou Os Esquecidos. |
| `poder` | int | Poder-base do modelo; no catálogo atual, unidades 3–10; especiais 0. |
| `raridade` | str | Uma das sete raridades. |
| `custo` | int | Custo cadastrado no modelo; ainda não é limite/validação do deck. |
| `habilidade` | str | ID genérico da habilidade ou string vazia. |
| `descricao` | str | Texto de lore/descrição do modelo; não deve ser fonte de regra mecânica. |
| `jogo_origem` | str | Campo de origem de recompensas de jogo. |
| `fileira` | str | `melee`, `ranged` ou `siege`; posição tática separada da facção. |

`Carta.para_dict()` acrescenta campos derivados como `row_label`, `papel_gwent`, `tipo_combate`, `categoria_arte` e normaliza a categoria. Valida facção e fileira. O motor cria um payload de batalha maior em `preparar_carta()`: `poder`, `raridade`, facção, fileira, ID de habilidade, nome/texto, `habilidade_identidade`, sinergias, combos compatíveis e URL de imagem. **O retorno atual de `preparar_carta()` não contém `custo`**, embora alguns chamadores atribuam `payload['custo']` antes de chamá-la.

### Persistência SQLite declarada em `database.py`


| Tabela | Campos-chave e papel |
| --- | --- |
| `cartas_colecao` | PK composta `(user_id, card_id)`; `quantidade`, `source`, `game_name`, `obtained_at`. Visão agregada/legada de propriedade. |
| `cartas_exemplares` | `id` PK; `user_id`, `card_id`, `rarity`, `power`, `source`, `origin_type`, `origin_card_id`, `is_sacrificable`, `obtained_at`, `updated_at` (parte das colunas é adicionada por migração). Exemplar individual. |
| `cartas_gwent_decks` | `user_id` PK, `card_ids_json`, `exemplar_ids_json`, `faction`, `leader_id`, `relic_id`, `updated_at`. Não contém total de custo de deck. |
| `cartas_gwent_matches` | `id` PK, `creator_id`, `opponent_id`, `status`, `state_json`, `created_at`, `updated_at`. Snapshot/estado da partida. |
| `cartas_gwent_rankings` | `user_id`, `mmr`, `wins`, `losses`, `draws`, `updated_at`. |
| `cartas_gwent_rewards` | `match_id`, `user_id`, recompensas, XP, delta de MMR e chaves de idempotência. |
| `cartas_atelie_sessoes` / `cartas_atelie_artes` / `cartas_atelie_submissoes` | Sessão, arte de referência/upload e fila de submissão/revisão. |
| `cartas_gwent_lideres_artes` | Arte específica de líder, revisionada. |
| `cartas_geradas` / `cartas_geradas_habilidades` / `cartas_geradas_artes` | Definições, habilidades e artes publicadas pelo fluxo de cartas pessoais/geradas. |
| `cartas_gwent_kit_inicial` / `cartas_gwent_especiais_kit` | Controle de entrega de kits iniciais. |

**Consequência de persistência:** o catálogo canônico de modelos vive no código Python; o banco guarda propriedade/exemplares e snapshots de deck/partida. Exemplares preservam raridade e poder, mas não um snapshot completo da lore/habilidade/textos canônicos. Uma partida existente possui `state_json` próprio: não se deve assumir que alterar o catálogo reescreva partidas em andamento. Artes completas podem guardar os textos antigos incorporados nos pixels.

## 4. Regras e parâmetros atuais no código


| Parâmetro | Valor atual | Observação |
| --- | --- | --- |
| `RARIDADES` | Comum, Rara, Épica, Lendária, Mítica, Primordial, Singular | Sete níveis. |
| `PESOS_RARIDADE` | 69.47%, 22.02%, 7.01%, 1.00%, 0.50%, 0%, 0% | Pesos de raridade da distribuição de pacote. |
| `CUSTO_RARIDADE` | 1, 2, 3, 4, 5, 6, 0 | Singular custa 0 nesta tabela; revisar regra antes de reaproveitar. |
| `FAIXA_PODER` | Comum 3–5; Rara 4–6; Épica 5–7; Lendária 6–8; Mítica 8–9; Primordial 8–9; Singular 8–10 | Faixas atuais; não implementam a regra futura 1–15 como política única. |
| `limite_poder_modelo()` | mínimo 5, máximo 12 | Teto distinto e divergente do clamp de 1–15 no payload de `preparar_carta()`. |
| `RARITY_EFFECT_BUDGET` | Comum 0; Rara 1; Épica 1; Lendária 2; Mítica 2; Primordial 3; Singular 3 | Orçamento adicional de alterações de bônus; não é custo do deck. |
| `FACTION_BOOST` | +1 à primeira unidade da facção do deck por rodada | Passiva de facção global, aplicada depois do efeito individual e combos. |
| Deck | 12 modelos diferentes; mínimo 8 unidades; máximo 4 especiais | Também valida propriedade, facção predominante, líder e relíquia. |
| Partida | 3 fileiras; até 3 rodadas; primeiro a 2 coroas encerra | Estado de partida e regras em `sistemas/gwent.py`. |

### Cálculo atual de raridade

Não há uma fórmula única `Poder Base + Efeitos + Custo → Raridade` no catálogo atual:

- Cartas estáticas têm raridade/poder/custo explícitos em cada `Carta(...)`.
- `carta_jogo()` escolhe facção/fileira/raridade/habilidade/poder por hash do jogo e marco; a habilidade tem seleção hash-condicional (não é aleatória a cada chamada, mas é uma atribuição algorítmica que não mede poder do efeito + custo).
- `carta_patente()` deriva raridade do nível mínimo e escolhe atributos por hash.
- `gerador_cartas.py` usa a mediana inferior das raridades dos ingredientes, mas escolhe habilidade e poder via `rng.choice`, `rng.random` e `rng.randint`; seed torna o resultado reproduzível, não determinístico em relação à regra de composição. `calcular_distribuicao_50_50()` somente mede uma amostra, não força o percentual individual.
- Cartas pessoais de transmutação têm uma validação separada que exige `custo == 0` na V31, e bloqueia Primordial/Singular nos exemplares da função de preparação pessoal.

## 5. Catálogo completo de habilidades declaradas (`HABILIDADES`)

São **59 IDs** no dicionário `HABILIDADES`. A tabela registra o nome e o texto que constam no código, a classificação e quais modelos atuais possuem o ID no campo `Carta.habilidade`. A presença de um ID nessa tabela não prova que esteja ligado a um handler efetivamente alcançável.


| ID | Nome declarado | Texto declarado no catálogo | Tipo | Situação do motor | Cartas que carregam este ID |
| --- | --- | --- | --- | --- | --- |
| primeira_luz | Graça Dourada | Na primeira rodada, ganha +1 de poder ao entrar em campo. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | chefe_rei_afogado, covenant_lua_velada |
| retaliacao | Retaliação dos Semideuses | Ganha +1 de poder quando sua pontuação total é menor que a do adversário. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | covenant_irmandade_ferro, patente_6, patente_8 |
| impeto | Ímpeto do Lorde | Ganha +1 de poder quando sua pontuação total é maior que a do adversário. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | chefe_oraculo_ruina, patente_9 |
| ultimo_folego | Último Suspiro | Na terceira rodada, ganha +1 de poder ao entrar em campo. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | chefe_dama_vazio, gwent_singular_nivel1 |
| contragolpe | Contragolpe | Ganha +2 de poder quando sua pontuação total é menor que a do adversário. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| encadeamento | Postura Encadeada | Ganha +2 de poder se for jogada na mesma fileira que sua última unidade. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | magia_nevoa_antiga, patente_5 |
| adaptacao | Passo do Peregrino | Ganha +1 de poder se for jogada em uma fileira diferente da sua última unidade. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | magia_selo_vigilia |
| sangue_frio | Concentração | Ganha +2 de poder quando os dois jogadores estão com a mesma pontuação. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| instinto | Instinto de Caçador | Ganha +2 de poder quando sua pontuação total é menor que a do adversário. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | arma_grande_sino, gwent_unidade_gigante |
| precisao | Mira Cariana | Ganha +1 de poder ao entrar na fileira de Longa Distância. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | arma_duas_luas, gwent_singular_intocavel |
| drenagem | Selo Enfraquecedor | Diminui em 1 o bônus dos inimigos, até o mínimo de -2. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | chefe_malenia_lamina_miquella, magia_trovao_oco, covenant_coroa_abismo |
| cacador_arcano | Caçador de Feitiços | Ganha +1 de poder se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus acima de zero. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | chefe_maliketh_morte_destinada, gwent_unidade_invocador, patente_1, patente_7 |
| quebra_ritmo | Ruptura de Postura | Ganha +1 de poder se o adversário jogou uma unidade na mesma fileira no turno anterior. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | chefe_guardiao_cinzas, chefe_radahn_flagelo_estrelas, chefe_messmer_impalador, magia_sol_negro, patente_10 |
| lei_primeva | Lei Primeva | Recebe +2 de poder ao entrar na primeira rodada. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | primordial_origem |
| decreto_soberano | Decreto Soberano | Reduz em 2 o bônus de todas as unidades inimigas, até o limite de -2. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | primordial_trono |
| olho_tempestade | Olho da Tempestade | Recebe +2 quando sua fileira estiver sob efeito climático. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | chefe_placidusax_lorde_dragao, primordial_tempestade |
| fome_abismo | Fome do Abismo | Ganha +2 de poder quando sua pontuação total é menor que a do adversário. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | primordial_abismo |
| paradoxo_eterno | Paradoxo Eterno | Recebe +2 na terceira rodada se o adversário venceu a segunda. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | gwent_singular_cacador_chefes, primordial_eternidade |
| guardiao_fileira | Guardião da Fileira | +1 para cada outra unidade sua na mesma fileira, até +3. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| cacador_solitario | Caçador Solitário | +2 se não houver outra unidade sua na fileira. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | gwent_singular_primeiro |
| estandarte | Estandarte | Concede +1 às outras unidades aliadas da mesma fileira. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | gwent_mitica_coroa |
| resistencia_climatica | Resistência Climática | Ignora até 2 pontos de penalidade climática; sem clima ativo ao entrar, recebe +1. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| eco_arcano | Eco Arcano | +2 se você tiver uma carta especial no descarte. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| gwent_clima | Tempestade dos Picos | Escolha uma fileira. A tempestade reduz em 1 o poder efetivo de todas as unidades dos dois lados nessa fileira enquanto o clima estiver ativo. | Especial | Motor especial/reliquia | gwent_especial_tempestade |
| gwent_nevoa | Névoa de Sellia | Aplica 1 marca de Podridão Escarlate a todas as unidades inimigas da fileira escolhida; raridades Lendárias ou superiores aplicam uma segunda marca. | Especial | Motor especial/reliquia | gwent_especial_nevoa |
| gwent_geada | Lua Gélida | Aplica 1 marca de Geada a todas as unidades inimigas em campo; raridades Lendárias ou superiores aplicam uma segunda marca. | Especial | Motor especial/reliquia | gwent_especial_geada |
| gwent_chuva | Sangue Corrompido | Aplica uma marca de Sangramento a todas as unidades inimigas na fileira de Cerco; a segunda marca reduz 2 de bônus (mínimo -2) e consome as marcas. | Especial | Motor especial/reliquia | gwent_especial_chuva |
| gwent_chifre | Rugido de Godfrey | Concede +2 às suas unidades na fileira escolhida até o fim da rodada. | Especial | Motor especial/reliquia | gwent_especial_chifre |
| gwent_medico | Lágrima Sagrada | Devolve à sua mão uma unidade do seu descarte com poder-base 4 ou menos; você pode escolher o alvo. | Especial | Motor especial/reliquia | gwent_especial_medico |
| gwent_queima | Chama Negra | Tenta remover a unidade de maior poder efetivo de cada lado; um escudo pode bloquear cada remoção. | Especial | Motor especial/reliquia | gwent_especial_queima |
| gwent_purificar | Lei da Regressão | Remove todos os efeitos climáticos. | Especial | Motor especial/reliquia | gwent_especial_purificar |
| gwent_execucao | Lâmina da Morte Destinada | Remove uma unidade inimiga escolhida da fileira selecionada se ela tiver poder efetivo 6 ou menos; um escudo pode bloquear a remoção. | Especial | Motor especial/reliquia | gwent_especial_execucao |
| gwent_vinculo | Juramento do Crisol | Se houver ao menos duas unidades aliadas na fileira escolhida, concede +2 a todas elas até o fim da rodada. | Especial | Motor especial/reliquia | gwent_especial_vinculo |
| gwent_batedor | Passo do Cão de Caça | Compra uma carta da reserva, se disponível. | Especial | Motor especial/reliquia | gwent_especial_batedor |
| gwent_muralha | Bastião de Leyndell | Concede +1 às suas unidades na fileira escolhida até o fim da rodada. | Especial | Motor especial/reliquia | gwent_especial_muralha |
| vinganca | Vingança | Ao cair, concede +1 às unidades aliadas da mesma fileira. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | gwent_unidade_herdeiro_portao, gwent_unidade_senhor_cacada, gwent_unidade_detonador |
| escudo_ferro | Escudo de Ferro | Entra com escudo: ignora a primeira remoção sofrida. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| ressurgir | Ressurgir | Se houver uma unidade elegível, traz do descarte a mais forte com poder base 5 ou menos diretamente ao campo. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | gwent_unidade_necromante |
| devorar | Devorar | Ao entrar, consome a unidade aliada de menor poder efetivo na mesma fileira e recebe bônus igual ao poder dela, até +4. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | gwent_unidade_carniceiro_forja |
| sobrevivente | Sobrevivente | Ao fim da rodada, permanece no campo (a mais forte, se houver várias). | Unidade / ciclo de vida | Sem resolução no motor; apenas aura visual | — |
| espolios | Espólios | Se você vencer a rodada com ela em campo, compra uma carta. | Unidade / ciclo de vida | Resolução no fim da rodada | — |
| gwent_egide | Bênção da Árvore Áurea | Concede escudo a uma unidade sua. | Especial | Motor especial/reliquia | gwent_especial_egide |
| gwent_requiem | Chamado dos Mortos | Traz do descarte diretamente ao campo uma unidade com poder base 6 ou menos. | Especial | Motor especial/reliquia | gwent_especial_requiem |
| gwent_passo | Passo do Lobo | Move uma unidade sua para a fileira escolhida. | Especial | Motor especial/reliquia | gwent_especial_passo |
| dupla_fornalha | Pacto da Fornalha | +2 se houver outra unidade aliada na mesma fileira. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| irmandade_veu | Formação do Véu | +2 se houver outra unidade aliada em uma fileira diferente. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| circulo_arcano | Círculo de Ressonância | +2 se houver outra unidade aliada na mesma fileira ou uma carta especial no descarte. | Unidade / ciclo de vida | Motor de unidade (entrada em campo) | — |
| gwent_sangramento | Sangramento | Marca as unidades inimigas da fileira; a segunda marca reduz o bônus em 2 (mínimo -2) e consome as marcas. Marcas expiram no fim da rodada. | Especial | Motor especial/reliquia | elden_especial_sangramento |
| gwent_geada_cariana | Geada Cariana | Aplica até duas marcas às unidades inimigas da fileira escolhida; cada marca reduz 1 de poder efetivo até o fim da rodada. | Especial | Motor especial/reliquia | elden_especial_geada |
| gwent_podrida | Podridão Escarlate | Cada marca reduz 1 de poder efetivo; a segunda também corrói 1 ponto de bônus positivo, se houver. Marcas expiram no fim da rodada. | Especial | Motor especial/reliquia | elden_especial_podrida |
| gwent_loucura | Loucura Frenética | Cada marca reduz 1 de poder efetivo; a segunda remove todos os bônus positivos da unidade. Marcas expiram no fim da rodada. | Especial | Motor especial/reliquia | elden_especial_loucura |
| gwent_chama | Chama do Gigante | Remove Geada de todas as suas unidades; cada unidade purificada recebe +1 de poder até o fim da rodada. | Especial | Motor especial/reliquia | elden_especial_chama |
| gwent_invocacao | Cinzas dos Lobos Solitários | Invoca Lobos Espirituais com 3 de poder na fileira escolhida. | Especial | Motor especial/reliquia | elden_especial_invocacao |
| reliquia_godrick | Grande Runa de Godrick | Exige ao menos uma unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas. | Relíquia | Motor especial/reliquia | reliquia_grande_runa_godrick |
| reliquia_renala | Grande Runa dos Não Nascidos | Remove Geada e Podridão das unidades aliadas afetadas; cada unidade purificada recebe +1 de bônus. | Relíquia | Motor especial/reliquia | reliquia_runa_nao_nascidos |
| reliquia_morte | Runa da Morte | Em cada fileira, reduz em até 2 o bônus positivo da unidade inimiga que tiver o maior bônus naquela fileira. | Relíquia | Motor especial/reliquia | reliquia_runa_morte |
| reliquia_noite_chama | Espada da Noite e da Chama | Na postura da Noite, aplica Geada a todas as unidades inimigas da fileira escolhida. Na postura da Chama, atinge a unidade de maior poder efetivo: reduz 1 de poder-base e 2 de bônus; Escudo bloqueia o golpe. | Relíquia | Motor especial/reliquia | reliquia_noite_chama |
| reliquia_lamina_negra | Lâmina Negra | Na fileira escolhida, reduz em 3 o bônus de uma unidade inimiga (a escolhida ou a de maior poder efetivo). Escudo bloqueia o efeito sem consumir a Relíquia. | Relíquia | Motor especial/reliquia | reliquia_lamina_negra |
| reliquia_algemas | Algemas de Margit | Na fileira escolhida, zera o bônus positivo de uma unidade inimiga (a escolhida ou a de maior bônus); bônus negativos permanecem inalterados. | Relíquia | Motor especial/reliquia | reliquia_algemas_margit |

### Interpretação da cobertura

- `HABILIDADES_UNIDADE_IMPLEMENTADAS` é um conjunto de contrato/nomes. Ele contém `gloria`, `espolios`, `legado`, `devoto`, `escolha_ritmo` e `sinergia_faccao`, mas nem todos esses nomes são executáveis como habilidade de entrada de unidade.
- `gloria` e `espolios` têm uso de ciclo de vida em `_resolve_round()`: Glória mantém uma unidade após vencer a rodada; Espólios compra uma carta ao vencer com a unidade em campo. `espolios` não está atribuído a uma carta atual.
- `sobrevivente` está declarado e possui aura visual; não encontrei ramo de resolução correspondente em `aplicar_jogada()` ou `_resolve_round()`.
- `legado`, `devoto`, `escolha_ritmo` e `sinergia_faccao` aparecem como `effect` em ramificações de `_aplicar_habilidade_identidade()`, mas a função não usa o campo `habilidade` para selecionar o efeito: ela primeiro procura o ID em `CARD_IDENTITY_ABILITIES`. Nenhuma das 22 identidades ativas aponta para esses quatro slugs. As cartas com esses nomes no campo genérico não ativam esses ramos.
- A lista `HABILIDADES_ESPECIAIS_IMPLEMENTADAS` contém as 21 especiais e 6 relíquias. Essas ramificações são tratadas no bloco de cartas especiais de `aplicar_jogada()`.

## 6. Habilidades de identidade por carta

O motor define originalmente 40 registros `CARD_IDENTITY_ABILITIES`; depois filtra IDs que pertencem a `CARTAS_SEM_EFEITO_IDS`. O mapa efetivamente consultado em runtime contém **22 identidades ativas**. Para cartas ativas, a identidade substitui a habilidade genérica: `aplicar_jogada()` define `skill = ''` quando o ID está no dicionário de identidade, e `preparar_carta()` exibe o texto de identidade em lugar do texto da habilidade genérica.

### 22 identidades ativas


| card_id | Nome de identidade | Handler (`effect`) | Texto de regra atualmente exibido |
| --- | --- | --- | --- |
| arma_duas_luas | Dança Espelhada | twin_dance | Ganha +1 se você tiver outro aliado em uma fileira diferente. |
| arma_grande_sino | Sino do Último Bastião | last_bell | Ganha +2 quando sua pontuação total for menor que a do adversário. |
| chefe_dama_vazio | Fenda do Vazio | void_rend | Ao entrar em campo, tira 2 pontos de bônus da unidade inimiga mais forte. O bônus dela não pode ficar abaixo de -2. |
| chefe_guardiao_cinzas | Égide das Cinzas | ash_guardian | Ao entrar em campo, dá +1 de bônus a um aliado da mesma fileira. Se já houver um aliado nessa fileira, esta carta também ganha +1. |
| chefe_malenia_lamina_miquella | Flor Escarlate | scarlet_bloom | Ao entrar em campo, aplica Podridão Escarlate aos inimigos da fileira. Quem já estiver contaminado recebe uma segunda marca. |
| chefe_maliketh_morte_destinada | Morte Destinada | destined_death | Ao entrar em campo, tira até 2 pontos de bônus do inimigo mais forte. |
| chefe_messmer_impalador | Lança do Impalador | impaling_spear | Ao entrar em campo, marca os inimigos da fileira com Sangramento. A segunda marca causa Hemorragia. |
| chefe_oraculo_ruina | Presságio da Ruína | ruin_omen | Tira 1 ponto de bônus da unidade inimiga mais forte. Também ganha +1 se o adversário estiver vencendo. |
| chefe_placidusax_lorde_dragao | Tempestade do Tempo | time_storm | Ao entrar em campo, aplica Geada aos inimigos da fileira e ganha +1 para cada inimigo atingido, até +3. |
| chefe_radahn_flagelo_estrelas | Gravidade do Flagelo | star_gravity | Ao entrar em campo, move o inimigo mais forte para sua fileira e tira 2 pontos de bônus dele. |
| chefe_rei_afogado | Dízimo do Abismo | abyss_tithe | Ganha +2 se você tiver uma unidade no descarte. Se não tiver, ganha +1 caso o adversário tenha mais unidades em campo. |
| covenant_lua_velada | Aliança Lunar | veiled_moon | Esta carta ganha +1 e dá +1 de bônus a um aliado em outra fileira. |
| gwent_v75_lua_graviturgista | Cisalhamento Gravitacional | v75_gravity_shear | Reduz em 1 o bônus de até dois inimigos com bônus positivo na fileira; se atingir dois, recebe +1. |
| gwent_v75_lua_oraculo_geada | Presságio da Geada | v75_frost_oracle | Aplica uma marca de Geada ao inimigo mais forte da fileira; se já tinha uma marca, completa a segunda e recebe +1. |
| gwent_v75_ordem_confessora_graca | Regressão Serena | v75_grace_mender | Purifica até dois aliados da mesma fileira de estados negativos; cada aliado purificado recebe +1. Se ninguém precisar de purificação, fortalece o aliado mais fraco em +1. |
| gwent_v75_ordem_veterano_juramento | Juramento Dourado | v75_golden_vow | Ao entrar, recebe +1; se houver aliado na mesma fileira, o aliado mais fraco também recebe +1. |
| gwent_v75_veu_acolito_sangue | Marca da Dinastia | v75_blood_mark | Aplica uma marca de Sangramento ao inimigo mais forte da fileira; a segunda marca provoca Hemorragia e reduz 2 de bônus. |
| gwent_v75_veu_carrasco_preco | Preço em Sangue | v75_blood_price | Sacrifica o aliado mais fraco da mesma fileira e recebe bônus igual ao seu poder efetivo, até +3; sem aliado, recebe +1. |
| magia_nevoa_antiga | Névoa Ancestral | ancient_mist | Ganha +2 se houver efeito climático em qualquer fileira. |
| magia_selo_vigilia | Selo de Vigília | vigil_seal | Reduz em 1 o dano do clima sofrido por esta carta e dá +1 de bônus a um aliado da mesma fileira. |
| magia_sol_negro | Eclipse Devorador | devouring_eclipse | Ganha +2 se algum inimigo tiver bônus acima de zero. |
| magia_trovao_oco | Descarga Oca | hollow_thunder | Tira 1 ponto de bônus de cada unidade inimiga na mesma fileira. |

### 18 identidades definidas no código, mas filtradas/desativadas em runtime


| card_id | Nome definido | Handler antigo |
| --- | --- | --- |
| arma_agulha_astro | Fio Astral | astral_thread |
| arma_arco_peregrino | Tiro de Cobertura | covering_shot |
| arma_cajado_marulho | Ressonância das Marés | tide_resonance |
| arma_lamina_peregrino | Duelo do Peregrino | pilgrim_duel |
| arma_lanca_fornalha | Investida da Fornalha | furnace_charge |
| arma_martelo_fornalha | Martelo de Cadência | forge_rhythm |
| chefe_aparicao_veio | Deslocamento Espectral | veil_shift |
| chefe_cacador_sem_rosto | Marca da Presa | faceless_hunt |
| chefe_cervo_sombrio | Passagem Sombria | shadow_paths |
| chefe_vigia_cinzento | Vigília Cinzenta | grey_watch |
| covenant_filhos_brasa | Herança da Brasa | ember_kin |
| covenant_peregrinos_nevoa | Rastro na Névoa | mist_trail |
| covenant_sentinelas | Sentinela Compartilhada | shared_sentinel |
| covenant_ultimos | Último Juramento | last_oath |
| magia_brasa_errante | Brasa Persistente | wandering_ember |
| magia_chama_fria | Contrafogo | counterflame |
| magia_fagulha | Faísca Condutora | conductive_spark |
| magia_orbe_eco | Orbe Refrator | echo_orb |

As 18 entradas anteriores continuam escritas no literal original e seus ramos ainda existem no corpo de `_aplicar_habilidade_identidade()`, mas o filtro faz a função devolver `None` para esses IDs. Para essas cartas, o motor não executa a identidade antiga; pode executar a habilidade genérica que esteja no campo `habilidade`. Não apagar sem verificar por que o ID entrou em `CARTAS_SEM_EFEITO_IDS`.

### Ramos de identidade sem ligação ativa

Além das 18 entradas filtradas, o corpo do resolver ainda contém estes handlers para os quais não existe uma associação ativa de identidade:


| Effect slug | Situação |
| --- | --- |
| devoto | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| escolha_ritmo | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| legado | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| sinergia_faccao | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| v75_blood_feast | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| v75_blood_pursuit | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| v75_crucible_guard | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| v75_golden_standard | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| v75_lunar_cartography | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |
| v75_moon_ward | Branch de `_aplicar_habilidade_identidade()` sem registro ativo que a invoque. |

Os quatro slugs `legado`, `devoto`, `escolha_ritmo` e `sinergia_faccao` são particularmente problemáticos: aparecem como valor `Carta.habilidade` em cartas da expansão Esquecidos, mas não são interpretados na cadeia normal de habilidades de unidade. O resolver de identidade só os alcançaria se um card ID fosse associado a eles em `CARD_IDENTITY_ABILITIES` — atualmente não é.

## 7. Sinergias: tags e combos

`CARD_SYNERGY_TAGS` contém 72 associações card_id→tags; cinco IDs não existem em `CARTAS_POR_ID`. O resolver atual `_aplicar_combo_de_cartas()` avalia as tags da carta que está entrando e as tags acumuladas no campo. A política oficial exige: carta atual contribuindo com pelo menos uma tag exigida pelo combo; `minimum: 2` instâncias distintas; `priority` explícita (menor número primeiro); no máximo um combo por jogada; cada combo uma vez por jogador/rodada. Combos pendentes permanecem possíveis, mas só são ativados por uma carta participante posterior. O bônus individual vai para essa carta; `team_bonus` continua alcançando aliados anteriores da mesma fileira.

### Todos os 27 combos — catálogo atual pós-política


| Prioridade | Combo ID | Nome | Tags requeridas | Mínimo de instâncias distintas | Bônus individual | Bônus de equipe | Descrição atual no motor |
|---:|---|---|---|---:|---:|---:|---|
| 10 | `cinzas_fornalha` | Aliança da Árvore Áurea | cinzas, fornalha | 2 | +2 | +0 | Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2). |
| 20 | `veu_sombrio` | Caçada da Faca Negra | veu_sombrio | 2 | +2 | +0 | Duas unidades do Véu Sombrio entram em sintonia (+2). |
| 30 | `vazio_astral` | Alinhamento Astral | astral, vazio | 2 | +2 | +0 | Ranni e uma unidade Astral distinta convergem (+2). |
| 40 | `mare_abissal` | Maré Abissal | abismo | 2 | +2 | +0 | Godfrey e Cavaleiro Carmesim despertam a mesma força (+2). |
| 50 | `juramento_estandarte` | Juramento de Leyndell | estandarte | 2 | +1 | +1 | Porta-estandarte e Guardas da Árvore Áurea fortalecem a formação (+1 para a carta participante que ativa o combo e +1 aos aliados na mesma fileira). |
| 60 | `passos_duas_luas` | Dança da Lua Negra | duas_luas | 2 | +2 | +0 | Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2). |
| 70 | `eco_convergente` | Eco das Pedras Cintilantes | astral, eco | 2 | +2 | +0 | O Erudito das Pedras Cintilantes e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2). |
| 80 | `chama_dupla` | Chamas do Monte Gelmir | chama | 2 | +2 | +0 | Piromante e Feiticeira da Lua Gélida equilibram suas chamas (+2). |
| 90 | `muralha_inabalavel` | Defesa de Leyndell | muralha | 2 | +2 | +1 | Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira). |
| 100 | `banquete_guerra` | Banquete de Sangue | banquete | 2 | +3 | +0 | Carniceiro da Forja e Intendente dividem o butim (+3). |
| 110 | `procissao_fantasma` | Procissão dos que Vivem na Morte | fantasmas | 2 | +2 | +1 | Duas unidades fantasmas marcham juntas (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira). |
| 120 | `caravana_saqueadora` | Saque da Cidade Eterna | caravana | 2 | +2 | +0 | Saqueadora e Contrabandista fecham o negócio (+2). |
| 130 | `ritual_runico` | Ritual das Runas | runico | 2 | +2 | +1 | Duas unidades rúnicas completam o círculo (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira). |
| 140 | `eclipse_voraz` | Eclipse Sanguíneo | eclipse_voraz | 2 | +3 | +0 | Cavaleiro de Sangue de Mohg e Bibliotecária eclipsam a mesma fonte (+3). |
| 150 | `rota_peregrina` | Caminho do Maculado | peregrino | 2 | +1 | +0 | Duelista e Batedor da Mansão Vulcânica coordenam o avanço (+1). |
| 160 | `juramento_erdtree` | Juramento da Árvore Áurea | ordem_dourada | 2 | +2 | +1 | Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira. |
| 170 | `convergencia_lunar` | Convergência da Lua Negra | lua_cariana | 2 | +2 | +0 | Duas unidades ligadas à Lua Negra convergem e recebem +2. |
| 180 | `ritual_dinastia` | Ritual do Véu Carmesim | sangue_mohgwyn | 2 | +2 | +1 | Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1). |
| 190 | `v75_juramento_dois_crisol` | Juramento do Crisol e da Graça | v75_crucible_guard, v75_erdtree_oath | 2 | +2 | +0 | Formação e proteção convergem: a carta participante que ativa o juramento recebe +2. |
| 200 | `v75_banquete_hemorragia` | Banquete da Hemorragia | v75_blood_feast, v75_blood_mark | 2 | +2 | +0 | Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2. |
| 210 | `v75_convergencia_gelida` | Convergência da Geada Lunar | v75_frost_lore, v75_lunar_paths | 2 | +2 | +0 | Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2. |
| 220 | `fe_gloria` | Glória Divina | fe, gloria_divina | 2 | +2 | +0 | A fé e a glória convergem: +2 para a carta participante que ativa o combo. |
| 230 | `fe_devocao` | Devoção | devocao, fe | 2 | +2 | +0 | Duas unidades devotas fortalecem a formação: +2. |
| 240 | `fe_evangelho` | Evangelho | evangelho, fe | 2 | +2 | +0 | Missionários espalham a palavra: +2. |
| 250 | `fe_irmandade` | Irmandade Esquecida | fe, irmandade | 2 | +2 | +0 | Irmãos e missionários unem forças: +2. |
| 260 | `fe_soberania` | Soberania Divina | fe, soberania | 2 | +2 | +0 | O Papa e seus seguidores estabelecem soberania: +2. |
| 270 | `fe_sacerdos` | Sacerdócio | fe, sacerdos | 2 | +2 | +0 | Sacerdotes abençoam a formação: +2. |

### Mapa completo de tags por card ID


| card_id | Tags | ID existe em `CARTAS_POR_ID`? |
| --- | --- | --- |
| arma_agulha_astro | astral, lua_cariana | sim |
| arma_arco_peregrino | peregrino | sim |
| arma_duas_luas | duas_luas, lua_cariana | sim |
| arma_lamina_peregrino | peregrino | sim |
| chefe_aparicao_veio | veu_sombrio | sim |
| chefe_cervo_sombrio | veu_sombrio | sim |
| chefe_dama_vazio | lua_cariana, vazio | sim |
| chefe_guardiao_cinzas | cinzas, ordem_dourada | sim |
| chefe_rei_afogado | abismo, sangue_mohgwyn | sim |
| covenant_coroa_abismo | abismo, sangue_mohgwyn | sim |
| covenant_irmandade_ferro | estandarte | sim |
| covenant_lobos_cinza | cinzas | sim |
| covenant_lua_velada | duas_luas, lua_cariana | sim |
| gwent_unidade_baluarte | fornalha, ordem_dourada | sim |
| gwent_unidade_bibliotecaria | eclipse_voraz | sim |
| gwent_unidade_cacadora_fantasma | fantasmas | sim |
| gwent_unidade_cantora_lamentos | fantasmas | sim |
| gwent_unidade_carniceiro_forja | banquete, sangue_mohgwyn | sim |
| gwent_unidade_cartografa | duas_luas | sim |
| gwent_unidade_cavaleira | veu_sombrio | sim |
| gwent_unidade_circulo | astral | sim |
| gwent_unidade_contrabandista | caravana | sim |
| gwent_unidade_cruzado | fe, gloria_divina | NÃO |
| gwent_unidade_detonador | runico | sim |
| gwent_unidade_devorador_mana | eclipse_voraz, sangue_mohgwyn | sim |
| gwent_unidade_dupla_veu | duas_luas, veu_sombrio | sim |
| gwent_unidade_eco | astral, eco | sim |
| gwent_unidade_evangelista | evangelho, fe | NÃO |
| gwent_unidade_guardiao_runas | runico | sim |
| gwent_unidade_herdeiro_portao | muralha, ordem_dourada | sim |
| gwent_unidade_intendente | banquete | sim |
| gwent_unidade_invocador | astral | sim |
| gwent_unidade_mestre_forja | fornalha, ordem_dourada | sim |
| gwent_unidade_missionario | evangelho, fe | NÃO |
| gwent_unidade_necromante | runico | sim |
| gwent_unidade_portaestandarte | estandarte, fornalha, ordem_dourada | sim |
| gwent_unidade_protetor | fe, protecao | NÃO |
| gwent_unidade_sacerdote | fe | NÃO |
| gwent_unidade_saqueadora_veu | caravana | sim |
| gwent_unidade_senhor_cacada | fantasmas | sim |
| gwent_unidade_sentinela_rubra | muralha, ordem_dourada | sim |
| gwent_unidade_veterano_cercos | muralha | sim |
| gwent_v75_lua_cartografo_lunar | v75_lunar_paths | sim |
| gwent_v75_lua_graviturgista | v75_frost_lore | sim |
| gwent_v75_lua_guardia | v75_lunar_paths | sim |
| gwent_v75_lua_oraculo_geada | v75_frost_lore | sim |
| gwent_v75_ordem_arauto_estandarte | v75_crucible_guard | sim |
| gwent_v75_ordem_confessora_graca | v75_erdtree_oath | sim |
| gwent_v75_ordem_guardiao_crisol | v75_crucible_guard | sim |
| gwent_v75_ordem_veterano_juramento | v75_erdtree_oath | sim |
| gwent_v75_veu_acolito_sangue | v75_blood_mark | sim |
| gwent_v75_veu_cacador_sangue | v75_blood_mark | sim |
| gwent_v75_veu_carrasco_preco | v75_blood_feast | sim |
| gwent_v75_veu_devota_hemorragia | v75_blood_feast | sim |
| luterano_anjo | fe, gloria_divina | sim |
| luterano_anjo2 | fe, gloria_divina | sim |
| luterano_apostolo | evangelho, fe | sim |
| luterano_bispo | devocao, fe | sim |
| luterano_cruzado | fe, gloria_divina | sim |
| luterano_diacon | diaconia, fe | sim |
| luterano_irmao | fe, irmandade | sim |
| luterano_missionario | evangelho, fe | sim |
| luterano_mistico | devocao, fe | sim |
| luterano_papa | fe, soberania | sim |
| luterano_pastor | fe, irmandade | sim |
| luterano_profeta | fe, soberania | sim |
| luterano_sacerdote | fe, sacerdos | sim |
| luterano_vigia | fe, gloria_divina | sim |
| magia_brasa_errante | chama | sim |
| magia_chama_fria | chama | sim |
| magia_nevoa_antiga | astral, lua_cariana | sim |
| magia_orbe_eco | eco | sim |

### IDs órfãos no mapa de tags


- `gwent_unidade_cruzado`
- `gwent_unidade_evangelista`
- `gwent_unidade_missionario`
- `gwent_unidade_protetor`
- `gwent_unidade_sacerdote`

Esses cinco IDs têm tags, mas não são modelos atuais do catálogo. Antes de remover, verificar se representam nomes antigos substituídos por IDs novos ou se são artefatos de uma expansão abandonada.

## 8. Líderes, relíquias e passivas globais

### Líderes


| leader_id | Nome | Facção | Handler | Descrição |
| --- | --- | --- | --- | --- |
| comandante_fornalha | Godfrey | Ordem Áurea | godfrey_warlord | Concede +2 de bônus a todas as suas unidades de Corpo a Corpo. |
| bastiao_ancestral | Morgott | Ordem Áurea | morgott_omen | Na fileira escolhida, concede Escudo a até 2 aliados mais fortes e +1 de bônus a eles. |
| juiz_cerco | Radagon | Ordem Áurea | radagon_purification | Remove Sangramento, Geada, Podridão e Loucura de todos os aliados; cada aliado purificado recebe +1 de bônus. |
| mestre_veu | Mohg | Véu Carmesim | mohg_blood_rite | Aplica uma marca de Sangramento aos 2 inimigos mais fortes da fileira escolhida; uma segunda marca causa Hemorragia (-2 de bônus). |
| sombra_caminhante | Rykard | Véu Carmesim | rykard_devour | Sacrifica seu aliado mais fraco na fileira escolhida; os demais aliados dessa fileira recebem +2 de bônus. |
| voz_caidos | Esgar | Véu Carmesim | esgar_blood_priest | Ressuscita do descarte a unidade mais forte de poder 5 ou menos na fileira escolhida, com +1 de bônus. |
| lider_papa_esquecido | Papa Esquecido | Os Esquecidos | forgotten_blessing | Concede +1 de bônus às unidades dos Esquecidos na fileira escolhida. |
| arquimaga_eclipse | Rennala | Lua Negra | rennala_full_moon | Remove Geada e Podridão dos aliados; cada aliado purificado em Cerco recebe +1 de bônus. |
| mestre_eclipse | Astel | Lua Negra | astel_gravity | A gravidade atinge os inimigos da fileira escolhida: aplica uma marca de Geada a até 3 unidades mais fortes. |
| oraculo_tempestade | Loretta | Lua Negra | loretta_knight | Concede +2 de bônus às 2 unidades aliadas mais fortes de Longa Distância. |

Os líderes são acionados por uma ação específica (`action == 'leader'` no motor), separada da habilidade das unidades. `DEFAULT_LEADERS` define o líder padrão por facção. O estado registra se a habilidade do líder já foi utilizada.

### Relíquias


| ID da relíquia | Nome de carta | Raridade/custo no modelo | ID/descrição de efeito |
| --- | --- | --- | --- |
| reliquia_grande_runa_godrick | Grande Runa de Godrick | Lendária / 3 | `reliquia_godrick` — Exige ao menos uma unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas. |
| reliquia_runa_nao_nascidos | Grande Runa dos Não Nascidos | Lendária / 3 | `reliquia_renala` — Remove Geada e Podridão das unidades aliadas afetadas; cada unidade purificada recebe +1 de bônus. |
| reliquia_runa_morte | Runa da Morte | Mítica / 4 | `reliquia_morte` — Em cada fileira, reduz em até 2 o bônus positivo da unidade inimiga que tiver o maior bônus naquela fileira. |
| reliquia_noite_chama | Espada da Noite e da Chama | Lendária / 3 | `reliquia_noite_chama` — Na postura da Noite, aplica Geada a todas as unidades inimigas da fileira escolhida. Na postura da Chama, atinge a unidade de maior poder efetivo: reduz 1 de poder-base e 2 de bônus; Escudo bloqueia o golpe. |
| reliquia_lamina_negra | Lâmina Negra | Mítica / 4 | `reliquia_lamina_negra` — Na fileira escolhida, reduz em 3 o bônus de uma unidade inimiga (a escolhida ou a de maior poder efetivo). Escudo bloqueia o efeito sem consumir a Relíquia. |
| reliquia_algemas_margit | Algemas de Margit | Épica / 2 | `reliquia_algemas` — Na fileira escolhida, zera o bônus positivo de uma unidade inimiga (a escolhida ou a de maior bônus); bônus negativos permanecem inalterados. |

Relíquias são ativadas dentro do ramo de cartas especiais. Têm uma ativação por partida (`relic_used`); a raridade não amplifica seus valores (budget fixo zero no cálculo de execução). A lista de IDs permitidos e a verificação de propriedade também estão em `bot.py`.

### Passiva de facção

`FACTION_BOOST` define +1 para cada uma das quatro facções. Em cada rodada, a primeira unidade da facção selecionada pelo jogador recebe +1; `faction_boost_used` impede uma segunda ativação na mesma rodada. É um efeito global de configuração de deck, não está escrito individualmente na carta.

## 9. Especial e relíquia — catálogo visual/funcional

São 27 cartas especiais: 21 efeitos `gwent_*` e 6 relíquias. O catálogo completo é:


| card_id | Nome de modelo | Raridade | Custo em `Carta` | habilidade ID | Nome da habilidade | Texto cadastrado |
| --- | --- | --- | --- | --- | --- | --- |
| gwent_especial_tempestade | Tempestade dos Picos | Rara | 2 | gwent_clima | Tempestade dos Picos | Escolha uma fileira. A tempestade reduz em 1 o poder efetivo de todas as unidades dos dois lados nessa fileira enquanto o clima estiver ativo. |
| gwent_especial_nevoa | Miasma da Podridão | Rara | 2 | gwent_nevoa | Névoa de Sellia | Aplica 1 marca de Podridão Escarlate a todas as unidades inimigas da fileira escolhida; raridades Lendárias ou superiores aplicam uma segunda marca. |
| gwent_especial_geada | Geada dos Picos dos Gigantes | Rara | 2 | gwent_geada | Lua Gélida | Aplica 1 marca de Geada a todas as unidades inimigas em campo; raridades Lendárias ou superiores aplicam uma segunda marca. |
| gwent_especial_chuva | Sangue Corrompido | Comum | 1 | gwent_chuva | Sangue Corrompido | Aplica uma marca de Sangramento a todas as unidades inimigas na fileira de Cerco; a segunda marca reduz 2 de bônus (mínimo -2) e consome as marcas. |
| gwent_especial_chifre | Rugido de Godfrey | Épica | 3 | gwent_chifre | Rugido de Godfrey | Concede +2 às suas unidades na fileira escolhida até o fim da rodada. |
| gwent_especial_medico | Lágrima Sagrada | Rara | 2 | gwent_medico | Lágrima Sagrada | Devolve à sua mão uma unidade do seu descarte com poder-base 4 ou menos; você pode escolher o alvo. |
| gwent_especial_queima | Chama Negra | Épica | 3 | gwent_queima | Chama Negra | Tenta remover a unidade de maior poder efetivo de cada lado; um escudo pode bloquear cada remoção. |
| gwent_especial_purificar | Lei da Regressão | Rara | 2 | gwent_purificar | Lei da Regressão | Remove todos os efeitos climáticos. |
| gwent_especial_execucao | Lâmina da Morte Destinada | Épica | 3 | gwent_execucao | Lâmina da Morte Destinada | Remove uma unidade inimiga escolhida da fileira selecionada se ela tiver poder efetivo 6 ou menos; um escudo pode bloquear a remoção. |
| gwent_especial_vinculo | Juramento do Crisol | Rara | 2 | gwent_vinculo | Juramento do Crisol | Se houver ao menos duas unidades aliadas na fileira escolhida, concede +2 a todas elas até o fim da rodada. |
| gwent_especial_batedor | Passo do Cão de Caça | Rara | 2 | gwent_batedor | Passo do Cão de Caça | Compra uma carta da reserva, se disponível. |
| gwent_especial_muralha | Bastião de Leyndell | Comum | 1 | gwent_muralha | Bastião de Leyndell | Concede +1 às suas unidades na fileira escolhida até o fim da rodada. |
| elden_especial_sangramento | Ritual de Sangue | Rara | 2 | gwent_sangramento | Sangramento | Marca as unidades inimigas da fileira; a segunda marca reduz o bônus em 2 (mínimo -2) e consome as marcas. Marcas expiram no fim da rodada. |
| elden_especial_geada | Lua Cheia de Rennala | Rara | 2 | gwent_geada_cariana | Geada Cariana | Aplica até duas marcas às unidades inimigas da fileira escolhida; cada marca reduz 1 de poder efetivo até o fim da rodada. |
| elden_especial_podrida | Flor da Podridão Escarlate | Épica | 3 | gwent_podrida | Podridão Escarlate | Cada marca reduz 1 de poder efetivo; a segunda também corrói 1 ponto de bônus positivo, se houver. Marcas expiram no fim da rodada. |
| elden_especial_loucura | Chama Frenética | Épica | 3 | gwent_loucura | Loucura Frenética | Cada marca reduz 1 de poder efetivo; a segunda remove todos os bônus positivos da unidade. Marcas expiram no fim da rodada. |
| elden_especial_chama | Chama do Gigante | Rara | 2 | gwent_chama | Chama do Gigante | Remove Geada de todas as suas unidades; cada unidade purificada recebe +1 de poder até o fim da rodada. |
| elden_especial_invocacao | Cinzas dos Lobos Solitários | Rara | 2 | gwent_invocacao | Cinzas dos Lobos Solitários | Invoca Lobos Espirituais com 3 de poder na fileira escolhida. |
| reliquia_grande_runa_godrick | Grande Runa de Godrick | Lendária | 3 | reliquia_godrick | Grande Runa de Godrick | Exige ao menos uma unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas. |
| reliquia_runa_nao_nascidos | Grande Runa dos Não Nascidos | Lendária | 3 | reliquia_renala | Grande Runa dos Não Nascidos | Remove Geada e Podridão das unidades aliadas afetadas; cada unidade purificada recebe +1 de bônus. |
| reliquia_runa_morte | Runa da Morte | Mítica | 4 | reliquia_morte | Runa da Morte | Em cada fileira, reduz em até 2 o bônus positivo da unidade inimiga que tiver o maior bônus naquela fileira. |
| reliquia_noite_chama | Espada da Noite e da Chama | Lendária | 3 | reliquia_noite_chama | Espada da Noite e da Chama | Na postura da Noite, aplica Geada a todas as unidades inimigas da fileira escolhida. Na postura da Chama, atinge a unidade de maior poder efetivo: reduz 1 de poder-base e 2 de bônus; Escudo bloqueia o golpe. |
| reliquia_lamina_negra | Lâmina Negra | Mítica | 4 | reliquia_lamina_negra | Lâmina Negra | Na fileira escolhida, reduz em 3 o bônus de uma unidade inimiga (a escolhida ou a de maior poder efetivo). Escudo bloqueia o efeito sem consumir a Relíquia. |
| reliquia_algemas_margit | Algemas de Margit | Épica | 2 | reliquia_algemas | Algemas de Margit | Na fileira escolhida, zera o bônus positivo de uma unidade inimiga (a escolhida ou a de maior bônus); bônus negativos permanecem inalterados. |
| gwent_especial_egide | Bênção da Árvore Áurea | Rara | 2 | gwent_egide | Bênção da Árvore Áurea | Concede escudo a uma unidade sua. |
| gwent_especial_requiem | Chamado dos Mortos | Épica | 3 | gwent_requiem | Chamado dos Mortos | Traz do descarte diretamente ao campo uma unidade com poder base 6 ou menos. |
| gwent_especial_passo | Passo do Lobo | Rara | 2 | gwent_passo | Passo do Lobo | Move uma unidade sua para a fileira escolhida. |

## 10. Falhas e inconsistências demonstráveis

### 10.1 Fontes de descrição divergentes

1. A interface principal usa `/api/gwent/cards` e prepara parte dos modelos/exemplares via `preparar_carta()`.
2. A biblioteca pública em `site/catalogo-cartas.html` usa `/api/gwent/catalogo-cartas` em `site_hub.py`.
3. `catalogo_cartas_api()` usa `Carta.para_dict()` e `HABILIDADES.get(data['habilidade'])`; não consulta `CARD_IDENTITY_ABILITIES`, não utiliza o texto final de `preparar_carta()` e usa `carta.descricao` como fallback para o campo de texto de habilidade.
4. `preparar_carta()` usa identidade ativa como texto prioritário, senão `habilidade_texto` ou `HABILIDADES`; adiciona textos extras para alguns efeitos de acordo com raridade.

**Impacto:** uma carta com identidade ativa pode exibir a habilidade genérica na biblioteca e a habilidade de identidade no jogo/coleção. Uma carta que não tem habilidade pode ter lore mostrada na coluna de habilidade no catálogo público. As duas rotas não constituem uma fonte única de texto.

### 10.2 Habilidade nominal sem execução ou sem cobertura

- `sobrevivente`: existe em `HABILIDADES` e em `_AURAS` de `arte_gwent_efeitos.py`, mas não há resolução funcional no motor. A carta não está atribuída no catálogo atual.
- `legado`: atribuído a `luterano_pastor`; ramo só existe no resolver de identidade, mas o ID não está mapeado para esse handler.
- `devoto`: atribuído a `luterano_bispo` e `luterano_mistico`; não está ligado ao handler de identidade por card ID.
- `sinergia_faccao`: atribuído a `luterano_cruzado`, `luterano_papa` e `luterano_profeta`; não está ligado ao handler de identidade por card ID.
- `escolha_ritmo`: handler no resolver de identidade sem carta atual que use o ID e sem associação ativa.
- `espolios`: regra de fim de rodada implementada, mas não atribuída a carta atual.
- A auditoria de `sistemas/auditoria_efeitos.py` compara nomes com conjuntos declarativos. Como esses conjuntos incluem slugs sem rota executável no fluxo genérico, a auditoria pode classificar como coberto algo que não é acionado pela carta atual.

### 10.3 Habilidade genérica suprimida por identidade

Para os 22 IDs de identidade ativa, `aplicar_jogada()` define `skill = ''`; a habilidade genérica presente no modelo é ignorada. Isso é intencional no comentário do motor para impedir dois efeitos, mas deixa os dados com dois valores concorrentes: `Carta.habilidade` pode parecer ativo e ser substituído pela identidade. `preparar_carta()` usa a identidade para o texto, mas o campo `habilidade` ainda retorna o valor genérico. Qualquer consumidor que observe apenas `habilidade` pode interpretar incorretamente qual efeito executará.

### 10.4 Custo: gravado em várias camadas, mas não validado como orçamento

- Há `Carta.custo` e `CUSTO_RARIDADE`.
- 19 cartas apresentam `Carta.custo != CUSTO_RARIDADE[raridade]` (tabela abaixo).
- O endpoint principal atribui `payload['custo']` antes de `preparar_carta()`, mas `preparar_carta()` não inclui `custo` em seu retorno. Portanto, o item preparado pode perder o custo atribuído pelo chamador.
- `/api/gwent/catalogo-cartas` expõe diretamente `carta.custo`, ao passo que rotas de coleção/deck recalculam o custo por raridade em pelo menos alguns payloads. O número exibido pode variar por rota.
- `POST /api/gwent/deck` valida 12 diferentes, propriedade, 8 unidades/máximo 4 especiais, facção predominante, líder e relíquia; não soma custo e não compara com um orçamento.
- `cartas_gwent_decks` não armazena custo total. O frontend não envia um `total_cost` autoritativo; backend deve ser a autoridade quando a regra for criada.
- `sistemas/arte_cartas.py` tem comentário explícito de que o espaço inferior da carta-base é usado para habilidade e o sistema atual não usa custo de carta/deck.

#### 19 divergências de custo


| card_id | Custo em `Carta` | Raridade | Custo por `CUSTO_RARIDADE` |
| --- | --- | --- | --- |
| chefe_malenia_lamina_miquella | 4 | Primordial | 6 |
| chefe_radahn_flagelo_estrelas | 4 | Primordial | 6 |
| chefe_placidusax_lorde_dragao | 4 | Primordial | 6 |
| reliquia_grande_runa_godrick | 3 | Lendária | 4 |
| reliquia_runa_nao_nascidos | 3 | Lendária | 4 |
| reliquia_runa_morte | 4 | Mítica | 5 |
| reliquia_noite_chama | 3 | Lendária | 4 |
| reliquia_lamina_negra | 4 | Mítica | 5 |
| reliquia_algemas_margit | 2 | Épica | 3 |
| luterano_bispo | 3 | Lendária | 4 |
| luterano_anjo | 2 | Épica | 3 |
| luterano_papa | 4 | Mítica | 5 |
| luterano_profeta | 4 | Mítica | 5 |
| luterano_anjo2 | 3 | Lendária | 4 |
| primordial_origem | 4 | Primordial | 6 |
| primordial_trono | 4 | Primordial | 6 |
| primordial_tempestade | 4 | Primordial | 6 |
| primordial_abismo | 4 | Primordial | 6 |
| primordial_eternidade | 4 | Primordial | 6 |

### 10.5 Poder-base e raridade não são a fórmula nova

- Unidades do catálogo atual: poder-base 3–10.
- Especiais do catálogo atual: poder 0 (por definição da categoria atual).
- `limite_poder_modelo()` estabelece teto 12, enquanto `preparar_carta()` clampa a exibição/payload para 1–15. São contratos diferentes.
- Raridade de modelos estáticos está declarada carta a carta; peso do pacote é separado; raridade de carta de jogo/patente deriva de regras específicas; carta procedural herda mediana inferior da raridade dos ingredientes.
- Não existe pontuação normalizada que some poder-base, magnitude/condição/abrangência do efeito e custo e então derive raridade.

### 10.6 Geração aleatória/probabilística de habilidades

- `gerar_carta_procedural()` seleciona `habilidade_id` com `rng.choice(pool_habilidades)` se `rng.random() < 0.5`; usa `rng.randint()` para poder; também sorteia arquétipo e epíteto.
- A seed torna os resultados reproduzíveis para a mesma entrada, mas a probabilidade de 50% não garante meta mínima de cartas puras no catálogo nem evita que um lote particular viole a proporção.
- `calcular_distribuicao_50_50()` e `avaliar_balanceamento_cumulativo()` apenas medem o desvio acumulado; não escolhem o próximo tipo de carta.
- `carta_jogo()` e `carta_patente()` fazem seleção determinística por hash para atribuir habilidade sob certas condições, mas também não avaliam o peso da habilidade/custo/poder para classificar raridade.

### 10.7 IDs de combo órfãos

Os cinco IDs listados na seção 7 permanecem em `CARD_SYNERGY_TAGS`, sem modelo em `CARTAS_POR_ID`.

### 10.8 Facção conflitante na expansão dos Esquecidos

A seção da lista `CARTAS_EXPANSAO_V75` introduz “Nova facção: Os Esquecidos — fé, tradição e rituais sagrados”; o comentário de `CARD_SYNERGY_TAGS` também agrupa os IDs abaixo como unidades dos Esquecidos. No entanto, os campos atuais de facção em `Carta(...)` não são todos `Os Esquecidos`:


| card_id | Nome | Facção atualmente cadastrada | Habilidade nominal | Tags |
| --- | --- | --- | --- | --- |
| luterano_apostolo | Apóstolo Esquecido | Ordem Áurea | — | evangelho, fe |
| luterano_pastor | Pastor Esquecido | Véu Carmesim | legado | fe, irmandade |
| luterano_mistico | Místico Esquecido | Lua Negra | devoto | devocao, fe |
| luterano_profeta | Profeta Esquecido | Ordem Áurea | sinergia_faccao | fe, soberania |
| luterano_vigia | Vigia da Noite | Véu Carmesim | gloria | fe, gloria_divina |
| luterano_anjo2 | Anjo de Segunda Ordem | Lua Negra | gloria | fe, gloria_divina |

A discrepância é demonstrável entre agrupamento/comentários e o campo de facção. A intenção provável é que os seis sejam `Os Esquecidos`, mas isso é uma inferência contextual; confirmar a regra de facção antes de mudar dados, especialmente porque facção influencia predominância e passiva da partida.

### 10.9 Imagem pode divergir dos dados e da habilidade executada

- `preparar_payload_carta_base()` chama `preparar_carta()` e replica `habilidade_nome`/`habilidade_texto` para a renderização gerada.
- Em `_draw_card()`, quando `illustration_bytes` contém arte oficial completa, o renderizador abre e redimensiona a imagem e retorna imediatamente; não sobrepõe nome, poder, raridade, habilidade, moldura ou efeitos. Os textos antigos estão literalmente incorporados nos pixels.
- A documentação do Ateliê (`docs/ATELIE_CARTA_COMPLETA.md`) confirma que a arte oficial é associada a `card_id + exemplar_id` e que imagens antigas já aprovadas não são reescritas pelo código.
- A imagem-base desenha aura usando `card['habilidade']`, não `habilidade_identidade` nem `CARD_IDENTITY_ABILITIES[card_id]['effect']`. Assim, as auras só cobrem algumas habilidades genéricas.
- `_AURAS` contém 6 entradas: `escudo_ferro`, `vinganca`, `ressurgir`, `devorar`, `sobrevivente`, `espolios`. A última lista inclui `sobrevivente`, que não tem resolução no motor.
- `_EMBLEMAS` de especiais também é um mapeamento específico e parcial; se o ID não for desenhado, o renderer usa emblema genérico.

**Impacto:** corrigir catálogo/motor não atualiza imagem completa aprovada. Uma carta pode continuar visualmente mostrando regra/nome/poder antigo mesmo após os dados atuais serem atualizados. As imagens precisam ser identificadas por revisão/fingerprint ou regeneradas/reaprovadas segundo política explícita.

### 10.10 Cobertura da lista V18 não equivale a carta pura

`CARTAS_SEM_EFEITO_IDS` é montada por regra V18, limpando o campo `habilidade` e aumentando o poder em +1 até o teto da faixa. O conjunto contém 43 IDs. Isso não torna automaticamente todas essas cartas puras sob a definição desta auditoria: tags de combo e/ou identidades ainda podem gerar efeitos. A contagem real de cartas puras usa também identidade ativa e tags.

## 11. Arte e geração de imagem — contratos atuais

### Imagem-base procedural

1. Endpoint público recebe `card_id` e parâmetros como raridade, poder, exemplar e thumbnail.
2. `bot.py` resolve a carta e o exemplar; usa `preparar_payload_carta_base()`/`etag_carta_base()` para formar o payload/fingerprint.
3. `sistemas/arte_cartas.py` escolhe paleta por facção, moldura por raridade, categoria e fileira; o texto é desenhado no painel inferior.
4. Para unidade, chama `desenhar_aura_unidade(..., card['habilidade'], ...)`.
5. Para especial, chama `desenhar_emblema_especial(..., card['habilidade'], ...)`; se não existir emblema, desenha símbolo genérico.
6. Cache existe em PNG/WebP e inclui fingerprints do renderer/templates; invalidar arte após alteração estrutural exige revisar `VERSAO_ARTES`/fingerprint e os parâmetros de ETag.

### Arte integral aprovada

- Arte integral é um asset distinto, associado ao exemplar no Ateliê.
- A imagem completa substitui a carta procedimental sem sobreposições. O conteúdo textual fica fora do sistema de composição.
- Para manter consistência após redesign, decidir entre: regenerar/reaprovar arte integral, guardar revisão/versionamento da arte, ou compor textos/metadados dinâmicos por cima da arte (mudança de arquitetura).

## 12. Estado da auditoria e riscos de limpeza

### Pode ser candidato a remoção, mas requer confirmação

- 18 registros de identidade filtrados em runtime, cujos handlers continuam no código.
- Seis handlers V75 adicionais sem associação ativa de identidade.
- Quatro handlers `legado`, `devoto`, `escolha_ritmo`, `sinergia_faccao` no resolver de identidade, sem associação ativa adequada.
- Cinco IDs de tags de combo órfãos.
- `sobrevivente` na definição e na arte, sem resolução no motor.
- Arquivos auxiliares de deck e auditoria sem chamada detectada em alguns fluxos; ausência de importação estática não prova ausência de uso por scripts externos.

### Não apagar sem migração/compatibilidade

- IDs de carta já gravados em `cartas_colecao`, `cartas_exemplares`, `cartas_gwent_decks`, `cartas_gwent_matches` e tabelas de artes.
- Campos `card_ids_json`, `exemplar_ids_json` e `state_json`.
- Imagens oficiais vinculadas a exemplares.
- Raridades/poderes individuais antigos; não há DB de produção neste pacote para determinar a distribuição de exemplares em uso.
- Efeitos usados por snapshots de partidas em andamento.
- Regras de líderes, relíquias e recompensas que dependam de IDs antigos.

## 13. Plano de correção proposto (ainda não executado)

1. Congelar este baseline; guardar cópia/hash do catálogo, tags, combos e snapshots de schema.
2. Definir especificação canônica versionada da carta e de habilidade (um ID de regra por efeito; separar lore de texto mecânico; nenhuma regra inferida de nome/descrição).
3. Decidir se especiais contam no denominador dos 30% puros; recomendado: 30% do catálogo total de modelos (42/137 no baseline), com cartas puras sendo unidades.
4. Especificar efeito puro como ausência de habilidade individual, identidade, participação em combo e qualquer trigger próprio. Definir explicitamente tratamento da passiva de facção.
5. Construir catálogo de efeitos canônicos; avaliar cada efeito por magnitude, alvos, condições, duração, possibilidade de resposta, economia de cartas e sinergia.
6. Fixar regra de poder-base 1–15 e especificar separadamente como cartas especiais tratam poder-base (hoje usam 0).
7. Definir função de custo de carta e orçamento máximo do deck; validar backend como autoridade; frontend apenas pré-valida/mostra.
8. Definir raridade como saída de score documentado que envolva poder, orçamento de efeito e custo; evitar círculo vicioso em que raridade determina orçamento de efeito e efeito determina raridade sem uma sequência/fórmula explícita.
9. Corrigir/unificar facções, IDs, tags e identidades; criar migração para exemplares existentes e compatibilidade dos decks salvos.
10. Unificar texto da carta para API principal, biblioteca, modal e renderizador.
11. Definir política para imagem oficial aprovada e cache de imagem antiga.
12. Criar testes por habilidade, combo, líder, relíquia, clima, cartas puras, deck custo e consistência do payload/arte.
13. Só então remover handlers mortos e campos obsoletos, com histórico por arquivo.

## 14. Arquivos e trechos mais relevantes para a próxima etapa


| Arquivo e região/função | Por que abrir primeiro |
| --- | --- |
| `sistemas/cartas.py:20–53` (`PESOS_RARIDADE`, `CUSTO_RARIDADE`, `FAIXA_PODER`, `limite_poder_modelo`) | Política atual de raridade/custo/poder e discrepância de teto. |
| `sistemas/cartas.py:58–194` (`HABILIDADES`) | Fonte do nome e texto genérico de efeito. |
| `sistemas/cartas.py:196–205` (`Carta`) | Schema canônico incompleto para nova especificação. |
| `sistemas/cartas.py:357–386` (V18) e `388–419` (V75 / catálogo) | Limpeza antiga de IDs e catálogo novo. |
| `sistemas/gwent.py:216–238` (conjuntos de implementação / facções / líderes) | Contrato de nomes, passivas e líderes. |
| `sistemas/gwent.py:261–426` (tags, combos, identidades e filtro) | Principal fonte de efeitos paralelos/legados. |
| `sistemas/gwent.py:428–638` (`_aplicar_habilidade_identidade`) | Handlers individuais; distinguir ativos de ramos sem chamada. |
| `sistemas/gwent.py:650–795` (orçamento e `preparar_carta`) | Amplificação de raridade e texto apresentado. |
| `sistemas/gwent.py:874–949` (estado/evento/combo) | Snapshot inicial e ativação de sinergias. |
| `sistemas/gwent.py:957–1176` (remoção/pontuação/resolução de rodada) | Estados, morte, Glória/Espólios, clima e fim da rodada. |
| `sistemas/gwent.py:1217–1880` (`aplicar_jogada`) | Ponto central que resolve ações, unidades, especiais, líderes e relíquias. |
| `bot.py:1093–1410` (GET/POST deck e snapshot) | Validação, persistência e construção do deck. |
| `bot.py:1431–1900` (partidas/ações) | Snapshots e comunicação com o motor. |
| `bot.py:2114–2200` (API cartas), `3012+` e `3342+` (imagens) | Payload da coleção/catálogo e servir imagens. |
| `site_hub.py:1073–1150` + router perto de 1174 | Biblioteca pública e descrição alternativa. |
| `site/app.js:175–200`, `400–420`, `1004–1080`, `2278–2400` | Consumo das APIs, carta/modal, deck builder e partida. |
| `site/catalogo-cartas.html:160` | A segunda fonte de catálogo no frontend. |
| `database.py:484–650`, migrações perto de 940–1148 e métodos deck perto de 3930 | Schema e compatibilidade do banco. |
| `sistemas/arte_cartas.py:1018–1380`, `1638–1660`, `1696–1815` | Render, arte integral, payload e cache. |
| `sistemas/arte_gwent_efeitos.py:48–55`, `169–190` | Mapa de auras e emblemas. |
| `sistemas/gerador_cartas.py:47–100`, `146–258`, `260–370` | Sorteio, balanceamento cumulativo e validação de cartas geradas. |
| `cogs/painel_jogo.py:451+` | Comando Discord `/jogo`. |

## 15. Critério de conclusão desta auditoria

- [x] ZIP descompactado e estrutura do projeto listada.
- [x] Módulos `sistemas.cartas` e `sistemas.gwent` importados para extrair catálogo e estruturas runtime.
- [x] Catálogo de habilidades e status de cobertura catalogados.
- [x] Identidades ativas vs. filtradas listadas.
- [x] Tags, combos, líderes, relíquias e facções mapeados.
- [x] Persistência, APIs, frontend e renderização rastreados estaticamente.
- [x] Falhas comprováveis e inferências explicitamente separadas.
- [ ] Execução do bot contra DB de produção.
- [ ] Testes de cada habilidade em partida real.
- [ ] Verificação de artes já aprovadas e cache em ambiente publicado.
- [ ] Alteração funcional, migração ou remoção de código (não iniciadas).

**Regra para continuidade:** este documento descreve o estado antigo. Após cada alteração, atualizar também `docs/card-game-handoff.md`, registrar arquivo/função/campo, motivação, impacto, teste executado e estado de validação. Não editar o baseline para apagar o histórico; criar nova revisão se for necessário corrigir a auditoria.


## 12. Matriz de rastreabilidade individual

A etapa subsequente gerou os seguintes documentos para cobrir todas as definições do catálogo runtime (137 modelos):

- [`card-game-card-traceability.md`](card-game-card-traceability.md): tabela e ficha individual por carta.
- [`card-game-card-traceability.csv`](card-game-card-traceability.csv): formato filtrável.
- [`card-game-card-traceability.json`](card-game-card-traceability.json): formato estruturado.

A matriz captura o valor runtime após a transformação V18, a habilidade nominal, identidade ativa e filtrada, tags, combos potenciais, classificação de carta pura, custo cadastrado/tabelado, texto preparado, alertas de execução e cobertura visual. Também formaliza a ambiguidade de payload: `preparar_carta()` mantém o ID genérico no campo `habilidade`, mas usa nome/texto da identidade; `aplicar_jogada()` suprime o genérico e executa apenas a identidade. A retificação completa está na seção “Correção técnica posterior” e na matriz JSON/CSV. A verificação individual também encontrou 43 declarações alteradas pela transformação V18 durante import, 9 cartas com IDs de habilidade sem metadados em `HABILIDADES` (três `gloria` executadas no ciclo de rodada e seis IDs sem ligação genérica ativa), e cinco IDs de tags sem carta correspondente no catálogo.


## Correção técnica posterior — identidade ativa e habilidade genérica (2026-11-27)

Uma afirmação anterior da matriz e do handoff foi retificada após leitura direta do resolver. Em `sistemas/gwent.py`, dentro de `aplicar_jogada()` no ramo `action == "play"`, o código calcula `skill = "" if card_id in CARD_IDENTITY_ABILITIES else card.get("habilidade", "")`. Portanto, para as 16 cartas com ambos os campos preenchidos, a habilidade genérica é suprimida e **não** é executada; a identidade ativa é chamada posteriormente por `_aplicar_habilidade_identidade()`.

O problema confirmado é ambiguidade do payload de `preparar_carta()` (aprox. linhas 695–795): o retorno mantém `"habilidade": skill` com o ID genérico, mas escolhe `habilidade_nome` e `habilidade_texto` da identidade. Consumidores que leiam somente o ID podem associar a regra errada. O próximo contrato canônico deve expor um único `effect_id` efetivo e, no máximo, guardar o ID substituído como metadado legado. A matriz JSON/CSV foi corrigida com `habilidade_generica_suprimida_por_identidade=true`.

Esta retificação não altera a evidência de que existem 16 registros com os dois campos preenchidos; corrige apenas a interpretação de execução.


## 16. Validação exploratória dos handlers e combos (2026-11-27)

A validação posterior está detalhada em [`card-game-balance-validation-v0.1.md`](card-game-balance-validation-v0.1.md). Os achados são diagnósticos, não alterações funcionais:

- `HABILIDADES` tem 59 IDs. A auditoria AST encontrou 56 habilidades com comparações/resolução no caminho direto de `aplicar_jogada()`; `instinto` e `fome_abismo` compartilham uma condição de conjunto e estão incluídas nessa contagem. `vinganca` e `espolios` são hooks de ciclo de vida em `_remover_unidade()` e `_resolve_round()`. `sobrevivente` não tem handler correspondente encontrado.
- `gloria` é um hook de retenção de unidade em `_resolve_round()`, mas não está em `HABILIDADES`. O teste sintético confirma a retenção ao vencer a rodada.
- Existem 22 identidades ativas, todas com ramo no resolvedor; o código mantém 50 valores de `effect` e 28 não têm mapeamento ativo. Não remover sem decidir se são legados a aposentar ou mecânicas a recuperar.
- Há 27 combos; as tags obrigatórias de todos têm provedores no catálogo. `CARD_SYNERGY_TAGS` tem 72 IDs mapeados, dos quais 67 são unidades atuais e cinco são IDs órfãos.
- Testes de fumaça chamaram o motor real em estados sintéticos: 56 ações diretas foram concluídas sem exceção; 22/22 identidades geraram evento de ativação; `vinganca` e `espolios` foram testados nos respectivos hooks; `sobrevivente` caiu no descarte. Isso não é cobertura completa dos ramos condicionais nem equilíbrio competitivo.
- Amostragem de 100.000 decks, seed 42: 57,19% ativaram pelo menos um combo; média 0,956 ativação na mão de dez cartas assumida jogada na mesma rodada. O resultado é sensível à ordem aleatória e não mede valor de pontuação/vitória.
- A amostragem de custo v0.2 reproduz: teto 32 aceita 68,8% sem relíquia e 45,4% com relíquia nas hipóteses do script. EFP e `leader_load` continuam provisórios.

Consulte os quatro artefatos JSON em `docs/` e os scripts correspondentes em `docs/scripts/`; não use valores da v0.1 de custo como justificativa para aprovar o teto 32.


## 17. Índice AST de handlers por identificador (2026-11-27)

O documento [`card-game-effect-source-map-v0.1.json`](card-game-effect-source-map-v0.1.json) é o índice AST histórico do baseline pré-política. Seu gerador `scripts/build-effect-source-map-v0.1.py` agora recusa execução no runtime atual para não sobrescrever esse registro; use `scripts/build-effect-source-map-v0.2.py` e `card-game-effect-source-map-v0.2.json` para referências atuais. O mapa atual diferencia 56 handlers diretos de habilidades genéricas, dois hooks de ciclo de vida (`vinganca`, `espolios`) e `sobrevivente` sem handler; as 22 identidades ativas e os dez líderes têm referências de execução. `gloria` é um hook oculto em `_resolve_round()` fora do catálogo declarado. O mapa AST é índice de evidência, não substitui teste comportamental por ramo. Para avaliação de força, consultar `card-game-efp-methodology-v0.2.md`; scores v0.1 permanecem não aprovados.


## 18. Primeiros asserts comportamentais (2026-11-27)

A primeira bateria está em [`scripts/assert-card-effect-behavior-v0.1.py`](scripts/assert-card-effect-behavior-v0.1.py), com saída em [`card-game-effect-behavior-assertions-v0.1.json`](card-game-effect-behavior-assertions-v0.1.json). Foram verificados 13 resultados explícitos no motor real em estados sintéticos; 13 passaram. Os casos cobrem exemplos de buff, debuff, compra, escudo, ressurreição, movimento, invocação, remoção, clima, marcas, execução e identidade. A cobertura é representativa e parcial; consultar `card-game-balance-validation-v0.1.md` e `card-game-efp-methodology-v0.2.md` para os limites e os próximos testes necessários.


## 19. Histórico pré-política: validação comportamental v0.2 — sete suites e 219/219 asserts

> **Registro histórico pré-patch.** O resultado atual foi ampliado para oito suites e 251/251 asserts; consulte a seção 21 e `card-game-behavior-validation-v0.3.md` para o estado vigente.

A validação sintética do motor foi expandida para sete suites, com **219/219 asserts aprovados**. O relatório agregado e as limitações estão em `card-game-behavior-validation-v0.2.md/.json`. Além das 13 amostras iniciais, identidades, habilidades genéricas, ciclo de vida, especiais, relíquias e líderes, a bateria agora exercita os 27 combos (um par ativador concreto por definição), requisitos incompletos, bloqueio de repetição do mesmo combo, passivas das quatro facções e o caso de especial que não consome a passiva de unidades.

A suite de combos/passivas contém 87 asserts: 27 positivos, 27 incompletos, 27 verificações de não repetição do mesmo `combo_id`, um caso sem tags, quatro passivas de facção (unidade estrangeira, primeira/segunda unidade e reset na rodada seguinte) e um caso de especial. O resolvedor pode ativar um segundo combo diferente a partir das mesmas tags; o teste verifica que o combo originalmente usado não é repetido, sem tratar outro combo válido como falha.

Limitações: cada combo foi testado com um par ativador descoberto a partir da tabela de tags atual. Pares alternativos, permutações de tags sobrepostas e precedência de múltiplos combos simultaneamente elegíveis não foram exauridos. Os testes continuam sendo fixtures sintéticos em memória, não partidas completas nem integração com banco, APIs, frontend, Discord, R2 ou arte publicada. Tampouco medem win rate ou EFP.

A auditoria de associação separa os 28 ramos de identidade sem carta ativa em 18 definições filtradas pela V18, quatro campos legados (`devoto`, `legado`, `escolha_ritmo`, `sinergia_faccao`) e seis ramos V75. A análise individual consta em `card-game-stale-identity-disposition-v0.1.md/.json`. Não remover antes de decidir o destino de cada carta e revisar tags/combos. `gloria` (hook de rodada fora do catálogo) e `sobrevivente` (sem handler localizado) são problemas adicionais, separados dessa contagem.

Naquela fase pré-patch, o motor e os dados funcionais continuavam inalterados. Essa afirmação não descreve o estado atual após a implementação aprovada da política de combos.


## 20. Histórico pré-patch: auditoria de sobreposição, precedência e participação em combos (2026-11-27)

> **Registro histórico do defeito original.** Os números e exemplos abaixo descrevem o resolver antes da política aprovada. O estado pós-correção está em `card-game-combo-overlap-v0.2.md/.json` e na seção 21 deste documento.

Relatório histórico: `card-game-combo-overlap-v0.1.md/.json`; o script `docs/scripts/audit-combo-overlap-v0.1.py` só reproduz esse baseline em um checkout pré-política. O script agora recusa execução no runtime atual para não produzir resultados enganadores. A auditoria pós-política vigente é `card-game-combo-overlap-v0.2.md/.json`, gerada por `audit-combo-overlap-v0.2.py`. O baseline histórico examinou 67 unidades com tags, 4.422 ordens de pares distintos e 287.430 sequências de três unidades.

Achados: 154 pares ordenados (3,4826%; 77 pares não ordenados) têm múltiplos combos simultaneamente elegíveis; a função aplica o primeiro pela ordem de inserção do dicionário e retorna, deixando outros pendentes. Em 11.780 trincas (4,0984%) ocorrem dois ou mais combos distintos ao longo das jogadas; 1.088 dessas trincas são de mesma facção. Em 8.096/11.784 acionamentos posteriores (68,7033%), a carta atual não fornece tag exigida pelo combo que recebe. O motivo é que a função só exige que a carta atual tenha qualquer tag não vazia; a condição do combo e `minimum` podem já estar completos no tabuleiro.

Três definições não declaram `minimum`: `cinzas_fornalha`, `vazio_astral` e `eco_convergente`. A unidade `gwent_unidade_eco` (`Erudito das Pedras Cintilantes`) ativa `eco_convergente` sozinha com as tags `astral` + `eco`, embora a descrição diga que outra unidade Astral também participa.

Exemplo multi-combo na Ordem Áurea: `chefe_guardiao_cinzas` + `gwent_unidade_baluarte` deixam `cinzas_fornalha` e `juramento_erdtree` elegíveis. A ordem do dicionário dispara `cinzas_fornalha` primeiro. Depois `covenant_irmandade_ferro`, com tag isolada `estandarte`, aciona o `juramento_erdtree` pendente e recebe o bônus individual sem contribuir com `ordem_dourada`.

O diagnóstico não era uma simulação completa de deck/partida e não media equilíbrio ou win rate. Naquela data, nenhuma alteração funcional havia sido feita; posteriormente o usuário aprovou a política descrita na seção 21 e ela foi implementada.


## 21. Estado atual pós-política de combos aprovada (2026-11-27)

A política descrita em `card-game-combo-policy-v0.1.md` foi aprovada pelo usuário e implementada em `sistemas/gwent.py`. Ela substitui, para jogadas resolvidas com o runtime atualizado, as condições do baseline documentadas nas seções 19–20.

- Os 27 combos agora declaram `minimum: 2` e `priority` único.
- A carta atual precisa contribuir com uma das tags exigidas pelo combo para poder receber o bônus individual.
- O mínimo conta instâncias distintas de unidade; a mesma instância não pode contar duas vezes.
- A precedência é `priority` crescente (menor valor primeiro), com ID como desempate defensivo; os valores atuais são únicos.
- No máximo um combo ativa por jogada; cada combo continua podendo ser usado uma vez por jogador/rodada via `synergy_used`. Combos pendentes podem ser ativados por participante posterior.
- O `team_bonus` permanece aplicado aos aliados anteriores na mesma fileira da carta participante que ativa o combo.

### Resultado pós-política

A auditoria `card-game-combo-overlap-v0.2.md/.json` percorreu 4.422 pares ordenados e 287.430 trincas ordenadas de IDs distintos entre 67 unidades com tags. Resultado: zero ativações solo; 152/4.422 pares têm sobreposição de elegibilidade, agora resolvida por prioridade; 2.582 trincas ativam múltiplos combos em jogadas sucessivas; todas as 2.582 cartas posteriores observadas contribuem com tag requerida. Esses resultados não são taxas de partida ou provas de equilíbrio.

O relatório agregado atual é `card-game-behavior-validation-v0.3.md/.json`: oito suites, 251/251 asserts, incluindo 32 regressões específicas para a política. As suites são sintéticas e não substituem integração de partidas completas, serialização, API/site/Discord, DB ou R2.

### Arquivos canônicos pós-política

- Regra: `card-game-combo-policy-v0.1.md`.
- Testes específicos: `scripts/assert-combo-policy-v0.1.py` e `card-game-combo-policy-assertions-v0.1.json`.
- Auditoria pós-correção: `scripts/audit-combo-overlap-v0.2.py` e `card-game-combo-overlap-v0.2.md/.json`.
- Mapa AST pós-política: `scripts/build-effect-source-map-v0.2.py` e `card-game-effect-source-map-v0.2.json`.
- Agregado: `scripts/summarize-card-game-behavior-v0.3.py` e `card-game-behavior-validation-v0.3.md/.json`.

A matriz individual das 137 cartas continua sendo snapshot dos atributos/campos do catálogo e não foi regenerada com semântica nova de nomes/lore/poder/custo; use este catálogo de combos atual junto da matriz baseline. Nenhum deck, exemplar, schema, API, frontend, imagem ou DB de produção foi migrado nesta etapa. Partidas já persistidas conservam bônus anteriores; o DB de produção não veio no ZIP.


## 22. Integração stateful de partidas, snapshots e persistência (2026-11-27)

A etapa seguinte à política de combos adicionou `docs/scripts/assert-full-match-stateful-v0.1.py`, com relatório em `docs/card-game-match-snapshot-integration-v0.1.json` e explicação em `.md`. O resultado reproduzido é **12/12 cenários aprovados**, separado dos 251/251 asserts das oito suites comportamentais anteriores; não somar as duas contagens como se fossem uma só bateria homogênea.

### Evidências executadas

- Quatro partidas controladas de três rodadas pelo motor em memória, em pares cruzados das quatro facções (Ordem Áurea, Véu Carmesim, Lua Negra e Os Esquecidos). As partidas percorreram mulligan, turnos, jogadas, passes, resolução de rodadas, coroas, estado final e round-trip JSON.
- Preparação dos **137 modelos** pela função `preparar_carta()`, verificando os campos do payload utilizados pela interface/renderizador; 110 unidades e 27 especiais.
- Ativação de `cinzas_fornalha` por jogadas normais em sequência, com bônus e `synergy_used` preservados no snapshot.
- Uso de Godfrey seguido de especial climático, encerramento de rodada e reset de clima; uso de líder rejeitado na segunda tentativa.
- Uso da Grande Runa de Godrick e da ação manual `weather`, incluindo consumo/limite de uso e persistência.
- Compatibilidade de snapshot legado sem alguns campos e rejeição de ação inválida sem mutar o objeto recebido.
- Execução das constantes `SCHEMA` e `SCHEMA_CARTAS` extraídas por AST de `database.py` em SQLite `:memory:`, com FK ligada e round-trip de `cartas_gwent_matches.state_json`.
- Verificação estática dos contratos `bot.py` ↔ `site/app.js`, além de `compileall`, `py_compile` do harness e `node --check site/app.js`.

### Limites que permanecem

1. As quatro partidas usam fixtures unitárias sintéticas, 12 cartas por jogador, com poder/resultado controlados. Não passam pelo endpoint de montagem/validação de deck e não medem equilíbrio competitivo.
2. `preparar_carta()` foi executada para o catálogo, mas isso não substitui chamada real à API nem validação no browser.
3. O teste SQLite executa o DDL real extraído de `database.py`, mas usa `sqlite3` em memória: não instancia a classe `Database`, `aiosqlite`, transações assíncronas nem DB de produção.
4. O contrato de API foi verificado estaticamente. `bot.py` não pôde ser importado porque `discord.py` não está instalado no ambiente; `database.py` não pôde ser importado porque `aiosqlite` não está instalado. A tentativa de instalar as versões fixadas no `requirements.txt` (`discord.py==2.7.1`, `aiosqlite==0.22.1`) foi bloqueada por falha de DNS/rede do ambiente; não foram usados mocks ou stubs. Não houve `aiohttp.TestClient`, dispatch de handler HTTP, gateway Discord, autenticação ou fluxo de convite real.
5. Convites, criação solo/IA, fallback da IA, recompensas, browser, R2 e artes aprovadas continuam sem validação de integração.

### Estado e sequência autorizada

O código funcional não foi alterado nesta etapa; a única alteração funcional aprovada permanece a política de combos em `sistemas/gwent.py`. Próximo passo recomendado: reproduzir o ambiente com dependências do projeto instaladas e executar testes HTTP reais (catálogo, criação/consulta de partidas, `/action`, autenticação e persistência pela classe `Database`); depois testar convites, solo/IA e recompensas. Só então avançar para browser/arte e decks legais de doze cartas. EFP, custo, raridade e teto de deck continuam propostas não aprovadas.


## 23. Mapa estático das 12 rotas HTTP Gwent e contrato bot/site/motor (2026-11-27)

A seção foi produzida pelo script `docs/scripts/audit-gwent-http-contracts-v0.1.py`; os resultados estão em `docs/card-game-http-contract-map-v0.1.md/.json`. O analisador usa AST em `bot.py` e `sistemas/gwent.py` e busca literais em `site/app.js`. **Não importa nem executa `bot.py`, `aiohttp`, Discord ou `Database`; é evidência estática, não integração HTTP.**

### Rotas encontradas

| Método | Rota | Handler |
|---|---|---|
| GET | `/api/gwent/cards` | `_api_gwent_cards` |
| GET | `/api/gwent/cards/{card_id}/image` | `_api_gwent_card_image` |
| GET | `/api/gwent/deck` | `_api_gwent_deck` |
| POST | `/api/gwent/deck` | `_api_gwent_deck_save` |
| POST | `/api/gwent/deck/reset` | `_api_gwent_deck_reset` |
| GET | `/api/gwent/matches` | `_api_gwent_matches` |
| POST | `/api/gwent/matches` | `_api_gwent_match_create` |
| POST | `/api/gwent/matches/solo` | `_api_gwent_match_create_solo` |
| POST | `/api/gwent/matches/{match_id}/respond` | `_api_gwent_match_respond` |
| GET | `/api/gwent/matches/{match_id}` | `_api_gwent_match_detail` |
| POST | `/api/gwent/matches/{match_id}/action` | `_api_gwent_match_action` |
| GET | `/api/gwent/public-cards/{card_id}/image` | `_api_gwent_public_card_image` |

### Contratos confirmados na fonte

- `POST /api/gwent/deck` recebe `cards: [{card_id, exemplar_id}]`, `faction`, `leader_id`, `relic_id`. Exige exatamente 12 modelos, IDs únicos, pelo menos oito unidades, no máximo quatro especiais, facção predominante/válida, líder da facção e relíquia permitida/possuída, além das verificações de propriedade dos exemplares. **Não há soma de custo nem validação de orçamento.**
- `preparar_carta()` retorna um dicionário explícito sem a chave `custo`. As rotas de cartas e deck atribuem `payload['custo']` antes de chamar a preparação; como a preparação reconstrói o dicionário, esse campo não chega ao payload final.
- O frontend envia ações com `action`, `card_id`, `row`, `card_ids`, `target_id`. A API responde `{ok: true}` e o frontend refaz GET do detalhe para desenhar o estado atualizado.
- Convite PvP cria snapshot de configuração/deck com estado `pending`; o endpoint `/respond` trata aceite/recusa/cancelamento. Aceite revalida relíquia, embaralha snapshots e chama `novo_estado()`.
- Criação solo duplica deck/config do usuário para NARA e desabilita recompensas. O handler de ação chama `aplicar_jogada()` e, quando pertinente, `executar_turno_ia()` no servidor, com fallback de passe em exceção.
- Detalhe de partida pendente retorna apenas ID/status; partida ativa/finalizada retorna o estado público completo. A imagem pública e a imagem privada seguem handlers separados.

### Bloqueio e próxima validação

O ambiente não possui `discord.py==2.7.1` nem `aiosqlite==0.22.1`; instalação temporária por `pip` falhou por DNS/rede. Não houve `aiohttp.TestClient`, execução real de handlers, classe `Database`, gateway Discord, browser, convite/solo/IA ou produção. Próximo passo: executar testes HTTP de cada rota em ambiente com dependências instaladas, incluindo autenticação, origem, ownership, status, rollback, resposta/refetch, convites, solo/IA e recompensas. O contrato de custo deve ser corrigido somente depois que custo/schema/budget forem aprovados.

