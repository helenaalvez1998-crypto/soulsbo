# Auditoria de fidelidade — catálogo completo de cartas

**Status:** OK  
**Cartas auditadas:** 137  
**Cartas publicadas no site:** 137  
**Habilidades catalogadas:** 65  
**Efeitos de identidade:** 22  
**Habilidades do pool de recompensas dinâmicas:** 13  
**Cartas de líder auditadas em separado:** 10  
**Divergências automáticas:** 0  

## Cobertura por tipo

- Habilidades exclusivas/identidade: 22
- Habilidades de unidade: 35
- Cartas especiais: 27
- Unidades sem habilidade individual, mas com combo: 38
- Sem efeito individual intencional: 15

## Como ler esta auditoria

O campo **Efeito de combate** reproduz o texto preparado pelo próprio motor `preparar_carta`, incluindo os limites de raridade realmente aplicáveis. O site recebe esse mesmo campo pelo catálogo público e a arte da carta usa o mesmo preparador. A **Lore** é narrativa e não substitui nem altera a regra. Cartas sem habilidade individual continuam podendo participar de combos quando isso estiver listado em suas sinergias.

A cobertura automatizada confirma definição/handler cadastrado para as habilidades do catálogo e para o pool de recompensas geradas dinamicamente, igualdade dos campos mecânicos, sinergias e combos enviados ao site, geração dinâmica do compêndio e encaixe integral do título e do efeito nos dois painéis físicos (procedural e template com arte personalizada). Ela não substitui testes funcionais de cada combinação possível de tabuleiro; as regras de entrada, efeitos especiais, remoção, fim de rodada e combos permanecem testadas separadamente na suíte do projeto.

## Cartas de líder

Os líderes não fazem parte do deck de 12 cartas, mas aparecem como cartas na interface da partida. Nome, facção, ID de efeito e descrição são lidos do registro `LEADERS`; o relatório também confirma que cada ID tem ramo correspondente no resolvedor de jogadas e que o navegador não mantém uma segunda tabela mecânica independente.

### Rennala (`arquimaga_eclipse`)

**Facção:** Lua Negra · **Efeito no motor:** `rennala_full_moon`
**Descrição canônica exibida:** Remove Geada e Podridão dos aliados; cada aliado purificado em Cerco recebe +1 de bônus.

### Morgott (`bastiao_ancestral`)

**Facção:** Ordem Áurea · **Efeito no motor:** `morgott_omen`
**Descrição canônica exibida:** Na fileira escolhida, concede Escudo a até 2 aliados mais fortes e +1 de bônus a eles.

### Godfrey (`comandante_fornalha`)

**Facção:** Ordem Áurea · **Efeito no motor:** `godfrey_warlord`
**Descrição canônica exibida:** Concede +2 de bônus a todas as suas unidades de Corpo a Corpo.

### Radagon (`juiz_cerco`)

**Facção:** Ordem Áurea · **Efeito no motor:** `radagon_purification`
**Descrição canônica exibida:** Remove Sangramento, Geada, Podridão e Loucura de todos os aliados; cada aliado purificado recebe +1 de bônus.

### Papa Esquecido (`lider_papa_esquecido`)

**Facção:** Os Esquecidos · **Efeito no motor:** `forgotten_blessing`
**Descrição canônica exibida:** Concede +1 de bônus às unidades dos Esquecidos na fileira escolhida.

### Astel (`mestre_eclipse`)

**Facção:** Lua Negra · **Efeito no motor:** `astel_gravity`
**Descrição canônica exibida:** A gravidade atinge os inimigos da fileira escolhida: aplica uma marca de Geada a até 3 unidades mais fortes.

### Mohg (`mestre_veu`)

**Facção:** Véu Carmesim · **Efeito no motor:** `mohg_blood_rite`
**Descrição canônica exibida:** Aplica uma marca de Sangramento aos 2 inimigos mais fortes da fileira escolhida; uma segunda marca causa Hemorragia (-2 de bônus).

### Loretta (`oraculo_tempestade`)

**Facção:** Lua Negra · **Efeito no motor:** `loretta_knight`
**Descrição canônica exibida:** Concede +2 de bônus às 2 unidades aliadas mais fortes de Longa Distância.

### Rykard (`sombra_caminhante`)

**Facção:** Véu Carmesim · **Efeito no motor:** `rykard_devour`
**Descrição canônica exibida:** Sacrifica seu aliado mais fraco na fileira escolhida; os demais aliados dessa fileira recebem +2 de bônus.

### Esgar (`voz_caidos`)

**Facção:** Véu Carmesim · **Efeito no motor:** `esgar_blood_priest`
**Descrição canônica exibida:** Ressuscita do descarte a unidade mais forte de poder 5 ou menos na fileira escolhida, com +1 de bônus.

## Cartas auditadas

