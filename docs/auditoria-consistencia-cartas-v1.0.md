# Auditoria de consistência das cartas — v1.0

**Resultado:** APROVADO — 179/179 IDs únicos.

## Verificações globais

- [x] `ids_unicos`
- [x] `custo_por_raridade`
- [x] `habilidade_nao_vazia`
- [x] `lore_separada`
- [x] `habilidade_implementada`
- [x] `lore_cabe_na_carta`
- [x] `lore_cabe_no_template`
- [x] `fileira_valida`

## Escopo e limite da auditoria

- Verifica consistência dos dados publicados com preparar_carta(), fonte de preparação compartilhada pelo motor e pelo site.
- Verifica que cada habilidade declarada está registrada como implementada ou é uma habilidade de identidade exclusiva.
- Verifica custo por raridade, separação entre regra e lore, fileira e encaixe integral da lore no painel físico (o efeito não é impresso na imagem).
- Não substitui testes de integração de todas as combinações possíveis de combate, efeitos cruzados, banco de dados, Discord ou produção.

## Catálogo completo

A regra abaixo é o texto preparado pelo mesmo contrato usado pelo motor e pela API do site. A lore fica em campo separado.

### Acólito Sanguíneo
`gwent_v75_veu_acolito_sangue` · Unidade · Véu Carmesim · Longa distância · Rara · Poder 4 · Custo 2

**Marca da Dinastia** (`sem habilidade`)
Marca o inimigo de maior poder efetivo na fileira. Na segunda marca, consome Sangramento, reduz 2 de bônus (mín. -2) e esta carta recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um acólito do Palácio de Mohgwyn prepara o altar para os ritos secretos da dinastia e reverencia a chama do sangue.

### Adaga da Faca Negra
`gwent_singular_intocavel` · Unidade · Véu Carmesim · Corpo a corpo · Singular · Poder 9 · Custo 0

**Mira Cariana** (`precisao`)
Recebe +1 de bônus ao entrar na fileira de Longa Distância. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Conquistada ao concluir um desafio sem sofrer dano.

### Algemas de Margit
`reliquia_algemas_margit` · Especial · Ordem Áurea · Carta especial · Épica · Poder 0 · Custo 3

**Algemas de Margit** (`reliquia_algemas`)
Na fileira escolhida, zera o bônus positivo do alvo escolhido ou do inimigo com maior bônus. Bônus negativos não mudam; Escudos não bloqueiam o efeito. A ativação consome a Relíquia.

*Lore:* Correntes forjadas para conter o Agouro caído, capazes de subjugar até mesmo um inimigo temível.

### Anjo de Segunda Ordem
`luterano_anjo2` · Unidade · Os Esquecidos · Cerco · Lendária · Poder 5 · Custo 4

**Glória** (`gloria`)
Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma presença alada atravessa os salões esquecidos, iluminando os vitrais partidos.

### Anjo do Último Selo
`gwent_v76_esq_anjo_selo` · Unidade · Os Esquecidos · Longa distância · Mítica · Poder 8 · Custo 5

**Glória** (`gloria`)
Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* O último guardião alado desce diante do portão selado, com as asas abertas sobre os fiéis restantes.

### Anjo Esquecido
`luterano_anjo` · Unidade · Os Esquecidos · Longa distância · Épica · Poder 3 · Custo 3

**Glória** (`gloria`)
Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um mensageiro alado atravessa os vitrais partidos da antiga catedral, levando uma luz que quase se apagou.

### Aprendiz Cariano
`magia_fagulha` · Unidade · Lua Negra · Longa distância · Comum · Poder 5 · Custo 1

**** (`sem habilidade`)


*Lore:* Um aprendiz da tradição cariana começa a dominar os projéteis de pedra cintilante.

### Apóstolo da Pele Divina
`magia_sol_negro` · Unidade · Véu Carmesim · Corpo a corpo · Lendária · Poder 8 · Custo 4

**Eclipse Devorador** (`quebra_ritmo`)
Ganha +2 se algum inimigo tiver bônus acima de zero. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Devoto da antiga ordem da Pele Divina, empunha a chama negra associada à morte dos deuses.

### Apóstolo Errante
`gwent_unidade_invocador` · Unidade · Véu Carmesim · Cerco · Épica · Poder 7 · Custo 3

**Caçador de Feitiços** (`cacador_arcano`)
Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Converte conhecimento arcano em força de combate.

### Apóstolo Esquecido
`luterano_apostolo` · Unidade · Os Esquecidos · Corpo a corpo · Épica · Poder 5 · Custo 3

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Um pregador percorre as estradas douradas com fragmentos de escrituras antigas.

### Arauto da Ruína
`patente_6` · Unidade · Véu Carmesim · Corpo a corpo · Épica · Poder 5 · Custo 3

**Retaliação dos Semideuses** (`retaliacao`)
Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Recompensa de patente concedida ao alcançar o nível 30.

### Arauto do Cântico
`gwent_v76_esq_arauto_cantico` · Unidade · Os Esquecidos · Longa distância · Lendária · Poder 7 · Custo 4

**Estandarte** (`estandarte`)
Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Com um estandarte bordado em prata gasta, o arauto conduz os fiéis através do vale coberto de névoa.

### Arauto do Sangue
`gwent_v76_veu_arauto_sangue` · Unidade · Véu Carmesim · Longa distância · Épica · Poder 6 · Custo 3

**Estandarte** (`estandarte`)
Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um arauto percorre a procissão carmesim carregando o símbolo da chama sanguínea.

### Arauto Áureo
`gwent_v75_ordem_arauto_estandarte` · Unidade · Ordem Áurea · Longa distância · Épica · Poder 5 · Custo 3

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Não possui habilidade individual. Pode completar combos de formação da Ordem Áurea com a unidade compatível.

### Assassina da Faca Negra
`chefe_cacador_sem_rosto` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 6 · Custo 2

**** (`sem habilidade`)


*Lore:* Uma assassina Numen ligada à Noite das Facas Negras, quando um fragmento da Runa da Morte foi usado para matar Godwyn.

### Assassina de Ravenmount
`gwent_unidade_cacadora_fantasma` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Uma assassina de Ravenmount atravessa a névoa sem deixar rastros fáceis de seguir.

### Astróloga de Liurnia
`magia_nevoa_antiga` · Unidade · Lua Negra · Cerco · Épica · Poder 7 · Custo 3

**Névoa Ancestral** (`encadeamento`)
Ganha +2 se houver efeito climático em qualquer fileira. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Sob os céus de Liurnia, uma astróloga procura nas estrelas sinais de destinos ainda ocultos.

### Bastião das Ruínas
`gwent_v77_esq_muralha` · Especial · Os Esquecidos · Carta especial · Comum · Poder 0 · Custo 1

**Bastião das Ruínas** (`gwent_v77_esq_muralha`)
Escolha uma fileira: seus aliados nela recebem +1 de bônus até o fim da rodada.

*Lore:* Os últimos guardiões se alinham sob os arcos quebrados e sustentam a fileira ameaçada.

### Bastião de Leyndell
`gwent_especial_muralha` · Especial · Ordem Áurea · Carta especial · Comum · Poder 0 · Custo 1

**Bastião de Leyndell** (`gwent_muralha`)
Escolha uma fileira: seus aliados nela recebem +1 de bônus até o fim da rodada.

*Lore:* As muralhas douradas de Leyndell erguem-se como símbolo da resistência da capital.

### Batedor de Gelmir
`arma_arco_peregrino` · Unidade · Véu Carmesim · Longa distância · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Um recusante percorre os caminhos do Monte Gelmir, atento às rotas e aos movimentos dos inimigos.

### Besta Prístina
`primordial_origem` · Unidade · Ordem Áurea · Cerco · Primordial · Poder 8 · Custo 6

**Lei Primeva** (`lei_primeva`)
Recebe +2 de bônus ao entrar na primeira rodada. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* A Besta Prístina manifesta a vontade que veio além das estrelas e deu forma à ordem dourada.

### Bibliotecária de Raya
`gwent_unidade_bibliotecaria` · Unidade · Lua Negra · Cerco · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* O conhecimento reunido na guerra vale mais que ouro.

### Bispo Esquecido
`luterano_bispo` · Unidade · Os Esquecidos · Cerco · Lendária · Poder 5 · Custo 4

