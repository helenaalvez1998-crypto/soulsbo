# Auditoria de fidelidade — catálogo completo de cartas

**Status:** OK  
**Cartas auditadas:** 179  
**Cartas publicadas no site:** 179  
**Cartas no pacote jogável:** 164  
**Novas especiais V77:** 17  
**Habilidades catalogadas:** 82  
**Efeitos de identidade:** 22  
**Habilidades do pool de recompensas dinâmicas:** 13  
**Cartas de líder auditadas em separado:** 12  
**Divergências automáticas:** 0  

## Paridade entre facções

- **Ordem Áurea:** 30 unidades, 11 especiais, 41 cartas no pacote e 3 líderes.
- **Véu Carmesim:** 30 unidades, 11 especiais, 41 cartas no pacote e 3 líderes.
- **Lua Negra:** 30 unidades, 11 especiais, 41 cartas no pacote e 3 líderes.
- **Os Esquecidos:** 30 unidades, 11 especiais, 41 cartas no pacote e 3 líderes.

Títulos: máximo atual de 27 caracteres; limite de 27; acima do limite: 0; duplicados: 0.

## Cobertura por tipo

- Habilidades exclusivas/identidade: 22
- Habilidades de unidade: 59
- Cartas especiais: 44
- Unidades sem habilidade individual, mas com combo: 39
- Sem efeito individual intencional: 15

## Cartas especiais adicionadas na V77

- **Égide da Graça** — Ordem Áurea · `gwent_v77_ord_egide` · efeito `gwent_egide`.
- **Cântico Dourado** — Ordem Áurea · `gwent_v77_ord_hino` · efeito `gwent_chifre`.
- **Silêncio Dourado** — Ordem Áurea · `gwent_v77_ord_silencio` · efeito `gwent_purificar`.
- **Rito Hemático** — Véu Carmesim · `gwent_v77_veu_sangramento` · efeito `gwent_sangramento`.
- **Névoa Rubra** — Véu Carmesim · `gwent_v77_veu_podrida` · efeito `gwent_podrida`.
- **Delírio Carmesim** — Véu Carmesim · `gwent_v77_veu_loucura` · efeito `gwent_loucura`.
- **Sentença Carmesim** — Véu Carmesim · `gwent_v77_veu_execucao` · efeito `gwent_execucao`.
- **Bastião das Ruínas** — Os Esquecidos · `gwent_v77_esq_muralha` · efeito `gwent_muralha`.
- **Cântico dos Fiéis** — Os Esquecidos · `gwent_v77_esq_chifre` · efeito `gwent_chifre`.
- **Misericórdia Final** — Os Esquecidos · `gwent_v77_esq_medico` · efeito `gwent_medico`.
- **Vigília do Relicário** — Os Esquecidos · `gwent_v77_esq_egide` · efeito `gwent_egide`.
- **Procissão dos Fiéis** — Os Esquecidos · `gwent_v77_esq_passo` · efeito `gwent_passo`.
- **Luz na Geada** — Os Esquecidos · `gwent_v77_esq_chama` · efeito `gwent_chama`.
- **Juramento dos Fiéis** — Os Esquecidos · `gwent_v77_esq_vinculo` · efeito `gwent_vinculo`.
- **Sino do Peregrino** — Os Esquecidos · `gwent_v77_esq_batedor` · efeito `gwent_batedor`.
- **Céu sem Cinzas** — Os Esquecidos · `gwent_v77_esq_purificar` · efeito `gwent_purificar`.
- **Bruma Sepulcral** — Os Esquecidos · `gwent_v77_esq_clima` · efeito `gwent_clima`.

## Como ler esta auditoria

O campo **Efeito de combate** reproduz o texto preparado pelo próprio motor `preparar_carta`, incluindo os limites de raridade realmente aplicáveis; ele permanece no site e na interface de jogo. A imagem física da carta imprime apenas a **lore** narrativa no painel inferior: não imprime nome de habilidade, regra, combo ou aviso 'Sem habilidade especial'. Cartas sem habilidade individual continuam podendo participar de combos quando isso estiver listado em suas sinergias.

A cobertura automatizada confirma definição/handler cadastrado para as habilidades do catálogo e para o pool de recompensas geradas dinamicamente, igualdade dos campos mecânicos e sinergias enviados ao site, geração dinâmica do compêndio e encaixe integral da lore nos dois painéis físicos (procedural e template com arte personalizada). O conteúdo de combate é verificado separadamente e nunca é inserido como texto na imagem. A auditoria não substitui testes funcionais de cada combinação possível de tabuleiro; as regras de entrada, efeitos especiais, remoção, fim de rodada e combos permanecem testadas na suíte do projeto.

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

### Abadessa das Ruínas (`lider_abadessa_ruinas`)

**Facção:** Os Esquecidos · **Efeito no motor:** `forgotten_purification`
**Descrição canônica exibida:** Purifica até 2 aliados dos Esquecidos afetados e de maior poder efetivo na fileira escolhida, removendo Sangramento, Geada, Podridão e Loucura. Cada um recebe +1 de bônus.

### Mártir da Vigília (`lider_martir_vigilia`)

**Facção:** Os Esquecidos · **Efeito no motor:** `forgotten_revival`
**Descrição canônica exibida:** Ressuscita do descarte a unidade mais forte dos Esquecidos com poder-base até 5 na fileira escolhida, com +1 de bônus.

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