### Acólito da Dinastia Sanguínea (`gwent_v75_veu_acolito_sangue`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Marca da Dinastia:** Marca o inimigo de maior poder efetivo na fileira. Na segunda marca, consome Sangramento, reduz 2 de bônus (mín. -2) e esta carta recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um acólito do Palácio de Mohgwyn prepara o altar para os ritos secretos da dinastia e reverencia a chama do sangue.
**Tags de sinergia:** v75_blood_mark
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Acólito Sanguíneo — Guardião das Cinzas (`patente_5`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Postura Encadeada:** Recebe +2 de bônus se entrar na mesma fileira da sua última unidade jogada. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Recompensa de patente concedida ao alcançar o nível 20.

### Adaga da Faca Negra (`gwent_singular_intocavel`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 9 · **Custo:** 0  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Mira Cariana:** Recebe +1 de bônus ao entrar na fileira de Longa Distância. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Conquistada ao concluir um desafio sem sofrer dano.

### Algemas de Margit (`reliquia_algemas_margit`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Algemas de Margit:** Na fileira escolhida, zera o bônus positivo do alvo escolhido ou do inimigo com maior bônus. Bônus negativos não mudam; Escudos não bloqueiam o efeito. A ativação consome a Relíquia.
**Lore:** Correntes forjadas para conter o Agouro caído, capazes de subjugar até mesmo um inimigo temível.

### Anjo de Segunda Ordem (`luterano_anjo2`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 5 · **Custo:** 4  
**Classificação:** unidade · **Linhas no render procedural/template:** 5/5 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma presença alada atravessa os salões esquecidos, iluminando os vitrais partidos.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Anjo Esquecido (`luterano_anjo`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 3 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 5/5 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um mensageiro alado atravessa os vitrais partidos da antiga catedral, levando uma luz que quase se apagou.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Aprendiz Cariano — Caçador de Almas (`patente_3`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Recompensa de patente concedida ao alcançar o nível 10.

### Aprendiz de Feitiçaria Cariana (`magia_fagulha`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Um aprendiz da tradição cariana começa a dominar os projéteis de pedra cintilante.

### Apóstolo da Pele Divina (`magia_sol_negro`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Eclipse Devorador:** Ganha +2 se algum inimigo tiver bônus acima de zero. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Devoto da antiga ordem da Pele Divina, empunha a chama negra associada à morte dos deuses.

### Apóstolo da Pele Divina Errante (`gwent_unidade_invocador`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Caçador de Feitiços:** Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Converte conhecimento arcano em força de combate.
**Tags de sinergia:** astral
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras Cintilantes e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Apóstolo Esquecido (`luterano_apostolo`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um pregador percorre as estradas douradas com fragmentos de escrituras antigas.
**Tags de sinergia:** evangelho, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Arauto do Estandarte Áureo (`gwent_v75_ordem_arauto_estandarte`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Não possui habilidade individual. Pode completar combos de formação da Ordem Áurea com a unidade compatível.
**Tags de sinergia:** v75_crucible_guard
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Assassina da Faca Negra (`chefe_cacador_sem_rosto`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Uma assassina Numen ligada à Noite das Facas Negras, quando um fragmento da Runa da Morte foi usado para matar Godwyn.

### Assassina de Ravenmount (`gwent_unidade_cacadora_fantasma`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Uma assassina de Ravenmount atravessa a névoa sem deixar rastros fáceis de seguir.
**Tags de sinergia:** fantasmas
**Combos compatíveis:** Procissão dos que Vivem na Morte: Duas unidades fantasmas marcham juntas (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Astróloga de Liurnia (`magia_nevoa_antiga`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Névoa Ancestral:** Ganha +2 se houver efeito climático em qualquer fileira. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sob os céus de Liurnia, uma astróloga procura nas estrelas sinais de destinos ainda ocultos.
**Tags de sinergia:** astral, lua_cariana
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras Cintilantes e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Bastião de Leyndell (`gwent_especial_muralha`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 0 · **Custo:** 1  
**Classificação:** especial · **Linhas no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Bastião de Leyndell:** Escolha uma fileira: seus aliados nela recebem +1 de bônus até o fim da rodada.
**Lore:** As muralhas douradas de Leyndell erguem-se como símbolo da resistência da capital.

### Batedor da Mansão Vulcânica (`arma_arco_peregrino`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um recusante percorre os caminhos do Monte Gelmir, atento às rotas e aos movimentos dos inimigos.
**Tags de sinergia:** peregrino
**Combos compatíveis:** Caminho do Maculado: Duelista e Batedor da Mansão Vulcânica coordenam o avanço (+1).

### Besta Prístina, Arauto da Vontade Maior (`primordial_origem`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Lei Primeva:** Recebe +2 de bônus ao entrar na primeira rodada. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A Besta Prístina manifesta a vontade que veio além das estrelas e deu forma à ordem dourada.

### Bibliotecária de Raya Lucaria (`gwent_unidade_bibliotecaria`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** O conhecimento reunido na guerra vale mais que ouro.
**Tags de sinergia:** eclipse_voraz
**Combos compatíveis:** Eclipse Sanguíneo: Cavaleiro de Sangue de Mohg e Bibliotecária eclipsam a mesma fonte (+3).

### Bispo Esquecido (`luterano_bispo`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 5 · **Custo:** 4  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Devoção:** Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um bispo dos Esquecidos conduz os fiéis entre ruínas de antigas catedrais.
**Tags de sinergia:** devocao, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Blaidd, o Meio-Lobo (`gwent_unidade_senhor_cacada`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Vingança:** Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A presa que o derruba desperta a matilha inteira.
**Tags de sinergia:** fantasmas
**Combos compatíveis:** Procissão dos que Vivem na Morte: Duas unidades fantasmas marcham juntas (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Bênção da Árvore Áurea (`gwent_especial_egide`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Bênção da Árvore Áurea:** Escolha um aliado sem Escudo para receber 1 Escudo; a raridade pode proteger até 3 aliados. Escudos não bloqueiam sacrifícios. Raridade Rara: protege até 2 aliados sem Escudo.
**Lore:** Uma prece antiga invoca a proteção dourada que envolve os campeões da capital.

### Carrasco da Procissão Carmesim (`gwent_v75_veu_carrasco_preco`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Preço em Sangue:** Sacrifica o aliado de menor poder efetivo da mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +3). Sem aliado, recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O carrasco conduz procissões sob estandartes vermelhos, vestindo as vestes cerimoniais dos guerreiros de Mohgwyn.
**Tags de sinergia:** v75_blood_feast
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Carrasco de Volcano Manor (`gwent_unidade_carniceiro_forja`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Devorar:** Ao entrar, sacrifica o aliado de menor poder efetivo na mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +4). Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um executor da Mansão Vulcânica veste o aço manchado dos recusantes e serve aos banquetes de Tanith.
**Tags de sinergia:** banquete, sangue_mohgwyn
**Combos compatíveis:** Banquete de Sangue: Carniceiro da Forja e Intendente dividem o butim (+3).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Cartógrafo das Cidades Eternas (`gwent_v75_lua_cartografo_lunar`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.
**Tags de sinergia:** v75_lunar_paths
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Cavaleira Cariana (`gwent_unidade_cavaleira`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Uma duelista cariana, treinada nas tradições de combate da realeza lunar.
**Tags de sinergia:** veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).

### Cavaleiro Consagrado do Haligtree (`gwent_mitica_coroa`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Mítica · **Poder-base:** 8 · **Custo:** 5  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Estandarte:** Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um cavaleiro consagrado guarda os ramos pálidos do Haligtree, onde a esperança resiste à decadência.

### Cavaleiro da Dinastia Mohgwyn (`covenant_coroa_abismo`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 7 · **Custo:** 4  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Selo Enfraquecedor:** Reduz em 1 o bônus de cada unidade inimiga, até o mínimo de -2. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guerreiro jurado à dinastia sanguínea guarda os domínios ocultos de Mohg.
**Tags de sinergia:** abismo, sangue_mohgwyn
**Combos compatíveis:** Maré Abissal: Godfrey e Cavaleiro Carmesim despertam a mesma força (+2).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Cavaleiro da Árvore Áurea (`chefe_guardiao_cinzas`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Égide das Cinzas:** Se já houver um aliado na mesma fileira, ele recebe +1 de bônus e esta carta também recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um sentinela montado patrulha os caminhos que conduzem à Árvore Áurea, impondo a autoridade da capital.
**Tags de sinergia:** cinzas, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Cavaleiro de Leyndell (`chefe_vigia_cinzento`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Um soldado da capital mantém a vigília entre as muralhas erguidas em nome da Ordem Áurea.

### Cavaleiro de Radahn (`gwent_unidade_sentinela_rubra`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um cavaleiro da hoste de Radahn mantém sua posição sob o estandarte vermelho de Caelid.
**Tags de sinergia:** muralha, ordem_dourada
**Combos compatíveis:** Defesa de Leyndell: Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Cavaleiro de Sangue de Mohg (`gwent_unidade_devorador_mana`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um cavaleiro ligado ao sangue de Mohg participa dos rituais sombrios da dinastia subterrânea.
**Tags de sinergia:** eclipse_voraz, sangue_mohgwyn
**Combos compatíveis:** Eclipse Sanguíneo: Cavaleiro de Sangue de Mohg e Bibliotecária eclipsam a mesma fonte (+3).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Cavaleiro do Crisol (`gwent_unidade_baluarte`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um cavaleiro do Crisol, marcado pelas antigas formas que antecederam a Árvore Áurea, guarda a formação com disciplina.
**Tags de sinergia:** fornalha, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Cavaleiro do Cão de Caça (`chefe_cervo_sombrio`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um cavaleiro errante segue a trilha de presas pelas florestas enevoadas das Terras Intermédias.
**Tags de sinergia:** veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).

### Cavaleiro Draconiano (`gwent_unidade_veterano_cercos`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Já viu mais muralhas caírem do que rostos conhecidos.
**Tags de sinergia:** muralha
**Combos compatíveis:** Defesa de Leyndell: Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Cavaleiros de Radahn (`covenant_lobos_cinza`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Veteranos da hoste do Flagelo das Estrelas, marcham sob o estandarte do general de Caelid.
**Tags de sinergia:** cinzas
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).

### Cavaleiros de sangue juramentados (`covenant_ultimos`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Combatentes unidos por juramentos de sangue permanecem ao lado de seu senhor até o último fôlego.

### Caçador das Catacumbas de Mohgwyn (`gwent_v75_veu_cacador_sangue`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Não possui habilidade individual. Pode completar combos de marca de Sangramento com a unidade compatível.
**Tags de sinergia:** v75_blood_mark
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Caçador de Dedos (`gwent_unidade_lamina_sem_juramento`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Caçador de Dedos, um duelista errante que prefere trilhas solitárias e confrontos sem testemunhas.

### Chama do Gigante (`elden_especial_chama`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Chama do Gigante:** Remove Geada de todos os aliados afetados; cada unidade purificada recebe +1 de bônus até o fim da rodada. A raridade pode ampliar esses bônus. Raridade Rara: acrescenta +1 de bônus a até 1 aliados purificados.
**Lore:** A chama dos gigantes arde contra o frio que tenta aprisionar os vivos.

### Chama Frenética (`elden_especial_loucura`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Loucura Frenética:** Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda zera bônus positivos. Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.
**Lore:** A chama frenética consome razão e identidade, deixando apenas o caos da Chama Frenética.

### Chama Negra (`gwent_especial_queima`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Chama Negra:** Em cada lado, tenta remover a unidade de maior poder efetivo. Escudo bloqueia a remoção; se ela ocorrer, gatilhos de queda são resolvidos. Raridade Épica: reforça bônus gerados por efeitos de queda em até 1 alvo; não amplia remoções nem atravessa Escudos.
**Lore:** A chama negra, temida até pelos deuses, consome tudo o que toca.

### Chamado dos Mortos (`gwent_especial_requiem`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Chamado dos Mortos:** Traz do descarte diretamente ao campo uma unidade escolhida com poder-base até 6; a raridade pode elevar esse limite até 9. Raridade Épica: o limite de poder-base sobe até 7.
**Lore:** Um cântico atravessa as catacumbas e ecoa entre os nomes que a história tentou apagar.

### Cinzas dos Lobos Solitários (`elden_especial_invocacao`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Cinzas dos Lobos Solitários:** Escolha uma fileira e invoque Lobos Espirituais nela com 3 de poder; a raridade pode elevar o poder da invocação até 6. Raridade Rara: invoca Lobos Espirituais com 4 de poder.
**Lore:** Cinzas antigas despertam os espíritos de lobos que outrora caçaram ao lado de seus mestres.

### Confessora da Graça Serena (`gwent_v75_ordem_confessora_graca`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Regressão Serena:** Purifica até 2 aliados da fileira de Sangramento, Geada, Podridão ou Loucura; cada um recebe +1. Se ninguém precisar, o aliado mais fraco recebe +1; sem aliados, esta carta recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma Confessora percorre os caminhos de Leyndell em silêncio, levando os ensinamentos da Lei da Regressão aos santuários esquecidos.
**Tags de sinergia:** v75_erdtree_oath
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Confessora da Ordem Áurea (`magia_selo_vigilia`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Selo de Vigília:** Esta carta recebe Resistência Climática 1. Se houver aliado na mesma fileira, o primeiro recebe +1 de bônus. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Treinada para agir discretamente, a Confessora combina devoção, infiltração e combate próximo.

### Coroa do Lorde Prístino (`gwent_singular_cacador_chefes`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 9 · **Custo:** 0  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Paradoxo Eterno:** Na terceira rodada, recebe +2 de bônus se o adversário venceu a rodada anterior. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Conquistada ao derrotar todos os chefes de um desafio.

### Cruzado Esquecido (`luterano_cruzado`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guerreiro sagrado guarda as estradas em ruínas e carrega no escudo o símbolo de uma ordem que já não existe.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Devota da Hemorragia (`gwent_v75_veu_devota_hemorragia`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Não possui habilidade individual. Pode completar o combo Banquete da Hemorragia com a unidade compatível.
**Tags de sinergia:** v75_blood_feast
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Discípulo da Academia (`gwent_unidade_circulo`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Discípulo de Raya Lucaria, dedica-se ao estudo dos círculos arcanos e dos resíduos de feitiçaria.
**Tags de sinergia:** astral
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras Cintilantes e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Discípulos do Monge do Fogo (`covenant_filhos_brasa`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Seguidores dos antigos monges preservam a chama dos gigantes e seus rituais esquecidos.

### Diácono Esquecido (`luterano_diacon`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Auxiliar dos rituais, mantém acesas as lâmpadas dos altares esquecidos.
**Tags de sinergia:** diaconia, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Dragoeiro Ancião (`magia_trovao_oco`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Descarga Oca:** Cada inimigo na mesma fileira perde 1 de bônus (mín. -2). Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guerreiro ligado aos antigos dragões canaliza relâmpagos ancestrais em meio à batalha.

### Duelista da Casa Hoslow (`arma_lamina_peregrino`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Herdeiro de uma casa de duelistas, transforma a elegância do aço em uma promessa de sangue.
**Tags de sinergia:** peregrino
**Combos compatíveis:** Caminho do Maculado: Duelista e Batedor da Mansão Vulcânica coordenam o avanço (+1).

### Erudito da Academia (`magia_orbe_eco`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Pesquisador de Raya Lucaria, dedica a vida ao estudo dos segredos das pedras cintilantes.
**Tags de sinergia:** eco
**Combos compatíveis:** Eco das Pedras Cintilantes: O Erudito das Pedras Cintilantes e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Erudito das Pedras Cintilantes (`gwent_unidade_eco`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um estudioso das pedras cintilantes investiga as ressonâncias deixadas por feitiçarias antigas.
**Tags de sinergia:** astral, eco
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras Cintilantes e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Escudeiro da Árvore Áurea — Cavaleiro do Abismo (`patente_4`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Recompensa de patente concedida ao alcançar o nível 15.

### Espada da Noite e da Chama (`reliquia_noite_chama`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 0 · **Custo:** 4  
**Classificação:** especial · **Linhas no render procedural/template:** 4/4 · **Validação:** OK

**Efeito de combate — Espada da Noite e da Chama:** Noite: aplica 1 marca de Geada (máx. 2) a todos os inimigos da fileira escolhida. Chama: atinge o inimigo de maior poder efetivo na fileira, reduzindo 1 de poder-base (mín. 1) e 2 de bônus. Escudo bloqueia o golpe; a Relíquia é consumida.
**Lore:** Arma lendária da Mansão Cariana. Sua postura especial libera um ataque mágico ou uma onda de fogo.

### Espadachim da Lua Negra (`arma_duas_luas`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Dança Espelhada:** Ganha +1 se você tiver outro aliado em uma fileira diferente. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um duelista das tradições carianas conduz a lâmina sob a luz fria da Lua Negra.
**Tags de sinergia:** duas_luas, lua_cariana
**Combos compatíveis:** Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Exploradora da Cidade Eterna (`gwent_unidade_cartografa`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Encontra rotas onde os outros veem obstáculos.
**Tags de sinergia:** duas_luas
**Combos compatíveis:** Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).

### Feiticeira da Lua Gélida (`magia_chama_fria`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Uma feiticeira errante combina o frio das antigas artes lunares com chamas de origem desconhecida.
**Tags de sinergia:** chama
**Combos compatíveis:** Chamas do Monte Gelmir: Piromante e Feiticeira da Lua Gélida equilibram suas chamas (+2).

### Feiticeiro Cariano (`arma_cajado_marulho`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Discípulo da realeza cariana, conjura feitiçarias de pedra cintilante sob a proteção da lua.

### Feiticeiro Cariano — Executor Sombrio (`patente_7`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Caçador de Feitiços:** Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Recompensa de patente concedida ao alcançar o nível 40.

### Ferreiro de Volcano Manor (`arma_martelo_fornalha`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Entre fornalhas e juramentos de traição, um artesão molda armas para os recusantes do Monte Gelmir.

### Fia, Companheira do Leito de Morte (`gwent_unidade_cantora_lamentos`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Fia, Companheira do Leito de Morte, entoa lamentos pelos que encontraram repouso entre os mortos.
**Tags de sinergia:** fantasmas
**Combos compatíveis:** Procissão dos que Vivem na Morte: Duas unidades fantasmas marcham juntas (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Flor da Podridão Escarlate (`elden_especial_podrida`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas no render procedural/template:** 5/5 · **Validação:** OK

**Efeito de combate — Podridão Escarlate:** Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda reduz 1 de bônus positivo (mín. 0). Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.
**Lore:** A flor escarlate floresce onde a podridão encontra carne, pedra e memória.

### Geada dos Picos dos Gigantes (`gwent_especial_geada`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Lua Gélida:** Todas as unidades inimigas recebem 1 marca de Geada; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada.
**Lore:** O frio dos Picos dos Gigantes avança sobre o campo e silencia o vigor dos combatentes.

### Gigante de Fogo (`gwent_unidade_gigante`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Instinto de Caçador:** Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma presença colossal na linha de frente.

### Godfrey, Primeiro Lorde Prístino (`chefe_rei_afogado`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Dízimo do Abismo:** Recebe +2 se houver qualquer carta no seu descarte; caso contrário, recebe +1 se o adversário tiver mais unidades em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Primeiro Lorde Prístino e consorte de Marika, Godfrey liderou os guerreiros que conquistaram as Terras Intermédias.
**Tags de sinergia:** abismo, sangue_mohgwyn
**Combos compatíveis:** Maré Abissal: Godfrey e Cavaleiro Carmesim despertam a mesma força (+2).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Godwyn, o Dourado (`gwent_unidade_herdeiro_portao`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Vingança:** Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O príncipe dourado foi amado por dragões e homens; sua queda marcou a primeira rachadura irreversível no destino das Terras Intermédias.
**Tags de sinergia:** muralha, ordem_dourada
**Combos compatíveis:** Defesa de Leyndell: Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Grande Runa de Godrick (`reliquia_grande_runa_godrick`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 0 · **Custo:** 4  
**Classificação:** especial · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Grande Runa de Godrick:** Exige ao menos 1 unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas; uso único por partida.
**Lore:** Fragmento do Anel Prístino reivindicado por Godrick, o Enxertado, que buscava poder por meio do enxerto.

### Grande Runa dos Não Nascidos (`reliquia_runa_nao_nascidos`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 0 · **Custo:** 4  
**Classificação:** especial · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Grande Runa dos Não Nascidos:** Remove Geada e Podridão dos aliados afetados; cada unidade purificada recebe +1 de bônus. Uso único por partida.
**Lore:** A Grande Runa guardada por Rennala conserva o poder do renascimento e da perfeição inacabada.

### Graviturgista de Nokron (`gwent_v75_lua_graviturgista`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Cisalhamento Gravitacional:** Até 2 inimigos com bônus positivo na fileira perdem 1 (mín. -2). Se atingir 2 alvos, esta carta recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um astrólogo das Cidades Eternas estuda as correntes gravitacionais que sustentam as ruínas suspensas de Nokron.
**Tags de sinergia:** v75_frost_lore
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Guardas da Árvore Áurea (`covenant_irmandade_ferro`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** unidade · **Linhas no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Retaliação dos Semideuses:** Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária.
**Lore:** Defensores juramentados protegem os caminhos e santuários consagrados à Árvore Áurea.
**Tags de sinergia:** estandarte
**Combos compatíveis:** Juramento de Leyndell: Porta-estandarte e Guardas da Árvore Áurea fortalecem a formação (+1 para a carta participante que ativa o combo e +1 aos aliados na mesma fileira).

### Guardiã do Juramento Lunar (`gwent_v75_lua_guardia`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Não possui habilidade individual. Pode completar combos de mobilidade lunar com a unidade compatível.
**Tags de sinergia:** v75_lunar_paths
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Guardião da Ordem Áurea (`gwent_unidade_guardiao_runas`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um guardião da Ordem Áurea carrega inscrições rúnicas ligadas aos ensinamentos da capital.
**Tags de sinergia:** runico
**Combos compatíveis:** Ritual das Runas: Duas unidades rúnicas completam o círculo (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Guardião do Crisol Menor (`gwent_v75_ordem_guardiao_crisol`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Não possui habilidade individual. Pode completar combos da Ordem Áurea quando estiver em campo com a unidade compatível.
**Tags de sinergia:** v75_crucible_guard
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Guardiões de Sellia (`covenant_sentinelas`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Vigias da cidade oculta de Sellia protegem seus segredos e as passagens de feitiçaria.

### Guerreiro da Chama Frenética (`gwent_unidade_detonador`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Vingança:** Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sua queda libera a energia que ele guardava.
**Tags de sinergia:** runico
**Combos compatíveis:** Ritual das Runas: Duas unidades rúnicas completam o círculo (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Gurranq, Clérigo Bestial (`chefe_oraculo_ruina`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 7 · **Custo:** 4  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Presságio da Ruína:** A unidade inimiga de maior poder efetivo perde 1 de bônus (mín. -2). Se sua pontuação estiver menor ao entrar, esta carta recebe +1. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O clérigo bestial consome Raiz da Morte e guarda um segredo ligado à própria Runa da Morte.

### Gêmeas da Cidade Eterna (`gwent_unidade_dupla_veu`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Duas irmãs das Cidades Eternas percorrem caminhos subterrâneos que raramente aparecem nos mapas.
**Tags de sinergia:** duas_luas, veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).; Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).

### Irmão Esquecido (`luterano_irmao`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um peregrino humilde permanece ao lado de sua irmandade, mesmo quando todos os demais recuam.
**Tags de sinergia:** fe, irmandade
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Juramentada de Ranni (`covenant_lua_velada`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/4 · **Validação:** OK

**Efeito de combate — Aliança Lunar:** Esta carta recebe +1. O aliado de menor poder efetivo em outra fileira também recebe +1 de bônus, se existir. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma aliada juramentada à princesa lunar acompanha sua busca por um caminho além da Ordem Áurea.
**Tags de sinergia:** duas_luas, lua_cariana
**Combos compatíveis:** Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Juramento do Crisol (`gwent_especial_vinculo`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Juramento do Crisol:** Escolha uma fileira com ao menos 2 aliados. Todas as unidades aliadas nela recebem +2 de bônus até o fim da rodada. Raridade Rara: acrescenta +1 de bônus a até 1 aliados afetados.
**Lore:** Um juramento ancestral une os guerreiros às formas primordiais que precederam a Erdtree.

### Juramento Primordial do Crisol (`gwent_singular_primeiro`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 10 · **Custo:** 0  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Caçador Solitário:** Recebe +2 de bônus ao entrar se não houver outro aliado na mesma fileira. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Exemplar singular conquistado por um feito extraordinário.

### Ladina da Cidade Eterna (`gwent_unidade_saqueadora_veu`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Nenhuma rota é cara demais para quem leva o butim.
**Tags de sinergia:** caravana
**Combos compatíveis:** Saque da Cidade Eterna: Saqueadora e Contrabandista fecham o negócio (+2).

### Lanceiro da Árvore Áurea (`arma_lanca_fornalha`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Treinado para defender os domínios da Árvore Áurea, avança com lança e disciplina militar.

### Lei da Regressão (`gwent_especial_purificar`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 2/1 · **Validação:** OK

**Efeito de combate — Lei da Regressão:** Remove o clima ativo das três fileiras para os dois jogadores.
**Lore:** A Lei da Regressão revela a verdade por trás das ilusões e desfaz os véus que encobrem o mundo.

### Leitora de Estrelas de Sellia (`arma_agulha_astro`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 3 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Uma estudiosa de Sellia observa os astros e procura caminhos ocultos na feitiçaria noturna.
**Tags de sinergia:** astral, lua_cariana
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras Cintilantes e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Lorde de Leyndell — Lenda do Coliseu (`patente_9`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Ímpeto do Lorde:** Recebe +1 de bônus ao entrar se sua pontuação estiver acima da adversária. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Recompensa de patente concedida ao alcançar o nível 75.

### Lua Cheia de Rennala (`elden_especial_geada`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Geada Cariana:** Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Geada; cada marca reduz 1 de poder efetivo até o fim da rodada. A raridade pode aplicar a segunda marca imediatamente a até 3 alvos. Raridade Rara: aplica a segunda marca imediatamente a até 1 alvos sem Geada prévia.
**Lore:** A lua cheia de Rennala ilumina o campo com a frieza ancestral da realeza cariana.

### Lágrima Sagrada (`gwent_especial_medico`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Lágrima Sagrada:** Devolve à sua mão uma unidade escolhida do seu descarte com poder-base até 4; a raridade pode elevar esse limite até 7. Raridade Rara: o limite de poder-base sobe até 5.
**Lore:** Uma lágrima consagrada guarda a memória dos que tombaram e ainda podem retornar à jornada.

### Lâmina da Morte Destinada (`gwent_especial_execucao`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas no render procedural/template:** 5/5 · **Validação:** OK

**Efeito de combate — Lâmina da Morte Destinada:** Escolha uma fileira e um inimigo nela com poder efetivo até 6. Tenta removê-lo; Escudo pode bloquear. Se a remoção ocorrer, gatilhos de queda são resolvidos. A raridade eleva o limite até 9. Raridade Épica: alcança poder efetivo até 7; pode reforçar bônus gerados por efeitos de queda em até 1 alvo.
**Lore:** A lâmina da Morte Destinada carrega o fragmento de um poder que deveria permanecer selado.

### Lâmina Negra (`reliquia_lamina_negra`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Mítica · **Poder-base:** 0 · **Custo:** 5  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Lâmina Negra:** Na fileira escolhida, reduz em 3 o bônus do alvo escolhido ou, sem alvo, do inimigo de maior poder efetivo. Escudo é consumido e bloqueia o efeito sem consumir a Relíquia.
**Lore:** A arma de Maliketh, que guarda a Morte Destinada selada em sua lâmina. Não é uma das adagas usadas pelas Assassinas da Faca Negra.

### Lâmina Negra Errante (`chefe_aparicao_veio`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Uma figura encapuzada atravessa as sombras, deixando apenas o rumor de uma lâmina silenciosa.
**Tags de sinergia:** veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).

### Malenia, Lâmina de Miquella (`chefe_malenia_lamina_miquella`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Primordial · **Poder-base:** 9 · **Custo:** 6  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Flor Escarlate:** Cada inimigo da fileira recebe 1 marca de Podridão (máx. 2); cada marca reduz 1 de poder efetivo. Ao atingir 2, bônus positivo perde 1 (mín. 0). Primordial: até 3 alvos nessa transição perdem mais 1 (mín. -2). Não reduz de novo com 2 marcas.
**Lore:** Malenia é uma Empírea e semideusa, filha de Marika e Radagon e irmã gêmea de Miquella. Nasceu afligida pela Podridão Escarlate e foi treinada por um espadachim cego, tornando-se uma espadachim incomparável. Como Lâmina de Miquella, protegeu o irmão e aguarda seu retorno em Elphael, sob a Árvore Sacra. Empunha a Mão de Malenia, uma katana, e combate com próteses douradas. Na batalha contra Radahn em Caelid, liberou uma florescência da Podridão Escarlate que devastou a região. Esta ficha representa Malenia antes de sua transformação na Deusa da Podridão.

### Maliketh, Guardião da Morte Destinada (`primordial_eternidade`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Paradoxo Eterno:** Na terceira rodada, recebe +2 de bônus se o adversário venceu a rodada anterior. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Maliketh guarda a Morte Destinada, o poder cuja ausência sustenta a ordem sem morte de Marika.

### Maliketh, Lâmina Negra (`chefe_maliketh_morte_destinada`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Morte Destinada:** Ao entrar, o inimigo de maior poder efetivo perde 2 de bônus (mín. -2). Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sombra leal de Marika e guardião da Runa da Morte, carrega a Morte Destinada selada em sua lâmina.

### Marika, Rainha Eterna (`primordial_trono`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Decreto Soberano:** Ao entrar, reduz em 2 o bônus de todas as unidades inimigas (mín. -2). Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Marika, a Rainha Eterna, ergueu a ordem dourada e rompeu o Anel Prístino, mudando para sempre as Terras Intermédias.

### Mercador Nômade (`gwent_unidade_intendente`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um mercador nômade percorre as Terras Intermédias levando provisões e notícias entre assentamentos.
**Tags de sinergia:** banquete
**Combos compatíveis:** Banquete de Sangue: Carniceiro da Forja e Intendente dividem o butim (+3).

### Messmer, o Empalador (`chefe_messmer_impalador`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Lança do Impalador:** Ao entrar, cada inimigo da fileira recebe 1 marca de Sangramento. A segunda marca consome as marcas e causa -2 de bônus (mín. -2); estados expiram no fim da rodada. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Filho de Marika e senhor da chama impura, comandou a purga que devastou o Reino das Sombras.

### Mestre Cariano — Sentinela Imortal (`patente_10`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 6 · **Custo:** 4  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Ruptura de Postura:** Recebe +1 de bônus se a última unidade jogada pelo adversário entrou na mesma fileira. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Recompensa de patente concedida ao alcançar o nível 100.

### Mestre Ferreiro de Volcano Manor (`gwent_unidade_mestre_forja`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um mestre ferreiro de Volcano Manor trabalha entre brasas, aço e os juramentos dos recusantes.
**Tags de sinergia:** fornalha, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Miasma da Podridão (`gwent_especial_nevoa`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Névoa de Sellia:** Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Podridão Escarlate; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada.
**Lore:** Uma nuvem pútrida se espalha pelo campo, lembrando os pântanos corrompidos de Caelid.

### Missionário Esquecido (`luterano_missionario`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um viajante percorre capelas abandonadas levando escrituras preservadas por gerações.
**Tags de sinergia:** evangelho, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Monge do Fogo (`magia_brasa_errante`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Devoto do fogo dos gigantes, preserva ritos antigos nas encostas geladas dos Picos dos Gigantes.
**Tags de sinergia:** chama
**Combos compatíveis:** Chamas do Monte Gelmir: Piromante e Feiticeira da Lua Gélida equilibram suas chamas (+2).

### Mãe Sem Forma (`primordial_abismo`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Fome do Abismo:** Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A Mãe Sem Forma é venerada pelos seguidores de Mohg como origem do poder sanguíneo.

### Místico Esquecido (`luterano_mistico`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Devoção:** Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um intérprete de sinais antigos contempla as estrelas sobre as ruínas de Sellia.
**Tags de sinergia:** devocao, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Novato de Raya Lucaria — Cinzas Novatas (`patente_1`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** unidade · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Caçador de Feitiços:** Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo.
**Lore:** Recompensa de patente concedida ao alcançar o nível 1.

### Novato de Raya Lucaria — Guerreiro Caído (`patente_2`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Recompensa de patente concedida ao alcançar o nível 5.

### Oráculo Gélido de Sellia (`gwent_v75_lua_oraculo_geada`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/4 · **Validação:** OK

**Efeito de combate — Presságio da Geada:** O inimigo de maior poder efetivo na fileira recebe 1 marca de Geada (máx. 2). Se já tinha marca, esta carta recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma astróloga de Sellia lê presságios nas lâminas de gelo que se formam sobre as águas imóveis da cidade.
**Tags de sinergia:** v75_frost_lore
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Papa Esquecido (`luterano_papa`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Mítica · **Poder-base:** 7 · **Custo:** 5  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sumo sacerdote dos Esquecidos, governa uma ordem que sobreviveu à queda de seus templos.
**Tags de sinergia:** fe, soberania
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Passo do Cão de Caça (`gwent_especial_batedor`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Passo do Cão de Caça:** Compra 1 carta da reserva; a raridade pode elevar a compra para 2, se houver cartas disponíveis. Raridade Rara: compra até 2 cartas da reserva.
**Lore:** O passo do cão de caça atravessa o campo antes que o inimigo perceba sua aproximação.

### Passo do Lobo (`gwent_especial_passo`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Passo do Lobo:** Escolha uma fileira e mova para ela uma unidade aliada que esteja em outra fileira. Raridade Rara: move até 2 aliados.
**Lore:** O antigo instinto de caça guia seus guerreiros por caminhos que parecem impossíveis.

### Pastor Esquecido (`luterano_pastor`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Legado:** Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guia errante conduz os fiéis por trilhas esquecidas e capelas abandonadas.
**Tags de sinergia:** fe, irmandade
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Peregrinos da Cidade Eterna (`covenant_peregrinos_nevoa`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** Viajantes das cidades subterrâneas cruzam a escuridão em busca de uma nova estrela.

### Placidusax, Lorde Dragão (`chefe_placidusax_lorde_dragao`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 9 · **Custo:** 6  
**Classificação:** identidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Tempestade do Tempo:** Ao entrar, cada inimigo da fileira recebe 1 marca de Geada (máx. 2); esta carta recebe +1 por inimigo atingido, até +3. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Lorde Dragão ancestral que aguarda, em Farum Azula, o retorno de seu deus desaparecido.

### Placidusax, Senhor Dragão (`primordial_tempestade`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Olho da Tempestade:** Recebe +2 de bônus ao entrar se sua fileira estiver sob clima ativo. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Placidusax, antigo lorde dos dragões, permanece suspenso no tempo em Farum Azula.

### Porta-estandarte de Leyndell (`gwent_unidade_portaestandarte`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 3 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** O estandarte de Leyndell reúne soldados dispersos sob o símbolo dourado da capital.
**Tags de sinergia:** estandarte, fornalha, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento de Leyndell: Porta-estandarte e Guardas da Árvore Áurea fortalecem a formação (+1 para a carta participante que ativa o combo e +1 aos aliados na mesma fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Profeta de Liurnia (`gwent_unidade_oraculo_clima`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Sem habilidade especial:** Sem habilidade especial.
**Lore:** O profeta de Liurnia observa as mudanças do céu e interpreta os sinais trazidos por tempestades e geadas.

### Profeta Esquecido (`luterano_profeta`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Mítica · **Poder-base:** 6 · **Custo:** 5  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Líder espiritual que reúne seus seguidores sob os vitrais partidos de Leyndell.
**Tags de sinergia:** fe, soberania
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Radahn, Flagelo das Estrelas (`chefe_radahn_flagelo_estrelas`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 9 · **Custo:** 6  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Gravidade do Flagelo:** Ao entrar, move o inimigo de maior poder efetivo para esta fileira e reduz seu bônus em 2 (mín. -2). Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** General temido da Fragmentação, dominou a gravidade para deter o curso das estrelas e permaneceu em Caelid após a Podridão.

### Ranni, Bruxa da Lua (`chefe_dama_vazio`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/4 · **Validação:** OK

**Efeito de combate — Fenda do Vazio:** Ao entrar em campo, tira 2 pontos de bônus da unidade inimiga mais forte. O bônus dela não pode ficar abaixo de -2. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A princesa lunar rompeu com os Dois Dedos e busca um destino independente da Vontade Maior.
**Tags de sinergia:** lua_cariana, vazio
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Recusante da Mansão Vulcânica (`gwent_unidade_contrabandista`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um recusante de Volcano Manor, acostumado a negociar favores e segredos nas encostas do Monte Gelmir.
**Tags de sinergia:** caravana
**Combos compatíveis:** Saque da Cidade Eterna: Saqueadora e Contrabandista fecham o negócio (+2).

### Ritual de Sangue (`elden_especial_sangramento`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sangramento:** Escolha uma fileira inimiga. Cada unidade nela recebe Sangramento; a segunda marca reduz 2 de bônus (mín. -2) e consome as marcas. Marcas expiram no fim da rodada. Raridade Rara: aplica a segunda marca a até 1 alvo sem marca; reforça a redução de bônus em até 1 alvo (mín. -2).
**Lore:** O ritual desperta o poder do sangue e transforma cada ferida em um presságio de ruína.

### Rugido de Godfrey (`gwent_especial_chifre`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Rugido de Godfrey:** Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada. Raridade Épica: acrescenta +1 de bônus a até 1 aliados afetados.
**Lore:** O rugido do Primeiro Lorde Prístino ecoa entre as fileiras e reacende a coragem dos guerreiros.

### Runa da Morte (`reliquia_runa_morte`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Mítica · **Poder-base:** 0 · **Custo:** 5  
**Classificação:** especial · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Runa da Morte:** Em cada fileira, a unidade inimiga com maior bônus positivo perde até 2 pontos de bônus (sem ficar negativa). Uso único por partida.
**Lore:** O fragmento da Morte Destinada recorda o poder que Maliketh recebeu para manter selado.

### Sacerdote Esquecido (`luterano_sacerdote`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** combo · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um sacerdote conserva os ritos de sua ordem em um santuário quase tomado pelo tempo.
**Tags de sinergia:** fe, sacerdos
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Sangue Corrompido (`gwent_especial_chuva`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 0 · **Custo:** 1  
**Classificação:** especial · **Linhas no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Sangue Corrompido:** Aplica 1 Sangramento a cada inimigo em Cerco. Na segunda marca, consome as marcas e reduz 2 de bônus (mín. -2). Estados expiram no fim da rodada.
**Lore:** Um rito sanguíneo mancha o campo de batalha com a promessa de uma dívida ainda não paga.

### Sentinela do Portão de Leyndell (`arma_grande_sino`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Sino do Último Bastião:** Ganha +2 quando sua pontuação total for menor que a do adversário. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guardião de elite protege os acessos da capital e enfrenta qualquer ameaça à ordem dourada.

### Servo dos que Vivem na Morte (`gwent_unidade_necromante`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas no render procedural/template:** 5/4 · **Validação:** OK

**Efeito de combate — Ressurgir:** Ao entrar, traz do seu descarte ao campo a unidade elegível de maior poder-base até 5; ela retorna sem bônus nem Escudo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um devoto da raiz da morte percorre criptas esquecidas, guiado por sussurros que os vivos não conseguem ouvir.
**Tags de sinergia:** runico
**Combos compatíveis:** Ritual das Runas: Duas unidades rúnicas completam o círculo (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Tempestade dos Picos (`gwent_especial_tempestade`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Tempestade dos Picos:** Escolha uma fileira. Enquanto o clima estiver ativo, todas as unidades dos dois lados nela perdem 1 de poder efetivo (mínimo 1); Resistência Climática pode absorver a penalidade.
**Lore:** Nuvens pesadas cobrem uma fileira. A chuva atravessa as defesas e enfraquece todas as unidades expostas enquanto o clima durar.

### Veterano de Leyndell — Arauto da Ruína (`patente_6`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Retaliação dos Semideuses:** Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Recompensa de patente concedida ao alcançar o nível 30.

### Veterano de Leyndell — Senhor das Almas (`patente_8`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Retaliação dos Semideuses:** Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Recompensa de patente concedida ao alcançar o nível 50.

### Veterano do Juramento Dourado (`gwent_v75_ordem_veterano_juramento`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** identidade · **Linhas no render procedural/template:** 4/4 · **Validação:** OK

**Efeito de combate — Juramento Dourado:** Ao entrar, esta carta recebe +1; o aliado de menor poder efetivo na mesma fileira também recebe +1, se existir. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Veterano das muralhas internas de Leyndell, traz no escudo o juramento feito diante da Árvore Áurea.
**Tags de sinergia:** v75_erdtree_oath
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Vigia da Noite (`luterano_vigia`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece.
**Lore:** Um sentinela solitário vigia os portões enquanto a noite cobre as ruínas.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Vontade de Marika (`gwent_singular_nivel1`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 10 · **Custo:** 0  
**Classificação:** unidade · **Linhas no render procedural/template:** 4/3 · **Validação:** OK

**Efeito de combate — Último Suspiro:** Na terceira rodada, recebe +1 de bônus ao entrar em campo. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Conquistada ao vencer um desafio no nível um.

## Divergências automáticas

Nenhuma divergência estrutural encontrada no cruzamento catálogo → motor → site → texto da arte.
