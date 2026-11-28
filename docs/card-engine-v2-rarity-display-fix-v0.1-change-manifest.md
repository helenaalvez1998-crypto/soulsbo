# Manifesto de alterações — correção visual de raridade (rev. 32)

Baseline: `soulsbo-main-continuity-2026-11-28-rev31.zip`

## Alterações

| Arquivo | Alteração | Impacto |
|---|---|---|
| `site/app.js` | Removidos mapas, cálculos e widgets da potência da raridade nas fichas, coleção e inspeção de partida; sanitizados o evento principal e a timeline legada. | Exibição sem escala 0–6 ou explicação textual do orçamento de raridade; demais logs preservados. |
| `site/index.html` | Removido bloco de detalhes da potência e adicionados cache-busters para CSS/JS/iframe Forja. | Navegador deixa de reutilizar versão antiga da interface. |
| `site/forja.html` | Removido badge `Potência da raridade / 6`. | Raridade e ascensão continuam visíveis sem medidor de potência. |
| `site/style.css` | Removidos estilos antigos de potência e ajustada grade de detalhes. | Sem widgets obsoletos. |
| `site/narabot-visual-v59.css` | Removida regra V54 residual. | Limpeza de estilo legado. |
| `site_hub.py` | Retirada de `potencia_raridade` das projeções JSON v2 de carta e Forja. | O campo interno legado não é exposto por essas rotas. Endpoints Gwent antigos em `bot.py` permanecem preservados por compatibilidade. |
| `sistemas/atelie_coliseu.py` | Corrigida contradição no prompt obrigatório e reforçada exclusão do campo visual. | Novas artes não recebem instrução contraditória. |
| `sistemas/prompt_arte_criador.py` | Reforçada regra de raridade classificatória no texto visual. | Novas artes não mostram escala/efeito de raridade. |
| `tests/test_site_rarity_classification_ui.py` | Cobertura para HTML, JS, CSS, prompts e projeção de API. | Previne regressão do indicador. |
| `docs/ATELIE_CARTA_COMPLETA.md` | Atualizada documentação. | Continuidade alinhada. |
| `docs/card-game-handoff.md` | Baseline rev. 32 adicionada. | Próxima sessão usa estado correto. |
| `docs/README-PACOTE-CONTINUIDADE.md` | Ponteiro de continuidade atualizado. | Índice aponta para rev. 32. |

## Arquivos preservados

Não houve alteração nas regras de gameplay, schema de bancos, `bot.py`, `database.py`, `sistemas/gwent.py` ou `sistemas/cartas.py`. O motor legado mantém comportamento histórico nesta entrega; a rev. 32 corrige a apresentação e a projeção web. O contrato do Card Engine v2 continua tratando raridade como classificação.

## Validação

Ver `docs/card-engine-v2-rarity-display-fix-v0.1-validation.json`.
