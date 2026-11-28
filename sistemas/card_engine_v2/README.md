# Soulsbo Card Engine v2 — alpha isolado

> **Continuidade rev. 31 (2026-11-28):** o motor continua em alpha isolada. O pacote inclui agora operação de deploy Docker/Compose, preflight e backup SQLite, conquistas autoritativas e bloqueio seguro de apostas/evolução com risco incompletas. A validação local atual é 240 testes + 61 subtests; sem Docker CLI, secrets, banco real ou staging conectado, não houve build nem deploy. Leia `docs/card-engine-v2-rev31-product-completion.md` e `deploy/README.md` antes de iniciar.

Este pacote contém uma fatia funcional alpha do motor novo: persistência transacional, resolvedor genérico, controlador de uma partida de teste melhor de três, famílias de efeitos, combos, passivas de facção e líderes.

## Interface e entrada do jogador

A interface web do motor v2 é servida em `/card-engine-v2` por `site_card_engine_v2.py`, usando a sessão Discord assinada. O comando `/jogo` é intencionalmente um painel de entrada compacto: aponta para Arena, Deck e Coleção e para o Card Engine v2 no site. Ele não replica deckbuilding, convites ou ações de partida dentro do Discord.

`cogs/card_engine_v2_ui.py` e `docs/card-engine-v2-discord-alpha-v0.1.md` documentam a primeira integração Discord alpha (rev. 28), mantida como implementação histórica/dormente. Ela não é mais exposta como botão no `/jogo`; a experiência ativa do Card Engine v2 fica no site. O gateway e a aplicação compartilhada continuam sendo a fronteira de autorização e persistência usada pelo site.

O painel Discord mantém somente o `Ritual de Convergência` porque a operação de sacrificar três exemplares do mesmo modelo/raridade para criar um exemplar da raridade seguinte não é substituída pelas receitas de Linhagem, pelos Rituais Ancestrais ou pela Transmutação do site. Consulte `docs/painel-jogo.md` para o mapa atual dos botões.

**Limite de validação desta revisão:** o ambiente de análise não possui `discord.py==2.7.1` nem `aiosqlite==0.22.1`, e não recebeu token Discord. A UI foi compilada e protegida por testes estáticos AST; o gateway e as regras foram executados em SQLite temporário. Login, despacho real de componentes, duas contas em servidor de staging e deploy ainda precisam ser testados no ambiente do bot.

## Requisitos

- Python 3.10 ou superior.
- SQLite da biblioteca padrão do Python.
- `jsonschema` é opcional e usado somente para os testes de schemas JSON.

## Executar a suíte

Na raiz do repositório:

```bash
python docs/scripts/test-card-engine-v2-playable-alpha-v0.5.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

Ou:

```bash
python -m unittest discover -s tests/card_engine_v2 -v
```

## Inicializar uma base local dedicada

Use somente um caminho novo e exclusivo para o engine v2:

```bash
python -m sistemas.card_engine_v2 ./var/card-engine-v2-alpha.sqlite3
```

O comando aplica a migration checksummed e apresenta o relatório de integridade. O repositório recusa SQLite não vazio sem o marcador `soulsbo-card-engine-v2`; não passe o caminho do banco legado.

## Núcleo de persistência disponível

- UUIDv4 para identidade física de cada ocorrência (`CardInstance`).
- Validação da partição de zonas e da proveniência de exemplares.
- Movimentação por `instance_id` exato, sem limpeza implícita de grants.
- `state_revision` e `expected_revision` com CAS sob `BEGIN IMMEDIATE`.
- Ledger durável de operações e replay idempotente.
- Journal append-only de eventos, com sequência por partida e cadeia causal.
- Commit atômico de snapshot, operação, eventos, recompensas e outbox.
- Outbox com lease, retry, dead-letter e confirmação.
- Migration ledger com checksum e backup SQLite verificado.
- Arquivamento de snapshot legado com hash e mapping determinístico persistido.

## Resolvedor de gameplay alpha disponível

`GameplayResolver` recebe registries confiáveis do servidor (`ActionDefinition`, `TargetPolicy` e `ProtectionProfile`) e hoje executa quatro famílias de ação:

- `unit.remove` e `unit.sacrifice`: seleção validada, causas distintas, escudos, consumo de carga, contadores separados, eventos diretos e Vingança reativa.
- `unit.move`: seleção de uma instância própria no campo e movimento restrito às fileiras liberadas na configuração.
- `unit.grant_bonus`: bônus com magnitude, duração e policy de clamp definidos no servidor.
- `unit.grant_protection`: concessão de perfil/cargas/duração definidos no servidor.

As ofertas de alvo são construídas no servidor e vinculadas a `state_revision`. O cliente só pode escolher identidades presentes na oferta. Para `manual_primary_auto_fill`, a oferta informa o alvo primário e a prévia dos alvos secundários; na confirmação, o servidor recalcula a oferta e a seleção antes de mutar o estado.

A resolução de remoção é atômica: valida os alvos e grants de proteção antes de aplicar mudanças. Sacrifício ignora escudos. A ordem de proteção usa o evento de aplicação mais antigo e `grant_id` como desempate. Em remoções múltiplas, todas as remoções diretas são concluídas antes da resolução de Vingança, para que uma unidade removida na mesma operação não receba bônus como sobrevivente.

Exemplo de fluxo interno (a configuração de ações/policies é criada pelo servidor a partir de um release confiável):

```python
import uuid