**Devoção** (`devoto`)
Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um bispo dos Esquecidos conduz os fiéis entre ruínas de antigas catedrais.

### Blaidd, o Meio-Lobo
`gwent_unidade_senhor_cacada` · Unidade · Lua Negra · Corpo a corpo · Épica · Poder 6 · Custo 3

**Vingança** (`vinganca`)
Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* A presa que o derruba desperta a matilha inteira.

### Bruma Sepulcral
`gwent_v77_esq_clima` · Especial · Os Esquecidos · Carta especial · Épica · Poder 0 · Custo 3

**Bruma Sepulcral** (`gwent_v77_esq_clima`)
Escolha uma fileira. Enquanto o clima estiver ativo, todas as unidades dos dois lados nela perdem 1 de poder efetivo (mín. 1); Resistência Climática pode absorver a penalidade.

*Lore:* Uma bruma fria emerge das criptas e cobre a fileira escolhida dos dois exércitos.

### Bênção da Árvore Áurea
`gwent_especial_egide` · Especial · Ordem Áurea · Carta especial · Rara · Poder 0 · Custo 2

**Bênção da Árvore Áurea** (`gwent_egide`)
Escolha um aliado sem Escudo para receber 1 Escudo; a raridade pode proteger até 3 aliados. Escudos não bloqueiam sacrifícios. Raridade Rara: protege até 2 aliados sem Escudo.

*Lore:* Uma prece antiga invoca a proteção dourada que envolve os campeões da capital.

### Cantor do Último Hino
`gwent_v76_esq_cantor_hino` · Unidade · Os Esquecidos · Longa distância · Rara · Poder 4 · Custo 2

**Sobrevivente** (`sobrevivente`)
Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Sua voz ecoa por uma nave vazia enquanto os últimos fiéis abandonam a catedral em ruínas.

### Carrasco Carmesim
`gwent_v75_veu_carrasco_preco` · Unidade · Véu Carmesim · Corpo a corpo · Épica · Poder 5 · Custo 3

**Preço em Sangue** (`sem habilidade`)
Sacrifica o aliado de menor poder efetivo da mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +3). Sem aliado, recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* O carrasco conduz procissões sob estandartes vermelhos, vestindo as vestes cerimoniais dos guerreiros de Mohgwyn.

### Carrasco de Gelmir
`gwent_unidade_carniceiro_forja` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 4 · Custo 2

**Devorar** (`devorar`)
Ao entrar, sacrifica o aliado de menor poder efetivo na mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +4). Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um executor da Mansão Vulcânica veste o aço manchado dos recusantes e serve aos banquetes de Tanith.

### Carrasco do Altar
`gwent_v76_veu_carrasco_altar` · Unidade · Véu Carmesim · Corpo a corpo · Épica · Poder 6 · Custo 3

**Devorar** (`devorar`)
Ao entrar, sacrifica o aliado de menor poder efetivo na mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +4). Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* O carrasco executa os ritos de sacrifício no altar rubro, sob os estandartes da dinastia.

### Cartógrafo de Nokron
`gwent_v75_lua_cartografo_lunar` · Unidade · Lua Negra · Longa distância · Rara · Poder 4 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.

### Cavaleira Cariana
`gwent_unidade_cavaleira` · Unidade · Lua Negra · Corpo a corpo · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Uma duelista cariana, treinada nas tradições de combate da realeza lunar.

### Cavaleiro Astral
`gwent_v76_lua_cavaleiro_astral` · Unidade · Lua Negra · Corpo a corpo · Rara · Poder 5 · Custo 2

**Resistência Climática** (`resistencia_climatica`)
Ignora até 2 pontos de penalidade climática; sem clima ativo ao entrar, recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um cavaleiro cariano avança sob uma chuva de cristais sem desviar os olhos do céu noturno.

### Cavaleiro Consagrado
`gwent_mitica_coroa` · Unidade · Ordem Áurea · Corpo a corpo · Mítica · Poder 8 · Custo 5

**Estandarte** (`estandarte`)
Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um cavaleiro consagrado guarda os ramos pálidos do Haligtree, onde a esperança resiste à decadência.

### Cavaleiro da Árvore Áurea
`chefe_guardiao_cinzas` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 5 · Custo 2

**Égide das Cinzas** (`quebra_ritmo`)
Se já houver um aliado na mesma fileira, ele recebe +1 de bônus e esta carta também recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um sentinela montado patrulha os caminhos que conduzem à Árvore Áurea, impondo a autoridade da capital.

### Cavaleiro de Leyndell
`chefe_vigia_cinzento` · Unidade · Ordem Áurea · Corpo a corpo · Comum · Poder 5 · Custo 1

**** (`sem habilidade`)


*Lore:* Um soldado da capital mantém a vigília entre as muralhas erguidas em nome da Ordem Áurea.

### Cavaleiro de Mohgwyn
`covenant_coroa_abismo` · Unidade · Véu Carmesim · Corpo a corpo · Lendária · Poder 7 · Custo 4

**Selo Enfraquecedor** (`drenagem`)
Reduz em 1 o bônus de cada unidade inimiga, até o mínimo de -2. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um guerreiro jurado à dinastia sanguínea guarda os domínios ocultos de Mohg.

### Cavaleiro de Radahn
`gwent_unidade_sentinela_rubra` · Unidade · Ordem Áurea · Corpo a corpo · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Um cavaleiro da hoste de Radahn mantém sua posição sob o estandarte vermelho de Caelid.

### Cavaleiro do Abismo
`patente_4` · Unidade · Os Esquecidos · Corpo a corpo · Rara · Poder 5 · Custo 2

**** (`sem habilidade`)


*Lore:* Recompensa de patente concedida ao alcançar o nível 15.

### Cavaleiro do Crisol
`gwent_unidade_baluarte` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Um cavaleiro do Crisol, marcado pelas antigas formas que antecederam a Árvore Áurea, guarda a formação com disciplina.

### Cavaleiro do Cão de Caça
`chefe_cervo_sombrio` · Unidade · Véu Carmesim · Corpo a corpo · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Um cavaleiro errante segue a trilha de presas pelas florestas enevoadas das Terras Intermédias.

### Cavaleiro Draconiano
`gwent_unidade_veterano_cercos` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Já viu mais muralhas caírem do que rostos conhecidos.

### Cavaleiro Penitente
`gwent_v76_esq_cavaleiro_penitente` · Unidade · Os Esquecidos · Corpo a corpo · Comum · Poder 4 · Custo 1

**Escudo de Ferro** (`escudo_ferro`)
Entra com 1 Escudo, que bloqueia a primeira tentativa de remoção; sacrifícios ignoram Escudos.

*Lore:* Um cavaleiro cobre o próprio escudo com cinzas e guarda a passagem de uma capela soterrada.

### Cavaleiro Sangrento
`gwent_unidade_devorador_mana` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Um cavaleiro ligado ao sangue de Mohg participa dos rituais sombrios da dinastia subterrânea.

### Cavaleiros de Radahn
`covenant_lobos_cinza` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Veteranos da hoste do Flagelo das Estrelas, marcham sob o estandarte do general de Caelid.

### Cavaleiros Juramentados
`covenant_ultimos` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 6 · Custo 2

**** (`sem habilidade`)


*Lore:* Combatentes unidos por juramentos de sangue permanecem ao lado de seu senhor até o último fôlego.

### Caçador de Almas
`patente_3` · Unidade · Lua Negra · Cerco · Rara · Poder 6 · Custo 2

**** (`sem habilidade`)


*Lore:* Recompensa de patente concedida ao alcançar o nível 10.

### Caçador de Dedos
`gwent_unidade_lamina_sem_juramento` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 6 · Custo 2

**** (`sem habilidade`)


*Lore:* Caçador de Dedos, um duelista errante que prefere trilhas solitárias e confrontos sem testemunhas.

### Caçador de Mohgwyn
`gwent_v75_veu_cacador_sangue` · Unidade · Véu Carmesim · Longa distância · Épica · Poder 5 · Custo 3

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Não possui habilidade individual. Pode completar combos de marca de Sangramento com a unidade compatível.

### Chama do Gigante
`elden_especial_chama` · Especial · Ordem Áurea · Carta especial · Rara · Poder 0 · Custo 2

