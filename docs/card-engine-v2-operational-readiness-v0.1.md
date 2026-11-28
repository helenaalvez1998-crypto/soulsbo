# Card Engine v2 — preflight operacional de staging (v0.1)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev29.zip`  
**Revisão resultante:** rev. 30  
**Escopo:** preparar e executar uma verificação operacional segura no host de staging, sem fazer deploy, migrar dados ou iniciar partidas automaticamente.

## O que foi adicionado

- `scripts/card_engine_v2_staging_preflight.py`: verificador executável de requisitos do runtime, wiring Discord/site, configuração de OAuth, segregação de segredo de sessão, permissões de armazenamento e schema do inventário legado.
- `tests/card_engine_v2/test_staging_preflight.py`: seis testes de configuração válida/inválida, divergência de callback, chave de sessão, dependências e leitura read-only do SQLite.
- `tests/card_engine_v2/test_legacy_collection_sql_contract.py`: dois testes que extraem os SQLs literais atuais de `Database.coliseu_listar_exemplares` no `database.py`, executam as consultas contra SQLite temporário em `query_only` e exercitam a projeção para o Card Engine v2. Isso valida a compatibilidade da consulta e do formato de exemplares, mas não substitui a execução de `aiosqlite` em produção.

## Execução no host de staging

A partir da raiz do checkout:

```bash
python -m pip install -r requirements.txt
python scripts/card_engine_v2_staging_preflight.py --project-root .
```

Depois de configurar `DISCORD_TOKEN`, é possível validar o token sem imprimir identidade nem resposta da API:

```bash
python scripts/card_engine_v2_staging_preflight.py --project-root . --probe-discord
```

O probe realiza somente `GET https://discord.com/api/v10/users/@me`. Não cria mensagem, não entra em servidor, não altera comandos e não faz deploy.

## Variáveis obrigatórias

Definir no ambiente do host, nunca no repositório ou no frontend:

- `DISCORD_TOKEN`
- `DISCORD_OAUTH_CLIENT_ID`
- `DISCORD_OAUTH_CLIENT_SECRET`
- `DISCORD_OAUTH_REDIRECT_URI`
- `SOULSBOT_WEB_SESSION_SECRET` (mínimo 32 caracteres, independente dos outros segredos)
- `SOULSBOT_PUBLIC_URL` (HTTPS público; HTTP só para localhost em staging)
- `DATA_DIR` (preferencialmente o volume persistente fornecido pela hospedagem)
- `DB_PATH` somente se o SQLite legado não estiver em `DATA_DIR/colizeu.db`

O callback precisa ser exatamente `SOULSBOT_PUBLIC_URL/auth/discord/callback`, e a mesma URI precisa estar cadastrada na aplicação Discord em OAuth2 → Redirects. O preflight compara as URLs, mas não consegue confirmar o cadastro no Developer Portal sem uma autenticação interativa.

No Discord Developer Portal, habilitar os privileged gateway intents que o bot solicita no código: **Server Members Intent**, **Presence Intent** e **Message Content Intent**. O preflight confirma apenas que o código os solicita; a tela do Developer Portal precisa ser conferida manualmente.

## O que o preflight verifica

1. Python 3.11+ e versões exatas de `discord.py`, `aiosqlite`, `aiohttp` e `python-dotenv` declaradas em `requirements.txt`.
2. Presença dos arquivos de entrada do bot, cog, gateway, página web e JavaScript.
3. Referências estáticas entre o comando `/jogo`, o painel Discord, o hub web e o callback OAuth.
4. Presença das credenciais obrigatórias sem exibir valores; mínimo e independência do segredo de sessão.
5. Validade da URL pública e correspondência exata do callback.
6. Capacidade de criar e remover arquivo temporário em `DATA_DIR`; isso testa permissões locais, não a durabilidade do volume após redeploy.
7. Existência do SQLite legado, `PRAGMA quick_check`, tabela `cartas_exemplares`, chave primária e colunas esperadas. O banco é aberto com `mode=ro` e `PRAGMA query_only=ON`; não exporta linhas, IDs de jogadores ou conteúdo de cartas.
8. Se solicitado, validação do token do bot via endpoint `users/@me`.

O programa emite JSON sem credenciais e retorna código 0 quando não há bloqueadores ou código 2 quando algum requisito está ausente/inválido. `warn` exige confirmação manual; `block` impede considerar staging pronto.

## Validação executada neste ambiente de desenvolvimento

O preflight foi executado contra o checkout rev. 29 e identificou bloqueadores reais do ambiente, não defeitos confirmados do código:

- `discord.py==2.7.1` ausente;
- `aiosqlite==0.22.1` ausente;
- `aiohttp` encontrado em versão diferente da pinagem;
- `python-dotenv` encontrado em versão diferente da pinagem;
- token Discord e variáveis OAuth ausentes;
- `SOULSBOT_PUBLIC_URL`/callback não configurados;
- nenhum `colizeu.db` foi fornecido no pacote.

A tentativa de instalar as duas dependências ausentes falhou porque este ambiente não consegue resolver o índice PyPI (falha de DNS/rede). Nenhuma credencial foi solicitada ou exibida, e nenhuma chamada real ao Discord foi feita. Portanto, este resultado não comprova login OAuth, conexão Gateway, callback `discord.ui`, consulta de coleção na base publicada ou deploy.

## Próximo procedimento operacional

1. Rodar `pip install -r requirements.txt` no host de staging com acesso ao índice de pacotes.
2. Configurar as variáveis acima no painel seguro da hospedagem.
3. Confirmar que `DATA_DIR` aponta para volume persistente e que `DB_PATH` aponta para a base de staging correta.
4. Executar o preflight sem `--probe-discord`; resolver todos os `block`.
5. Executar novamente com `--probe-discord`; resolver qualquer falha do token.
6. Iniciar uma cópia de staging do bot com banco de teste, nunca apontando primeiro para produção.
7. Fazer login OAuth real no navegador e abrir `/card-engine-v2` com duas contas Discord de teste.
8. Validar inventário real, decks, convite/aceite, ações, privacidade, atualizações, reinício do processo e reabertura da partida.
9. Só depois disso aprovar deploy. Não compartilhar `.env`, token, client secret ou snapshot SQLite no chat.

## Limite de conclusão

A revisão 30 entrega um preflight e testes mais próximos do contrato real de coleção. **Ela não é um deploy nem uma validação de staging real.** O ambiente atual não possui dependências Discord/SQLite async, segredos, OAuth configurado ou banco legado. Essas dependências externas precisam ser fornecidas pelo host de staging para concluir o último teste operacional.
