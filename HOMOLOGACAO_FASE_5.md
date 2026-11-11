# NARA — Fase 5: pré-homologação e preparação para produção

## O que foi realizado
- Fase 5 construída a partir do pacote cumulativo da Fase 4; fases anteriores preservadas.
- Corrigida a possibilidade de `transaction()` abrir um arquivo SQLite antes de `connect()`, o que poderia criar um banco vazio após falha de inicialização.
- Incluído `tools/verificar_producao.py`: compila todos os fontes, executa o schema em SQLite real, testa uma operação e executa `PRAGMA integrity_check` sem precisar do token do bot.
- Adicionados dois testes de regressão do pré-check e da validação de conexão.
- Nenhuma migração de dados nem alteração do schema de produção.

## Executar na hospedagem
1. Fazer backup do banco existente e do `.env` (não incluir esses arquivos em pacotes públicos).
2. Criar ambiente Python 3.11+ e instalar `pip install -r requirements.txt` e `pip install -r requirements-dev.txt`.
3. Executar `python tools/verificar_producao.py` e `python -m pytest -q`.
4. Em servidor Discord privado, validar: acesso de membro vs. moderador, categorias do `/adm`, aprovação/rejeição com justificativa, sincronização do cartão, histórico, reinício e persistência.
5. Em banco de teste, disparar duas aprovações simultâneas da mesma solicitação; confirmar uma única recompensa e uma decisão registrada.
6. Testar shutdown e reinício com solicitação pendente e verificar recuperação.
7. Monitorar logs após implantação; voltar ao backup se houver inconsistência.

## Limitações
O pré-check SQLite testa um banco temporário, não migra nem modifica o banco real. Sem `discord.py`, `aiosqlite`, credenciais e servidor de homologação, não há comprovação de integração real ou de capacidade em produção. O pacote deve ser tratado como candidato à homologação, não como produção certificada.