**Chama do Gigante** (`gwent_chama`)
Remove Geada de todos os aliados afetados; cada unidade purificada recebe +1 de bônus até o fim da rodada. A raridade pode ampliar esses bônus. Raridade Rara: acrescenta +1 de bônus a até 1 aliados purificados.

*Lore:* A chama dos gigantes arde contra o frio que tenta aprisionar os vivos.

### Chama Frenética
`elden_especial_loucura` · Especial · Lua Negra · Carta especial · Épica · Poder 0 · Custo 3

**Loucura Frenética** (`gwent_loucura`)
Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda zera bônus positivos. Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.

*Lore:* A chama frenética consome razão e identidade, deixando apenas o caos da Chama Frenética.

### Chama Negra
`gwent_especial_queima` · Especial · Lua Negra · Carta especial · Épica · Poder 0 · Custo 3

**Chama Negra** (`gwent_queima`)
Em cada lado, tenta remover a unidade de maior poder efetivo. Escudo bloqueia a remoção; se ela ocorrer, gatilhos de queda são resolvidos. Raridade Épica: reforça bônus gerados por efeitos de queda em até 1 alvo; não amplia remoções nem atravessa Escudos.

*Lore:* A chama negra, temida até pelos deuses, consome tudo o que toca.

### Chamado dos Mortos
`gwent_especial_requiem` · Especial · Os Esquecidos · Carta especial · Épica · Poder 0 · Custo 3

**Chamado dos Mortos** (`gwent_requiem`)
Traz do descarte diretamente ao campo uma unidade escolhida com poder-base até 6; a raridade pode elevar esse limite até 9. Raridade Épica: o limite de poder-base sobe até 7.

*Lore:* Um cântico atravessa as catacumbas e ecoa entre os nomes que a história tentou apagar.

### Cinzas Novatas
`patente_1` · Unidade · Ordem Áurea · Longa distância · Comum · Poder 3 · Custo 1

**Caçador de Feitiços** (`cacador_arcano`)
Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo.

*Lore:* Recompensa de patente concedida ao alcançar o nível 1.

### Confessor Velado
`gwent_v76_esq_confessor_velado` · Unidade · Os Esquecidos · Longa distância · Rara · Poder 5 · Custo 2

**Devoção** (`devoto`)
Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Sob um capuz de linho, o confessor ouve os últimos arrependimentos dos viajantes que chegam à cripta.

### Confessora da Graça
`gwent_v75_ordem_confessora_graca` · Unidade · Ordem Áurea · Cerco · Épica · Poder 5 · Custo 3

**Regressão Serena** (`sem habilidade`)
Purifica até 2 aliados da fileira de Sangramento, Geada, Podridão ou Loucura; cada um recebe +1. Se ninguém precisar, o aliado mais fraco recebe +1; sem aliados, esta carta recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma Confessora percorre os caminhos de Leyndell em silêncio, levando os ensinamentos da Lei da Regressão aos santuários esquecidos.

### Confessora da Ordem Áurea
`magia_selo_vigilia` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 5 · Custo 2

**Selo de Vigília** (`adaptacao`)
Esta carta recebe Resistência Climática 1. Se houver aliado na mesma fileira, o primeiro recebe +1 de bônus. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Treinada para agir discretamente, a Confessora combina devoção, infiltração e combate próximo.

### Coroa do Lorde Prístino
`gwent_singular_cacador_chefes` · Unidade · Lua Negra · Corpo a corpo · Singular · Poder 9 · Custo 0

**Paradoxo Eterno** (`paradoxo_eterno`)
Na terceira rodada, recebe +2 de bônus se o adversário venceu a rodada anterior. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Conquistada ao derrotar todos os chefes de um desafio.

### Cruzado Esquecido
`luterano_cruzado` · Unidade · Os Esquecidos · Corpo a corpo · Épica · Poder 6 · Custo 3

**Sinergia de Facção** (`sinergia_faccao`)
Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um guerreiro sagrado guarda as estradas em ruínas e carrega no escudo o símbolo de uma ordem que já não existe.

### Cântico dos Fiéis
`gwent_v77_esq_chifre` · Especial · Os Esquecidos · Carta especial · Rara · Poder 0 · Custo 2

**Cântico dos Fiéis** (`gwent_v77_esq_chifre`)
Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada. Raridade Rara: acrescenta +1 de bônus a até 1 aliados afetados.

*Lore:* Vozes esquecidas unem os sobreviventes e renovam sua força diante do altar vazio.

### Cântico Dourado
`gwent_v77_ord_hino` · Especial · Ordem Áurea · Carta especial · Rara · Poder 0 · Custo 2

**Cântico Dourado** (`gwent_v77_ord_hino`)
Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada. Raridade Rara: acrescenta +1 de bônus a até 1 aliados afetados.

*Lore:* O coro dos sacerdotes ecoa pelas muralhas e reforça a formação dos guardiões.

### Cão Rubro
`gwent_v76_veu_cao_rubro` · Unidade · Véu Carmesim · Corpo a corpo · Comum · Poder 4 · Custo 1

**Instinto de Caçador** (`instinto`)
Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária.

*Lore:* Um cão de guerra fareja intrusos entre as muralhas úmidas do palácio de Mohgwyn.

### Céu sem Cinzas
`gwent_v77_esq_purificar` · Especial · Os Esquecidos · Carta especial · Rara · Poder 0 · Custo 2

**Céu sem Cinzas** (`gwent_v77_esq_purificar`)
Remove o clima ativo das três fileiras para os dois jogadores.

*Lore:* O último hino atravessa o campo e dissipa todo clima que ainda cobre as fileiras.

### Delírio Carmesim
`gwent_v77_veu_loucura` · Especial · Véu Carmesim · Carta especial · Épica · Poder 0 · Custo 3

**Delírio Carmesim** (`gwent_v77_veu_loucura`)
Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda zera bônus positivos. Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.

*Lore:* O cântico frenético dos devotos rompe a disciplina dos inimigos escolhidos.

### Devota da Hemorragia
`gwent_v75_veu_devota_hemorragia` · Unidade · Véu Carmesim · Cerco · Rara · Poder 4 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Não possui habilidade individual. Pode completar o combo Banquete da Hemorragia com a unidade compatível.

### Diaconisa do Altar
`gwent_v76_esq_diaconisa_altar` · Unidade · Os Esquecidos · Cerco · Rara · Poder 5 · Custo 2

**Ritmo de Combate** (`escolha_ritmo`)
Ao entrar em campo, recebe +1 de bônus. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* A diaconisa prepara o altar com cálices antigos e conduz um rito antes da chegada dos invasores.

### Discípulo da Academia
`gwent_unidade_circulo` · Unidade · Lua Negra · Cerco · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Discípulo de Raya Lucaria, dedica-se ao estudo dos círculos arcanos e dos resíduos de feitiçaria.

### Discípulos do Fogo
`covenant_filhos_brasa` · Unidade · Ordem Áurea · Corpo a corpo · Comum · Poder 5 · Custo 1

**** (`sem habilidade`)


*Lore:* Seguidores dos antigos monges preservam a chama dos gigantes e seus rituais esquecidos.

### Diácono Esquecido
`luterano_diacon` · Unidade · Os Esquecidos · Longa distância · Comum · Poder 3 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Auxiliar dos rituais, mantém acesas as lâmpadas dos altares esquecidos.

### Dragoeiro Ancião
`magia_trovao_oco` · Unidade · Ordem Áurea · Longa distância · Épica · Poder 6 · Custo 3

**Descarga Oca** (`drenagem`)
Cada inimigo na mesma fileira perde 1 de bônus (mín. -2). Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um guerreiro ligado aos antigos dragões canaliza relâmpagos ancestrais em meio à batalha.

### Duelista da Casa Hoslow
`arma_lamina_peregrino` · Unidade · Véu Carmesim · Corpo a corpo · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Herdeiro de uma casa de duelistas, transforma a elegância do aço em uma promessa de sangue.

### Erudito da Academia
`magia_orbe_eco` · Unidade · Lua Negra · Longa distância · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Pesquisador de Raya Lucaria, dedica a vida ao estudo dos segredos das pedras cintilantes.

