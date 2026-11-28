> **Registro histórico — não representa a navegação atual.** A interface Discord alpha descrita abaixo foi substituída como ponto de entrada: `/jogo` agora abre os links do site e `Card Engine v2 · Alpha` aponta para `/card-engine-v2`. A UI Discord antiga permanece no código como referência/dormante, mas não é exposta pelo painel atual. Consulte `docs/painel-jogo.md` e `sistemas/card_engine_v2/README.md` para a arquitetura em uso.

# Card Engine v2 — integração Discord alpha v0.1

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev27.zip`  
**Revisão resultante:** rev. 28  
**Status:** handlers e UI adicionados ao projeto; validação do gateway e análise estática aprovadas; despacho real no Discord não executado neste ambiente.

## Entrada no bot

A entrada usa o comando existente `/jogo`. O `PainelJogoView` ganhou o botão **Partidas v2 · Alpha**, que abre uma view privada `AlphaHomeView`. O módulo `cogs/card_engine_v2_ui.py` é importado de forma lazy pelo botão; não foi necessário registrar um novo Cog nem alterar a lista de extensões de `bot.py`.

## Fluxos de jogador disponíveis

### 1. Montar deck

1. O usuário autenticado abre o painel e escolhe **Montar deck**.
2. O adapter consulta `Database.coliseu_listar_exemplares` através de `legacy_collection_exemplars`, em modo somente leitura.
3. O Deck Builder apresenta apenas modelos da allowlist de 27 cartas e cada cópia física por `exemplar_id`.
4. O jogador escolhe 30 exemplares físicos distintos; o limite de três cópias por `card_id` é verificado na UI e novamente pelo `AlphaDeckBuilder` no servidor.
5. O jogador escolhe um dos dez líderes alpha; a facção é obtida da definição confiável do líder, não de texto enviado pelo usuário.
6. Antes do save, a posse e o modelo de cada exemplar são lidos novamente. O deck é persistido no banco dedicado `card_engine_v2/decks.sqlite3`.

A UI desta entrega cria decks novos e lista decks salvos. Edição/substituição de deck existente e exclusão pela interface ainda não foram incluídas, embora a camada de aplicação já ofereça controle de versão e exclusão.

### 2. Desafiar um jogador

1. O desafiante escolhe um dos próprios decks salvos e um usuário não-bot do servidor.
2. O convite é publicado no canal e direcionado ao usuário selecionado.
3. Somente o usuário convidado pode aceitar/recusar.
4. Para aceitar, o oponente precisa escolher um deck que pertence à própria conta.
5. O gateway reconsulta os inventários vivos dos dois jogadores e o matchmaking revalida IDs físicos, propriedade, modelo e proveniência antes de criar a partida.
6. O servidor sorteia o primeiro jogador e embaralha os slots com seus exemplares. Seeds fornecidas pelo cliente não fazem parte desta API.

Convites pendentes são estado temporário em memória, expiram em dez minutos e são descartados quando o processo do bot reinicia. Isso não afeta decks ou partidas já gravados.

### 3. Reabrir partidas

O painel tem a opção **Minhas partidas**. `SQLiteMatchRepository.list_matches_for_player()` devolve apenas metadados mínimos de partidas em que o usuário é participante; não retorna snapshot ou mãos. A seleção abre a partida pelo `view_match_for_player()` e autoriza novamente a identidade no gateway.

Essa lista permite reabrir partidas persistidas depois de reinicialização do bot, mesmo quando o botão temporário da mensagem de convite deixou de funcionar. A consulta atual percorre os registros de partidas do banco dedicado e limita a resposta a 25 jogos; é adequada à alpha inicial, mas deve receber paginação/índice antes de um volume alto.

### 4. Ações durante a partida

A view privada da partida usa somente a projeção segura do jogador autenticado. O usuário consegue:

- ver a própria mão, energia, vida, fatigue, pilha de compra, campo e placar;
- jogar unidades na fileira impressa na definição da carta;
- jogar os quatro especiais da allowlist: Égide, Execução, Tempestade e Geada/Frost;
- escolher alvos a partir das ofertas construídas no servidor e vinculadas à `state_revision`;
- ativar o líder (uma vez por partida), escolhendo a fileira quando a UI pede uma;
- sacrificar unidade aliada pela oferta server-side;
- passar o turno e atualizar a view.

Seleções de alvo com mais de 25 opções são paginadas. IDs de instância são usados internamente para confirmar o alvo; a descrição curta ajuda a distinguir cópias iguais na lista.

Nenhuma das 27 cartas alpha declara habilidade manual no registry atual. A UI não cria botões fictícios para essas habilidades; a API genérica continua disponível no motor para definições futuras.

## Segurança e fronteiras

- IDs de jogador para o desafiante/ator são derivados de `Interaction.user.id`; o oponente só passa a ser aceito como principal depois de clicar no convite, e a view verifica que `interaction.user.id` é o usuário convidado.
- O gateway valida IDs de plataforma como dígitos ASCII positivos e não aceita ações fora da allowlist.
- `execute_action`, ofertas de alvo e abertura de partida exigem projeção segura do participante antes de operar.
- `view_match()` privilegiada não é chamada pela UI. A UI chama somente `gateway.player_view()`.
- `cogs/card_engine_v2_ui.py` não lê nem grava SQLite diretamente e não chama métodos de escrita do banco legado. O gateway usa `AsyncAlphaGameApplication`; operações SQLite do v2 são executadas em `asyncio.to_thread`.
- O inventário legado é consultado em modo somente leitura. Nenhuma escrita, migração ou transação distribuída com o banco legado foi introduzida.
- Os bancos do motor são separados, sob `DATA_DIR/card_engine_v2/matches.sqlite3` e `DATA_DIR/card_engine_v2/decks.sqlite3`.
- Mensagens de erro exibidas ao jogador são genéricas e não reproduzem caminhos, SQL ou exceções internas.
- O botão de entrada `/jogo` registra falhas de inicialização no log do bot e responde com mensagem genérica; detalhes de exceção não são expostos ao jogador.

## Limitações conhecidas da alpha

- A integração é uma superfície Discord alpha, não um lançamento competitivo.
- O ambiente usado para produzir a revisão não tem `discord.py==2.7.1` nem `aiosqlite==0.22.1` instalados. Não foi possível importar o bot, instanciar o Cog real, despachar interações ou testar chamadas à API Discord.
- Não havia token, `.env` operacional, sessão/canal de teste ou bot Discord conectado neste pacote. Não houve deploy.
- O código dos handlers foi compilado com `py_compile`; o gateway de transporte, autorização, revalidação de coleção, matchmaking, listagem de partidas e view segura foram executados em testes automatizados independentes de discord.py; a UI recebeu testes estáticos AST.
- Os controles de partida são efêmeros e expiram localmente após 15 minutos; o usuário pode reabrir a partida pelo painel. Convites expiram em dez minutos e não sobrevivem ao restart.
- O painel de partida não envia atualização push automática para a view privada do oponente. Cada jogador deve pressionar **Atualizar** para consultar o estado mais recente.
- A UI ainda não inclui chat de partida, fila pública/ranked, matchmaking automático, espectador, IA, edição/exclusão de decks, interface web ou handlers HTTP.
- Catálogo limitado a 27 modelos; 110 modelos históricos continuam bloqueados. Custos de energia são provisórios e ainda não foram validados por playtests humanos.
- O sistema não foi validado contra uma instância publicada de `Database`, credenciais reais, banco de produção ou múltiplas instâncias de bot.

## Preparação para validar no ambiente do bot

1. Instalar as dependências já fixadas em `requirements.txt`, incluindo `discord.py==2.7.1` e `aiosqlite==0.22.1`.
2. Usar o `DATA_DIR` persistente do bot e confirmar que o processo possui permissão de criar o subdiretório `card_engine_v2`.
3. Iniciar o bot de staging com o banco legado de teste; confirmar que `bot.db.coliseu_listar_exemplares()` devolve exemplares com IDs globais e proprietário.
4. Abrir `/jogo` com duas contas de teste; montar dois decks legais, enviar/aceitar convite e concluir uma partida.
5. Reiniciar o bot e confirmar que decks e partidas podem ser reabertos, enquanto convites pendentes expiram.
6. Validar privacidade com as duas contas, incluindo tentativa de abrir a partida de terceiro, responder a convite de outro usuário, escolher alvo fora da oferta e repetir ação com `state_revision` obsoleta.
7. Somente depois do staging, configurar deploy. Não apontar os arquivos SQLite v2 para o banco legado.

## Comandos executados nesta revisão

```bash
python -m py_compile cogs/card_engine_v2_ui.py cogs/painel_jogo.py \
  sistemas/card_engine_v2/*.py tests/card_engine_v2/*.py
python -m unittest discover -s tests/card_engine_v2 -v
python docs/scripts/test-card-engine-v2-playable-alpha-v0.5.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

Os comandos de testes de gameplay e simulação validam a lógica do motor e o SQLite descartável; não constituem teste de despacho Discord ou produção.