# A oferta é calculada pelo servidor e contém state_revision e candidatos.
offer = resolver.target_offer_for_action(
    repository,
    match_id,
    actor_player_id=player_id,
    action_type="unit.remove",
    source_instance_id=source_instance_id,
    cause_id="normal_removal",
)

request = {
    "operation_id": str(uuid.uuid4()),
    "actor": {"type": "player", "player_id": player_id},
    "expected_revision": offer["state_revision"],
    "action_type": "unit.remove",
    "payload": {
        "source_instance_id": source_instance_id,
        "cause_id": "normal_removal",
        "selection": {
            "mode": "manual_set",
            "target_instance_ids": [chosen_target_instance_id],
        },
    },
}
receipt = resolver.execute(repository, match_id, request)
```

O exemplo omite a construção dos registries e as verificações de autorização HTTP/Discord. A oferta não é uma autorização: o resolvedor reconstrói a elegibilidade durante a execução e o repositório verifica `expected_revision` sob transação.

A allowlist atual é mantida em `data/card_game/card-engine-v2-alpha-catalog.v0.3.json`; os registries alpha de combos, passivas e líderes ficam em `data/card_game/card-engine-v2-alpha-combos.v0.1.json`, `data/card_game/card-engine-v2-alpha-faction-passives.v0.1.json` e `data/card_game/card-engine-v2-alpha-leaders.v0.1.json`; esse arquivo é validado pelo carregador e seu hash fica preso ao manifesto da partida. O catálogo de staging completo é apenas material de revisão e não é importado por `AlphaCatalog`.

## Partida jogável de teste (alpha)

`AlphaMatchController` fornece um fluxo reproduzível de partida para dois jogadores, melhor de três, em uma base SQLite descartável. A partida usa uma allowlist explícita de 27 cartas, versionada em `data/card_game/card-engine-v2-alpha-catalog.v0.3.json`. O `AlphaCatalog` valida tipo, status, contagem, IDs duplicados, igualdade com a allowlist revisada no código e presença no snapshot de origem. O hash do arquivo entra no `DefinitionManifest`. O baseline histórico contém 137 modelos: 27 são permitidos somente para testes isolados e 110 permanecem bloqueados. A raridade é classificatória; não multiplica efeitos.

O fluxo implementado cobre:

- Criação da partida, UUIDv4 por cópia física, mão inicial padrão de quatro cartas e alternância de turnos. Fixtures determinísticos de regressão podem sobrescrever o tamanho da mão.
- Jogar unidades e resolver 12 famílias de efeitos de entrada explicitamente implementadas: vantagem pelo descarte, presságio da ruína, redução de bônus inimigo, presença em outra fileira, suporte/resistência climática, afinidade climática, condição de bônus positivo inimigo, recuperação de placar, fileira solitária, vantagem no placar, sequência de fileira e caçador arcano.
- Resolver o efeito de entrada do Veterano do Juramento Dourado (`+1` próprio e `+1` ao aliado mais fraco já presente na mesma fileira).
- Cálculo de poder efetivo com bônus, clima por fileira, resistência climática e penalidade de Frost, com piso de 1.
- Especiais de Tempestade, Geada/Frost, Égide e Execução.
- Ofertas de alvos produzidas pelo servidor. Égide e Execução exigem `expected_revision` correspondente à oferta; ofertas antigas são rejeitadas.
- Sacrifício normal no `AlphaMatchController`: a oferta autoritativa enumera aliados no campo; a confirmação exige a revisão da oferta, remove a instância física exata, consome a ação do turno, incrementa `sacrifice_count` e encadeia Vingança quando aplicável.
- Escudos, bloqueio de execução, consumo da fonte, remoção e Vingança reativa causal.
- Passar, congelar pontuação, resolver vencedor da rodada, arquivar unidades sem Vingança, expirar grants em todas as zonas, limpar clima, comprar cartas e terminar a série melhor de três.
- Persistência atômica do snapshot, runtime da partida, ledger de operações e journal de eventos.

Para executar uma partida de demonstração em um banco temporário e obter um relatório JSON para o catálogo alpha v0.3:

```bash
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
```

Para salvar o relatório:

```bash
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py --json-out /tmp/soulsbo-match.json
```

O cenário esperado termina com Player A vencendo por 2–1, após três rodadas. O script verifica `quick_check`, `integrity_check`, chaves estrangeiras, revisão e sequência de eventos antes de finalizar.

Para reproduzir todos os testes:

```bash
python -m unittest discover -s tests/card_engine_v2 -v
```

## Combate por fileira alpha v0.1

`combat.py` resolve simultaneamente as três fileiras no fechamento da rodada. O poder efetivo de cada lado é totalizado por fileira; o lado com maior valor causa a diferença positiva à vida do adversário. A vida começa em 20, fica persistida no runtime e é exibida na view. Vida zero encerra a partida; se ambos chegarem a zero na mesma resolução, o resultado é empate. O Bo3 permanece como fallback desta alpha.

O combate reutiliza `effective_power`, então bônus, clima, resistência climática e estados de controle são computados antes do dano. Não há atributos de ataque, armadura, defesa física ou HP por unidade no contrato atual; esta implementação não destrói automaticamente unidades. Remoções explícitas, Execução, sacrifício integrado ao controlador, proteção e Vingança usam o `GameplayResolver`.

Ruleset atual: `data/card_game/card-engine-v2-alpha-ruleset.v0.5.json`. A economia alpha concede +1 energia no início de cada turno, limitada a 5, com saldo persistente entre rodadas. Há preços provisórios explícitos para todas as 27 cartas permitidas e dez líderes; ações sem preço explícito são rejeitadas. A agenda não foi aprovada para release nem validada por playtest humano. Raridade e `legacy_deck_cost` não são entradas do cálculo energético. O registry de habilidades manuais permanece vazio porque nenhuma carta atual declara esse tipo de habilidade; a API genérica é testada apenas com uma definição sintética. Energia fica no runtime sidecar persistido, sem alterar CardInstance v7 ou schema SQLite. Ver `docs/card-engine-v2-energy-economy-alpha-v0.2.md`, `docs/card-engine-v2-alpha-energy-cost-schedule-v0.1.md` e `docs/card-engine-v2-alpha-activated-abilities-v0.1.md`.

## Sacrifício normal da partida alpha v0.1

`AlphaMatchController.sacrifice_target_offer()` constrói uma oferta de alvos aliados no campo, vinculada à revisão atual. `AlphaMatchController.sacrifice_unit()` aceita a identidade física escolhida somente com `expected_revision` da oferta mais recente. A execução revalida a seleção dentro da transação, usa `unit.sacrifice`/causa canônica `sacrifice`, consome a ação do turno e grava os eventos de remoção, Vingança e conclusão da ação no mesmo commit.

O comportamento preserva as decisões do Grupo F: sacrifício ignora Égide sem consumir a carga do escudo; incrementa `sacrifice_count` (não `board_removal_count`); e dispara `effect.vengeance_on_removal` somente depois da remoção bem-sucedida, aplicando o bônus a aliados sobreviventes na fileira original. O replay da mesma `operation_id` não repete a remoção nem o bônus. O sacrifício consome o turno alpha, mas não tem custo energético configurado nesta revisão.

Ver `docs/card-engine-v2-sacrifice-match-alpha-v0.1.md` para o contrato da operação, eventos e limites.

## Deck fatigue — ruleset alpha v0.3 conectado ao controlador (documentação v0.2)

`AlphaMatchController` aplica fatigue no início de cada turno individual quando a pilha de compra do jogador está vazia. A política alpha usa 1 de dano inicial e incremento 1 por aplicação posterior, sem teto; cada jogador mantém contador próprio durante a partida. O primeiro turno de cada jogador após a distribuição inicial é isento. Dano letal encerra imediatamente a partida antes da ação do jogador. Os parâmetros são provisórios e dependem de balanceamento/playtests; não são aprovados para publicação.

A mão inicial padrão agora é quatro cartas. A compra de até duas cartas no começo da nova rodada permanece uma regra do harness de teste; a cadência geral de compra por turno não foi inferida nem implementada. `docs/card-engine-v2-deck-fatigue-contract-v0.1.md` e `deck_fatigue_candidate.py` são referências históricas da fase de decisão, não a fonte ativa de runtime.

O runtime persiste `deck_fatigue_count_by_player` e `initial_turn_exemption_pending_by_player` no sidecar de partida; eventos de fatigue/dano/derrota/fim são transacionais e causais. Não há mudança de CardInstance schema 7, SQL ou migração. Detalhes e limites estão em `docs/card-engine-v2-deck-fatigue-alpha-v0.2.md`.

O teste histórico de referência matemática ainda pode ser executado com:

```bash
python -m unittest tests.card_engine_v2.test_deck_fatigue_candidate -v
```

## Limites atuais da partida alpha

- A allowlist é deliberadamente limitada a 27 cartas, 12 famílias de efeitos de entrada, combos, quatro passivas de facção e dez líderes alpha; não representa o catálogo inteiro nem significa que suas definições foram aprovadas para publicação.
- O staging contém os 137 registros históricos para rastreabilidade, mas apenas 27 estão autorizados na alpha; os outros 110 continuam `blocked_staging_only`. Todos os 137 ainda constam como não reconstruídos e com revisão de facção pendente no snapshot utilizado.
- Não há interface Discord, HTTP ou frontend, nem integração com o banco publicado.
- Combos, passivas e líderes estão conectados apenas no subconjunto alpha: 27 definições de combo são carregadas, mas nove têm tags-fonte completas na allowlist atual; 18 continuam inativas. As quatro passivas e os dez líderes possuem handlers alpha e testes isolados, mas não constituem o sistema completo de facções/líderes de produção. Sacrifício normal já é uma ação do controlador alpha, mas ainda não está ligado a uma interface Discord/HTTP; Rykard mantém seu handler específico de líder.
- A partida alpha demonstra o conjunto de cartas e regras allowlisted; não é uma implementação integral de todos os contratos A–F.
- O SQLite é local/single-host e síncrono. Não há adapter `aiosqlite`/worker para chamadas em event loop.
- Nenhuma migração de partidas reais, cutover ou substituição do motor antigo está autorizada ou executada.

## Limites do resolvedor genérico (separado do controlador de partida)

- Não existe catálogo completo ligado ao registry: `ActionDefinition`, políticas, perfis e parâmetros do resolvedor genérico continuam vindo de configuração confiável do servidor. O controlador de partida usa apenas a allowlist alpha documentada acima.
- O cálculo de poder efetivo está implementado em `power.py` e ligado ao `AlphaMatchController` com releases alpha de clima/estados. Chamadas independentes ao `GameplayResolver` ainda precisam fornecer `metric_resolver` explicitamente.
- `bonus_clamp_policy_id` é preservado; apenas `balance.alpha.raw_grants.v1` é aceito nesta alpha. Não existe catálogo geral de políticas de clamp.
- O controlador de partida implementa turnos/passagem e cobrança alpha por ID para `play_unit`, `play_special` e `activate_leader`; a API genérica `activate_card_ability` aceita somente habilidades declaradas no registry server-side e ainda não há uma habilidade ativa real registrada nas 27 cartas.
- O controlador ainda não expõe todas as ações do `GameplayResolver`; movimento e grants genéricos de bônus/proteção continuam sem API geral no fluxo da partida, salvo quando explicitamente declarados como uma habilidade manual no registry. Sacrifício normal está integrado no recorte alpha.
- A seleção `manual_secondary_set` e algumas estratégias de seleção genérica continuam não suportadas; o resolvedor rejeita configurações fora do subconjunto implementado.

## Restrições operacionais

- Handlers de jogo são callbacks síncronos e puros; não podem fazer I/O externo.
- O repositório usa `sqlite3` síncrono. Não chame diretamente no event loop do Discord/HTTP sem adapter assíncrono ou worker.
- WAL pressupõe arquivo local/single-host; multi-host e filesystem de rede não estão cobertos.
- O arquivamento legado ainda não é um migrador completo nem lê o banco de produção.
- Não executar cutover ou migração de partidas reais com este alpha.


## Combos, passivas e líderes na partida alpha

A release de conteúdo `alpha-test-only.catalog.v0.3` carrega registries hash-pinned de 27 combos históricos, quatro passivas de facção e dez líderes. `AlphaMatchController` resolve no máximo um combo por jogada, exige que a carta recém-jogada contribua com uma tag requerida, respeita prioridade explícita e limita cada combo a uma ativação por jogador por rodada. O bônus individual vai para a carta ativadora; o bônus coletivo alcança aliados previamente presentes na mesma fileira.

As passivas são declaradas no setup por `player_factions` (ou inferidas do líder selecionado) e concedem +1 à primeira unidade jogada da mesma facção, uma vez por rodada. Os líderes são selecionados no setup por `leaders` e podem ser usados uma vez por partida com `activate_leader`. Os handlers alpha incluem Godfrey, Morgott, Radagon, Mohg, Rykard, Esgar, Papa Esquecido, Rennala, Astel e Loretta. Esses registries e handlers são exclusivos do ambiente de teste; não equivalem a aprovação do catálogo integral ou integração com Discord/API.


Para validar combos, quatro passivas de facção e os dez líderes implementados na alpha, execute:

```bash
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