### Erudito das Pedras
`gwent_unidade_eco` · Unidade · Lua Negra · Cerco · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Um estudioso das pedras cintilantes investiga as ressonâncias deixadas por feitiçarias antigas.

### Espada da Noite e da Chama
`reliquia_noite_chama` · Especial · Lua Negra · Carta especial · Lendária · Poder 0 · Custo 4

**Espada da Noite e da Chama** (`reliquia_noite_chama`)
Noite: aplica 1 marca de Geada (máx. 2) a todos os inimigos da fileira escolhida. Chama: atinge o inimigo de maior poder efetivo na fileira, reduzindo 1 de poder-base (mín. 1) e 2 de bônus. Escudo bloqueia o golpe; a Relíquia é consumida.

*Lore:* Arma lendária da Mansão Cariana. Sua postura especial libera um ataque mágico ou uma onda de fogo.

### Espadachim da Lua Negra
`arma_duas_luas` · Unidade · Lua Negra · Corpo a corpo · Épica · Poder 7 · Custo 3

**Dança Espelhada** (`precisao`)
Ganha +1 se você tiver outro aliado em uma fileira diferente. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um duelista das tradições carianas conduz a lâmina sob a luz fria da Lua Negra.

### Executor Sombrio
`patente_7` · Unidade · Lua Negra · Corpo a corpo · Épica · Poder 7 · Custo 3

**Caçador de Feitiços** (`cacador_arcano`)
Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Recompensa de patente concedida ao alcançar o nível 40.

### Exploradora de Nokron
`gwent_unidade_cartografa` · Unidade · Lua Negra · Longa distância · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Encontra rotas onde os outros veem obstáculos.

### Feiticeira da Lua Gélida
`magia_chama_fria` · Unidade · Lua Negra · Longa distância · Comum · Poder 4 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Uma feiticeira errante combina o frio das antigas artes lunares com chamas de origem desconhecida.

### Feiticeiro Cariano
`arma_cajado_marulho` · Unidade · Lua Negra · Longa distância · Rara · Poder 6 · Custo 2

**** (`sem habilidade`)


*Lore:* Discípulo da realeza cariana, conjura feitiçarias de pedra cintilante sob a proteção da lua.

### Ferreiro de Gelmir
`gwent_unidade_mestre_forja` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Um mestre ferreiro de Volcano Manor trabalha entre brasas, aço e os juramentos dos recusantes.

### Ferreiro Vulcânico
`arma_martelo_fornalha` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 6 · Custo 2

**** (`sem habilidade`)


*Lore:* Entre fornalhas e juramentos de traição, um artesão molda armas para os recusantes do Monte Gelmir.

### Fia, Leito de Morte
`gwent_unidade_cantora_lamentos` · Unidade · Véu Carmesim · Longa distância · Rara · Poder 5 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Fia, Companheira do Leito de Morte, entoa lamentos pelos que encontraram repouso entre os mortos.

### Flagelante de Mohgwyn
`gwent_v76_veu_flagelante` · Unidade · Véu Carmesim · Corpo a corpo · Rara · Poder 4 · Custo 2

**Legado** (`legado`)
Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um penitente percorre os degraus do palácio sanguíneo, deixando marcas vermelhas na pedra.

### Flor da Podridão Escarlate
`elden_especial_podrida` · Especial · Lua Negra · Carta especial · Épica · Poder 0 · Custo 3

**Podridão Escarlate** (`gwent_podrida`)
Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda reduz 1 de bônus positivo (mín. 0). Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.

*Lore:* A flor escarlate floresce onde a podridão encontra carne, pedra e memória.

### Geada dos Picos
`gwent_especial_geada` · Especial · Lua Negra · Carta especial · Rara · Poder 0 · Custo 2

**Lua Gélida** (`gwent_geada`)
Todas as unidades inimigas recebem 1 marca de Geada; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada.

*Lore:* O frio dos Picos dos Gigantes avança sobre o campo e silencia o vigor dos combatentes.

### Gigante de Fogo
`gwent_unidade_gigante` · Unidade · Ordem Áurea · Corpo a corpo · Épica · Poder 7 · Custo 3

**Instinto de Caçador** (`instinto`)
Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma presença colossal na linha de frente.

### Godfrey, Primeiro Lorde
`chefe_rei_afogado` · Unidade · Ordem Áurea · Corpo a corpo · Épica · Poder 7 · Custo 3

**Dízimo do Abismo** (`primeira_luz`)
Recebe +2 se houver qualquer carta no seu descarte; caso contrário, recebe +1 se o adversário tiver mais unidades em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Primeiro Lorde Prístino e consorte de Marika, Godfrey liderou os guerreiros que conquistaram as Terras Intermédias.

### Godwyn, o Dourado
`gwent_unidade_herdeiro_portao` · Unidade · Ordem Áurea · Corpo a corpo · Épica · Poder 6 · Custo 3

**Vingança** (`vinganca`)
Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* O príncipe dourado foi amado por dragões e homens; sua queda marcou a primeira rachadura irreversível no destino das Terras Intermédias.

### Grande Runa de Godrick
`reliquia_grande_runa_godrick` · Especial · Ordem Áurea · Carta especial · Lendária · Poder 0 · Custo 4

**Grande Runa de Godrick** (`reliquia_godrick`)
Exige ao menos 1 unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas; uso único por partida.

*Lore:* Fragmento do Anel Prístino reivindicado por Godrick, o Enxertado, que buscava poder por meio do enxerto.

### Graviturgista de Nokron
`gwent_v75_lua_graviturgista` · Unidade · Lua Negra · Cerco · Épica · Poder 5 · Custo 3

**Cisalhamento Gravitacional** (`sem habilidade`)
Até 2 inimigos com bônus positivo na fileira perdem 1 (mín. -2). Se atingir 2 alvos, esta carta recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um astrólogo das Cidades Eternas estuda as correntes gravitacionais que sustentam as ruínas suspensas de Nokron.

### Guardas da Árvore Áurea
`covenant_irmandade_ferro` · Unidade · Ordem Áurea · Corpo a corpo · Comum · Poder 4 · Custo 1

**Retaliação dos Semideuses** (`retaliacao`)
Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária.

*Lore:* Defensores juramentados protegem os caminhos e santuários consagrados à Árvore Áurea.

### Guardiã do Juramento Lunar
`gwent_v75_lua_guardia` · Unidade · Lua Negra · Corpo a corpo · Épica · Poder 5 · Custo 3

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.

### Guardiã do Santuário
`gwent_v76_esq_guardia_santuario` · Unidade · Os Esquecidos · Corpo a corpo · Rara · Poder 5 · Custo 2

**Guardião da Fileira** (`guardiao_fileira`)
Ao entrar, recebe +1 de bônus por aliado na mesma fileira (máx. +3). Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma defensora vigia o altar de pedra e mantém a entrada do santuário livre de profanadores.

### Guardião da Ordem Áurea
`gwent_unidade_guardiao_runas` · Unidade · Ordem Áurea · Corpo a corpo · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Um guardião da Ordem Áurea carrega inscrições rúnicas ligadas aos ensinamentos da capital.

### Guardião das Cinzas
`patente_5` · Unidade · Ordem Áurea · Longa distância · Rara · Poder 6 · Custo 2

**Postura Encadeada** (`encadeamento`)
Recebe +2 de bônus se entrar na mesma fileira da sua última unidade jogada. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Recompensa de patente concedida ao alcançar o nível 20.

### Guardião do Crisol Menor
`gwent_v75_ordem_guardiao_crisol` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 4 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Não possui habilidade individual. Pode completar combos da Ordem Áurea quando estiver em campo com a unidade compatível.

### Guardião do Graal
`gwent_v76_ordem_guardiao_graal` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 4 · Custo 2

**Guardião da Fileira** (`guardiao_fileira`)
Ao entrar, recebe +1 de bônus por aliado na mesma fileira (máx. +3). Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um protetor vigia o cálice consagrado nos salões inferiores de Leyndell.

### Guardião do Relicário
`gwent_v76_esq_guardiao_relicario` · Unidade · Os Esquecidos · Corpo a corpo · Lendária · Poder 7 · Custo 4

