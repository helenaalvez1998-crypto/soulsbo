# Manifesto de alterações — preflight operacional Card Engine v2 (rev. 30)

**Baseline:** rev. 29  
**Entrega:** rev. 30  
**Escopo:** ferramenta de preflight e testes read-only; nenhuma alteração no runtime de gameplay ou no banco legado.

## Arquivos adicionados

- `scripts/card_engine_v2_staging_preflight.py` — verificador operacional sem exposição de segredos; SQLite somente leitura; opcional `--probe-discord`.
- `tests/card_engine_v2/test_staging_preflight.py` — seis testes de ambiente, OAuth, storage, schema e não exposição de segredos.
- `tests/card_engine_v2/test_legacy_collection_sql_contract.py` — dois testes que extraem os SQLs atuais de `Database.coliseu_listar_exemplares` e executam as consultas em SQLite temporário `query_only`.
- `docs/card-engine-v2-operational-readiness-v0.1.md` — procedimento de staging.
- `docs/card-engine-v2-staging-preflight-current-environment.json` — saída sanitizada do preflight neste ambiente de desenvolvimento.

## Arquivos atualizados

- `docs/card-game-handoff.md` — novo handoff de rev. 30.
- `docs/README-PACOTE-CONTINUIDADE.md` — nova referência de continuidade no topo.
- `docs/card-engine-v2-playable-alpha-validation-v0.5.json/.md` — relatório oficial atualizado de 209 para 217 testes.

## Validação desta revisão

- `python -m unittest discover -s tests/card_engine_v2 -v`: **217/217**, zero falhas.
- `py_compile` dos módulos de bot, gateway, site e testes: PASS.
- `node --check site/assets/card-engine-v2.js`: PASS.
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.5.py`: PASS, 217/217.
- `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py`: PASS, 137 modelos/27 permitidos/110 bloqueados.
- Simulação Bo3: A venceu 2–1, 97 eventos, integridade SQLite `ok`.
- Demo combo/passiva/líder: 20–10, 49 eventos, integridade SQLite `ok`.
- Preflight de staging executado neste ambiente: **não pronto**, por dependências fixadas ausentes/diferentes, credenciais Discord/OAuth não fornecidas e DB legado não fornecido. O relatório não contém valores secretos.

## Comparação com o ZIP rev. 29

- Seis arquivos adicionados e quatro arquivos modificados; nenhum arquivo removido.
- Os cinco arquivos protegidos (`bot.py`, `database.py`, `sistemas/gwent.py`, `sistemas/cartas.py`, `site/app.js`) permaneceram byte a byte idênticos ao ZIP rev. 29.
- Nenhum arquivo-fonte de runtime do Card Engine v2, Discord ou site foi modificado nesta revisão.

## Limites importantes

- A tentativa de instalar `discord.py==2.7.1` e `aiosqlite==0.22.1` não chegou ao índice PyPI por falha DNS/rede deste ambiente. Não inferir que as versões não existam.
- Não houve conexão real com Discord, OAuth, bot Gateway, banco publicado ou servidor de staging.
- O teste SQL de coleção extrai os comandos literais do método atual de `database.py` e os executa contra SQLite temporário; não equivale a executar o driver `aiosqlite` real.
- Nenhum runtime, schema de gameplay, catálogo, `bot.py`, `database.py`, `sistemas/gwent.py`, `sistemas/cartas.py` ou `site/app.js` foi modificado nesta revisão.
