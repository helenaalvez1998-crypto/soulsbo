# Ateliê — três ações separadas

Na área Direção de arte e prompts existem três ações independentes:

1. **Baixar PDF para IA**: gera o PDF com Prompt fixo, Análise artística e referência visual na última página.
2. **Copiar os 2 prompts**: copia somente o Prompt fixo e a Análise artística (PT), nesta ordem.
3. **Copiar somente a imagem de referência**: copia exclusivamente o arquivo de imagem PNG para a área de transferência, sem texto.

Se o navegador não oferecer Clipboard API para imagens, a terceira ação baixa o PNG e informa claramente que será necessário anexá-lo manualmente. Não mostra mensagem de cópia bem-sucedida nessa situação.

O prompt fixo também exige carta isolada, sem fundo externo, em PNG com canal alfa. O fundo artístico interno da carta deve permanecer intacto.