**Ressurgir** (`ressurgir`)
Ao entrar, traz do seu descarte ao campo a unidade elegível de maior poder-base até 5; ela retorna sem bônus nem Escudo. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um guardião protege as relíquias da ordem numa câmara selada sob a antiga catedral.

### Guardião dos Vitrais
`gwent_v76_esq_guardiao_vitrais` · Unidade · Os Esquecidos · Cerco · Comum · Poder 4 · Custo 1

**Estandarte** (`estandarte`)
Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira.

*Lore:* Um sentinela permanece diante dos vitrais partidos, protegendo os símbolos de uma fé quase apagada.

### Guardiões de Sellia
`covenant_sentinelas` · Unidade · Lua Negra · Corpo a corpo · Comum · Poder 5 · Custo 1

**** (`sem habilidade`)


*Lore:* Vigias da cidade oculta de Sellia protegem seus segredos e as passagens de feitiçaria.

### Guerreiro Caído
`patente_2` · Unidade · Véu Carmesim · Cerco · Comum · Poder 3 · Custo 1

**** (`sem habilidade`)


*Lore:* Recompensa de patente concedida ao alcançar o nível 5.

### Guerreiro Frenético
`gwent_unidade_detonador` · Unidade · Véu Carmesim · Corpo a corpo · Épica · Poder 6 · Custo 3

**Vingança** (`vinganca`)
Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Sua queda libera a energia que ele guardava.

### Gurranq, Clérigo Bestial
`chefe_oraculo_ruina` · Unidade · Ordem Áurea · Corpo a corpo · Lendária · Poder 7 · Custo 4

**Presságio da Ruína** (`impeto`)
A unidade inimiga de maior poder efetivo perde 1 de bônus (mín. -2). Se sua pontuação estiver menor ao entrar, esta carta recebe +1. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* O clérigo bestial consome Raiz da Morte e guarda um segredo ligado à própria Runa da Morte.

### Gêmeas da Cidade Eterna
`gwent_unidade_dupla_veu` · Unidade · Lua Negra · Corpo a corpo · Rara · Poder 6 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Duas irmãs das Cidades Eternas percorrem caminhos subterrâneos que raramente aparecem nos mapas.

### Irmã das Ruínas
`gwent_v76_esq_irma_ruinas` · Unidade · Os Esquecidos · Longa distância · Comum · Poder 3 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Uma irmã recolhe velas e fragmentos de escritura nas galerias abandonadas do antigo mosteiro.

### Irmão Esquecido
`luterano_irmao` · Unidade · Os Esquecidos · Corpo a corpo · Comum · Poder 4 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Um peregrino humilde permanece ao lado de sua irmandade, mesmo quando todos os demais recuam.

### Juramentada de Ranni
`covenant_lua_velada` · Unidade · Lua Negra · Longa distância · Épica · Poder 6 · Custo 3

**Aliança Lunar** (`primeira_luz`)
Esta carta recebe +1. O aliado de menor poder efetivo em outra fileira também recebe +1 de bônus, se existir. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma aliada juramentada à princesa lunar acompanha sua busca por um caminho além da Ordem Áurea.

### Juramento do Crisol
`gwent_especial_vinculo` · Especial · Ordem Áurea · Carta especial · Rara · Poder 0 · Custo 2

**Juramento do Crisol** (`gwent_vinculo`)
Escolha uma fileira com ao menos 2 aliados. Todas as unidades aliadas nela recebem +2 de bônus até o fim da rodada. Raridade Rara: acrescenta +1 de bônus a até 1 aliados afetados.

*Lore:* Um juramento ancestral une os guerreiros às formas primordiais que precederam a Erdtree.

### Juramento dos Fiéis
`gwent_v77_esq_vinculo` · Especial · Os Esquecidos · Carta especial · Épica · Poder 0 · Custo 3

**Juramento dos Fiéis** (`gwent_v77_esq_vinculo`)
Escolha uma fileira com ao menos 2 aliados. Todas as unidades aliadas nela recebem +2 de bônus até o fim da rodada. Raridade Épica: acrescenta +1 de bônus a até 1 aliados afetados.

*Lore:* Duas ou mais vozes repetem o juramento antigo e fortalecem a fileira reunida.

### Juramento Primordial
`gwent_singular_primeiro` · Unidade · Véu Carmesim · Corpo a corpo · Singular · Poder 10 · Custo 0

**Caçador Solitário** (`cacador_solitario`)
Recebe +2 de bônus ao entrar se não houver outro aliado na mesma fileira. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Exemplar singular conquistado por um feito extraordinário.

### Ladina da Cidade Eterna
`gwent_unidade_saqueadora_veu` · Unidade · Lua Negra · Longa distância · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Nenhuma rota é cara demais para quem leva o butim.

### Lanceiro da Árvore Áurea
`arma_lanca_fornalha` · Unidade · Ordem Áurea · Corpo a corpo · Comum · Poder 5 · Custo 1

**** (`sem habilidade`)


*Lore:* Treinado para defender os domínios da Árvore Áurea, avança com lança e disciplina militar.

### Lei da Regressão
`gwent_especial_purificar` · Especial · Lua Negra · Carta especial · Rara · Poder 0 · Custo 2

**Lei da Regressão** (`gwent_purificar`)
Remove o clima ativo das três fileiras para os dois jogadores.

*Lore:* A Lei da Regressão revela a verdade por trás das ilusões e desfaz os véus que encobrem o mundo.

### Leitora de Sellia
`arma_agulha_astro` · Unidade · Lua Negra · Longa distância · Comum · Poder 4 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 3 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Uma estudiosa de Sellia observa os astros e procura caminhos ocultos na feitiçaria noturna.

### Lenda do Coliseu
`patente_9` · Unidade · Ordem Áurea · Cerco · Lendária · Poder 8 · Custo 4

**Ímpeto do Lorde** (`impeto`)
Recebe +1 de bônus ao entrar se sua pontuação estiver acima da adversária. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Recompensa de patente concedida ao alcançar o nível 75.

### Lobos Solitários
`elden_especial_invocacao` · Especial · Lua Negra · Carta especial · Rara · Poder 0 · Custo 2

**Lobos Solitários** (`gwent_invocacao`)
Escolha uma fileira e invoque Lobos Espirituais nela com 3 de poder; a raridade pode elevar o poder da invocação até 6. Raridade Rara: invoca Lobos Espirituais com 4 de poder.

*Lore:* Cinzas antigas despertam os espíritos de lobos que outrora caçaram ao lado de seus mestres.

### Lua Cheia de Rennala
`elden_especial_geada` · Especial · Lua Negra · Carta especial · Rara · Poder 0 · Custo 2

**Geada Cariana** (`gwent_geada_cariana`)
Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Geada; cada marca reduz 1 de poder efetivo até o fim da rodada. A raridade pode aplicar a segunda marca imediatamente a até 3 alvos. Raridade Rara: aplica a segunda marca imediatamente a até 1 alvos sem Geada prévia.

*Lore:* A lua cheia de Rennala ilumina o campo com a frieza ancestral da realeza cariana.

### Luz na Geada
`gwent_v77_esq_chama` · Especial · Os Esquecidos · Carta especial · Rara · Poder 0 · Custo 2

**Luz na Geada** (`gwent_v77_esq_chama`)
Remove Geada dos aliados afetados; cada unidade purificada recebe +1 de bônus até o fim da rodada. A raridade pode ampliar esses bônus. Raridade Rara: acrescenta +1 de bônus a até 1 aliados purificados.

*Lore:* Uma chama pálida aquece os sobreviventes e desfaz o gelo que os prende.

### Lágrima Sagrada
`gwent_especial_medico` · Especial · Véu Carmesim · Carta especial · Rara · Poder 0 · Custo 2

**Lágrima Sagrada** (`gwent_medico`)
Devolve à sua mão uma unidade escolhida do seu descarte com poder-base até 4; a raridade pode elevar esse limite até 7. Raridade Rara: o limite de poder-base sobe até 5.

*Lore:* Uma lágrima consagrada guarda a memória dos que tombaram e ainda podem retornar à jornada.

### Lâmina da Morte Destinada
`gwent_especial_execucao` · Especial · Ordem Áurea · Carta especial · Épica · Poder 0 · Custo 3