### Acólito Sanguíneo (`gwent_v75_veu_acolito_sangue`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Marca da Dinastia:** Marca o inimigo de maior poder efetivo na fileira. Na segunda marca, consome Sangramento, reduz 2 de bônus (mín. -2) e esta carta recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um acólito do Palácio de Mohgwyn prepara o altar para os ritos secretos da dinastia e reverencia a chama do sangue.
**Tags de sinergia:** v75_blood_mark
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Adaga da Faca Negra (`gwent_singular_intocavel`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 9 · **Custo:** 0  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Mira Cariana:** Recebe +1 de bônus ao entrar na fileira de Longa Distância. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Forjada para as Assassinas da Faca Negra, a lâmina recebeu um fragmento da Runa da Morte na noite em que Godwyn foi assassinado.

### Algemas de Margit (`reliquia_algemas_margit`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Algemas de Margit:** Na fileira escolhida, zera o bônus positivo do alvo escolhido ou do inimigo com maior bônus. Bônus negativos não mudam; Escudos não bloqueiam o efeito. A ativação consome a Relíquia.
**Lore:** Correntes forjadas para conter o Agouro caído, capazes de subjugar até mesmo um inimigo temível.

### Anjo de Segunda Ordem (`luterano_anjo2`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 5 · **Custo:** 4  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma presença alada atravessa os salões esquecidos, iluminando os vitrais partidos.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Anjo do Último Selo (`gwent_v76_esq_anjo_selo`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Mítica · **Poder-base:** 8 · **Custo:** 5  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O último guardião alado desce diante do portão selado, com as asas abertas sobre os fiéis restantes.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Anjo Esquecido (`luterano_anjo`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 3 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um mensageiro alado atravessa os vitrais partidos da antiga catedral, levando uma luz que quase se apagou.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Aprendiz Cariano (`magia_fagulha`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Um aprendiz da tradição cariana começa a dominar os projéteis de pedra cintilante.

### Apóstolo da Pele Divina (`magia_sol_negro`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Eclipse Devorador:** Ganha +2 se algum inimigo tiver bônus acima de zero. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Devoto da antiga ordem da Pele Divina, empunha a chama negra associada à morte dos deuses.

### Apóstolo Errante (`gwent_unidade_invocador`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Caçador de Feitiços:** Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O apóstolo errante percorre as estradas em busca de manuscritos proibidos, levando consigo os ritos que aprendeu com seus mestres.
**Tags de sinergia:** astral
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Apóstolo Esquecido (`luterano_apostolo`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um pregador percorre as estradas douradas com fragmentos de escrituras antigas.
**Tags de sinergia:** evangelho, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Arauto da Ruína (`patente_6`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Retaliação dos Semideuses:** Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O arauto percorre as fronteiras devastadas e anuncia a queda dos antigos estandartes, reunindo os sobreviventes sob um novo juramento.

### Arauto do Cântico (`gwent_v76_esq_arauto_cantico`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Lendária · **Poder-base:** 7 · **Custo:** 4  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Estandarte:** Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Com um estandarte bordado em prata gasta, o arauto conduz os fiéis através do vale coberto de névoa.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Arauto do Sangue (`gwent_v76_veu_arauto_sangue`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Estandarte:** Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um arauto percorre a procissão carmesim carregando o símbolo da chama sanguínea.
**Tags de sinergia:** banquete, sangue_mohgwyn
**Combos compatíveis:** Banquete de Sangue: Carniceiro da Forja e Intendente dividem o butim (+3).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Arauto Áureo (`gwent_v75_ordem_arauto_estandarte`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** O arauto ergue o estandarte de Leyndell e proclama, diante das muralhas, o juramento que une os defensores à Ordem Áurea.
**Tags de sinergia:** v75_crucible_guard
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Assassina da Faca Negra (`chefe_cacador_sem_rosto`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Uma assassina Numen ligada à Noite das Facas Negras, quando um fragmento da Runa da Morte foi usado para matar Godwyn.

### Assassina de Ravenmount (`gwent_unidade_cacadora_fantasma`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Uma assassina de Ravenmount atravessa a névoa sem deixar rastros fáceis de seguir.
**Tags de sinergia:** fantasmas
**Combos compatíveis:** Procissão dos que Vivem na Morte: Duas unidades fantasmas marcham juntas (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Astróloga de Liurnia (`magia_nevoa_antiga`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Névoa Ancestral:** Ganha +2 se houver efeito climático em qualquer fileira. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sob os céus de Liurnia, uma astróloga procura nas estrelas sinais de destinos ainda ocultos.
**Tags de sinergia:** astral, lua_cariana
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Bastião das Ruínas (`gwent_v77_esq_muralha`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Comum · **Poder-base:** 0 · **Custo:** 1  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Bastião das Ruínas:** Escolha uma fileira: seus aliados nela recebem +1 de bônus até o fim da rodada.
**Lore:** Os últimos guardiões se abrigam sob os arcos quebrados e juram impedir que as ruínas de sua antiga irmandade sejam profanadas.

### Bastião de Leyndell (`gwent_especial_muralha`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Comum · **Poder-base:** 0 · **Custo:** 1  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Bastião de Leyndell:** Escolha uma fileira: seus aliados nela recebem +1 de bônus até o fim da rodada.
**Lore:** As muralhas douradas de Leyndell erguem-se como símbolo da resistência da capital.

### Batedor de Gelmir (`arma_arco_peregrino`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um recusante percorre os caminhos do Monte Gelmir, atento às rotas e aos movimentos dos inimigos.
**Tags de sinergia:** peregrino
**Combos compatíveis:** Caminho do Maculado: Duelista e Batedor de Gelmir coordenam o avanço (+1).

### Besta Prístina (`primordial_origem`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Lei Primeva:** Recebe +2 de bônus ao entrar na primeira rodada. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A Besta Prístina manifesta a vontade que veio além das estrelas e deu forma à ordem dourada.

### Bibliotecária de Raya (`gwent_unidade_bibliotecaria`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Entre os salões da Academia de Raya Lucaria, a bibliotecária guarda os estudos de pedra cintilante e os escritos que sobreviveram às disputas dos sábios.
**Tags de sinergia:** eclipse_voraz
**Combos compatíveis:** Eclipse Sanguíneo: Cavaleiro Sangrento e Bibliotecária eclipsam a mesma fonte (+3).

### Bispo Esquecido (`luterano_bispo`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 5 · **Custo:** 4  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Devoção:** Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Mesmo após a queda das catedrais, o bispo reúne os sobreviventes dos Esquecidos e conduz suas preces entre as colunas partidas do antigo santuário.
**Tags de sinergia:** devocao, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Blaidd, o Meio-Lobo (`gwent_unidade_senhor_cacada`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Vingança:** Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sombra meio-lobo jurada a Ranni, Blaidd protege a princesa lunar desde a infância. A lealdade que o liga a ela o coloca em conflito com o destino imposto pelos Dois Dedos.
**Tags de sinergia:** fantasmas
**Combos compatíveis:** Procissão dos que Vivem na Morte: Duas unidades fantasmas marcham juntas (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Bruma Sepulcral (`gwent_v77_esq_clima`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Bruma Sepulcral:** Escolha uma fileira. Enquanto o clima estiver ativo, todas as unidades dos dois lados nela perdem 1 de poder efetivo (mín. 1); Resistência Climática pode absorver a penalidade.
**Lore:** As criptas dos Esquecidos exalam uma névoa fria; dizem que ela preserva os sussurros dos que foram enterrados sem nome.

### Bênção da Árvore Áurea (`gwent_especial_egide`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Bênção da Árvore Áurea:** Escolha um aliado sem Escudo para receber 1 Escudo; a raridade pode proteger até 3 aliados. Escudos não bloqueiam sacrifícios. Raridade Rara: protege até 2 aliados sem Escudo.
**Lore:** Quando a Graça alcança os santuários de Leyndell, os guardiões renovam seus votos diante da Árvore Áurea e recebem sua bênção dourada.

### Cantor do Último Hino (`gwent_v76_esq_cantor_hino`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sobrevivente:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sua voz ecoa por uma nave vazia enquanto os últimos fiéis abandonam a catedral em ruínas.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Carrasco Carmesim (`gwent_v75_veu_carrasco_preco`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Preço em Sangue:** Sacrifica o aliado de menor poder efetivo da mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +3). Sem aliado, recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O carrasco conduz procissões sob estandartes vermelhos, vestindo as vestes cerimoniais dos guerreiros de Mohgwyn.
**Tags de sinergia:** v75_blood_feast
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Carrasco de Gelmir (`gwent_unidade_carniceiro_forja`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Devorar:** Ao entrar, sacrifica o aliado de menor poder efetivo na mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +4). Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um executor da Mansão Vulcânica veste o aço manchado dos recusantes e serve aos banquetes de Tanith.
**Tags de sinergia:** banquete, sangue_mohgwyn
**Combos compatíveis:** Banquete de Sangue: Carniceiro da Forja e Intendente dividem o butim (+3).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Carrasco do Altar (`gwent_v76_veu_carrasco_altar`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Devorar:** Ao entrar, sacrifica o aliado de menor poder efetivo na mesma fileira e recebe bônus igual ao poder efetivo dele (mín. +1, máx. +4). Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O carrasco executa os ritos de sacrifício no altar rubro, sob os estandartes da dinastia.
**Tags de sinergia:** sangue_mohgwyn, v75_blood_feast
**Combos compatíveis:** Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).; Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Cartógrafo de Nokron (`gwent_v75_lua_cartografo_lunar`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** À luz das estrelas subterrâneas, o cartógrafo registra pontes, aquedutos e passagens ocultas que ligam as ruínas de Nokron.
**Tags de sinergia:** v75_lunar_paths
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Cavaleira Cariana (`gwent_unidade_cavaleira`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** A cavaleira recebeu treinamento nas fileiras da realeza cariana e guarda as passagens de Liurnia com a disciplina dos antigos juramentos lunares.
**Tags de sinergia:** veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).

### Cavaleiro Astral (`gwent_v76_lua_cavaleiro_astral`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Resistência Climática:** Ignora até 2 pontos de penalidade climática; sem clima ativo ao entrar, recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um cavaleiro cariano avança sob uma chuva de cristais sem desviar os olhos do céu noturno.
**Tags de sinergia:** lua_cariana, v75_lunar_paths
**Combos compatíveis:** Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.; Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Cavaleiro Consagrado (`gwent_mitica_coroa`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Mítica · **Poder-base:** 8 · **Custo:** 5  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Estandarte:** Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um cavaleiro consagrado guarda os ramos pálidos do Haligtree, onde a esperança resiste à decadência.

### Cavaleiro da Árvore Áurea (`chefe_guardiao_cinzas`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Égide das Cinzas:** Se já houver um aliado na mesma fileira, ele recebe +1 de bônus e esta carta também recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um sentinela montado patrulha os caminhos que conduzem à Árvore Áurea, impondo a autoridade da capital.
**Tags de sinergia:** cinzas, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Cavaleiro de Leyndell (`chefe_vigia_cinzento`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Um soldado da capital mantém a vigília entre as muralhas erguidas em nome da Ordem Áurea.

### Cavaleiro de Mohgwyn (`covenant_coroa_abismo`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 7 · **Custo:** 4  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Selo Enfraquecedor:** Reduz em 1 o bônus de cada unidade inimiga, até o mínimo de -2. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guerreiro jurado à dinastia sanguínea guarda os domínios ocultos de Mohg.
**Tags de sinergia:** abismo, sangue_mohgwyn
**Combos compatíveis:** Maré Abissal: Godfrey e Cavaleiro Carmesim despertam a mesma força (+2).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Cavaleiro de Radahn (`gwent_unidade_sentinela_rubra`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um cavaleiro da hoste de Radahn mantém sua posição sob o estandarte vermelho de Caelid.
**Tags de sinergia:** muralha, ordem_dourada
**Combos compatíveis:** Defesa de Leyndell: Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Cavaleiro do Abismo (`patente_4`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Nas profundezas onde a luz da Árvore Áurea não alcança, o cavaleiro vigia a passagem entre as ruínas e as trevas antigas.

### Cavaleiro do Crisol (`gwent_unidade_baluarte`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um cavaleiro do Crisol, marcado pelas antigas formas que antecederam a Árvore Áurea, guarda a formação com disciplina.
**Tags de sinergia:** fornalha, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Cavaleiro do Cão de Caça (`chefe_cervo_sombrio`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um cavaleiro errante segue a trilha de presas pelas florestas enevoadas das Terras Intermédias.
**Tags de sinergia:** veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).

### Cavaleiro Draconiano (`gwent_unidade_veterano_cercos`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Revestido de escamas e armadura dourada, o cavaleiro draconiano guarda os acessos da capital; seus golpes carregam o trovão dos dragões ancestrais.
**Tags de sinergia:** muralha
**Combos compatíveis:** Defesa de Leyndell: Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Cavaleiro Penitente (`gwent_v76_esq_cavaleiro_penitente`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Escudo de Ferro:** Entra com 1 Escudo, que bloqueia a primeira tentativa de remoção; sacrifícios ignoram Escudos.
**Lore:** Um cavaleiro cobre o próprio escudo com cinzas e guarda a passagem de uma capela soterrada.
**Tags de sinergia:** fe, irmandade
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Cavaleiro Sangrento (`gwent_unidade_devorador_mana`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um cavaleiro ligado ao sangue de Mohg participa dos rituais sombrios da dinastia subterrânea.
**Tags de sinergia:** eclipse_voraz, sangue_mohgwyn
**Combos compatíveis:** Eclipse Sanguíneo: Cavaleiro Sangrento e Bibliotecária eclipsam a mesma fonte (+3).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Cavaleiros de Radahn (`covenant_lobos_cinza`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Veteranos da hoste do Flagelo das Estrelas, marcham sob o estandarte do general de Caelid.
**Tags de sinergia:** cinzas
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).

### Cavaleiros Juramentados (`covenant_ultimos`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Combatentes unidos por juramentos de sangue permanecem ao lado de seu senhor até o último fôlego.

### Caçador de Almas (`patente_3`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** O caçador segue os rastros deixados pelos espíritos inquietos e recolhe as almas que vagam sem descanso.

### Caçador de Dedos (`gwent_unidade_lamina_sem_juramento`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Entre as trilhas esquecidas das Terras Intermédias, o caçador segue o rastro dos emissários dos Dois Dedos e evita qualquer juramento que limite sua caça.

### Caçador de Mohgwyn (`gwent_v75_veu_cacador_sangue`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** O caçador patrulha os salões do Palácio de Mohgwyn, seguindo os rastros deixados pelos ritos sangrentos da dinastia.
**Tags de sinergia:** v75_blood_mark
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Chama do Gigante (`elden_especial_chama`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Chama do Gigante:** Remove Geada de todos os aliados afetados; cada unidade purificada recebe +1 de bônus até o fim da rodada. A raridade pode ampliar esses bônus. Raridade Rara: acrescenta +1 de bônus a até 1 aliados purificados.
**Lore:** Nos Picos dos Gigantes, o último de sua linhagem guarda a chama eterna da Forja, cujo poder ainda pode incendiar a Árvore Áurea.

### Chama Frenética (`elden_especial_loucura`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Loucura Frenética:** Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda zera bônus positivos. Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.
**Lore:** A chama oferecida pelos Três Dedos invade os olhos dos que a contemplam e reduz vontade, carne e lembranças a um único caos ardente.

### Chama Negra (`gwent_especial_queima`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Chama Negra:** Em cada lado, tenta remover a unidade de maior poder efetivo. Escudo bloqueia a remoção; se ela ocorrer, gatilhos de queda são resolvidos. Raridade Épica: reforça bônus gerados por efeitos de queda em até 1 alvo; não amplia remoções nem atravessa Escudos.
**Lore:** A chama negra nasceu do poder da Runa da Morte e foi usada pelos Apóstolos da Pele Divina para caçar os próprios deuses.

### Chamado dos Mortos (`gwent_especial_requiem`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Chamado dos Mortos:** Traz do descarte diretamente ao campo uma unidade escolhida com poder-base até 6; a raridade pode elevar esse limite até 9. Raridade Épica: o limite de poder-base sobe até 7.
**Lore:** Um cântico atravessa as catacumbas e ecoa entre os nomes que a história tentou apagar.

### Cinzas Novatas (`patente_1`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Caçador de Feitiços:** Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo.
**Lore:** Recém-chegado às capelas abandonadas, o novato aprende com os guardiões a preservar a chama entre as cinzas.

### Confessor Velado (`gwent_v76_esq_confessor_velado`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Devoção:** Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sob um capuz de linho, o confessor ouve os últimos arrependimentos dos viajantes que chegam à cripta.
**Tags de sinergia:** devocao, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Confessora da Graça (`gwent_v75_ordem_confessora_graca`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Regressão Serena:** Purifica até 2 aliados da fileira de Sangramento, Geada, Podridão ou Loucura; cada um recebe +1. Se ninguém precisar, o aliado mais fraco recebe +1; sem aliados, esta carta recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma Confessora percorre os caminhos de Leyndell em silêncio, levando os ensinamentos da Lei da Regressão aos santuários esquecidos.
**Tags de sinergia:** v75_erdtree_oath
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Confessora da Ordem Áurea (`magia_selo_vigilia`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Selo de Vigília:** Esta carta recebe Resistência Climática 1. Se houver aliado na mesma fileira, o primeiro recebe +1 de bônus. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Treinada para agir discretamente, a Confessora combina devoção, infiltração e combate próximo.

### Coroa do Lorde Prístino (`gwent_singular_cacador_chefes`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 9 · **Custo:** 0  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Paradoxo Eterno:** Na terceira rodada, recebe +2 de bônus se o adversário venceu a rodada anterior. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A coroa relembra o reinado de Godfrey, o Primeiro Lorde Prístino, e os guerreiros que abriram caminho para o domínio da Árvore Áurea.

### Cruzado Esquecido (`luterano_cruzado`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guerreiro sagrado guarda as estradas em ruínas e carrega no escudo o símbolo de uma ordem que já não existe.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Cântico dos Fiéis (`gwent_v77_esq_chifre`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Cântico dos Fiéis:** Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada. Raridade Rara: acrescenta +1 de bônus a até 1 aliados afetados.
**Lore:** Nas ruínas, os fiéis entoam o último cântico da irmandade e preservam uma tradição que o tempo tentou apagar.

### Cântico Dourado (`gwent_v77_ord_hino`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Cântico Dourado:** Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada. Raridade Rara: acrescenta +1 de bônus a até 1 aliados afetados.
**Lore:** O coro dos sacerdotes atravessa as muralhas de Leyndell, celebrando a ordem estabelecida sob a luz da Árvore Áurea.

### Cão Rubro (`gwent_v76_veu_cao_rubro`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Instinto de Caçador:** Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária.
**Lore:** Um cão de guerra fareja intrusos entre as muralhas úmidas do palácio de Mohgwyn.
**Tags de sinergia:** banquete, sangue_mohgwyn
**Combos compatíveis:** Banquete de Sangue: Carniceiro da Forja e Intendente dividem o butim (+3).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Céu sem Cinzas (`gwent_v77_esq_purificar`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Céu sem Cinzas:** Remove o clima ativo das três fileiras para os dois jogadores.
**Lore:** Quando o último hino ecoa pelos vitrais partidos, as nuvens se afastam e a cinza deixa de cobrir os santuários dos Esquecidos.

### Delírio Carmesim (`gwent_v77_veu_loucura`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Delírio Carmesim:** Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda zera bônus positivos. Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.
**Lore:** Nos salões de Mohgwyn, os devotos entoam um cântico febril à Mãe Sem Forma e se perdem no êxtase do sangue.

### Devota da Hemorragia (`gwent_v75_veu_devota_hemorragia`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** A devota ajoelha-se diante do altar de Mohgwyn e oferece seu sangue à dinastia que aguarda o nascimento de uma nova era.
**Tags de sinergia:** v75_blood_feast
**Combos compatíveis:** Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Diaconisa do Altar (`gwent_v76_esq_diaconisa_altar`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Ritmo de Combate:** Ao entrar em campo, recebe +1 de bônus. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A diaconisa prepara o altar com cálices antigos e conduz um rito antes da chegada dos invasores.
**Tags de sinergia:** devocao, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Discípulo da Academia (`gwent_unidade_circulo`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Discípulo de Raya Lucaria, dedica-se ao estudo dos círculos arcanos e dos resíduos de feitiçaria.
**Tags de sinergia:** astral
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Discípulos do Fogo (`covenant_filhos_brasa`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Seguidores dos antigos monges preservam a chama dos gigantes e seus rituais esquecidos.

### Diácono Esquecido (`luterano_diacon`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Nas capelas dos Esquecidos, o diácono alimenta as lamparinas do altar e conduz os ritos que os sacerdotes já não conseguem manter.
**Tags de sinergia:** diaconia, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Dragoeiro Ancião (`magia_trovao_oco`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Descarga Oca:** Cada inimigo na mesma fileira perde 1 de bônus (mín. -2). Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guerreiro ligado aos antigos dragões canaliza relâmpagos ancestrais em meio à batalha.

### Duelista da Casa Hoslow (`arma_lamina_peregrino`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Herdeiro de uma casa de duelistas, transforma a elegância do aço em uma promessa de sangue.
**Tags de sinergia:** peregrino
**Combos compatíveis:** Caminho do Maculado: Duelista e Batedor de Gelmir coordenam o avanço (+1).

### Erudito da Academia (`magia_orbe_eco`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Pesquisador de Raya Lucaria, dedica a vida ao estudo dos segredos das pedras cintilantes.
**Tags de sinergia:** eco
**Combos compatíveis:** Eco das Pedras Cintilantes: O Erudito das Pedras e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Erudito das Pedras (`gwent_unidade_eco`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um estudioso das pedras cintilantes investiga as ressonâncias deixadas por feitiçarias antigas.
**Tags de sinergia:** astral, eco
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).

### Espada da Noite e da Chama (`reliquia_noite_chama`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Lendária · **Poder-base:** 0 · **Custo:** 4  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Espada da Noite e da Chama:** Noite: aplica 1 marca de Geada (máx. 2) a todos os inimigos da fileira escolhida. Chama: atinge o inimigo de maior poder efetivo na fileira, reduzindo 1 de poder-base (mín. 1) e 2 de bônus. Escudo bloqueia o golpe; a Relíquia é consumida.
**Lore:** Herança da família real cariana, a espada preserva duas tradições arcanas antigas: a feitiçaria da noite e a chama dos gigantes.

### Espadachim da Lua Negra (`arma_duas_luas`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Dança Espelhada:** Ganha +1 se você tiver outro aliado em uma fileira diferente. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Formado nas artes marciais da realeza cariana, o espadachim treina seus golpes sob a luz fria da Lua Negra e protege os caminhos de Liurnia.
**Tags de sinergia:** duas_luas, lua_cariana
**Combos compatíveis:** Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Executor Sombrio (`patente_7`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Caçador de Feitiços:** Recebe +1 de bônus ao entrar se o adversário tiver uma unidade da Lua Negra ou qualquer unidade com bônus positivo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sob o manto da noite, o executor cumpre as sentenças que os senhores das Terras Intermédias preferem manter ocultas.

### Exploradora de Nokron (`gwent_unidade_cartografa`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Sob o céu subterrâneo de Nokron, a exploradora mapeia pontes suspensas e passagens ocultas entre os palácios em ruínas.
**Tags de sinergia:** duas_luas
**Combos compatíveis:** Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).

### Feiticeira da Lua Gélida (`magia_chama_fria`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** A feiticeira percorre Liurnia estudando as artes gélidas dos antigos astrólogos e os encantamentos lunares preservados pela realeza cariana.
**Tags de sinergia:** chama
**Combos compatíveis:** Chamas do Monte Gelmir: Piromante e Feiticeira da Lua Gélida equilibram suas chamas (+2).

### Feiticeiro Cariano (`arma_cajado_marulho`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Discípulo da realeza cariana, conjura feitiçarias de pedra cintilante sob a proteção da lua.

### Ferreiro de Gelmir (`gwent_unidade_mestre_forja`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um mestre ferreiro de Volcano Manor trabalha entre brasas, aço e os juramentos dos recusantes.
**Tags de sinergia:** fornalha, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Ferreiro Vulcânico (`arma_martelo_fornalha`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Entre fornalhas e juramentos de traição, um artesão molda armas para os recusantes do Monte Gelmir.

### Fia, Leito de Morte (`gwent_unidade_cantora_lamentos`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Fia, Companheira do Leito de Morte, entoa lamentos pelos que encontraram repouso entre os mortos.
**Tags de sinergia:** fantasmas
**Combos compatíveis:** Procissão dos que Vivem na Morte: Duas unidades fantasmas marcham juntas (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Flagelante de Mohgwyn (`gwent_v76_veu_flagelante`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Legado:** Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um penitente percorre os degraus do palácio sanguíneo, deixando marcas vermelhas na pedra.
**Tags de sinergia:** sangue_mohgwyn, v75_blood_mark
**Combos compatíveis:** Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).; Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Flor da Podridão Escarlate (`elden_especial_podrida`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Podridão Escarlate:** Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda reduz 1 de bônus positivo (mín. 0). Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Épica: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.
**Lore:** Na planície de Aeonia, a florescência de Malenia deixou uma flor escarlate; desde então, a Podridão se espalha pelas terras feridas de Caelid.

### Geada dos Picos (`gwent_especial_geada`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Lua Gélida:** Todas as unidades inimigas recebem 1 marca de Geada; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada.
**Lore:** O vento que desce dos Picos dos Gigantes congela os caminhos e cobre de gelo as ruínas esquecidas.

### Gigante de Fogo (`gwent_unidade_gigante`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Instinto de Caçador:** Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Último de sua linhagem, o Gigante de Fogo guarda a chama primordial nos Picos dos Gigantes e carrega o dever de impedir que ela se apague.

### Godfrey, Primeiro Lorde (`chefe_rei_afogado`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 7 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Dízimo do Abismo:** Recebe +2 se houver qualquer carta no seu descarte; caso contrário, recebe +1 se o adversário tiver mais unidades em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Primeiro Lorde Prístino e consorte de Marika, Godfrey liderou os guerreiros que conquistaram as Terras Intermédias.
**Tags de sinergia:** abismo, sangue_mohgwyn
**Combos compatíveis:** Maré Abissal: Godfrey e Cavaleiro Carmesim despertam a mesma força (+2).; Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).

### Godwyn, o Dourado (`gwent_unidade_herdeiro_portao`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Vingança:** Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O príncipe dourado foi amado por dragões e homens; sua queda marcou a primeira rachadura irreversível no destino das Terras Intermédias.
**Tags de sinergia:** muralha, ordem_dourada
**Combos compatíveis:** Defesa de Leyndell: Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Grande Runa de Godrick (`reliquia_grande_runa_godrick`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Lendária · **Poder-base:** 0 · **Custo:** 4  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Grande Runa de Godrick:** Exige ao menos 1 unidade aliada em campo. Concede +1 de bônus a todas as unidades aliadas; uso único por partida.
**Lore:** Fragmento do Anel Prístino reivindicado por Godrick, o Enxertado, que buscava poder por meio do enxerto.

### Graviturgista de Nokron (`gwent_v75_lua_graviturgista`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Cisalhamento Gravitacional:** Até 2 inimigos com bônus positivo na fileira perdem 1 (mín. -2). Se atingir 2 alvos, esta carta recebe +1. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um astrólogo das Cidades Eternas estuda as correntes gravitacionais que sustentam as ruínas suspensas de Nokron.
**Tags de sinergia:** v75_frost_lore
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Guardas da Árvore Áurea (`covenant_irmandade_ferro`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Retaliação dos Semideuses:** Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária.
**Lore:** Defensores juramentados protegem os caminhos e santuários consagrados à Árvore Áurea.
**Tags de sinergia:** estandarte
**Combos compatíveis:** Juramento de Leyndell: Porta-estandarte e Guardas da Árvore Áurea fortalecem a formação (+1 para a carta participante que ativa o combo e +1 aos aliados na mesma fileira).

### Guardiã do Juramento Lunar (`gwent_v75_lua_guardia`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Épica: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** A guardiã preserva os antigos pactos da realeza cariana e vigia os caminhos escolhidos por Ranni sob a luz fria da lua.
**Tags de sinergia:** v75_lunar_paths
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Guardiã do Santuário (`gwent_v76_esq_guardia_santuario`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Guardião da Fileira:** Ao entrar, recebe +1 de bônus por aliado na mesma fileira (máx. +3). Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma defensora vigia o altar de pedra e mantém a entrada do santuário livre de profanadores.
**Tags de sinergia:** fe, sacerdos
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Guardião da Ordem Áurea (`gwent_unidade_guardiao_runas`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um guardião da Ordem Áurea carrega inscrições rúnicas ligadas aos ensinamentos da capital.
**Tags de sinergia:** runico
**Combos compatíveis:** Ritual das Runas: Duas unidades rúnicas completam o círculo (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Guardião das Cinzas (`patente_5`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Postura Encadeada:** Recebe +2 de bônus se entrar na mesma fileira da sua última unidade jogada. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Diante dos altares cobertos de cinza, o guardião protege a última brasa da irmandade.

### Guardião do Crisol Menor (`gwent_v75_ordem_guardiao_crisol`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** O guardião carrega as marcas do Crisol, vestígios das formas primordiais que existiam antes de a Árvore Áurea moldar a ordem das Terras Intermédias.
**Tags de sinergia:** v75_crucible_guard
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Guardião do Graal (`gwent_v76_ordem_guardiao_graal`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Guardião da Fileira:** Ao entrar, recebe +1 de bônus por aliado na mesma fileira (máx. +3). Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Nos salões inferiores de Leyndell, o guardião jurou proteger o cálice consagrado que os sacerdotes ocultaram durante a queda da capital.
**Tags de sinergia:** muralha, ordem_dourada
**Combos compatíveis:** Defesa de Leyndell: Duas unidades da Muralha Rubra erguem a linha (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Guardião do Relicário (`gwent_v76_esq_guardiao_relicario`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 7 · **Custo:** 4  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Ressurgir:** Ao entrar, traz do seu descarte ao campo a unidade elegível de maior poder-base até 5; ela retorna sem bônus nem Escudo. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guardião protege as relíquias da ordem numa câmara selada sob a antiga catedral.
**Tags de sinergia:** fe, sacerdos
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Guardião dos Vitrais (`gwent_v76_esq_guardiao_vitrais`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Estandarte:** Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira.
**Lore:** Um sentinela permanece diante dos vitrais partidos, protegendo os símbolos de uma fé quase apagada.
**Tags de sinergia:** fe, sacerdos
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Guardiões de Sellia (`covenant_sentinelas`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Vigias da cidade oculta de Sellia protegem seus segredos e as passagens de feitiçaria.

### Guerreiro Caído (`patente_2`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Mesmo após a derrota, o guerreiro permanece ligado ao juramento que o levou à batalha e se recusa a abandonar seus companheiros.

### Guerreiro Frenético (`gwent_unidade_detonador`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Vingança:** Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A chama frenética tomou-lhe os olhos e apagou o nome que um dia teve; agora, ele vagueia pelas Terras Intermédias sob a influência dos Três Dedos.
**Tags de sinergia:** runico
**Combos compatíveis:** Ritual das Runas: Duas unidades rúnicas completam o círculo (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Gurranq, Clérigo Bestial (`chefe_oraculo_ruina`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 7 · **Custo:** 4  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Presságio da Ruína:** A unidade inimiga de maior poder efetivo perde 1 de bônus (mín. -2). Se sua pontuação estiver menor ao entrar, esta carta recebe +1. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O clérigo bestial consome Raiz da Morte e guarda um segredo ligado à própria Runa da Morte.

### Gêmeas da Cidade Eterna (`gwent_unidade_dupla_veu`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 2 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Duas irmãs das Cidades Eternas percorrem caminhos subterrâneos que raramente aparecem nos mapas.
**Tags de sinergia:** duas_luas, veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).; Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).

### Irmã das Ruínas (`gwent_v76_esq_irma_ruinas`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Uma irmã recolhe velas e fragmentos de escritura nas galerias abandonadas do antigo mosteiro.
**Tags de sinergia:** fe, irmandade
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Irmão Esquecido (`luterano_irmao`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um peregrino humilde permanece ao lado de sua irmandade, mesmo quando todos os demais recuam.
**Tags de sinergia:** fe, irmandade
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Juramentada de Ranni (`covenant_lua_velada`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Aliança Lunar:** Esta carta recebe +1. O aliado de menor poder efetivo em outra fileira também recebe +1 de bônus, se existir. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma aliada juramentada à princesa lunar acompanha sua busca por um caminho além da Ordem Áurea.
**Tags de sinergia:** duas_luas, lua_cariana
**Combos compatíveis:** Dança da Lua Negra: Dançarina, Gêmea ou Cartógrafa sincronizam seus movimentos (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Juramento do Crisol (`gwent_especial_vinculo`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Juramento do Crisol:** Escolha uma fileira com ao menos 2 aliados. Todas as unidades aliadas nela recebem +2 de bônus até o fim da rodada. Raridade Rara: acrescenta +1 de bônus a até 1 aliados afetados.
**Lore:** Um juramento ancestral une os guerreiros às formas primordiais que precederam a Erdtree.

### Juramento dos Fiéis (`gwent_v77_esq_vinculo`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Juramento dos Fiéis:** Escolha uma fileira com ao menos 2 aliados. Todas as unidades aliadas nela recebem +2 de bônus até o fim da rodada. Raridade Épica: acrescenta +1 de bônus a até 1 aliados afetados.
**Lore:** Os sobreviventes repetem o juramento dos antigos monges diante do altar vazio, preservando uma fé que já não encontra templos.

### Juramento Primordial (`gwent_singular_primeiro`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 10 · **Custo:** 0  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Caçador Solitário:** Recebe +2 de bônus ao entrar se não houver outro aliado na mesma fileira. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O juramento foi selado quando o Crisol ainda reunia as formas primordiais da vida, antes de a ordem dourada definir as fronteiras do mundo.

### Ladina da Cidade Eterna (`gwent_unidade_saqueadora_veu`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Nas passagens ocultas de Nokron, a ladina recolhe relíquias esquecidas e evita os sentinelas que guardam a Cidade Eterna.
**Tags de sinergia:** caravana
**Combos compatíveis:** Saque da Cidade Eterna: Saqueadora e Contrabandista fecham o negócio (+2).

### Lanceiro da Árvore Áurea (`arma_lanca_fornalha`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Treinado para defender os domínios da Árvore Áurea, avança com lança e disciplina militar.

### Lei da Regressão (`gwent_especial_purificar`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Lei da Regressão:** Remove o clima ativo das três fileiras para os dois jogadores.
**Lore:** A Lei da Regressão revela a verdade por trás das ilusões e desfaz os véus que encobrem o mundo.

### Leitora de Sellia (`arma_agulha_astro`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 3 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Uma estudiosa de Sellia observa os astros e procura caminhos ocultos na feitiçaria noturna.
**Tags de sinergia:** astral, lua_cariana
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Lenda do Coliseu (`patente_9`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Ímpeto do Lorde:** Recebe +1 de bônus ao entrar se sua pontuação estiver acima da adversária. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Seu nome atravessa as arquibancadas e chega aos confins das Terras Intermédias; no Coliseu, cada vitória passa a integrar a memória dos combatentes.

### Lobos Solitários (`elden_especial_invocacao`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Lobos Solitários:** Escolha uma fileira e invoque Lobos Espirituais nela com 3 de poder; a raridade pode elevar o poder da invocação até 6. Raridade Rara: invoca Lobos Espirituais com 4 de poder.
**Lore:** Cinzas antigas despertam os espíritos de lobos que outrora caçaram ao lado de seus mestres.

### Lua Cheia de Rennala (`elden_especial_geada`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Geada Cariana:** Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Geada; cada marca reduz 1 de poder efetivo até o fim da rodada. A raridade pode aplicar a segunda marca imediatamente a até 3 alvos. Raridade Rara: aplica a segunda marca imediatamente a até 1 alvos sem Geada prévia.
**Lore:** A lua cheia de Rennala ilumina o campo com a frieza ancestral da realeza cariana.

### Luz na Geada (`gwent_v77_esq_chama`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Luz na Geada:** Remove Geada dos aliados afetados; cada unidade purificada recebe +1 de bônus até o fim da rodada. A raridade pode ampliar esses bônus. Raridade Rara: acrescenta +1 de bônus a até 1 aliados purificados.
**Lore:** Entre os Esquecidos, uma chama pálida é mantida acesa nos invernos mais cruéis, lembrando aos peregrinos que ainda existe abrigo.

### Lágrima Sagrada (`gwent_especial_medico`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Lágrima Sagrada:** Devolve à sua mão uma unidade escolhida do seu descarte com poder-base até 4; a raridade pode elevar esse limite até 7. Raridade Rara: o limite de poder-base sobe até 5.
**Lore:** Uma lágrima consagrada guarda a memória dos que tombaram e ainda podem retornar à jornada.

### Lâmina da Morte Destinada (`gwent_especial_execucao`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Lâmina da Morte Destinada:** Escolha uma fileira e um inimigo nela com poder efetivo até 6. Tenta removê-lo; Escudo pode bloquear. Se a remoção ocorrer, gatilhos de queda são resolvidos. A raridade eleva o limite até 9. Raridade Épica: alcança poder efetivo até 7; pode reforçar bônus gerados por efeitos de queda em até 1 alvo.
**Lore:** A lâmina fragmentada carrega a Morte Destinada que Maliketh selou, lembrança de uma força capaz de pôr fim até à imortalidade dos semideuses.

### Lâmina Hemática (`gwent_v76_veu_lamina_hemantica`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Contragolpe:** Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma duelista da dinastia sanguínea desembainha uma lâmina estreita diante do altar de Mohgwyn.
**Tags de sinergia:** sangue_mohgwyn, v75_blood_mark
**Combos compatíveis:** Ritual do Véu Carmesim: Duas unidades do Véu Carmesim fortalecem a carta participante que ativa o ritual (+2) e os aliados na fileira (+1).; Banquete da Hemorragia: Uma marca aberta alimenta o ritual: a carta participante que ativa o combo recebe +2.

### Lâmina Negra (`reliquia_lamina_negra`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Mítica · **Poder-base:** 0 · **Custo:** 5  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 3/2 · **Validação:** OK

**Efeito de combate — Lâmina Negra:** Na fileira escolhida, reduz em 3 o bônus do alvo escolhido ou, sem alvo, do inimigo de maior poder efetivo. Escudo é consumido e bloqueia o efeito sem consumir a Relíquia.
**Lore:** Maliketh empunha a Lâmina Negra para manter selada a Morte Destinada, poder que Marika confiou ao seu guardião para sustentar a ordem sem morte.

### Lâmina Negra Errante (`chefe_aparicao_veio`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Uma figura encapuzada atravessa as sombras, deixando apenas o rumor de uma lâmina silenciosa.
**Tags de sinergia:** veu_sombrio
**Combos compatíveis:** Caçada da Faca Negra: Duas unidades do Véu Sombrio entram em sintonia (+2).

### Malenia, Lâmina de Miquella (`chefe_malenia_lamina_miquella`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Corpo a corpo  
**Raridade:** Primordial · **Poder-base:** 9 · **Custo:** 6  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 6/6 · **Validação:** OK

**Efeito de combate — Flor Escarlate:** Cada inimigo da fileira recebe 1 marca de Podridão (máx. 2); cada marca reduz 1 de poder efetivo. Ao atingir 2, bônus positivo perde 1 (mín. 0). Primordial: até 3 alvos nessa transição perdem mais 1 (mín. -2). Não reduz de novo com 2 marcas.
**Lore:** Malenia, Empírea nascida sob a Podridão Escarlate, é filha de Marika e Radagon e irmã gêmea de Miquella. Treinada por um espadachim cego, tornou-se a Lâmina de Miquella e protegeu o irmão em Elphael. Com a Mão de Malenia e suas próteses douradas, enfrentou Radahn em Caelid e liberou a florescência que cobriu a região com Podridão Escarlate. Esta carta retrata Malenia antes de sua transformação em Deusa da Podridão.

### Maliketh, Guardião da Morte (`primordial_eternidade`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Paradoxo Eterno:** Na terceira rodada, recebe +2 de bônus se o adversário venceu a rodada anterior. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Maliketh guarda a Morte Destinada, o poder cuja ausência sustenta a ordem sem morte de Marika.

### Maliketh, Lâmina Negra (`chefe_maliketh_morte_destinada`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Morte Destinada:** Ao entrar, o inimigo de maior poder efetivo perde 2 de bônus (mín. -2). Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sombra leal de Marika e guardião da Runa da Morte, carrega a Morte Destinada selada em sua lâmina.

### Marika, Rainha Eterna (`primordial_trono`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Decreto Soberano:** Ao entrar, reduz em 2 o bônus de todas as unidades inimigas (mín. -2). Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Marika, a Rainha Eterna, ergueu a ordem dourada e rompeu o Anel Prístino, mudando para sempre as Terras Intermédias.

### Mercador Nômade (`gwent_unidade_intendente`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um mercador nômade percorre as Terras Intermédias levando provisões e notícias entre assentamentos.
**Tags de sinergia:** banquete
**Combos compatíveis:** Banquete de Sangue: Carniceiro da Forja e Intendente dividem o butim (+3).

### Messmer, o Empalador (`chefe_messmer_impalador`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Lança do Impalador:** Ao entrar, cada inimigo da fileira recebe 1 marca de Sangramento. A segunda marca consome as marcas e causa -2 de bônus (mín. -2); estados expiram no fim da rodada. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Filho de Marika e senhor da chama impura, comandou a purga que devastou o Reino das Sombras.

### Miasma da Podridão (`gwent_especial_nevoa`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Névoa de Sellia:** Escolha uma fileira inimiga. Cada unidade nela recebe 1 marca de Podridão Escarlate; cada marca reduz 1 de poder efetivo, até 2 marcas. Raridades Lendárias ou superiores aplicam a segunda marca imediatamente. As marcas acabam no fim da rodada.
**Lore:** O hálito dos pântanos de Caelid carrega esporos da Podridão Escarlate, transformando o ar em uma névoa difícil de atravessar.

### Misericórdia Final (`gwent_v77_esq_medico`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Misericórdia Final:** Devolve à sua mão uma unidade escolhida do seu descarte com poder-base até 4; a raridade pode elevar esse limite até 7. Raridade Rara: o limite de poder-base sobe até 5.
**Lore:** Nas catacumbas dos Esquecidos, uma irmã recolhe os que tombaram e pronuncia a última prece antes de conduzi-los de volta à irmandade.

### Missionário Esquecido (`luterano_missionario`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Nas capelas esquecidas, este missionário preserva escrituras da antiga irmandade e mantém seus ritos vivos entre os poucos fiéis que restaram.
**Tags de sinergia:** evangelho, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Monge do Fogo (`magia_brasa_errante`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 4 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Devoto do fogo dos gigantes, preserva ritos antigos nas encostas geladas dos Picos dos Gigantes.
**Tags de sinergia:** chama
**Combos compatíveis:** Chamas do Monte Gelmir: Piromante e Feiticeira da Lua Gélida equilibram suas chamas (+2).

### Mártir Cinzento (`gwent_v76_esq_martir_cinzento`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Vingança:** Quando esta unidade é removida, cada aliado da mesma fileira recebe +1 de bônus. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Ferido diante do relicário, o mártir permanece de pé para impedir que a chama sagrada se apague.
**Tags de sinergia:** fe, irmandade
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Mãe Sem Forma (`primordial_abismo`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Fome do Abismo:** Recebe +2 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A Mãe Sem Forma é venerada pelos seguidores de Mohg como origem do poder sanguíneo.

### Místico Esquecido (`luterano_mistico`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Devoção:** Recebe +1 de bônus ao entrar se já houver pelo menos 2 outras unidades da mesma facção em campo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um intérprete de sinais antigos contempla as estrelas sobre as ruínas de Sellia.
**Tags de sinergia:** devocao, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Névoa Rubra (`gwent_v77_veu_podrida`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Névoa Rubra:** Escolha uma fileira inimiga. Cada marca reduz 1 de poder efetivo; a segunda reduz 1 de bônus positivo (mín. 0). Marcas expiram no fim da rodada; a raridade antecipa marcas. Raridade Rara: aplica a segunda marca imediatamente a até 1 alvos sem marca prévia; reforça reduções de bônus causadas, até -2.
**Lore:** Uma névoa escarlate paira sobre o Palácio de Mohgwyn, nascida dos ritos que oferecem sangue à Mãe Sem Forma.

### Oráculo Gélido de Sellia (`gwent_v75_lua_oraculo_geada`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Presságio da Geada:** O inimigo de maior poder efetivo na fileira recebe 1 marca de Geada (máx. 2). Se já tinha marca, esta carta recebe +1. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma astróloga de Sellia lê presságios nas lâminas de gelo que se formam sobre as águas imóveis da cidade.
**Tags de sinergia:** v75_frost_lore
**Combos compatíveis:** Convergência da Geada Lunar: Geada e leitura das fileiras entram em ressonância: a carta participante que ativa o combo recebe +2.

### Oráculo Silencioso (`gwent_v76_esq_oraculo_silencioso`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Eco Arcano:** Recebe +2 de bônus ao entrar se houver ao menos uma carta especial no seu descarte. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Entre colunas rachadas, um oráculo interpreta inscrições que sobreviveram à queda do santuário.
**Tags de sinergia:** fe, sacerdos
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Papa Esquecido (`luterano_papa`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Mítica · **Poder-base:** 7 · **Custo:** 5  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Sumo sacerdote dos Esquecidos, governa uma ordem que sobreviveu à queda de seus templos.
**Tags de sinergia:** fe, soberania
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Passo do Cão de Caça (`gwent_especial_batedor`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Passo do Cão de Caça:** Compra 1 carta da reserva; a raridade pode elevar a compra para 2, se houver cartas disponíveis. Raridade Rara: compra até 2 cartas da reserva.
**Lore:** Os Cavaleiros do Cão de Caça perseguem suas presas sem hesitação; seu passo silencioso os conduz pelas sombras antes que o alvo perceba a aproximação.

### Passo do Lobo (`gwent_especial_passo`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Passo do Lobo:** Escolha uma fileira e mova para ela uma unidade aliada que esteja em outra fileira. Raridade Rara: move até 2 aliados.
**Lore:** Nas terras devastadas de Caelid, os lobos seguem rastros de sangue entre ruínas e desfiladeiros, alcançando presas que julgavam ter escapado.

### Pastor Esquecido (`luterano_pastor`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Legado:** Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guia errante conduz os fiéis por trilhas esquecidas e capelas abandonadas.
**Tags de sinergia:** fe, irmandade
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Peregrino das Cinzas (`gwent_v76_esq_peregrino_cinza`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Legado:** Recebe +2 de bônus ao entrar se você venceu a rodada imediatamente anterior.
**Lore:** Um viajante cruza estradas cobertas de cinza levando consigo as últimas páginas de um evangelho perdido.
**Tags de sinergia:** evangelho, fe
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Peregrinos de Nokron (`covenant_peregrinos_nevoa`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** Viajantes das cidades subterrâneas cruzam a escuridão em busca de uma nova estrela.

### Placidusax, Lorde Dragão (`chefe_placidusax_lorde_dragao`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 9 · **Custo:** 6  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Tempestade do Tempo:** Ao entrar, cada inimigo da fileira recebe 1 marca de Geada (máx. 2); esta carta recebe +1 por inimigo atingido, até +3. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Lorde Dragão ancestral que aguarda, em Farum Azula, o retorno de seu deus desaparecido.

### Placidusax, Senhor Dragão (`primordial_tempestade`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 8 · **Custo:** 6  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Olho da Tempestade:** Recebe +2 de bônus ao entrar se sua fileira estiver sob clima ativo. Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Placidusax, antigo lorde dos dragões, permanece suspenso no tempo em Farum Azula.

### Porta-estandarte Áureo (`gwent_unidade_portaestandarte`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 3 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** O estandarte de Leyndell reúne soldados dispersos sob o símbolo dourado da capital.
**Tags de sinergia:** estandarte, fornalha, ordem_dourada
**Combos compatíveis:** Aliança da Árvore Áurea: Um Cavaleiro da Árvore Áurea (ou de Radahn) e uma unidade da Fornalha, em cartas distintas, coordenam a formação (+2).; Juramento de Leyndell: Porta-estandarte e Guardas da Árvore Áurea fortalecem a formação (+1 para a carta participante que ativa o combo e +1 aos aliados na mesma fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Prelado das Ruínas (`gwent_v76_esq_prelado_ruinas`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O prelado reúne os sobreviventes sob os arcos desmoronados e ergue o antigo selo da irmandade.
**Tags de sinergia:** fe, soberania
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Procissão dos Fiéis (`gwent_v77_esq_passo`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Procissão dos Fiéis:** Escolha uma fileira e mova para ela uma unidade aliada que esteja em outra fileira; a raridade pode mover até 3. Raridade Rara: move até 2 aliados.
**Lore:** Sob estandartes gastos, os sobreviventes cruzam as ruínas em procissão e mantêm viva a fé que ainda os reúne.

### Profeta de Liurnia (`gwent_unidade_oraculo_clima`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 6 · **Custo:** 2  
**Classificação:** sem_efeito_individual · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate:** Sem habilidade especial.
**Lore:** O profeta de Liurnia observa as mudanças do céu e interpreta os sinais trazidos por tempestades e geadas.

### Profeta Esquecido (`luterano_profeta`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Mítica · **Poder-base:** 6 · **Custo:** 5  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O profeta reúne os últimos fiéis sob os vitrais partidos de Leyndell e interpreta as escrituras que sobreviveram à queda de sua irmandade.
**Tags de sinergia:** fe, soberania
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Radahn, Flagelo Estelar (`chefe_radahn_flagelo_estrelas`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Cerco  
**Raridade:** Primordial · **Poder-base:** 9 · **Custo:** 6  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Gravidade do Flagelo:** Ao entrar, move o inimigo de maior poder efetivo para esta fileira e reduz seu bônus em 2 (mín. -2). Raridade Primordial: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** General temido da Fragmentação, dominou a gravidade para deter o curso das estrelas e permaneceu em Caelid após a Podridão.

### Ranni, Bruxa da Lua (`chefe_dama_vazio`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Fenda do Vazio:** Ao entrar em campo, tira 2 pontos de bônus da unidade inimiga mais forte. O bônus dela não pode ficar abaixo de -2. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A princesa lunar rompeu com os Dois Dedos e busca um destino independente da Vontade Maior.
**Tags de sinergia:** lua_cariana, vazio
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Recusante Vulcânico (`gwent_unidade_contrabandista`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Longa distância  
**Raridade:** Comum · **Poder-base:** 5 · **Custo:** 1  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 1 combo; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site.
**Lore:** Um recusante de Volcano Manor, acostumado a negociar favores e segredos nas encostas do Monte Gelmir.
**Tags de sinergia:** caravana
**Combos compatíveis:** Saque da Cidade Eterna: Saqueadora e Contrabandista fecham o negócio (+2).

### Rito Hemático (`gwent_v77_veu_sangramento`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Rito Hemático:** Escolha uma fileira inimiga. Cada unidade nela recebe Sangramento; a segunda marca reduz 2 de bônus (mín. -2) e consome as marcas. Marcas expiram no fim da rodada. Raridade Rara: aplica a segunda marca a até 1 alvo sem marca; reforça a redução de bônus em até 1 alvo (mín. -2).
**Lore:** No altar subterrâneo, os acólitos de Mohgwyn repetem o rito de sangue e juram sua devoção à dinastia carmesim.

### Ritual de Sangue (`elden_especial_sangramento`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sangramento:** Escolha uma fileira inimiga. Cada unidade nela recebe Sangramento; a segunda marca reduz 2 de bônus (mín. -2) e consome as marcas. Marcas expiram no fim da rodada. Raridade Rara: aplica a segunda marca a até 1 alvo sem marca; reforça a redução de bônus em até 1 alvo (mín. -2).
**Lore:** Os acólitos de Mohgwyn repetem antigos ritos de sangue diante da Mãe Sem Forma, oferecendo feridas e devoção à dinastia carmesim.

### Rugido de Godfrey (`gwent_especial_chifre`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Rugido de Godfrey:** Escolha uma fileira: seus aliados nela recebem +2 de bônus até o fim da rodada. Raridade Épica: acrescenta +1 de bônus a até 1 aliados afetados.
**Lore:** O rugido de Godfrey, o Primeiro Lorde Prístino, ainda ressoa nos campos de batalha como memória dos guerreiros que o seguiram.

### Runa da Morte (`reliquia_runa_morte`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Mítica · **Poder-base:** 0 · **Custo:** 5  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Runa da Morte:** Em cada fileira, a unidade inimiga com maior bônus positivo perde até 2 pontos de bônus (sem ficar negativa). Uso único por partida.
**Lore:** O fragmento da Morte Destinada guarda a força que Maliketh selou para impedir que a morte verdadeira retornasse às Terras Intermédias.

### Runa dos Não Nascidos (`reliquia_runa_nao_nascidos`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Lendária · **Poder-base:** 0 · **Custo:** 4  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Runa dos Não Nascidos:** Remove Geada e Podridão dos aliados afetados; cada unidade purificada recebe +1 de bônus. Uso único por partida.
**Lore:** A Grande Runa guardada por Rennala conserva o poder do renascimento e da perfeição inacabada.

### Sacerdote Esquecido (`luterano_sacerdote`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** combo · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de combate:** Sinergia: participa de 6 combos; ativa ao reunir as tags exigidas e 2 unidades distintas. Cada combo ativa 1 vez por jogador/rodada. Requisitos e bônus no site. Raridade Rara: quando o combo alterar bônus, reforça até 1 alvo (+1 aliado; -1 inimigo, mín. -2).
**Lore:** Um sacerdote conserva os ritos de sua ordem em um santuário quase tomado pelo tempo.
**Tags de sinergia:** fe, sacerdos
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Sangue Corrompido (`gwent_especial_chuva`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Comum · **Poder-base:** 0 · **Custo:** 1  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sangue Corrompido:** Aplica 1 Sangramento a cada inimigo em Cerco. Na segunda marca, consome as marcas e reduz 2 de bônus (mín. -2). Estados expiram no fim da rodada.
**Lore:** Nos degraus do Palácio de Mohgwyn, o sangue derramado alimenta os ritos dos devotos que oferecem sua devoção à Mãe Sem Forma.

### Santo Sem Nome (`gwent_v76_esq_santo_sem_nome`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Cerco  
**Raridade:** Mítica · **Poder-base:** 8 · **Custo:** 5  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sinergia de Facção:** Recebe +1 de bônus por cada outra unidade aliada da mesma facção que já esteja em campo. Raridade Mítica: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma figura venerada sem registro nos livros atravessa o santuário, envolta em luz pálida e poeira dourada.
**Tags de sinergia:** fe, soberania
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Senhor das Almas (`patente_8`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 5 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Retaliação dos Semideuses:** Recebe +1 de bônus ao entrar se sua pontuação estiver abaixo da adversária. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** O senhor reúne espíritos errantes sob seu domínio e conhece os nomes que os vivos esqueceram.

### Sentença Carmesim (`gwent_v77_veu_execucao`)

**Tipo:** Especial · **Facção:** Véu Carmesim · **Fileira:** Carta especial  
**Raridade:** Lendária · **Poder-base:** 0 · **Custo:** 4  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sentença Carmesim:** Escolha uma fileira e um inimigo nela. Escudo pode bloquear; se a remoção ocorrer, gatilhos de queda são resolvidos. A raridade amplia o limite de poder efetivo, respeitando o teto do efeito. Raridade Lendária: alcança poder efetivo até 8; pode reforçar bônus gerados por efeitos de queda em até 2 alvos.
**Lore:** No altar de Mohgwyn, o carrasco recebe a lâmina ritual e pronuncia a sentença sobre aqueles que traíram a dinastia.

### Sentinela da Graça (`gwent_v76_ordem_sentinela_luz`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Longa distância  
**Raridade:** Rara · **Poder-base:** 5 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Estandarte:** Ao entrar, concede +1 de bônus aos outros aliados na mesma fileira. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma sentinela ergue o estandarte dourado sobre a muralha voltada para a Árvore Áurea.
**Tags de sinergia:** estandarte, ordem_dourada
**Combos compatíveis:** Juramento de Leyndell: Porta-estandarte e Guardas da Árvore Áurea fortalecem a formação (+1 para a carta participante que ativa o combo e +1 aos aliados na mesma fileira).; Juramento da Árvore Áurea: Duas unidades da Ordem Áurea reforçam a formação: +2 para a carta participante que ativa o combo e +1 aos aliados da mesma fileira.

### Sentinela de Leyndell (`arma_grande_sino`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Lendária · **Poder-base:** 8 · **Custo:** 4  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sino do Último Bastião:** Ganha +2 quando sua pontuação total for menor que a do adversário. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um guardião de elite protege os acessos da capital e enfrenta qualquer ameaça à ordem dourada.

### Sentinela Imortal (`patente_10`)

**Tipo:** Unidade · **Facção:** Véu Carmesim · **Fileira:** Cerco  
**Raridade:** Lendária · **Poder-base:** 6 · **Custo:** 4  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Ruptura de Postura:** Recebe +1 de bônus se a última unidade jogada pelo adversário entrou na mesma fileira. Raridade Lendária: se esta entrada alterar bônus, reforça até 2 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A sentinela vigia os caminhos antigos sem ceder ao tempo, fiel ao posto mesmo após a queda de seu reino.

### Serafim Caído (`gwent_v76_esq_serafim_caido`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Longa distância  
**Raridade:** Épica · **Poder-base:** 6 · **Custo:** 3  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece. Raridade Épica: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um serafim de asas marcadas desce sobre a catedral, recolhendo as últimas preces entre as ruínas.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Servo dos Mortos (`gwent_unidade_necromante`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Ressurgir:** Ao entrar, traz do seu descarte ao campo a unidade elegível de maior poder-base até 5; ela retorna sem bônus nem Escudo. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Um devoto da raiz da morte percorre criptas esquecidas, guiado por sussurros que os vivos não conseguem ouvir.
**Tags de sinergia:** runico
**Combos compatíveis:** Ritual das Runas: Duas unidades rúnicas completam o círculo (+2 para a carta participante que ativa o combo e +1 aos aliados na fileira).

### Silêncio Dourado (`gwent_v77_ord_silencio`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Épica · **Poder-base:** 0 · **Custo:** 3  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Silêncio da Graça:** Remove o clima ativo das três fileiras para os dois jogadores.
**Lore:** Quando os sacerdotes da Ordem Áurea erguem a voz, o brilho da Graça recobre as muralhas e silencia os presságios do céu.

### Sino do Peregrino (`gwent_v77_esq_batedor`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Comum · **Poder-base:** 0 · **Custo:** 1  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Sino do Peregrino:** Compra 1 carta da reserva; a raridade pode elevar a compra para 2, se houver cartas disponíveis.
**Lore:** O sino de bronze convoca peregrinos dispersos de volta à capela; seu toque é reconhecido mesmo sob as pedras das catacumbas.

### Tecelã da Névoa (`gwent_v76_lua_tecela_nevoa`)

**Tipo:** Unidade · **Facção:** Lua Negra · **Fileira:** Cerco  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Eco Arcano:** Recebe +2 de bônus ao entrar se houver ao menos uma carta especial no seu descarte. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Uma feiticeira traça runas no ar e observa a névoa se fechar sobre as ruínas de Nokron.
**Tags de sinergia:** astral, lua_cariana
**Combos compatíveis:** Alinhamento Astral: Ranni e uma unidade Astral distinta convergem (+2).; Eco das Pedras Cintilantes: O Erudito das Pedras e outra unidade Astral, em cartas distintas, amplificam a mesma magia (+2).; Convergência da Lua Negra: Duas unidades ligadas à Lua Negra convergem e recebem +2.

### Tempestade dos Picos (`gwent_especial_tempestade`)

**Tipo:** Especial · **Facção:** Lua Negra · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Tempestade dos Picos:** Escolha uma fileira. Enquanto o clima estiver ativo, todas as unidades dos dois lados nela perdem 1 de poder efetivo (mínimo 1); Resistência Climática pode absorver a penalidade.
**Lore:** Nas encostas dos Picos dos Gigantes, tempestades antigas varrem os desfiladeiros e castigam os viajantes que desafiam o inverno.

### Veterano do Juramento (`gwent_v75_ordem_veterano_juramento`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Rara · **Poder-base:** 4 · **Custo:** 2  
**Classificação:** identidade · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Juramento Dourado:** Ao entrar, esta carta recebe +1; o aliado de menor poder efetivo na mesma fileira também recebe +1, se existir. Raridade Rara: se esta entrada alterar bônus, reforça até 1 alvo: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** Veterano das muralhas internas de Leyndell, traz no escudo o juramento feito diante da Árvore Áurea.
**Tags de sinergia:** v75_erdtree_oath
**Combos compatíveis:** Juramento do Crisol e da Graça: Formação e proteção convergem: a carta participante que ativa o juramento recebe +2.

### Vigia da Noite (`luterano_vigia`)

**Tipo:** Unidade · **Facção:** Os Esquecidos · **Fileira:** Corpo a corpo  
**Raridade:** Comum · **Poder-base:** 3 · **Custo:** 1  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 1/1 · **Validação:** OK

**Efeito de combate — Glória:** Ao vencer a rodada, mantém no campo a unidade com Glória ou Sobrevivente de maior poder efetivo; as demais são descartadas. Em empate ou derrota, nenhuma permanece.
**Lore:** Um sentinela solitário vigia os portões enquanto a noite cobre as ruínas.
**Tags de sinergia:** fe, gloria_divina
**Combos compatíveis:** Glória Divina: A fé e a glória convergem: +2 para a carta participante que ativa o combo.; Devoção: Duas unidades devotas fortalecem a formação: +2.; Evangelho: Missionários espalham a palavra: +2.; Irmandade Esquecida: Irmãos e missionários unem forças: +2.; Soberania Divina: O Papa e seus seguidores estabelecem soberania: +2.; Sacerdócio: Sacerdotes abençoam a formação: +2.

### Vigília do Relicário (`gwent_v77_esq_egide`)

**Tipo:** Especial · **Facção:** Os Esquecidos · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Vigília do Relicário:** Escolha um aliado sem Escudo para receber 1 Escudo; a raridade pode proteger até 3 aliados. Escudos não bloqueiam sacrifícios. Raridade Rara: protege até 2 aliados sem Escudo.
**Lore:** Os monges dos Esquecidos velam a relíquia sem nome, repetindo preces antigas para impedir que a última luz do santuário se apague.

### Vontade de Marika (`gwent_singular_nivel1`)

**Tipo:** Unidade · **Facção:** Ordem Áurea · **Fileira:** Corpo a corpo  
**Raridade:** Singular · **Poder-base:** 10 · **Custo:** 0  
**Classificação:** unidade · **Linhas de lore no render procedural/template:** 3/3 · **Validação:** OK

**Efeito de combate — Último Suspiro:** Na terceira rodada, recebe +1 de bônus ao entrar em campo. Raridade Singular: se esta entrada alterar bônus, reforça até 3 alvos: aliados +1; inimigos -1 (mín. -2). Não muda poder-base.
**Lore:** A vontade da Rainha Eterna permanece gravada no Anel Prístino; mesmo após sua ruptura, seus fragmentos continuam a determinar o destino das Terras Intermédias.

### Égide da Graça (`gwent_v77_ord_egide`)

**Tipo:** Especial · **Facção:** Ordem Áurea · **Fileira:** Carta especial  
**Raridade:** Rara · **Poder-base:** 0 · **Custo:** 2  
**Classificação:** especial · **Linhas de lore no render procedural/template:** 2/2 · **Validação:** OK

**Efeito de combate — Égide da Graça:** Escolha um aliado sem Escudo para receber proteção. A raridade pode ampliar a proteção a até 3 aliados; Escudos não bloqueiam sacrifícios. Raridade Rara: protege até 2 aliados sem Escudo.
**Lore:** Uma muralha de luz dourada envolve os defensores que juraram proteger a Árvore Áurea.

## Divergências automáticas

Nenhuma divergência estrutural encontrada no cruzamento catálogo → motor → site. A imagem contém somente a lore.
