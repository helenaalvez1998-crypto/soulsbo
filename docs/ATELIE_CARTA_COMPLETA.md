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
- O upload preserva os bytes, formato, transparência, dimensões e enquadramento do arquivo original. Não recorta para 5:4, não força 1200×960 e não recompacta a imagem.
- A validação mantém limite de 8 MB, formatos PNG/JPEG/WEBP, imagem estática, lado mínimo de 512 px e máximo de 18 megapixels.
- Toda arte aprovada é exibida diretamente como imagem final da carta. O renderizador automático só é usado quando não existe arte aprovada; não há composição, moldura, textos ou ícones adicionados ao upload.\n- O fluxo atual de submissão, aprovação, Discord e R2 foi preservado.

## Observação
O fluxo foi validado por sintaxe Python. É necessário publicar em ambiente de teste e confirmar:
1. Seleção da referência das quatro facções.
2. Exibição do prompt fixo.
3. Upload de carta vertical completa sem corte.
4. Visualização na fila de aprovação e publicação após aprovação.

Não apague o SQLite nem as variáveis R2 durante a atualização.

O prompt fixo também exige carta isolada, sem fundo externo, em PNG com canal alfa. O fundo artístico interno da carta deve permanecer intacto.
