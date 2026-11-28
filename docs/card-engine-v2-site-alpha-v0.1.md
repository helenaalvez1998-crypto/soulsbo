# Card Engine v2 — integração do site alpha v0.1

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev28.zip`  
**Revisão resultante:** rev. 29  
**Status:** página e API HTTP integradas ao hub autenticado; testes de integração HTTP executados em `aiohttp.TestServer`; não houve deploy nem validação com banco publicado.

## Entrada e autenticação

A página privada está disponível em `/card-engine-v2` e foi adicionada como link ao hub inicial. Sem sessão Discord assinada, a rota redireciona para `/auth/discord/login?next=%2Fcard-engine-v2`. A página reutiliza a sessão já implementada pelo bot; não cria cookie ou autenticação paralela.

O servidor obtém o ID Discord exclusivamente por `bot._api_user_id(request)`. Nenhum endpoint aceita `player_id` como autoridade enviada pelo navegador. As operações de escrita exigem `bot._api_origin_ok(request)` para proteção CSRF, e as respostas privadas usam `Cache-Control: private, no-store`.

## Experiência no site

A página `site/card-engine-v2.html`, com `site/assets/card-engine-v2.css` e `site/assets/card-engine-v2.js`, oferece:

- Consulta da coleção alpha do usuário autenticado, com exemplares físicos individuais.
- Construção de decks com 30 exemplares, máximo de três cópias por `card_id` e líder válido da mesma facção; cada exemplar precisa continuar pertencendo à coleção do usuário.
- Criação, edição com controle de versão otimista (`expected_version`) e exclusão de decks próprios. Excluir deck não remove cartas da coleção.
- Listagem de até 50 partidas em que o jogador participa e reabertura da sua própria projeção privada.
- Visualização de vida, energia, mão própria, campo, placar, fatigue, estado da partida e histórico sanitizado.
- Paginação incremental do histórico e atualização automática da partida aberta a cada dez segundos.
- Ações de partida suportadas pelo motor: jogar unidade, jogar especial, ativar líder, sacrificar unidade e passar turno. As ofertas de alvos vêm do servidor e continuam vinculadas à revisão do estado.

O matchmaking/desafio entre dois jogadores continua sendo iniciado pelo fluxo de convite do Discord. O site permite montar decks, acompanhar e continuar partidas próprias; não cria fila pública/ranked nem convites diretamente.

## Integração técnica

- `site_hub.py` registra as rotas de `site_card_engine_v2.py` no servidor HTTP existente.
- A API usa o mesmo `CardEngineV2DiscordGateway` quando a instância Discord já o criou (`bot.card_engine_v2_shared_gateway`). Se a API inicializar primeiro, constrói a aplicação sobre os mesmos arquivos dedicados em `DATA_DIR/card_engine_v2/` e publica a instância compartilhada para o cogs.
- O banco legado de coleção é consultado somente por `Database.coliseu_listar_exemplares`; a API não grava coleção nem modifica inventário.
- SQLite do motor é operado através de `AsyncAlphaGameApplication`, que descarrega trabalho de `sqlite3` para threads.
- A listagem de partidas retorna metadados mínimos; abrir uma partida e executar ações passam novamente pelo gateway, que valida participação e devolve a projeção segura do jogador.
- Histórico é gerado por `get_event_history_for_player`: não inclui `instance_id`, UUID de operação, ID bruto de evento, IDs de causalidade ou payload bruto. A API não retorna os IDs de operação usados para idempotência.
- Ações exigem `expected_revision` e `operation_id` UUIDv4. Replays idempotentes são aceitos pelo motor; conflito de fingerprint ou de revisão retorna HTTP 409.
- Corpos JSON têm limite de 32 KiB, inclusive requests em transferência chunked. Campos extras e tipos inválidos são rejeitados.

## Atualização de partidas no Discord

A `MatchPlayView` privada agora faz polling do `state_revision` a cada 12 segundos enquanto a view está ativa. Ao detectar uma revisão nova, substitui a embed e os componentes pela projeção mais recente daquele jogador. A view renovada passa a monitorar a próxima revisão. Views antigas são encerradas em interação/timeout para evitar loops duplicados. O botão **Histórico** abre a linha do tempo sanitizada, com paginação.

Views Discord continuam efêmeras e temporárias; se expirarem, o jogador reabre a partida pelo painel **Minhas partidas**. O polling do site (dez segundos) continua enquanto a partida está aberta na página.

## Segurança e limites

- O site não aceita identidade, proprietário, custos, alvos ou estado de jogo definidos pelo navegador.
- A propriedade de decks é verificada no gateway, e cada escrita de deck usa `expected_version`.
- O gateway valida a participação antes de visualizar, pedir ofertas ou executar ação.
- Ofertas de alvo/sacrifício não aceitam IDs de jogador fornecidos pelo cliente.
- A projeção ao jogador não expõe a mão do adversário nem os IDs físicos privados dele.
- A interface ainda é alpha: sem fila ranqueada, espectador, chat, matchmaking pelo site, suporte para todas as habilidades futuras, nem volume/telemetria de produção.
- Os custos de energia seguem provisórios e não foram balanceados por partidas humanas. A allowlist continua em 27 cartas; 110 modelos históricos seguem bloqueados.

## Validação e limitações do ambiente

- Suíte `tests/card_engine_v2`: 209/209 testes aprovados.
- `py_compile` para rotas, handlers Discord, motor e testes: PASS.
- `node --check site/assets/card-engine-v2.js`: PASS.
- Testes HTTP em servidor aiohttp local: sessão obrigatória, redirecionamento de login, bootstrap de coleção própria, CSRF, criação/edição/exclusão de deck, controle de versão, privacidade de partida, autorização por participante, idempotência, sanitização de histórico e limite de corpo: PASS.
- Registro de `site_hub.registrar_rotas`: 77 registros de método/caminho; página e bootstrap v2 presentes: PASS.
- Staging histórico: 137 modelos, 27 liberados, 110 bloqueados: PASS.
- Simulação Bo3: Player A venceu por 2–1, 97 eventos, SQLite `integrity_check=ok`.
- Demonstração de combo/passiva/líder: placar 20–10, 49 eventos, SQLite `integrity_check=ok`.
- `aiohttp` está instalado neste ambiente. `discord.py==2.7.1` e `aiosqlite==0.22.1` não estão instalados; o token, OAuth operacional, banco publicado e servidor Discord de staging também não estão disponíveis. Portanto, o gateway HTTP foi executado com `aiohttp.TestServer` e inventário fake, mas não houve execução do bot real, login Discord real, callbacks reais de `discord.ui`, integração com o banco publicado ou deploy.

## Próxima prioridade

1. Instalar as dependências declaradas e validar no ambiente de staging com bot Discord e credenciais reais.
2. Exercitar o contrato de coleção contra `Database.coliseu_listar_exemplares` real, inclusive exemplares evoluídos/aprimorados.
3. Testar dois usuários reais: criar decks, desafiar, aceitar, jogar todas as ações, acompanhar atualização nos dois painéis, reiniciar o bot e reabrir a partida pelo site/Discord.
4. Corrigir o que surgir no staging antes de expandir catálogo ou abrir o beta.
