# NARA — Fase 2: Central de Moderação Integrada

## Entregas

- A seleção de uma solicitação no `/adm` abre uma ficha privada com o cartão/comprovantes originais e os controles de decisão.
- Aprovação e rejeição reutilizam os handlers existentes de Platinas, Runs/Desafios e Jogos Zerados. Recompensas, transações, notificações e validações continuam nos módulos responsáveis.
- Após uma decisão, o cartão original no canal central é atualizado, recebe o resultado e perde os botões, evitando que continue parecendo pendente.
- Rejeições de platinas e jogos zerados agora exigem justificativa (mínimo de 5 caracteres). Runs mantêm seu modal de justificativa existente.
- Motivos de rejeição são registrados no log de auditoria; runs também mantêm `reject_reason` na tabela já existente.
- Fila com paginação de 25 solicitações por página e filtros por categoria; a consulta suporta até 100 registros por categoria por carregamento.
- O fluxo preserva a proteção de acesso a moderadores e as proteções transacionais contra dupla aprovação/recompensa duplicada.

## Limites e observações

- A ficha privada reaproveita o embed do cartão original e os handlers existentes. Os arquivos anexados continuam hospedados na mensagem original do Discord; o embed e links de comprovante são reaproveitados.
- Não foi necessário alterar o schema principal do banco nesta fase.
- O log de motivo das platinas/zerados é um evento separado no log de auditoria; não foi criada uma coluna de motivo nessas tabelas.
- A sincronização do cartão original depende do canal central configurado e de permissões do bot para visualizar, buscar e editar a mensagem.

## Validação

- `compileall` passou para o projeto.
- `pytest -q`: 108 testes passaram.
- Integridade do ZIP validada após empacotamento.
- Não foi possível executar teste de interação real: `discord.py` não está instalado neste ambiente e não há servidor Discord de homologação conectado. A implantação deve ser validada em servidor de teste antes da produção.