O catálogo registra 27 combinações históricas, mas apenas 9 têm todas as tags obrigatórias presentes nas 27 cartas da allowlist atual. As outras 18 permanecem registradas e inativas até que cartas participantes sejam adicionadas ao ambiente de teste.


## Economia de energia alpha v0.2 — ruleset v0.5

O ruleset atual é `data/card_game/card-engine-v2-alpha-ruleset.v0.5.json`. O jogador ativo recebe +1 energia no início de cada turno, até 5; o saldo permanece entre rodadas. A agenda provisória tem preços explícitos por ID para as 27 cartas permitidas e os dez líderes (cartas 1–5; líderes 2–3). Não são preços aprovados para release; não foram testados com jogadores humanos nem telemetry. Raridade (`rarity_id`) e `deck_cost_legacy` não são fontes de custo energético. Ações `play_unit`, `play_special` e `activate_leader` sem preço configurado são rejeitadas; saldo insuficiente também rejeita antes de qualquer consumo. Pagamentos aprovados são persistidos na mesma transação e auditados por `player_energy_spent`. A energia continua no runtime sidecar, sem alterar CardInstance v7 ou DDL. Ver `docs/card-engine-v2-energy-economy-alpha-v0.2.md` e `docs/card-engine-v2-alpha-energy-cost-schedule-v0.1.md`.

