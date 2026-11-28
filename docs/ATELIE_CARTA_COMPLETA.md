# Ateliê — carta completa, prompt fixo e quatro facções

## Alterações
- As quatro referências foram substituídas pelas imagens enviadas em 26/11/2026.
- A Análise artística (PT) foi refeita para descrever a carta diretamente a partir dos dados cadastrados, sem inventar aparência, cenário, equipamento ou efeitos.
- A análise não contém instruções de resolução, dimensões, proporção, orientação ou margens.
- A rota `/api/gwent/atelier/prompt` retorna Análise artística (PT), o prompt fixo de `sistemas/prompt_carta_completa_fixo.txt` e a referência correspondente à facção.
- Referências estáticas em `site/assets/atelier-referencias/`:
  - Ordem Áurea: `ordem-aurea.png`
  - Lua Negra: `lua-negra.png`
  - Véu Carmesim: `veu-carmesim.png`
  - Os Esquecidos: `os-esquecidos.png`
- A tela principal do Ateliê exibe o prompt fixo e a referência da facção; remove a função do negative prompt.
- O upload preserva o enquadramento e a proporção da carta completa. Não recorta para 5:4 nem força 1200×960.
- A validação mantém limite de 8 MB, formatos PNG/JPEG/WEBP, imagem estática, lado mínimo de 512 px e máximo de 18 megapixels.
- O fluxo atual de submissão, aprovação, Discord e R2 foi preservado.

## Observação
O fluxo foi validado por sintaxe Python. É necessário publicar em ambiente de teste e confirmar:
1. Seleção da referência das quatro facções.
2. Exibição do prompt fixo.
3. Upload de carta vertical completa sem corte.
4. Visualização na fila de aprovação e publicação após aprovação.

Não apague o SQLite nem as variáveis R2 durante a atualização.

O prompt fixo também exige carta isolada, sem fundo externo, em PNG com canal alfa. O fundo artístico interno da carta deve permanecer intacto.


## Fonte de verdade e validação por exemplar (Opção B · v3.1)

- O Ateliê exige selecionar um exemplar específico da coleção. Cada exemplar possui `exemplar_id`, raridade, poder-base e poder máximo próprios.
- O prompt recebe os dados do exemplar confirmado no banco; identidade, facção, categoria e fileira são verificadas contra o catálogo.
- Poder-base, poder máximo e custo são os campos numéricos visíveis autorizados. A raridade é apenas classificatória no Card Engine v2: não desenhar potência, orçamento, escala de efeito, medidor ou pontuação de raridade.
- O arquivo aprovado fica associado ao par `card_id` + `exemplar_id`. Outra cópia do mesmo modelo não herda essa arte completa.
- Cartas completas aprovadas continuam vinculadas ao exemplar, mas não são servidas diretamente como pixels finais. O renderizador extrai somente a janela da ilustração e recompõe a moldura, nome, poder-base, raridade, facção, posição tática e efeito de combate a partir dos dados canônicos atuais. Texto antigo incorporado à imagem aprovada não pode substituir a regra executada no jogo.
- Artes legadas por modelo continuam sendo fallback apenas para instâncias sem arte nova específica.
- Classificação tática válida: Corpo a corpo, Longa distância ou Cerco. Cartas especiais usam Carta especial. Força, Destreza e Magia não são classificações de combate.
- Modelos de imagem podem errar tipografia; revisão humana antes da aprovação continua obrigatória. O renderizador não confia nos textos impressos pelo modelo: usa apenas a região de arte e sobrepõe a regra mecânica canônica do jogo.


## Varredura de consistência (Opção B · v3.1)

- Todos os 136 modelos do catálogo foram usados para testar os dois construtores de prompt; ambos retornaram sem erro.
- O prompt de carta criada por transmutação preserva o custo específico definido para a carta (inclusive zero). Metadados legados de potência da raridade podem continuar existindo internamente, mas não são enviados como campo visual ao gerador.
- O número do medalhão é sempre o poder-base do exemplar. Poder máximo e custo são apresentados em campos próprios. Nenhuma potência numérica de raridade deve aparecer na arte.
- A classificação tática é obtida somente de `fileira`: `melee` = Corpo a corpo, `ranged` = Longa distância e `siege` = Cerco. `funcao_tatica` permanece uma função de jogo separada, não uma posição.
- `tipo` legado não é fonte de facção nem de posição nos prompts ou no payload novo. Referências antigas a Força/Destreza/Magia aparecem somente como proibição explícita de classe de combate; Magia permanece permitida como afinidade, tema, habilidade ou lore documentada.
- A saída da IA continua sendo uma carta integral vertical 2:3; os endpoints de upload preservam o enquadramento e rejeitam imagens horizontais.
- O cache de renderização foi invalidado com `VERSAO_ARTES = 32`.
- Imagens completas antigas aprovadas são preservadas no armazenamento, mas a visualização pública extrai a janela de ilustração e compõe novamente todos os dados da carta. Assim, revisões de habilidade, raridade, poder ou fileira atualizam o cartão exibido sem editar o arquivo aprovado original.


## Correção visual de raridade (rev. 32)

- O site não exibe mais potência de raridade nem a escala incorreta de 0–6 em fichas, coleção, partida, portal ou Forja.
- As respostas JSON da ponte web também deixam de serializar `potencia_raridade`; a compatibilidade/metadado legado permanece apenas no lado do servidor quando necessário.
- A raridade permanece visível como classificação e continua disponível para o caminho de evolução/ascensão.
- Os construtores de prompt do Ateliê foram alinhados para não imprimir potência ou orçamento de raridade em novas artes. A lista de campos visíveis obrigatórios não contém mais potência de raridade.
- Artes completas antigas não são alteradas automaticamente: se o texto estiver incorporado nos pixels da imagem, o exemplar precisa ter a arte regenerada e reaprovada.
