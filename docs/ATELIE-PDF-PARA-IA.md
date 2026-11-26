# PDF do Ateliê para criação por IA

O botão `Baixar PDF para IA` chama `POST /api/gwent/atelier/pdf`, com autenticação e validação de que o usuário possui a carta selecionada.

O PDF é montado no servidor com ReportLab e contém, nesta ordem:
1. Prompt fixo integral (`sistemas/prompt_carta_completa_fixo.txt`), podendo ocupar várias páginas.
2. Análise artística (PT) específica da carta selecionada.
3. Imagem real da referência visual da facção, incorporada na última página.

A referência é escolhida no servidor com base na facção da carta e lida de `site/assets/atelier-referencias/`. O arquivo é enviado como `application/pdf` e baixado pelo navegador.

Dependência adicionada: `reportlab>=4.2,<5.0`.

O prompt fixo também exige carta isolada, sem fundo externo, em PNG com canal alfa. O fundo artístico interno da carta deve permanecer intacto.