O registry de habilidades manuais (`card-engine-v2-alpha-activated-abilities.v0.1.json`) está intencionalmente vazio: nenhuma das cartas alpha atuais declara habilidade manual. A infraestrutura `activate_card_ability` exige registry/custo/TargetPolicy explícitos, usa ofertas server-side, consome energia e turno atomicamente e limita usos por instância. A API é coberta por fixture sintética, não por habilidade fictícia adicionada ao catálogo. Ver `docs/card-engine-v2-alpha-activated-abilities-v0.1.md`.

## Histórico — economia de energia alpha v0.1 (rev. 24)

A revisão v0.4 implementava ganho de energia e infraestrutura de custo explícito, porém seus mapas estavam vazios e ações sem preço eram permitidas sem cobrança. Essa política foi substituída pelo ruleset v0.5; consultar o documento histórico `docs/card-engine-v2-energy-economy-alpha-v0.1.md` apenas para entender a primeira tranche.


## Deck Builder competitivo e proveniência de exemplares alpha v0.2

O fluxo competitivo usa identidade física exata, separado do harness determinístico:

- `card_id` identifica o modelo do catálogo; `exemplar_id` é a chave global da cópia em `cartas_exemplares.id`; `instance_id` é o UUIDv4 que representa a ocorrência dentro da partida.
- `AlphaDeckBuilder` valida 30 slots, máximo três cópias por modelo, allowlist, facção/líder, um exemplar real por slot, propriedade do jogador e igualdade entre `card_id` do slot e do exemplar.
- `SQLiteDeckRepository` persiste `card_ids` e `exemplar_ids` em arrays alinhados. A migração v1→v2 adiciona proveniência vazia aos decks antigos; nenhum ID físico é inventado. Decks antigos precisam ser regravados a partir da coleção antes do matchmaking.
- `legacy_collection_exemplars(database, user_id)` lê `Database.coliseu_listar_exemplares`, incluindo ID global, dono, modelo, raridade de exibição e poder individual atual. A ponte é somente leitura; `database.py` e o banco legado não são modificados.
- No matchmaking, a posse e o modelo são revalidados, IDs globais repetidos entre jogadores são rejeitados e cada slot embaralha junto com seu exemplar. A API sync/async de aplicação não aceita seed de shuffle; a ordem e o primeiro jogador usam aleatoriedade do servidor. Seeds reproduzíveis ficam somente no controlador interno de testes.
- O snapshot da instância congela o poder individual atual no momento da partida. `effective_power`, métricas de targeting e filtros de líder usam esse poder por exemplar; raridade é somente classificação de apresentação e não altera poder, elegibilidade ou efeitos. `Primordial` está incluída no vocabulário de exibição.
- `view_match_for_player()` cria projeção que mostra os exemplares da mão própria e oculta as cartas e IDs físicos da mão adversária. O handler HTTP/Discord deve derivar `authenticated_player_id` da sessão/principal autenticado, não do corpo da requisição. `view_match()` sem viewer continua sendo uma projeção privilegiada para diagnóstico/testes.
- `AsyncAlphaGameApplication` encaminha operações SQLite por `asyncio.to_thread`; continua sendo apenas uma fachada de aplicação, não uma integração Discord/HTTP pronta.

