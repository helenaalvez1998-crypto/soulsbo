# NARA — Fase 4: Segurança, estabilidade e desempenho

## Correção implementada

- O modo SQLite `:memory:` compartilha uma única conexão. Transações concorrentes nessa conexão poderiam intercalar `BEGIN`, `COMMIT` ou `ROLLBACK`.
- Foi adicionado um `asyncio.Lock` por instância de `Database` para serializar transações no modo `:memory:`.
- A transação agora falha com mensagem explícita se `Database.connect()` ainda não tiver sido chamado.
- Bancos em arquivo continuam usando conexões independentes por transação, `BEGIN IMMEDIATE`, `busy_timeout` e WAL configurado na conexão principal.

## Revisão de segurança realizada

- Os painéis administrativos, de auditoria e moderação verificam a função de moderador nas interações.
- O painel administrativo principal e seus subpainéis restringem o uso a membros autorizados.
- Os comandos de publicação de painéis encontrados usam permissões padrão `manage_guild`.
- O tratamento central de erros de slash commands responde de forma privada e evita expor credenciais nas mensagens ao usuário.
- O encerramento do bot fecha a conexão SQLite.

## Limites desta fase

- A execução de transações reais não pôde ser testada neste ambiente porque `aiosqlite` e `discord.py` não estão instalados.
- A revisão estática não substitui testes concorrentes com SQLite real nem homologação em servidor Discord.
- Não foi feita alteração de schema nem migração de dados.
- Não foi feita rotação de segredos; o `.env` não deve ser distribuído junto do pacote.

## Antes de produção

1. Fazer backup do banco e preservar `.env`/variáveis da hospedagem.
2. Instalar dependências do projeto.
3. Executar toda a suíte de testes no mesmo ambiente da hospedagem.
4. Testar em servidor privado: permissões, aprovações simultâneas, shutdown/restart e persistência dos dados.
