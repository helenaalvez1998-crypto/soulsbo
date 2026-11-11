# Atualização — Central de Moderação NARA

## O que mudou

- O painel `/adm` ganhou o botão **Central de Moderação**.
- A central reúne solicitações pendentes de Platinas, Runs/Desafios Soulslike e Jogos Zerados.
- A opção **Todas as categorias** monta uma fila combinada por ordem de chegada.
- Filtros individuais permitem consultar cada categoria.
- Ao selecionar uma solicitação, a central apresenta um link direto para o cartão original no canal de aprovação.
- O cartão original continua sendo o ponto oficial de decisão: os botões Aprovar/Rejeitar permanecem nele.
- Ao decidir no cartão original, os fluxos existentes atualizam a própria mensagem, removem os botões e executam as recompensas/notificações correspondentes.
- O botão **Atualizar fila** recarrega os registros pendentes.
- O acesso ao `/adm` e à central é validado pela função de moderador (cargo configurado, Gerenciar servidor ou cargo fallback configurado).

## Importante sobre o funcionamento

Esta etapa centraliza a localização e a navegação das solicitações. A aprovação/rejeição ainda é realizada no cartão original dentro do canal de aprovação, e não diretamente na lista do painel. Isso preserva a implementação atual de cada módulo e evita duplicar regras transacionais de recompensas, rankings e notificações.

O canal central configurado em `/adm` continua obrigatório para os cartões. Não é necessário criar canais novos nem alterar os canais públicos de anúncios.

## Instalação

1. Faça backup da pasta `data` e do arquivo `.env`.
2. Substitua os arquivos do projeto pelos desta atualização, preservando `.env` e os dados existentes.
3. Reinicie o bot.
4. Execute `/adm` com uma conta que tenha permissão de moderação.
5. Abra **Central de Moderação** e teste com solicitações de teste antes de liberar o fluxo para membros.

Não apague nem recrie o banco `data/colizeu.db`.

## Validação executada

- `python -m py_compile` nos módulos principais.
- `pytest -q`: 104 testes aprovados.
- Não foi realizado teste conectado a um servidor Discord real.