**Lâmina da Morte Destinada** (`gwent_execucao`)
Escolha uma fileira e um inimigo nela com poder efetivo até 6. Tenta removê-lo; Escudo pode bloquear. Se a remoção ocorrer, gatilhos de queda são resolvidos. A raridade eleva o limite até 9. Raridade Épica: alcança poder efetivo até 7; pode reforçar bônus gerados por efeitos de queda em até 1 alvo.

*Lore:* A lâmina da Morte Destinada carrega o fragmento de um poder que deveria permanecer selado.

### Lâmina Hemática
`gwent_v76_veu_lamina_hemantica` · Unidade · Véu Carmesim · Longa distância · Rara · Poder 5 · Custo 2

**Contragolpe** (`contragolpe`)
Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma duelista da dinastia sanguínea desembainha uma lâmina estreita diante do altar de Mohgwyn.

### Lâmina Negra
`reliquia_lamina_negra` · Especial · Véu Carmesim · Carta especial · Mítica · Poder 0 · Custo 5

**Lâmina Negra** (`reliquia_lamina_negra`)
Na fileira escolhida, reduz em 3 o bônus do alvo escolhido ou, sem alvo, do inimigo de maior poder efetivo. Escudo é consumido e bloqueia o efeito sem consumir a Relíquia.

*Lore:* A arma de Maliketh, que guarda a Morte Destinada selada em sua lâmina. Não é uma das adagas usadas pelas Assassinas da Faca Negra.

### Lâmina Negra Errante
`chefe_aparicao_veio` · Unidade · Véu Carmesim · Corpo a corpo · Comum · Poder 4 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Uma figura encapuzada atravessa as sombras, deixando apenas o rumor de uma lâmina silenciosa.

### Malenia, Lâmina de Miquella
`chefe_malenia_lamina_miquella` · Unidade · Véu Carmesim · Corpo a corpo · Primordial · Poder 9 · Custo 6

**Flor Escarlate** (`scarlet_bloom`)
Cada inimigo da fileira recebe 1 marca de Podridão (máx. 2); cada marca reduz 1 de poder efetivo. Ao atingir 2, bônus positivo perde 1 (mín. 0). Primordial: até 3 alvos nessa transição perdem mais 1 (mín. -2). Não reduz de novo com 2 marcas.

*Lore:* Malenia é uma Empírea e semideusa, filha de Marika e Radagon e irmã gêmea de Miquella. Nasceu afligida pela Podridão Escarlate e foi treinada por um espadachim cego, tornando-se uma espadachim incomparável. Como Lâmina de Miquella, protegeu o irmão e aguarda seu retorno em Elphael, sob a Árvore Sacra. Empunha a Mão de Malenia, uma katana, e combate com próteses douradas. Na batalha contra Radahn em Caelid, liberou uma florescência da Podridão Escarlate que devastou a região. Esta ficha representa Malenia antes de sua transformação na Deusa da Podridão.

### Maliketh, Guardião da Morte
`primordial_eternidade` · Unidade · Ordem Áurea · Corpo a corpo · Primordial · Poder 8 · Custo 6

**Paradoxo Eterno** (`paradoxo_eterno`)
Na terceira rodada, recebe +2 de bônus se o adversário venceu a rodada anterior. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Maliketh guarda a Morte Destinada, o poder cuja ausência sustenta a ordem sem morte de Marika.

### Maliketh, Lâmina Negra
`chefe_maliketh_morte_destinada` · Unidade · Ordem Áurea · Corpo a corpo · Lendária · Poder 8 · Custo 4

**Morte Destinada** (`cacador_arcano`)
Ao entrar, o inimigo de maior poder efetivo perde 2 de bônus (mín. -2). Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Sombra leal de Marika e guardião da Runa da Morte, carrega a Morte Destinada selada em sua lâmina.

### Marika, Rainha Eterna
`primordial_trono` · Unidade · Ordem Áurea · Corpo a corpo · Primordial · Poder 8 · Custo 6

**Decreto Soberano** (`decreto_soberano`)
Ao entrar, reduz em 2 o bônus de todas as unidades inimigas (mín. -2). Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Marika, a Rainha Eterna, ergueu a ordem dourada e rompeu o Anel Prístino, mudando para sempre as Terras Intermédias.

### Mercador Nômade
`gwent_unidade_intendente` · Unidade · Ordem Áurea · Longa distância · Comum · Poder 4 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Um mercador nômade percorre as Terras Intermédias levando provisões e notícias entre assentamentos.

### Messmer, o Empalador
`chefe_messmer_impalador` · Unidade · Ordem Áurea · Corpo a corpo · Lendária · Poder 8 · Custo 4

**Lança do Impalador** (`quebra_ritmo`)
Ao entrar, cada inimigo da fileira recebe 1 marca de Sangramento. A segunda marca consome as marcas e causa -2 de bônus (mín. -2); estados expiram no fim da rodada. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Filho de Marika e senhor da chama impura, comandou a purga que devastou o Reino das Sombras.

### Miasma da Podridão
`gwent_especial_nevoa` · Especial · Lua Negra · Carta especial · Rara · Poder 0 · Custo 2

**Névoa de Sellia** (`gwent_nevoa`)
Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Podridão Escarlate; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada.

*Lore:* Uma nuvem pútrida se espalha pelo campo, lembrando os pântanos corrompidos de Caelid.

### Misericórdia Final
`gwent_v77_esq_medico` · Especial · Os Esquecidos · Carta especial · Rara · Poder 0 · Custo 2

**Misericórdia Final** (`gwent_v77_esq_medico`)
Devolve à sua mão uma unidade escolhida do seu descarte com poder-base até 4; a raridade pode elevar esse limite até 7. Raridade Rara: o limite de poder-base sobe até 5.

*Lore:* Uma irmã recolhe um combatente do silêncio do descarte e o devolve à mão dos fiéis.

### Missionário Esquecido
`luterano_missionario` · Unidade · Os Esquecidos · Longa distância · Rara · Poder 5 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Um viajante percorre capelas abandonadas levando escrituras preservadas por gerações.

### Monge do Fogo
`magia_brasa_errante` · Unidade · Lua Negra · Corpo a corpo · Comum · Poder 4 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Devoto do fogo dos gigantes, preserva ritos antigos nas encostas geladas dos Picos dos Gigantes.

### Mártir Cinzento
`gwent_v76_esq_martir_cinzento` · Unidade · Os Esquecidos · Corpo a corpo · Épica · Poder 6 · Custo 3

**Vingança** (`vinganca`)
Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Ferido diante do relicário, o mártir permanece de pé para impedir que a chama sagrada se apague.

### Mãe Sem Forma
`primordial_abismo` · Unidade · Véu Carmesim · Cerco · Primordial · Poder 8 · Custo 6

**Fome do Abismo** (`fome_abismo`)
Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* A Mãe Sem Forma é venerada pelos seguidores de Mohg como origem do poder sanguíneo.

### Místico Esquecido
`luterano_mistico` · Unidade · Os Esquecidos · Cerco · Rara · Poder 5 · Custo 2

**Devoção** (`devoto`)
Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um intérprete de sinais antigos contempla as estrelas sobre as ruínas de Sellia.

### Névoa Rubra
`gwent_v77_veu_podrida` · Especial · Véu Carmesim · Carta especial · Rara · Poder 0 · Custo 2

**Névoa Rubra** (`gwent_v77_veu_podrida`)
Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda reduz 1 de bônus positivo (mín. 0). Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Rara: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.

*Lore:* Uma névoa escarlate invade a fileira adversária e deixa marcas de corrupção nos combatentes.

### Oráculo Gélido de Sellia
`gwent_v75_lua_oraculo_geada` · Unidade · Lua Negra · Cerco · Rara · Poder 4 · Custo 2

**Presságio da Geada** (`sem habilidade`)
O inimigo de maior poder efetivo na fileira recebe 1 marca de Geada (máx. 2). Se já tinha marca, esta carta recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma astróloga de Sellia lê presságios nas lâminas de gelo que se formam sobre as águas imóveis da cidade.

### Oráculo Silencioso
`gwent_v76_esq_oraculo_silencioso` · Unidade · Os Esquecidos · Cerco · Épica · Poder 6 · Custo 3

**Eco Arcano** (`eco_arcano`)
Recebe +2 de bônus ao entrar se houver ao menos uma carta especial no seu descarte. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Entre colunas rachadas, um oráculo interpreta inscrições que sobreviveram à queda do santuário.

