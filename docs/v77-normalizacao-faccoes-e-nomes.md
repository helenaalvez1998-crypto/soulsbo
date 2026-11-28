# V77 — paridade das facções, expansão de Os Esquecidos e nomes compactos

**Estado:** implementado e testado no código-fonte do pacote. **Não implantado no host de produção.**

## Resultado de paridade

O pacote jogável estático foi normalizado para a mesma quantidade de cartas em todas as facções:

| Facção | Unidades | Especiais | Cartas no pacote | Líderes |
|---|---:|---:|---:|---:|
| Ordem Áurea | 30 | 11 | 41 | 3 |
| Véu Carmesim | 30 | 11 | 41 | 3 |
| Lua Negra | 30 | 11 | 41 | 3 |
| Os Esquecidos | 30 | 11 | 41 | 3 |
| **Total** | **120** | **44** | **164** | **12** |

O índice completo contém **179 modelos**: 164 cartas no pacote jogável e 15 registros de recompensa/Primordial fora do pacote estático.

## Líderes de Os Esquecidos

Os dois líderes adicionais pedidos já haviam sido introduzidos na expansão V76. A V77 preserva e valida o trio completo, sem criar duplicatas:

| ID | Líder | Efeito aplicado pelo motor |
|---|---|---|
| `lider_papa_esquecido` | Papa Esquecido | Concede +1 de bônus às unidades dos Esquecidos na fileira escolhida. |
| `lider_abadessa_ruinas` | Abadessa das Ruínas | Purifica até 2 aliados dos Esquecidos afetados e de maior poder efetivo na fileira escolhida; cada um recebe +1 de bônus. |
| `lider_martir_vigilia` | Mártir da Vigília | Recupera do descarte a unidade mais forte dos Esquecidos com poder-base até 5, na fileira escolhida, com +1 de bônus. |

Os três líderes usam os handlers existentes em `sistemas/gwent.py`, os registros `LEADERS`, o seletor de alvo e as imagens publicadas em `site/assets/leaders`. A cobertura V76 é preservada e a auditoria V77 continua verificando os IDs no site e no motor.

## 17 cartas especiais novas

As 17 cartas abaixo fecham a paridade de especiais: três para Ordem Áurea, quatro para Véu Carmesim e dez para Os Esquecidos. Lua Negra já possuía onze especiais e não precisou receber substituições.

| Carta | Facção | Raridade | Handler efetivo |
|---|---|---|---|
| Égide da Graça | Ordem Áurea | Rara | `gwent_egide` |
| Cântico Dourado | Ordem Áurea | Rara | `gwent_chifre` |
| Silêncio Dourado | Ordem Áurea | Épica | `gwent_purificar` |
| Rito Hemático | Véu Carmesim | Rara | `gwent_sangramento` |
| Névoa Rubra | Véu Carmesim | Rara | `gwent_podrida` |
| Delírio Carmesim | Véu Carmesim | Épica | `gwent_loucura` |
| Sentença Carmesim | Véu Carmesim | Lendária | `gwent_execucao` |
| Bastião das Ruínas | Os Esquecidos | Comum | `gwent_muralha` |
| Cântico dos Fiéis | Os Esquecidos | Rara | `gwent_chifre` |
| Misericórdia Final | Os Esquecidos | Rara | `gwent_medico` |
| Vigília do Relicário | Os Esquecidos | Rara | `gwent_egide` |
| Procissão dos Fiéis | Os Esquecidos | Rara | `gwent_passo` |
| Luz na Geada | Os Esquecidos | Rara | `gwent_chama` |
| Juramento dos Fiéis | Os Esquecidos | Épica | `gwent_vinculo` |
| Sino do Peregrino | Os Esquecidos | Comum | `gwent_batedor` |
| Céu sem Cinzas | Os Esquecidos | Rara | `gwent_purificar` |
| Bruma Sepulcral | Os Esquecidos | Épica | `gwent_clima` |

Cada ID tem uma habilidade declarada própria para catálogo, lore e arte, mapeada por `SPECIAL_EFFECT_ALIASES` para um handler canônico já executado pelo resolvedor. O site recebe os dois IDs: `habilidade_id_declarada` para identidade da carta e `habilidade_id`/`habilidade_id_efetiva` para selecionar os controles e executar a regra real. O seletor de alvo também resolve o handler efetivo. Testes comparam o estado de jogo produzido pelo alias com o estado produzido diretamente pelo handler canônico para os 17 casos.

