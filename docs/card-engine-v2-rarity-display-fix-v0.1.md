# Correção da exibição de raridade — rev. 32 (2026-11-28)

## Objetivo

Remover do site o indicador numérico incorreto de potência da raridade (escala 0–6) e alinhar os prompts de novas artes à regra aprovada para o Card Engine v2: raridade é classificação, não um multiplicador ou orçamento de execução.

## Alterações no site

- `site/app.js`: removidos o mapa `RARITY_POWER`, funções auxiliares e badges/faixas de potência da ficha, coleção e inspeção de partida. Os detalhes mantêm poder-base, poder máximo e bônus como campos separados. Textos residuais de fallback para Névoa/Geada deixaram de atribuir quantidade de marcas à raridade.
- `site/index.html`: removida a seção `POTÊNCIA DA RARIDADE / 6` do modal de detalhes. Mantida a etiqueta de raridade e a progressão visual de raridade.
- `site/forja.html`: removido o badge `Potência da raridade: N / 6`. Mantidos raridade, nível/caminho de ascensão e poder individual do exemplar em campos distintos.
- `site_hub.py`: removido `potencia_raridade` das respostas JSON v2 de detalhe de carta e listagem da Forja; metadados legados embutidos em definições persistidas são retirados da projeção enviada ao navegador. O construtor de prompt continua podendo validar compatibilidade interna no servidor.
- `site/app.js`: a timeline, o evento principal e o resultado da partida sanitizam textos de log emitidos pelo motor legado que ainda mencionem explicitamente o orçamento de raridade. A ação/evento original continua persistida; somente a apresentação web passa a usar uma mensagem neutra.
- `site/style.css` e `site/narabot-visual-v59.css`: removidos estilos obsoletos do widget de potência. A grade dos detalhes foi ajustada ao número de campos que restaram.
- `site/index.html`: atualizados os parâmetros de cache de CSS/JS e do iframe da Forja para evitar que o navegador continue carregando a interface antiga.

## Prompts de arte

- `sistemas/prompt_arte_criador.py`: novas artes recebem instrução explícita para não imprimir potência/orçamento de raridade, escala numérica ou amplificação de efeito.
- `sistemas/atelie_coliseu.py`: corrigida uma contradição no prompt de saída. O campo de potência de raridade deixou de aparecer na lista de campos visíveis obrigatórios; metadados legados permanecem somente para validação interna e não são enviados como campo visual.
- `docs/ATELIE_CARTA_COMPLETA.md`: documentação alinhada.

## O que foi preservado

- Nome e cor/etiqueta da raridade continuam visíveis.
- A raridade continua disponível no fluxo de ascensão/Forja como classificação.
- Poder-base, poder máximo, custo e bônus continuam sendo exibidos em seus campos próprios.
- Não foram alteradas as regras de gameplay, a tabela interna legada, os custos de ascensão, o inventário ou os cinco arquivos centrais do motor antigo.

## Limitação de assets já gerados

O site ainda possui endpoints do Gwent legado em `bot.py` que mantêm o campo numérico interno no payload para preservar a compatibilidade do motor antigo; o frontend não o utiliza para exibição e neutraliza a mensagem histórica no log. As projeções novas do Card Engine v2/Forja em `site_hub.py` não serializam o campo. Isso não altera nem desativa a mecânica histórica do legado.

O site pode exibir artes integrais armazenadas externamente (por exemplo, em R2). Quando uma arte antiga contém o texto “potência da raridade” incorporado nos próprios pixels, remover o HTML/CSS não remove esse texto da imagem. Esses exemplares precisam ter a arte regenerada com os novos prompts e passar por aprovação humana antes da substituição. Nenhuma imagem externa foi reescrita automaticamente nesta revisão.

## Validação

- Testes de regressão da UI/prompt e sanitização do histórico: `tests/test_site_rarity_classification_ui.py`; inclui geração real de prompt de uma carta de catálogo e confirmação de ausência de campo numérico visível.
- Suíte completa e verificações estáticas registradas em `docs/card-engine-v2-rarity-display-fix-v0.1-validation.json`.
- JavaScript principal e scripts inline das páginas verificados com Node.js.
- Busca estática no diretório `site/` sem referências funcionais ao antigo indicador ou à escala 0–6; testes garantem que as APIs v2 não serializam o campo legado e que o log visível mascara a descrição histórica.
- Não houve deploy nem verificação visual em navegador conectado ao servidor; a validação desta revisão é estática e automatizada.