### Papa Esquecido
`luterano_papa` · Unidade · Os Esquecidos · Cerco · Mítica · Poder 7 · Custo 5

**Sinergia de Facção** (`sinergia_faccao`)
Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Sumo sacerdote dos Esquecidos, governa uma ordem que sobreviveu à queda de seus templos.

### Passo do Cão de Caça
`gwent_especial_batedor` · Especial · Véu Carmesim · Carta especial · Rara · Poder 0 · Custo 2

**Passo do Cão de Caça** (`gwent_batedor`)
Compra 1 carta da reserva; a raridade pode elevar a compra para 2, se houver cartas disponíveis. Raridade Rara: compra até 2 cartas da reserva.

*Lore:* O passo do cão de caça atravessa o campo antes que o inimigo perceba sua aproximação.

### Passo do Lobo
`gwent_especial_passo` · Especial · Véu Carmesim · Carta especial · Rara · Poder 0 · Custo 2

**Passo do Lobo** (`gwent_passo`)
Escolha uma fileira e mova para ela uma unidade aliada que esteja em outra fileira. Raridade Rara: move até 2 aliados.

*Lore:* O antigo instinto de caça guia seus guerreiros por caminhos que parecem impossíveis.

### Pastor Esquecido
`luterano_pastor` · Unidade · Os Esquecidos · Longa distância · Rara · Poder 4 · Custo 2

**Legado** (`legado`)
Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um guia errante conduz os fiéis por trilhas esquecidas e capelas abandonadas.

### Peregrino das Cinzas
`gwent_v76_esq_peregrino_cinza` · Unidade · Os Esquecidos · Longa distância · Comum · Poder 3 · Custo 1

**Legado** (`legado`)
Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior.

*Lore:* Um viajante cruza estradas cobertas de cinza levando consigo as últimas páginas de um evangelho perdido.

### Peregrinos de Nokron
`covenant_peregrinos_nevoa` · Unidade · Lua Negra · Longa distância · Comum · Poder 5 · Custo 1

**** (`sem habilidade`)


*Lore:* Viajantes das cidades subterrâneas cruzam a escuridão em busca de uma nova estrela.

### Placidusax, Lorde Dragão
`chefe_placidusax_lorde_dragao` · Unidade · Lua Negra · Cerco · Primordial · Poder 9 · Custo 6

**Tempestade do Tempo** (`olho_tempestade`)
Ao entrar, cada inimigo da fileira recebe 1 marca de Geada (máx. 2); esta carta recebe +1 por inimigo atingido, até +3. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Lorde Dragão ancestral que aguarda, em Farum Azula, o retorno de seu deus desaparecido.

### Placidusax, Senhor Dragão
`primordial_tempestade` · Unidade · Lua Negra · Cerco · Primordial · Poder 8 · Custo 6

**Olho da Tempestade** (`olho_tempestade`)
Recebe +2 de bônus ao entrar se sua fileira estiver sob clima ativo. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Placidusax, antigo lorde dos dragões, permanece suspenso no tempo em Farum Azula.

### Porta-estandarte Áureo
`gwent_unidade_portaestandarte` · Unidade · Ordem Áurea · Corpo a corpo · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 3 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* O estandarte de Leyndell reúne soldados dispersos sob o símbolo dourado da capital.

### Prelado das Ruínas
`gwent_v76_esq_prelado_ruinas` · Unidade · Os Esquecidos · Cerco · Épica · Poder 6 · Custo 3

**Sinergia de Facção** (`sinergia_faccao`)
Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* O prelado reúne os sobreviventes sob os arcos desmoronados e ergue o antigo selo da irmandade.

### Procissão dos Fiéis
`gwent_v77_esq_passo` · Especial · Os Esquecidos · Carta especial · Rara · Poder 0 · Custo 2

**Procissão dos Fiéis** (`gwent_v77_esq_passo`)
Escolha uma fileira e mova para ela uma unidade aliada que esteja em outra fileira; a raridade pode mover até 3. Raridade Rara: move até 2 aliados.

*Lore:* A procissão atravessa as ruínas e conduz os aliados para a fileira escolhida.

### Profeta de Liurnia
`gwent_unidade_oraculo_clima` · Unidade · Lua Negra · Cerco · Rara · Poder 6 · Custo 2

**** (`sem habilidade`)


*Lore:* O profeta de Liurnia observa as mudanças do céu e interpreta os sinais trazidos por tempestades e geadas.

### Profeta Esquecido
`luterano_profeta` · Unidade · Os Esquecidos · Corpo a corpo · Mítica · Poder 6 · Custo 5

**Sinergia de Facção** (`sinergia_faccao`)
Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Líder espiritual que reúne seus seguidores sob os vitrais partidos de Leyndell.

### Radahn, Flagelo Estelar
`chefe_radahn_flagelo_estrelas` · Unidade · Ordem Áurea · Cerco · Primordial · Poder 9 · Custo 6

**Gravidade do Flagelo** (`quebra_ritmo`)
Ao entrar, move o inimigo de maior poder efetivo para esta fileira e reduz seu bônus em 2 (mín. -2). Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* General temido da Fragmentação, dominou a gravidade para deter o curso das estrelas e permaneceu em Caelid após a Podridão.

### Ranni, Bruxa da Lua
`chefe_dama_vazio` · Unidade · Lua Negra · Cerco · Épica · Poder 6 · Custo 3

**Fenda do Vazio** (`ultimo_folego`)
Ao entrar em campo, tira 2 pontos de bônus da unidade inimiga mais forte. O bônus dela não pode ficar abaixo de -2. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* A princesa lunar rompeu com os Dois Dedos e busca um destino independente da Vontade Maior.

### Recusante Vulcânico
`gwent_unidade_contrabandista` · Unidade · Véu Carmesim · Longa distância · Comum · Poder 5 · Custo 1

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.

*Lore:* Um recusante de Volcano Manor, acostumado a negociar favores e segredos nas encostas do Monte Gelmir.

### Rito Hemático
`gwent_v77_veu_sangramento` · Especial · Véu Carmesim · Carta especial · Rara · Poder 0 · Custo 2

**Rito Hemático** (`gwent_v77_veu_sangramento`)
Escolha uma fileira inimiga. Cada unidade nela recebe Sangramento; a segunda marca reduz 2 de bônus (mín. -2) e consome as marcas. Marcas expiram no fim da rodada. Raridade Rara: aplica a segunda marca a até 1 alvo sem marca; reforça a redução de bônus em até 1 alvo (mín. -2).

*Lore:* O oficiante corta a palma diante do altar e consagra a fileira inimiga ao rito do sangue.

### Ritual de Sangue
`elden_especial_sangramento` · Especial · Véu Carmesim · Carta especial · Rara · Poder 0 · Custo 2

**Sangramento** (`gwent_sangramento`)
Escolha uma fileira inimiga. Cada unidade nela recebe Sangramento; a segunda marca reduz 2 de bônus (mín. -2) e consome as marcas. Marcas expiram no fim da rodada. Raridade Rara: aplica a segunda marca a até 1 alvo sem marca; reforça a redução de bônus em até 1 alvo (mín. -2).

*Lore:* O ritual desperta o poder do sangue e transforma cada ferida em um presságio de ruína.

### Rugido de Godfrey
`gwent_especial_chifre` · Especial · Ordem Áurea · Carta especial · Épica · Poder 0 · Custo 3

**Rugido de Godfrey** (`gwent_chifre`)
Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada. Raridade Épica: acrescenta +1 de bônus a até 1 aliados afetados.

*Lore:* O rugido do Primeiro Lorde Prístino ecoa entre as fileiras e reacende a coragem dos guerreiros.

### Runa da Morte
`reliquia_runa_morte` · Especial · Véu Carmesim · Carta especial · Mítica · Poder 0 · Custo 5

**Runa da Morte** (`reliquia_morte`)
Em cada fileira, a unidade inimiga com maior bônus positivo perde até 2 pontos de bônus (sem ficar negativa). Uso único por partida.

*Lore:* O fragmento da Morte Destinada recorda o poder que Maliketh recebeu para manter selado.

