# Correção do fluxo de imagem final — V83

## Comportamento
Toda imagem aprovada no Ateliê passa a ser a imagem final da carta. O endpoint de imagem retorna os bytes originais armazenados, sem passar por `render_arte_oficial_cacheada_por_id`, `_draw_card` ou cache de composição.

O renderizador automático continua ativo exclusivamente quando não existe uma arte aprovada para a carta.

## Causa da falha anterior
O desvio anterior dependia de uma marca especial em `prompt_text` e tentava acessar a linha retornada pelo SQLite usando `.get()`. O banco retorna `sqlite3.Row`, que deve ser acessado por índice/chave. Além disso, o fluxo antigo podia reencodar ou recortar imagens dependendo do marcador usado no upload.

## Alterações
- A consulta de imagem retorna qualquer arte aprovada diretamente, sem exigir marcador.
- O acesso aos metadados usa `official_meta["id"]`.
- O Ateliê valida PNG/JPEG/WEBP, mas mantém os bytes, formato, proporção e transparência originais.
- Removida a opção que diferenciava ilustração e carta completa: qualquer upload aprovado é tratado como imagem final.
- Removida a exigência de gerar um prompt antes de enviar a imagem final.
- As prévias e miniaturas usam `object-fit: contain`, evitando corte visual.
- Cache da imagem atualizado para V31.
- O fluxo de aprovação/moderação permanece igual.

## Validação
- `tests/test_prompt_mestre_v70.py`
- `tests/test_gwent_catalog_audit_v77.py`
- `tests/test_card_catalog_quality.py`
- `tests/test_gwent_reward_identity_v76.py`
- `tests/test_gwent_competitivo_v74.py`
- `tests/test_gwent_expansao_v75.py`
- `tests/test_elden_gwent.py`

Resultado: 75 testes aprovados e 61 subtestes aprovados.
`node --check site/app.js` aprovado; módulos Python modificados compilados com `py_compile`.