O texto do efeito é composto com os limites de raridade reais do resolvedor. Em especial, o limite de execução de `Sentença Carmesim` é calculado dinamicamente pelo orçamento da raridade e nunca anuncia um valor fixo incompatível com a carta.

## Direção artística das novas especiais

O motor procedural recebeu direções semânticas próprias para os sujeitos das novas cartas: muralha, coro ritual, névoa hemática, execução, recuperação de um caído, vigília de relíquia, procissão, chama que derrete geada, sino, limpeza climática e bruma sepulcral. A arte não usa apenas o mesmo fundo genérico de facção. O teste `test_v77_specials_have_art_direction_specific_to_their_names_and_lore` verifica sujeito, cena, ação e materiais para cada uma das 17 cartas.

As imagens continuam imprimindo apenas a lore narrativa no painel inferior. Regras, limites e seletores permanecem na interface e no combate; o painel físico não voltou a imprimir habilidade ou o placeholder “Sem habilidade especial”. `VERSAO_ARTES` foi incrementada para invalidar imagens antigas em cache e regenerá-las com os títulos atuais.

## Revisão dos nomes

Foram encurtados títulos longos em nomes de personagens, criaturas, armas, locais e grupos. Alguns exemplos:

| Antes | Nome atual |
|---|---|
| Peregrinos da Cidade Eterna | Peregrinos de Nokron |
| Exploradora da Cidade Eterna | Exploradora de Nokron |
| Servo dos que Vivem na Morte | Servo dos Mortos |
| Radahn, Flagelo das Estrelas | Radahn, Flagelo Estelar |
| Geada dos Picos dos Gigantes | Geada dos Picos |
| Cinzas dos Lobos Solitários | Lobos Solitários |
| Grande Runa dos Não Nascidos | Runa dos Não Nascidos |
| Batedor da Mansão Vulcânica | Batedor de Gelmir |
| Carrasco de Volcano Manor | Carrasco de Gelmir |
| Guerreiro da Chama Frenética | Guerreiro Frenético |
| Cavaleiro de Sangue de Mohg | Cavaleiro Sangrento |
| Discípulos do Monge do Fogo | Discípulos do Fogo |
| Confessora da Graça Serena | Confessora da Graça |
| Arauto do Estandarte Áureo | Arauto Áureo |
| Porta-estandarte de Leyndell | Porta-estandarte Áureo |
| Ferreiro de Volcano Manor | Ferreiro Vulcânico |

A revisão foi aplicada no catálogo canônico e nas referências de apresentação, eventos e combos encontradas no código ativo. IDs antigos foram preservados: decks, coleções e snapshots continuam resolvendo para a carta canônica pelo ID. Rótulos de Relíquia e textos de sinergia que repetiam os títulos antigos foram alinhados.

Auditoria automática de nomes em `CARTAS_POR_ID`: **179/179 nomes preenchidos, únicos e com no máximo 27 caracteres**. Não foram renomeados IDs internos.

## Verificações executadas

- 30 unidades e 11 especiais em cada uma das quatro facções.
- Três líderes por facção; 12 no total.
- 164 cartas estáticas no pacote e 179 modelos no índice público.
- 17 novas especiais com descrição catalogada e handler efetivo.
- Equivalência funcional por alias/handler para os 17 efeitos, incluindo controles de seleção de alvo.
- Títulos únicos, limite de 27 caracteres e IDs anteriores preservados.
- Auditoria catálogo → motor → site: 179/179 publicados, **zero divergências**.
- Encaixe integral da lore nos painéis procedural e template com arte personalizada.
- Suíte completa do repositório: **340 testes e 109 subtestes aprovados**. `py_compile`, `node --check site/app.js` e auditoria catálogo → motor → site também passaram. A bateria focada V76/V77 está incluída nesse total.

A suíte completa do repositório precisa ser considerada junto aos resultados finais do pacote; os testes acima são apenas o subconjunto focado nesta alteração. A validação não executa automaticamente cada combinação possível de cartas em banco real nem confirma a implantação no host. O pacote precisa ser instalado e o serviço reiniciado para publicar a V77.