### Runa dos Não Nascidos
`reliquia_runa_nao_nascidos` · Especial · Lua Negra · Carta especial · Lendária · Poder 0 · Custo 4

**Runa dos Não Nascidos** (`reliquia_renala`)
Remove Geada e Podridão dos aliados afetados; cada unidade purificada recebe +1 de bônus. Uso único por partida.

*Lore:* A Grande Runa guardada por Rennala conserva o poder do renascimento e da perfeição inacabada.

### Sacerdote Esquecido
`luterano_sacerdote` · Unidade · Os Esquecidos · Longa distância · Rara · Poder 5 · Custo 2

**Sinergia de combate** (`sem habilidade`)
Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).

*Lore:* Um sacerdote conserva os ritos de sua ordem em um santuário quase tomado pelo tempo.

### Sangue Corrompido
`gwent_especial_chuva` · Especial · Véu Carmesim · Carta especial · Comum · Poder 0 · Custo 1

**Sangue Corrompido** (`gwent_chuva`)
Aplica 1 Sangramento a cada inimigo em Cerco. Na segunda marca, consome as marcas e reduz 2 de bônus (mín. -2). Estados expiram no fim da rodada.

*Lore:* Um rito sanguíneo mancha o campo de batalha com a promessa de uma dívida ainda não paga.

### Santo Sem Nome
`gwent_v76_esq_santo_sem_nome` · Unidade · Os Esquecidos · Cerco · Mítica · Poder 8 · Custo 5

**Sinergia de Facção** (`sinergia_faccao`)
Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma figura venerada sem registro nos livros atravessa o santuário, envolta em luz pálida e poeira dourada.

### Senhor das Almas
`patente_8` · Unidade · Os Esquecidos · Longa distância · Épica · Poder 5 · Custo 3

**Retaliação dos Semideuses** (`retaliacao`)
Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Recompensa de patente concedida ao alcançar o nível 50.

### Sentença Carmesim
`gwent_v77_veu_execucao` · Especial · Véu Carmesim · Carta especial · Lendária · Poder 0 · Custo 4

**Sentença Carmesim** (`gwent_v77_veu_execucao`)
Escolha uma fileira e um inimigo nela. Escudo pode bloquear; se a remoção ocorrer, gatilhos de queda são resolvidos. A raridade amplia o limite de poder efetivo, respeitando o teto do efeito. Raridade Lendária: alcança poder efetivo até 8; pode reforçar bônus gerados por efeitos de queda em até 2 alvos.

*Lore:* O carrasco ergue a lâmina sobre um inimigo vulnerável na fileira marcada pelo sangue.

### Sentinela da Graça
`gwent_v76_ordem_sentinela_luz` · Unidade · Ordem Áurea · Longa distância · Rara · Poder 5 · Custo 2

**Estandarte** (`estandarte`)
Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma sentinela ergue o estandarte dourado sobre a muralha voltada para a Árvore Áurea.

### Sentinela de Leyndell
`arma_grande_sino` · Unidade · Ordem Áurea · Corpo a corpo · Lendária · Poder 8 · Custo 4

**Sino do Último Bastião** (`instinto`)
Ganha +2 quando sua pontuação total for menor que a do adversário. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um guardião de elite protege os acessos da capital e enfrenta qualquer ameaça à ordem dourada.

### Sentinela Imortal
`patente_10` · Unidade · Véu Carmesim · Cerco · Lendária · Poder 6 · Custo 4

**Ruptura de Postura** (`quebra_ritmo`)
Recebe +1 de bônus se a última unidade jogada pelo adversário entrou na mesma fileira. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Recompensa de patente concedida ao alcançar o nível 100.

### Serafim Caído
`gwent_v76_esq_serafim_caido` · Unidade · Os Esquecidos · Longa distância · Épica · Poder 6 · Custo 3

**Glória** (`gloria`)
Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um serafim de asas marcadas desce sobre a catedral, recolhendo as últimas preces entre as ruínas.

### Servo dos Mortos
`gwent_unidade_necromante` · Unidade · Lua Negra · Cerco · Rara · Poder 4 · Custo 2

**Ressurgir** (`ressurgir`)
Ao entrar, traz do seu descarte ao campo a unidade elegível de maior poder-base até 5; ela retorna sem bônus nem Escudo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Um devoto da raiz da morte percorre criptas esquecidas, guiado por sussurros que os vivos não conseguem ouvir.

### Silêncio Dourado
`gwent_v77_ord_silencio` · Especial · Ordem Áurea · Carta especial · Épica · Poder 0 · Custo 3

**Silêncio da Graça** (`gwent_v77_ord_silencio`)
Remove o clima ativo das três fileiras para os dois jogadores.

*Lore:* Uma onda de graça dissipa as forças climáticas que ameaçam as fileiras da Ordem.

### Sino do Peregrino
`gwent_v77_esq_batedor` · Especial · Os Esquecidos · Carta especial · Comum · Poder 0 · Custo 1

**Sino do Peregrino** (`gwent_v77_esq_batedor`)
Compra 1 carta da reserva; a raridade pode elevar a compra para 2, se houver cartas disponíveis.

*Lore:* O sino chama um mensageiro de volta às reservas e revela o próximo recurso da irmandade.

### Tecelã da Névoa
`gwent_v76_lua_tecela_nevoa` · Unidade · Lua Negra · Cerco · Rara · Poder 4 · Custo 2

**Eco Arcano** (`eco_arcano`)
Recebe +2 de bônus ao entrar se houver ao menos uma carta especial no seu descarte. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Uma feiticeira traça runas no ar e observa a névoa se fechar sobre as ruínas de Nokron.

### Tempestade dos Picos
`gwent_especial_tempestade` · Especial · Lua Negra · Carta especial · Rara · Poder 0 · Custo 2

**Tempestade dos Picos** (`gwent_clima`)
Escolha uma fileira. Enquanto o clima estiver ativo, todas as unidades dos dois lados nela perdem 1 de poder efetivo (mínimo 1); Resistência Climática pode absorver a penalidade.

*Lore:* Nuvens pesadas cobrem uma fileira. A chuva atravessa as defesas e enfraquece todas as unidades expostas enquanto o clima durar.

### Veterano do Juramento
`gwent_v75_ordem_veterano_juramento` · Unidade · Ordem Áurea · Corpo a corpo · Rara · Poder 4 · Custo 2

**Juramento Dourado** (`sem habilidade`)
Ao entrar, esta carta recebe +1; o aliado de menor poder efetivo na mesma fileira também recebe +1, se existir. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Veterano das muralhas internas de Leyndell, traz no escudo o juramento feito diante da Árvore Áurea.

### Vigia da Noite
`luterano_vigia` · Unidade · Os Esquecidos · Corpo a corpo · Comum · Poder 3 · Custo 1

**Glória** (`gloria`)
Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece.

*Lore:* Um sentinela solitário vigia os portões enquanto a noite cobre as ruínas.

### Vigília do Relicário
`gwent_v77_esq_egide` · Especial · Os Esquecidos · Carta especial · Rara · Poder 0 · Custo 2

**Vigília do Relicário** (`gwent_v77_esq_egide`)
Escolha um aliado sem Escudo para receber 1 Escudo; a raridade pode proteger até 3 aliados. Escudos não bloqueiam sacrifícios. Raridade Rara: protege até 2 aliados sem Escudo.

*Lore:* Os monges formam um círculo ao redor da relíquia e erguem um escudo sobre os aliados.

### Vontade de Marika
`gwent_singular_nivel1` · Unidade · Ordem Áurea · Corpo a corpo · Singular · Poder 10 · Custo 0

**Último Suspiro** (`ultimo_folego`)
Na terceira rodada, recebe +1 de bônus ao entrar em campo. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.

*Lore:* Conquistada ao vencer um desafio no nível um.

### Égide da Graça
`gwent_v77_ord_egide` · Especial · Ordem Áurea · Carta especial · Rara · Poder 0 · Custo 2

**Égide da Graça** (`gwent_v77_ord_egide`)
Escolha um aliado sem Escudo para receber proteção. A raridade pode ampliar a proteção a até 3 aliados; Escudos não bloqueiam sacrifícios. Raridade Rara: protege até 2 aliados sem Escudo.

*Lore:* Uma muralha de luz dourada envolve os defensores que juraram proteger a Árvore Áurea.
