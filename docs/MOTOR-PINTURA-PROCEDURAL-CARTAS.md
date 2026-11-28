# Motor de pintura procedural das cartas

## Objetivo e escopo

O motor cria a janela de ilustração de cada carta a partir dos próprios dados do catálogo: nome, descrição/lore, habilidade (como referência visual), categoria, facção e identificador. No texto impresso da carta, o painel narrativo contém somente a lore; habilidade, regra, combo ou aviso de ausência de habilidade nunca são impressos na imagem. A saída é uma imagem RGBA determinística, sem carregar ilustrações externas.

A implementação usa Pillow e a biblioteca padrão do Python. Não usa NumPy, OpenCV, modelos remotos ou arquivos de imagem de terceiros. O estilo é uma pintura digital procedural estilizada: volumes, pigmento, névoa, luz e textura são sintetizados por código.

## Pipeline de renderização

1. **Normalização textual** — remove diferenças de acentuação e caixa para comparar termos sem perder os dados originais da carta.
2. **Direção semântica (`analisar_direcao`)** — escolhe sujeito, ação, cena, material, facção visual, personagem canônico e equipamento sustentado pelo texto.
3. **Paleta e semente** — a semente SHA-256 deriva dos campos da carta. Mesmo cartão, paleta e dimensões produzem os mesmos pixels.
4. **Atmosfera** — céu, planos de arquitetura, névoa, partículas e profundidade do cenário são pintados primeiro.
5. **Silhueta e pose** — personagens, grupos, montarias, criaturas, relíquias ou eventos são desenhados em um plano mais nítido que o fundo.
6. **Materiais** — cada forma recebe gradiente de luz/sombra, pigmento recortado por máscara, costuras, placas, reflexos ou marcas de uso conforme seu papel.
7. **Acabamento** — grão sutil, pinceladas esparsas, vinheta e redução Lanczos para a dimensão final; uma máscara de nitidez leve recupera detalhes.

O canvas usa coordenadas de referência 384 × 430 e supersampling quando a dimensão solicitada permite. A arte é composta em camadas RGBA do Pillow; máscaras e recortes mantêm a textura dentro da silhueta.

## Camadas visuais

| Ordem | Camada | Função |
|---|---|---|
| 1 | Céu e atmosfera | Estabelece clima, horário, fonte de luz e profundidade. |
| 2 | Arquitetura distante | Identifica local e escala sem competir com o sujeito. |
| 3 | Névoa e partículas | Separa planos e integra cenário e personagem. |
| 4 | Sombra de contato | Ancora personagens/objetos no chão quando a cena pede. |
| 5 | Sujeito principal | Silhueta, anatomia, pose, face, roupa e equipamento. |
| 6 | Elementos secundários | Asas, invocações, montaria, estandarte, relíquia ou efeito nomeado. |
| 7 | Luz e materiais | Recorte de luz, reflexos, pigmento, desgaste e detalhes de superfície. |
| 8 | Acabamento | Grão fino, vinheta discreta e redimensionamento final. |

## Linguagem de materiais

- **Aço e placas:** planos de luz e sombra, bordas gastas, rebites e reflexos metálicos localizados.
- **Couro e correias:** tons terrosos, faixas sobrepostas, fivelas e costuras; sem transformar roupa leve em armadura.
- **Tecido e mantos:** volumes em painéis, dobras direcionais, bordas e costuras de baixa opacidade.
- **Pele e anatomia:** volumes diferenciados por escala e arquétipo; gigantes não usam proporções de humano comum.
- **Osso e espectral:** ossos claros em contraste com sombras frias, transparência e névoa localizada.
- **Penas:** base estrutural, remiges sobrepostas, eixos de luz e variação tonal.
- **Pedra, madeira e arquitetura:** massas em planos, desgaste, juntas e profundidade atmosférica.
- **Chamas e magia:** cor, direção e forma variam conforme o evento; efeitos não são um brilho universal aplicado a qualquer carta.

## Arquétipos e regras semânticas

O motor diferencia, entre outros:

- personagens canônicos do catálogo;
- cavaleiro, nobre/comandante, duelista/infiltrador e guerreiro ligado a dragões;
- erudito/explorador, artesão/mercador e clérigo/pregador;
- porta-estandarte, dupla de personagens, necromante e anjo alado;
- gigante, montaria, criatura e formação militar;
- relíquia/arma como objeto focal;
- tempestade, geada, corrupção, rugido/onda sônica, bênção, purificação, chama, juramento, fortificação, invocação, lua cheia e flor escarlate.

A categoria isolada não determina o sujeito. Um item da categoria `Especial` pode ser uma arma, uma relíquia ou um fenômeno. O nome e o texto da carta têm prioridade: `Lágrima Sagrada` é um objeto, `Lâmina da Morte Destinada` é uma arma, `Rugido de Godfrey` é uma onda sônica e `Dragoeiro Ancião` é desenhado como guerreiro humano quando a lore o descreve dessa forma. Prefixos internos de ID não são tratados como prova de que a carta representa uma arma ou magia.

## Cenas dedicadas

O catálogo conta com ambientes semânticos para ruínas lunares, forja vulcânica, terras congeladas, ermo escarlate, Haligtree, fortaleza sombria, palácio da dinastia sanguínea, templo de tempestade, observatório acadêmico, caravana de estrada, catedral esquecida, câmara de relíquias sagradas, santuário da Morte Destinada, santuário da Chama Negra, catedral da Chama Frenética e santuário do Crisol.

Cenas específicas são escolhidas antes dos fallbacks de facção. Isso impede que uma facção apague a identidade de uma cena pedida explicitamente pelo título/lore.

## Integração e cache

`renderizar_pintura_carta(card, size, palette)` é o ponto de entrada. `sistemas/arte_cartas.py` o integra à janela de arte, preservando a identidade visual da moldura, a raridade, a facção e a possibilidade de uma ilustração personalizada substituir a arte procedural.

A versão do renderizador participa da chave de cache. Ao modificar regras ou desenho, incremente `VERSAO_RENDERIZADOR` para invalidar artes antigas. A semente inclui ID, nome, descrição, lore, habilidade, facção e categoria.

## Como ampliar com segurança

1. Adicione primeiro um teste com o ID real da carta e a classificação esperada.
2. Escreva regras específicas antes dos fallbacks genéricos; use correspondências por palavra inteira quando um radical puder gerar falso positivo.
3. Não atribua arma, montaria, asas ou poderes sem evidência no nome ou na lore.
4. Para novo arquétipo, implemente uma função de desenho isolada e conecte-a ao despacho de `renderizar_pintura_carta`.
5. Para novo cenário, adicione o mapeamento semântico e a arquitetura/atmosfera correspondente.
6. Compare uma folha de contato em tamanho real de cartas diferentes e execute a suíte de regressão.

## Limites conhecidos

Este é um motor de pintura procedural 2D estilizada. Ele produz composições consistentes, específicas e reproduzíveis, mas não equivale a um ilustrador humano nem a um modelo generativo treinado para pintura de fantasia de alto realismo. A anatomia, as mãos, faces e cenas muito específicas continuam limitadas pelas formas e regras que foram codificadas. Para atingir ilustração conceitual realista de nível editorial/AAA, o caminho tecnicamente superior é integrar um modelo de imagem ou assets artísticos revisados, mantendo este motor como fallback determinístico e como sistema de direção/validação visual.
