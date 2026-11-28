# Soulsbo — implantação reproduzível v0.1

## Artefatos

- `Dockerfile`: imagem Python 3.13, dependências fixadas, usuário não-root.
- `compose.yaml`: processo único bot + HTTP, volume nomeado `/data`, porta vinculada a localhost por padrão para uso atrás de reverse proxy HTTPS, root filesystem somente leitura, `tmpfs` para temporários e healthcheck Discord+SQLite.
- `.env.production.example`: modelo de configuração sem segredos reais.
- `deploy/docker-entrypoint.sh`: executa preflight antes do `bot.py`.
- `scripts/runtime_preflight.py`: verifica dependências fixadas, secrets, OAuth callback, host base sem placeholder/subpath, `DB_PATH` dentro do `DATA_DIR` persistente, volume e schema real da coleção em read-only.
- `scripts/backup_sqlite.py`: backup consistente através da API online backup do SQLite e `integrity_check`.
- `.github/workflows/ci.yml`: testes, compilação, JS, Compose config e build Docker.

## Operação

Consulte `deploy/README.md`. O deploy é bloqueado por padrão se não encontrar o banco legado. Uma instalação realmente nova pode definir `SOULSBOT_ALLOW_EMPTY_DATABASE=true`, mas isso não restaura coleção, usuários nem histórico anteriores.

O healthcheck só fica saudável quando `GET /api/status` reporta API online, SQLite conectado e Discord conectado. Não há credenciais ou banco real incluídos no repositório.

## Limite de validação

O Dockerfile/Compose foram revisados estaticamente e a configuração pode ser validada no CI. O ambiente de criação desta revisão não tem Docker Engine, acesso ao índice PyPI, token Discord, credenciais OAuth ou banco de staging; portanto não foi feito `docker build`, login Discord, OAuth real nem deploy. A primeira execução conectada deve ocorrer em staging, usando uma cópia restaurável do banco.
