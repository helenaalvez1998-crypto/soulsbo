# Implantação do Soulsbo (Card Engine v2)

O pacote usa um único processo para o bot Discord e o servidor HTTP do site. O banco legado e os bancos do Card Engine v2 ficam no volume persistente `/data`; não remova esse volume durante atualização.

## 1. Preparar a aplicação Discord

No Discord Developer Portal:

1. Abra a aplicação e confirme que o bot está criado.
2. Copie o token do bot para o segredo `DISCORD_TOKEN` no arquivo `.env` do servidor.
3. Em **OAuth2 → General → Redirects**, cadastre exatamente `https://SEU-DOMINIO/auth/discord/callback`.
4. Preencha `DISCORD_OAUTH_CLIENT_ID` e `DISCORD_OAUTH_CLIENT_SECRET`.
5. Em **Bot → Privileged Gateway Intents**, habilite os intents que o código solicita: Server Members, Presence e Message Content. Se a aplicação não tiver aprovação para um intent privilegiado, resolva isso no portal antes de iniciar.
6. Convide o bot ao servidor com permissões de aplicações/comandos e as permissões de mensagens que seus comandos atuais exigem.

Não coloque tokens, client secrets ou session secrets no Git, no ZIP, em screenshots ou no frontend.

## 2. Preparar a configuração

```bash
cp .env.production.example .env
chmod 600 .env
```

Preencha no host:

- `DISCORD_TOKEN`
- `DISCORD_OAUTH_CLIENT_ID`
- `DISCORD_OAUTH_CLIENT_SECRET`
- `DISCORD_OAUTH_REDIRECT_URI`
- `SOULSBOT_WEB_SESSION_SECRET`
- `SOULSBOT_PUBLIC_URL`

Gere uma chave de sessão exclusiva com:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`SOULSBOT_PUBLIC_URL` deve ser a URL HTTPS pública sem barra final. O callback precisa ser exatamente `${SOULSBOT_PUBLIC_URL}/auth/discord/callback`.

O Compose configura `DATA_DIR=/data` e `DB_PATH=/data/colizeu.db`. Por segurança, a porta publicada fica vinculada a `127.0.0.1` por padrão (`HOST_BIND_IP`); configure um reverse proxy HTTPS no host apontando para `http://127.0.0.1:8080`. `deploy/Caddyfile.example` fornece um exemplo para Caddy, que gerencia TLS automaticamente quando DNS e portas 80/443 estão corretos. Mantenha TLS público e encaminhe `Host`, `X-Forwarded-Host` e `X-Forwarded-Proto`. Só altere `HOST_BIND_IP` para `0.0.0.0` quando a plataforma de hospedagem fornecer ingresso HTTPS e isolamento de rede adequados. O preflight exige banco existente por padrão. Defina `SOULSBOT_ALLOW_EMPTY_DATABASE=true` somente numa instalação realmente nova, sem inventário e sem dados antigos. Para migrar uma comunidade existente, restaure primeiro um backup do SQLite antigo; não inicie com banco vazio por engano.

## 3. Backup e restauração do banco legado

Antes da atualização, pare o processo que escreve no banco ou use o script de backup online:

```bash
python scripts/backup_sqlite.py /caminho/colizeu.db ./backups/colizeu-pre-deploy.db
```

O script usa a API de backup do próprio SQLite (compatível com WAL) e valida `PRAGMA integrity_check` no destino. Armazene o backup fora do volume que será atualizado.

Para restaurar o banco no volume Docker, pare o serviço e copie o arquivo validado para `/data/colizeu.db`. Não restaure por cima de um processo em execução. Preserve também os arquivos de configuração e os demais ativos persistentes que a instalação usa (por exemplo, arquivos de templates/cache que não possam ser regenerados).

## 4. Rodar preflight e iniciar

```bash
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose logs -f soulsbo
```

O entrypoint executa `scripts/runtime_preflight.py` antes de `bot.py`. Se faltar dependência, segredo, callback, permissão no volume ou banco compatível, o processo encerra sem iniciar parcialmente.

O healthcheck consulta `/api/status` e exige HTTP ativo e Discord conectado; em seguida abre o SQLite do volume em modo somente leitura e exige `PRAGMA quick_check=ok`. O campo `database` antigo da API é estático, por isso não é usado isoladamente como prova de saúde do arquivo. A primeira conexão pode levar mais que um ciclo de healthcheck; acompanhe os logs.

Verificações úteis:

```bash
docker compose ps
docker compose exec soulsbo python scripts/runtime_preflight.py --project-root /app
docker compose exec soulsbo python scripts/card_engine_v2_staging_preflight.py --project-root /app --probe-discord
```

O segundo preflight verifica a configuração operacional complementar. O probe Discord só faz `GET /users/@me`, sem enviar mensagens nem alterar comandos.

## 5. Backup recorrente

Exemplo manual dentro do contêiner:

```bash
docker compose exec soulsbo python scripts/backup_sqlite.py /data/colizeu.db /data/backups/colizeu-backup.db
```

O diretório `/data/backups` fica no volume persistente. Para uma estratégia robusta, agende a execução diária via cron (use um nome com data/hora para não sobrescrever o backup anterior), copie o arquivo para armazenamento externo e mantenha retenção fora do mesmo host. Teste restauração periodicamente.

## 6. Atualização

1. Faça backup do banco e confirme o `integrity_check`.
2. Atualize o código/ZIP no host.
3. Mantenha o mesmo volume `soulsbo-data`.
4. Rode `docker compose build --pull && docker compose up -d`.
5. Confirme healthcheck, login OAuth e coleção com contas de teste.

Nunca execute `docker compose down -v` em uma instalação com dados: `-v` remove o volume persistente.

## 7. Estado funcional e módulos deliberadamente bloqueados

- O painel de conquistas calcula progresso no servidor, a partir de inventário, movimentos e resultados de partidas. O navegador não pode enviar progresso.
- “Apostador” e “Sobrevivente” aparecem como rastreamento pendente porque o nível individual e as tentativas/falhas da evolução com risco ainda não são registrados.
- Apostas em Denários/cartas/torneios ficam desativadas até haver escrow, aceitação dos dois jogadores, cancelamento, liquidação atômica e auditoria. Nenhum endpoint bloqueado debita saldo.
- A evolução com risco fica desativada até haver persistência por exemplar de nível, custo transacional, registro de tentativas e inventário real de amuletos. A Forja de ascensão de raridade (`/forja`) é um sistema separado e permanece disponível.
- Os 110 modelos históricos ainda bloqueados não são liberados automaticamente.

## 8. O que o pacote não consegue fazer sozinho

O ZIP não contém token Discord, client secret OAuth, chave de sessão, banco da comunidade ou acesso ao provedor de hospedagem. Essas credenciais e a base real precisam ser configuradas no host pelo proprietário da aplicação. Depois do primeiro deploy, execute uma partida com duas contas Discord de teste e confirme a recuperação após reiniciar o processo antes de convidar jogadores reais.