Exemplo simplificado (a parte de autenticação é responsabilidade do adapter de transporte):

```python
from sistemas.card_engine_v2.application import (
    AlphaGameApplication, AsyncAlphaGameApplication, legacy_collection_exemplars
)

app = AlphaGameApplication(
    match_database_path="var/card-engine-v2-matches.sqlite3",
    deck_database_path="var/card-engine-v2-decks.sqlite3",
)
async_app = AsyncAlphaGameApplication(app)

# O transporte obtém este ID da sessão autenticada, nunca do payload do cliente.
owned_exemplars = await legacy_collection_exemplars(bot.db, authenticated_user_id)
await async_app.save_deck(
    owner_player_id=authenticated_user_id,
    deck_id="main",
    name="Principal",
    card_ids=deck_card_ids,
    exemplar_ids=selected_exemplar_ids,  # mesmo tamanho/ordem que card_ids
    faction_id="golden_order",
    leader_id="comandante_fornalha",
    owned_exemplars=owned_exemplars,
)

# Na view pública, passe o principal autenticado para ocultar a mão rival.
match_view = await async_app.view_match_for_player(match_id, authenticated_user_id)
```

**Limites atuais:** o adapter de coleção está implementado e testado com o contrato de `coliseu_listar_exemplares`, mas ainda não existe um handler real que injete `bot.db`/principal autenticado. Não há UI Discord/site, endpoints HTTP, autenticação de produção, transação distribuída entre banco de coleção e SQLite v2, nem playtests humanos. A projeção sem viewer é privilegiada e não deve ser enviada a jogadores. Consulte `docs/card-engine-v2-deck-builder-alpha-v0.2-exemplar-provenance.md`.

O documento `docs/card-engine-v2-deck-builder-alpha-v0.1.md` permanece como registro histórico do estágio anterior, em que a posse era validada por quantidade de `card_id`.
