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
- Poder-base, poder máximo, custo e potência da raridade são campos independentes. A arte precisa reproduzi-los nos campos visuais corretos.
- O arquivo aprovado fica associado ao par `card_id` + `exemplar_id`. Outra cópia do mesmo modelo não herda essa arte completa.
- Cartas completas aprovadas são servidas como imagem integral, sem aplicação de moldura, medalhão, título ou texto adicional. Arte legada por modelo continua sendo fallback apenas para instâncias sem arte nova específica.
- Classificação tática válida: Corpo a corpo, Longa distância ou Cerco. Cartas especiais usam Carta especial. Força, Destreza e Magia não são classificações de combate.
- Modelos de imagem podem errar tipografia; revisão humana antes da aprovação continua obrigatória.


## Varredura de consistência (Opção B · v3.1)

- Todos os 136 modelos do catálogo foram usados para testar os dois construtores de prompt; ambos retornaram sem erro.
- O prompt de carta criada por transmutação preserva o custo específico definido para a carta (inclusive zero) e deriva a potência da raridade do orçamento oficial quando o snapshot não a informa.
- O número do medalhão é sempre o poder-base do exemplar. Poder máximo, custo e potência da raridade são campos independentes.
- A classificação tática é obtida somente de `fileira`: `melee` = Corpo a corpo, `ranged` = Longa distância e `siege` = Cerco. `funcao_tatica` permanece uma função de jogo separada, não uma posição.
- `tipo` legado não é fonte de facção nem de posição nos prompts ou no payload novo. Referências antigas a Força/Destreza/Magia aparecem somente como proibição explícita de classe de combate; Magia permanece permitida como afinidade, tema, habilidade ou lore documentada.
- A saída da IA continua sendo uma carta integral vertical 2:3; os endpoints de upload preservam o enquadramento e rejeitam imagens horizontais.
- O cache de renderização foi invalidado com `VERSAO_ARTES = 32`.
- Imagens completas antigas já aprovadas não são reescritas pelo código: como os textos estão incorporados nos pixels, precisam ser regeneradas com o novo prompt e reaprovadas para remover rótulos antigos.
