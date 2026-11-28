# Handoff mais recente — fechamento de produto e prontidão operacional (rev. 31, 2026-11-28)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev30.zip`.  
**Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev31.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, ainda é draft implementado, não congelado.  
**Ruleset:** `alpha-test-only.ruleset.v0.5`; deck competitivo 30 cartas, máximo de três cópias por modelo, quatro cartas iniciais, vida 20, combate por fileira, fatigue por turno individual e energia alpha.  
**Catálogo:** 137 modelos históricos; 27 permitidos e 110 bloqueados; 27 combos (nove alcançáveis, 18 inativos), quatro passivas, dez líderes e 12 famílias de efeitos de entrada.  
**Validação do motor:** 240 testes aprovados + 61 subtests parametrizados; suite oficial playable alpha aprovada; staging 137/27/110; Bo3 A 2–1 B (97 eventos) e demo combo/passiva/líder 20–10 (49 eventos), ambas com SQLite íntegro.  
**Validação operacional local:** YAML/Compose parseado com PyYAML, entrypoint shell validado por `sh -n`, Python compilado, JavaScript validado por Node 22. Docker Engine não está instalado no ambiente; portanto o build da imagem não foi executado.  
**Preflight do ambiente de criação:** 9 pass, 0 warnings, 22 blockers. Faltam pacotes exatos, secrets Discord/OAuth, URL pública, `DATA_DIR` e banco legado real. Não houve login Discord, OAuth, `docker build`, staging conectado ou deploy.

## O que mudou na rev. 31

- Conquistas passaram a derivar progresso no servidor a partir de exemplares, movimentações, ranking legado e partidas finalizadas do Card Engine v2. O navegador não pode fornecer progresso. O desbloqueio é monotônico e persistido por transação; GET permanece somente leitura. “Apostador” e “Sobrevivente” aparecem como tracking pendente porque o inventário ainda não registra nível individual e tentativas/falhas de evolução com risco.
- A rota `/apostas` agora tem página explícita de indisponibilidade. Endpoints de apostas em Denários/cartas/torneios falham fechados e não debita nem reserva recursos. Não existe escrow, aceitação bilateral, cancelamento e liquidação atômica completos.
- A evolução com risco permanece desabilitada e não altera exemplares ou amuletos. Foi mantida separada da Forja de ascensão de raridade. O esquema atual de inventário não sustenta de forma segura níveis individuais, trilha de tentativas/falhas e consumo de amuleto.
- Adicionado `Dockerfile` com Python 3.13, dependências fixadas e usuário não-root; `compose.yaml` com volume nomeado persistente, root filesystem read-only, tmpfs, cap_drop, no-new-privileges e healthcheck condicionado a HTTP+SQLite+Discord; entrypoint executa o preflight antes de iniciar o bot.
- Adicionado `.env.production.example` sem credenciais, `deploy/README.md`, `requirements-dev.txt` e GitHub Actions para testes, compilação, JavaScript, configuração Compose e build Docker.
- Adicionado `scripts/runtime_preflight.py` para validar versões exatas, secrets sem imprimi-los, callback OAuth, hostname público, volume gravável e schema legado em read-only. Placeholders como `https://SEU-DOMINIO` são rejeitados mesmo quando o callback combina literalmente.
- Adicionado `scripts/backup_sqlite.py`, que usa a Online Backup API e `integrity_check`; caminhos com espaços e caracteres especiais são cobertos por teste.
- Corrigido o endpoint de sincronização de conquistas: aceita somente objeto JSON vazio, rejeita progresso enviado pelo cliente e rejeita JSON malformado. GET não persiste progresso.

## Módulos que continuam intencionalmente bloqueados

- **Apostas:** não abrir até completar escrow de Denários e exemplares, aceitação dos dois jogadores, idempotência, timeout/cancelamento, liquidação atômica, auditoria e testes de abuso.
- **Evolução com risco:** não abrir até schema por exemplar para nível, ledger de tentativas, probabilidades/custos aprovados, transação de recursos e inventário real de amuletos. Falha pode destruir carta conforme redesign; não implementar com SQL legado incompleto.
- **Conquistas Apostador/Sobrevivente:** tracking pendente pelas mesmas lacunas do sistema de evolução com risco; não são reportadas como zero e não podem ser forjadas pelo cliente.
- **Catálogo completo:** 110 modelos permanecem bloqueados; 18 combos inativos; as 12 famílias de efeitos da alpha não equivalem às 54 famílias canônicas do catálogo histórico.
- **Balanceamento:** custos são provisórios e ainda não receberam playtests humanos/telemetria com custos individuais reais.

## Resultado do preflight neste ambiente

`docs/card-engine-v2-rev31-validation.json` registra o resultado desta revisão. A execução real de `scripts/runtime_preflight.py` neste host encontrou 9 pass e 22 blockers: `discord.py` e `aiosqlite` ausentes; outras distribuições em versão diferente da pinagem; `google-genai` ausente; variáveis Discord/OAuth/session/public URL ausentes; `DATA_DIR` e banco não configurados. O ambiente não possui Docker CLI e não conseguiu acessar PyPI por rede/DNS, portanto nenhum pacote foi instalado e nenhum container foi construído.

**Não declarar o Soulsbo como publicado ou pronto para jogadores reais.** A rev. 31 entrega código e artefatos de implantação reproduzível, além de proteção para módulos incompletos; a ativação exige que o proprietário configure secrets, restaure a base real e execute o runbook em um host compatível. A validação final exige duas contas Discord em staging, partidas completas, reinício/recuperação, verificação OAuth, coleção e backups.

## Próxima sequência obrigatória

1. No host de staging, preencher `.env` a partir de `.env.production.example` no painel seguro, restaurar backup real para volume persistente e instalar as dependências através do Docker build/CI.
2. Executar `python scripts/runtime_preflight.py --project-root /app` e `python scripts/card_engine_v2_staging_preflight.py --project-root /app --probe-discord`.
3. Fazer login OAuth de duas contas, montar decks com exemplares reais, desafiar/aceitar, completar Bo3, verificar privacidade, histórico e recovery após reinício.
4. Corrigir qualquer falha de staging antes de migrar/abrir para jogadores.
5. Em paralelo, fechar a implementação das demais famílias de efeito e expansão do catálogo sem liberar os 110 bloqueados por conveniência.
6. Só depois concluir escrow de apostas e evolução com risco transacional, revisar balanceamento com humanos e preparar beta fechado.

Leia nesta ordem: `docs/card-engine-v2-rev31-product-completion.md`, `docs/card-engine-v2-rev31-change-manifest.md`, `docs/card-engine-v2-rev31-validation.json`, `docs/card-engine-v2-operational-deployment-v0.1.md`, `deploy/README.md`, `scripts/runtime_preflight.py`, `scripts/backup_sqlite.py`, `sistemas/card_game_achievements.py`, `sistemas/card_engine_v2/README.md`.

---

---

# Handoff mais recente — integração web e atualização automática do Card Engine v2 (rev. 29)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev28.zip`.  
**Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev29.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset:** `alpha-test-only.ruleset.v0.5`; 30 cartas por deck, até três cópias por modelo, quatro cartas iniciais, vida 20, combate por fileira, fatigue por turno e economia de energia alpha.  
**Catálogo:** 137 modelos históricos; 27 permitidos, 110 bloqueados; 27 combos registrados (nove alcançáveis, 18 inativos); quatro passivas, dez líderes e 12 famílias de efeitos de entrada.  
**Validação:** 209/209 testes; `py_compile` e `node --check` aprovados; sete testes HTTP; 77 rotas registradas no hub; staging 137/27/110; simulação Bo3 A 2–1 B (97 eventos) e demonstração combo/passiva/líder 20–10 (49 eventos), ambas com SQLite íntegro.

## O que mudou na rev. 29

- O link **Card Engine v2 · Alpha** foi adicionado ao hub inicial. A página privada `/card-engine-v2` reutiliza a sessão Discord assinada existente; sem sessão, redireciona ao login Discord.
- `site_card_engine_v2.py` registra API e página pelo `site_hub.py`, usando o mesmo gateway compartilhado pelo cogs Discord e os bancos dedicados em `DATA_DIR/card_engine_v2/`.
- A página apresenta a coleção permitida do próprio usuário, construtor de deck, decks salvos e partidas em que ele participa. O deck exige 30 exemplares físicos distintos, máximo de três cópias por `card_id`, líder válido e posse atual revalidada pelo servidor.
- O jogador pode criar, editar com compare-and-swap de versão e excluir decks próprios. Excluir um deck não remove os exemplares da coleção.
- O site lista até 50 partidas próprias, permite reabrir a projeção privada, acompanhar o estado do tabuleiro e executar jogar unidade, jogar especial, ativar líder, sacrifício e passar turno. Ofertas de alvos permanecem server-side. Convites e criação de desafio entre jogadores continuam no Discord; o site não implementa fila ou matchmaking próprio.
- A página atualiza a partida aberta a cada dez segundos e busca histórico sanitizado por cursor. A UI Discord verifica `state_revision` a cada 12 segundos e substitui a view privada por estado novo; o botão **Histórico** abre timeline paginada.
- A API deriva a identidade de `bot._api_user_id`, exige origem same-site nas escritas, limita JSON a 32 KiB, exige `expected_revision`/UUIDv4 para ações e não confia em `player_id`, custos, proprietário ou alvos enviados pelo navegador. O histórico omite IDs de instância, operação e causalidade.
- O gateway e as consultas de histórico/decks foram ampliados, sem escrita no banco legado. A aplicação async continua despachando SQLite para threads.

## Evidência e limitações

- `tests/card_engine_v2`: 209/209. Os sete testes HTTP cobrem login obrigatório, coleção própria, CSRF, deck create/update/delete, controle de versão, isolamento de partidas, ações idempotentes, sanitização de histórico e tamanho do payload.
- `site_hub.registrar_rotas` foi executado com bot fake; 77 registros de método/caminho, incluindo página e API v2. `py_compile` e `node --check` passaram.
- Simulações oficiais preservadas: Bo3 A 2–1 B, 97 eventos e SQLite `integrity_check=ok`; combo/passiva/líder A 20–10, 49 eventos e SQLite `integrity_check=ok`. Staging 137/27/110 aprovado.
- `aiohttp` está presente; `discord.py==2.7.1` e `aiosqlite==0.22.1` não estão instalados neste ambiente. Não foi possível importar/rodar o bot conectado ao Discord, abrir OAuth real, testar callbacks reais de `discord.ui`, chamar o banco publicado ou fazer deploy. As dependências estão declaradas no `requirements.txt`.
- A integração web foi exercitada em `aiohttp.TestServer` com gateway e inventário fake; ainda é necessário validar a ponte `Database.coliseu_listar_exemplares` contra a instância real da coleção.
- A lista de partidas do site limita-se a 50 itens; o histórico pagina por cursor. O desafio entre jogadores continua sendo criado pelo Discord. Sem playtest humano ou validação de balanceamento; 110 cartas continuam bloqueadas; preços de energia seguem provisórios.
- Os cinco arquivos protegidos do legado permanecem byte a byte idênticos: `bot.py`, `database.py`, `sistemas/gwent.py`, `sistemas/cartas.py`, `site/app.js`.

## Próxima prioridade

Executar staging com dependências instaladas, OAuth, bot Discord e dois usuários de teste. Validar inventário real e exemplares evoluídos, criar decks, desafiar/aceitar, jogar ações, verificar refresh nos dois painéis, reiniciar o bot e reabrir a partida no site e no Discord. Corrigir problemas de runtime antes de ampliar catálogo ou liberar beta.

Leia nesta ordem: `docs/card-engine-v2-site-alpha-v0.1.md`, `docs/card-engine-v2-site-alpha-v0.1-validation.json`, `docs/card-engine-v2-site-alpha-v0.1-change-manifest.md`, `site_card_engine_v2.py`, `site/card-engine-v2.html`, `site/assets/card-engine-v2.js`, `cogs/card_engine_v2_ui.py`, `sistemas/card_engine_v2/discord_gateway.py` e `sistemas/card_engine_v2/README.md`.

---


# Handoff mais recente — proveniência física de exemplares no Deck Builder competitivo (rev. 27)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev26.zip`.  
**Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev27.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset ativo:** `alpha-test-only.ruleset.v0.5`; mão inicial quatro, vida inicial 20, combate por fileira, fatigue por turno e economia de energia.  
**Regras de deck:** 30 cartas, até três cópias por `card_id`, mão inicial quatro; primeiro jogador sorteado no servidor.  
**Catálogo:** 137 modelos históricos; 27 permitidos na alpha, 110 bloqueados; 27 combos registrados (nove alcançáveis, 18 inativos); quatro passivas de facção; dez líderes; 12 famílias de efeitos de entrada.  
**Validação:** 188/188 testes; `py_compile` aprovado; staging 137/27/110 aprovado; simulação Bo3 A 2–1 B (97 eventos), demo combo/passiva/líder 20–10 (49 eventos), ambas com SQLite íntegro.

## O que mudou na rev. 27

- A identidade física chega agora até o matchmaking e às instâncias da partida: `card_id` identifica o modelo, `exemplar_id` é `cartas_exemplares.id` global e `instance_id` é o UUIDv4 da ocorrência na partida.
- Cada slot competitivo salva um `card_id` e um `exemplar_id` alinhados. O serviço valida propriedade, modelo, unicidade por deck, allowlist e limite de três cópias; revalida os dados vivos no matchmaking e rejeita ID físico repetido entre os dois jogadores.
- `legacy_collection_exemplars()` consulta `Database.coliseu_listar_exemplares` em modo somente leitura e transporta dono, modelo, ID global, poder individual, raridade e origem. Nenhuma escrita ou migração foi feita no banco legado.
- No matchmaking, o poder atual do exemplar é congelado em `exemplar_snapshot.power_base`, independente do snapshot estático do catálogo. Cálculo de poder, métricas de targeting e filtros dos líderes usam a mesma função `base_power(instance)`.
- A raridade permanece apenas classificatória. A ponte agora reconhece `Primordial`, existente no banco e na progressão legada; não concede poder, custo, elegibilidade ou efeito.
- `SQLiteDeckRepository` usa schema 2, persiste `exemplar_ids_json` e migra saved decks schema 1 preenchendo `[]`, sem inventar IDs. Decks antigos sem proveniência não entram em matchmaking até serem regravados com IDs físicos reais.
- A view destinada ao jogador inclui os exemplares da mão própria e oculta a mão e os IDs físicos do oponente. `view_match_for_player` exige que o adapter de transporte forneça o ID do principal autenticado; a projeção sem viewer é privilegiada e serve somente para simulação/diagnóstico.
- O serviço sync/async de aplicação não aceita seeds de embaralhamento nem seed do primeiro jogador. O matchmaking usa `SystemRandom`; seeds determinísticas permanecem restritas ao controlador interno de baixo nível, usado por simulações/testes.
- O schema draft `CardInstance v0.7` continua na versão 7; `exemplar_snapshot` é opcional para compatibilidade estrutural, mas novas instâncias competitivas `deck_exemplar` exigem `exemplar_id` e snapshot validado.
- Foram acrescentados testes para IDs físicos, poder por exemplar, raridade Primordial, duplicidade global, revalidação de posse, privacidade da view e rejeição de seeds fornecidas pelo cliente à API sync/async de aplicação.

## Limites que continuam bloqueando produção

- A integração de coleção é um adapter de leitura testado pelo contrato `coliseu_listar_exemplares`; nenhum handler real injeta ainda `bot.db` e identidade autenticada.
- Discord, HTTP, site/frontend, autenticação de produção e UI de deck builder não estão conectados. A fachada async é somente a camada de aplicação preparada.
- Não existe transação distribuída entre o banco legado da coleção e os SQLite separados do Card Engine v2; a coleção é revalidada antes de a instância da partida congelar seu snapshot.
- O catálogo alpha continua com 27 cartas; 110 modelos históricos seguem bloqueados. 18 combos não são alcançáveis com as tags presentes.
- Os custos energéticos continuam provisórios e sem playtests humanos; os resultados de simulação usam fixtures para isolar mecânicas.
- Não há aprovação de balanceamento, migração de usuários/partidas, cutover ou substituição do motor antigo. Os cinco arquivos centrais do legado permanecem intocados.

## Próxima prioridade

Implementar a primeira integração de transporte/UI para o Deck Builder e partida usando `AsyncAlphaGameApplication`, com player ID derivado do principal autenticado e view segura por jogador. Não passar `owner_player_id` arbitrário do cliente; não chamar SQLite diretamente em handler; não enviar a projeção privilegiada sem viewer. Em paralelo, preparar o plano de reconstrução dos 110 modelos sem liberá-los automaticamente.

Leia nesta ordem: `docs/card-engine-v2-deck-builder-alpha-v0.2-exemplar-provenance.md`, `docs/card-engine-v2-deck-builder-alpha-v0.2-exemplar-provenance-validation.json`, `docs/card-engine-v2-deck-builder-alpha-v0.2-exemplar-provenance-change-manifest.md`, `sistemas/card_engine_v2/application.py`, `sistemas/card_engine_v2/deck_builder.py`, `sistemas/card_engine_v2/deck_repository.py`, `sistemas/card_engine_v2/match.py` e `sistemas/card_engine_v2/README.md`.

---

# Handoff mais recente — Deck Builder e serviço de aplicação competitiva (rev. 26)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev25.zip`.  
**Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev26.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset ativo:** `alpha-test-only.ruleset.v0.5`; mão inicial quatro, vida inicial 20, combate por fileira, fatigue por turno e economia de energia.  
**Regras oficiais de deck aplicadas:** 30 cartas, até três cópias por `card_id`, mão inicial de quatro; primeiro jogador sorteado pelo servidor. A proposta de 12 cartas/orçamento de 32 pontos segue não aprovada e não foi aplicada.  
**Catálogo:** 137 modelos históricos; 27 permitidos na alpha e 110 bloqueados; dez líderes alpha.  
**Validação:** 171/171 testes; compilação Python aprovada; staging 137/27/110 aprovado; simulação Bo3 A 2–1 B (97 eventos), demo combo/passiva/líder (49 eventos), ambas com SQLite íntegro.

## O que mudou na rev. 26

- `AlphaDeckBuilder` aplica validação autoritativa de 30 cartas, máximo três cópias, IDs na allowlist, tipos reconhecidos, facção/líder compatíveis e quantidade possuída. Não foram adicionadas regras de deckbuilding não especificadas pela fonte oficial.
- `SQLiteDeckRepository` persiste decks salvos em banco SQLite exclusivo, com isolamento por proprietário, chave `(owner_player_id, deck_id)`, atualizações/exclusões por versionamento otimista e marcador para recusar bases não identificadas.
- `AlphaGameApplication` implementa casos de uso para validar, salvar, consultar, listar e excluir decks e criar partidas a partir dos decks pertencentes a cada jogador. A propriedade é revalidada na hora do matchmaking.
- `AlphaMatchController.create_competitive_match()` é a entrada estrita para partidas competitivas alpha; `create_match()` continua disponível para fixtures internas curtas e determinísticas.
- O caminho competitivo embaralha ambos os decks no servidor, distribui quatro cartas e sorteia o primeiro jogador com aleatoriedade do sistema. O sorteio também determina quem começa com o primeiro incremento de energia. A API de aplicação não expõe seed nem escolha do jogador inicial ao cliente.
- `AsyncAlphaGameApplication` encaminha I/O SQLite por `asyncio.to_thread`; a superfície de ações é allowlisted. `legacy_collection_counts()` consulta somente `coliseu_listar_colecao` no banco legado.
- Foram adicionados 21 testes para validação, persistência, autorização por proprietário, revalidação de inventário, fachada async e setup competitivo.

## Limites que continuam bloqueando produção

- O catálogo permite apenas 27 dos 137 modelos históricos; 110 continuam bloqueados.
- A validação de posse é por quantidade de modelo (`card_id`), não liga ainda cada slot à identidade de `cartas_exemplares.id` nem a exemplares evoluídos.
- Não existe ainda interface de deck builder no Discord/site, nem handlers HTTP/Discord conectados à `AlphaGameApplication`. A fachada async é uma fronteira preparada, não a integração final.
- Autenticação/autorização do transporte ainda precisa derivar o player ID da sessão/Discord; não confiar em IDs enviados pelo cliente.
- Ruleset de compra, preços experimentais e catálogo permanecem alpha; não houve playtest humano nem validação de balanceamento.
- Sem migração, cutover ou conexão a banco publicado. Os cinco arquivos centrais legados permanecem intocados.

## Próxima prioridade

Completar proveniência de exemplares e validar integração do inventário de ponta a ponta; em seguida construir o fluxo de deck builder na interface/Discord usando somente `AlphaGameApplication`, com player ID obtido do principal autenticado. Não conectar diretamente o bot ao SQLite nem permitir que o cliente escolha starter, deck de outro usuário, alvo ou custo.

Leia nesta ordem: `docs/card-engine-v2-deck-builder-alpha-v0.1.md`, `docs/card-engine-v2-deck-builder-alpha-v0.1-validation.json`, `docs/card-engine-v2-deck-builder-alpha-v0.1-change-manifest.md`, `sistemas/card_engine_v2/application.py`, `sistemas/card_engine_v2/deck_builder.py`, `sistemas/card_engine_v2/deck_repository.py` e este README.

---

# Handoff mais recente — agenda de custos e infraestrutura de habilidades manuais (rev. 25)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev24.zip`.  
**Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev25.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset ativo:** `alpha-test-only.ruleset.v0.5`; mão inicial quatro, vida inicial 20, combate por fileira, fatigue por turno e economia de energia.  
**Catálogo:** 137 modelos históricos; 27 permitidos na alpha e 110 bloqueados.  
**Validação:** 150/150 testes aprovados; staging 137/27/110; simulação Bo3 (97 eventos) e demonstração combo/passiva/líder (49 eventos) com SQLite íntegro; ZIP rev. 25 extraído em diretório limpo e testado com 150/150.

## O que mudou na rev. 25

- A agenda alpha experimental define custos explícitos para os 27 `card_id` permitidos e dez `leader_id`. Cartas variam de 1 a 5 de energia; líderes de 2 a 3.
- Os custos são propostas de playtest, não aprovadas para release nem validadas por playtest humano/telemetria. São baseados em poder-base, magnitude/alcance dos efeitos implementados, condicionalidade e custo de oportunidade da ação; raridade e `deck_cost_legacy` não são entradas.
- `play_unit`, `play_special` e `activate_leader` exigem preço explícito; ID sem preço ou energia insuficiente rejeita sem consumir carta/turno/energia/ativação. Não existem ações de carta/líder gratuitas por ausência de preço.
- O pagamento é persistido atomicamente com a execução e auditado pelo evento `player_energy_spent`. O jogador recebe +1 energia no início do seu turno, máximo 5, saldo persistente entre rodadas.
- A infraestrutura genérica `activate_card_ability` usa um registry server-side, oferta de alvo, custo explícito, limite por instância e pagamento transacional. A oferta é negada quando falta energia ou quando o limite já foi utilizado.
- O registry real segue vazio: nenhuma das 27 cartas alpha declara habilidade manual. Os efeitos `unit_on_play` não foram convertidos em habilidades repetíveis. O teste de ativação usa uma habilidade sintética somente em fixture isolada.
- Sacrifício permanece ação de turno sem custo energético.
- Não houve mudança de `CardInstance v0.7`, schema/DDL SQLite, migração ou cinco arquivos centrais do motor legado.

## Evidência e limites

- Suíte principal: 150/150.
- Matriz de preços: os 27 custos de carta e dez custos de líder são aceitos com saldo exato e rejeitados com saldo imediatamente inferior.
- Pagamentos de unidade, especial e líder testados; persistência/reabertura SQLite, limite 5, recusa sem mutação, replay idempotente e ativação sintética também testados.
- As simulações gerais usam uma fixture uniforme de custo 1 para isolar mecânicas de combate/efeitos/combos. Elas não validam o equilíbrio da tabela provisória. A tabela é verificada em testes de economia dedicados.
- Sem integração Discord/HTTP/frontend, banco publicado, adapter assíncrono, telemetria ou playtest humano. Preços devem ser revistos após partidas controladas.

## Próxima prioridade

Rodar playtests controlados com a allowlist de 27 cartas usando a tabela real por ID, recolher duração/energia por turno/uso e taxa de vitória e recalibrar custos. Em paralelo, revisar o conteúdo para identificar habilidades manuais que realmente existam nas fontes; só então povoar o registry. Não expandir a allowlist nem alterar raridade como parâmetro mecânico sem decisão própria.

Leia `docs/card-engine-v2-energy-economy-alpha-v0.2.md`, `docs/card-engine-v2-alpha-energy-cost-schedule-v0.1.md`, `docs/card-engine-v2-alpha-activated-abilities-v0.1.md`, `docs/card-engine-v2-playable-alpha-validation-v0.5.md` e `sistemas/card_engine_v2/README.md`.

---

# Handoff histórico — economia de energia alpha v0.1 (rev. 24)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev23.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-28-rev24.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset:** `alpha-test-only.ruleset.v0.4`; mão inicial padrão de quatro cartas.  
**Economia:** +1 energia no início de cada turno individual, máximo 5, saldo que persiste entre rodadas. A energia é persistida no runtime sidecar com CAS e exposta na view.  
**Custos:** mapas explícitos por `card_id` e `leader_id` estão conectados ao controlador, mas vazios na baseline. Cartas e líderes sem preço configurado permanecem jogáveis/ativáveis sem cobrança nesta alpha de compatibilidade. Custos de energia não são derivados de raridade nem de `deck_cost_legacy`.  
**Validação executada:** 145/145 testes; `py_compile` aprovado; staging 137/27/110 aprovado; simulação Bo3 Player A 2–1 Player B, 87 eventos, seis aplicações de fatigue e SQLite íntegro; demonstração combo/passiva/líder Player A 20–10 Player B, 44 eventos e SQLite íntegro. A verificação final do ZIP extraído e dos hashes legados está registrada no manifesto da entrega.

## O que mudou nesta revisão

- Runtime ganha +1 energia no início de cada turno, limitado a 5; o jogador inicial começa com 1 e o oponente recebe seu primeiro ponto quando seu turno começa.
- Energia não zera entre rodadas e é independente por jogador.
- `play_unit` e `play_special` consultam `card_energy_cost_by_card_id`; `activate_leader` consulta `leader_activation_energy_cost_by_leader_id`.
- Preço explícito é validado antes de efeitos/mutação. Saldo insuficiente rejeita a operação sem consumir carta, ativação, turno ou energia.
- Pagamento bem-sucedido é persistido na mesma transação e produz `player_energy_spent`; início de turno produz `player_energy_gained`.
- `view()` expõe saldo, máximo, turnos iniciados e custo configurado de cada carta da mão.
- O runtime rejeita saldos fora de faixa, mapas incompletos e contadores inválidos.
- Não houve alteração de `CardInstance v0.7`/schema 7 ou de DDL/migração SQLite; energia fica no sidecar.

## Limites deliberados

- Os mapas de preço de cartas e líderes permanecem vazios. Portanto, o ciclo de energia é funcional, mas a allowlist atual não está ainda limitada por custo energético. Não inventar preços por raridade: BUF-001, aprovado no Grupo B, estabelece raridade apenas classificatória. Não converter `deck_cost_legacy` em energia; esse campo pertence a construção de deck e não define custo por turno.
- A tabela de custo associada à raridade no redesign precisa ser reconciliada com a decisão aprovada BUF-001 antes de qualquer uso. Nesta revisão, valores energéticos são apenas suportados por ID explícito e não preenchidos.
- Ativação de líder aceita custo explícito por `leader_id`, porém nenhum líder tem custo configurado na baseline. Ainda não existe uma API genérica para ativar todas as habilidades individuais das cartas.
- Sacrifício e passar não consomem energia; continuam consumindo a ação/turno conforme regras alpha.
- A economia é alpha-only, sem Discord/HTTP/frontend/produção. Não houve mudança dos cinco arquivos centrais legados.

## Próxima prioridade

Elaborar uma tabela de custo energético explícita para as 27 cartas alpha, avaliando efeitos executáveis e impacto no ritmo de turno, independente da raridade. Revisar líderes separadamente e especificar uma ação genérica para habilidades ativas. Só depois atribuir preços ao catálogo ampliado e ligar o bot/interface ao motor.

---

# Handoff histórico — deck fatigue integrado ao controlador alpha (rev. 23)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev22.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-28-rev23.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset:** `alpha-test-only.ruleset.v0.3`; mão inicial padrão de quatro cartas.  
**Validação:** 135/135 testes; py_compile aprovado; staging 137/27/110; partida Bo3 A 2–1 B com 72 eventos, seis aplicações de fatigue e SQLite íntegro; demo combo/passiva/líder com SQLite íntegro.

## O que mudou nesta revisão

- Deck fatigue foi conectado ao `AlphaMatchController` e ocorre no início de cada turno individual quando a pilha de compra está vazia.
- Política provisória alpha: dano 1, depois 2, 3, 4...; sem teto; contador independente por jogador, persistente até o fim da partida.
- Cada jogador tem uma isenção no seu primeiro turno após a distribuição inicial.
- Dano é aplicado antes da ação. Vida zero finaliza a partida imediatamente e declara o outro jogador vencedor.
- A compra parcial de até duas cartas na nova rodada permanece como comportamento do harness alpha; fatigue é avaliada depois da compra, antes da ação do jogador que inicia a rodada.
- O setup padrão agora distribui quatro cartas na mão inicial, conforme `docs/CARD_GAME_REDESIGN.md`.
- Contadores são persistidos no runtime sidecar e expostos em `view()`. Eventos `deck_fatigue_applied`, `player_damage_applied`, `player_defeated` e `match_finished` são registrados causalmente.
- Não há mudança de CardInstance schema v7, SQL ou migração de banco.

## Decisões de balanceamento (provisórias, alpha-only)

A fonte oficial define dano crescente por turno, mas não fixa valores. Para permitir implementação/teste, esta alpha adota 1 de dano inicial, incremento de 1, sem teto, sem reset do contador durante a partida e sem reciclar o descarte automaticamente. Não tratar esses números como balanceamento publicado; serão revisados depois de playtests.

O redesign não define a cadência completa de compra. O harness mantém até duas cartas compradas na transição para cada nova rodada; não foi inventada compra automática a cada turno. Deck fatigue está ativo quando a pilha de compra esvazia, mas um deck padrão de 30 cartas normalmente não se esgota no harness Bo3 de três rodadas apenas com essas duas compras por rodada.

## Guardrails

- Card fatigue só está conectada ao controlador alpha isolado; sem integração Discord/HTTP/frontend ou produção.
- A allowlist permanece em 27 cartas; 110 modelos históricos continuam bloqueados.
- O motor legado e os cinco arquivos centrais permanecem byte a byte idênticos ao baseline rev. 22.
- Não há ataque/armadura/HP individual nem morte automática de unidade pelo dano de combate.
- O artefato candidato v0.1 permanece apenas como histórico; o ruleset v0.3 é a fonte ativa da configuração alpha.

## Próxima prioridade

Completar custos, energia e regras de ativação/consumo de turno antes de ampliar catálogo. A cadência geral de compra e a frequência de compra por turno ainda precisam de especificação própria; não inferir isso da regra de fatigue.

Leia `docs/card-engine-v2-deck-fatigue-alpha-v0.2.md`, `docs/card-engine-v2-deck-fatigue-alpha-v0.2-change-manifest.md`, `docs/card-engine-v2-playable-alpha-validation-v0.4.md` e `sistemas/card_engine_v2/README.md`.

---

# Handoff histórico — ciclo de vida revisado e contrato candidato de deck fatigue (rev. 22)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev21.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-28-rev22.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Status de implementação:** nenhum comportamento novo foi conectado ao `AlphaMatchController`; a tranche adiciona auditoria, contrato candidato e referência matemática isolada.  
**Validação:** 126/126 testes (120 anteriores + seis novos testes candidatos); `py_compile` aprovado; staging 137/27/110; simulação Bo3 A 2–1 B, 60 eventos e SQLite íntegro; demo combo/passiva/líder 25 eventos e SQLite íntegro.

## O que foi conferido

- Remoções e sacrifício reutilizam transições por identidade física exata `board` → `discard`.
- Causas permanecem no enum aprovado: `normal_removal`, `execution`, `sacrifice`.
- Contadores permanecem separados (`board_removal_count` e `sacrifice_count`); arquivamento de fim de rodada não é remoção.
- Proteção e Vingança seguem as decisões aprovadas dos Grupos C/F: sacrifício faz bypass de proteção; Vingança ocorre após remoção bem-sucedida e alcança apenas sobreviventes da fileira original.
- O combate atual afeta `life_by_player`; não há ataque, armadura, HP individual ou morte automática de unidade. O evento correto continua sendo `unit_removed`, não `unit_died`.

## Deck fatigue — contrato candidato

A fonte `docs/CARD_GAME_REDESIGN.md` diz que deck vazio causa dano crescente por turno; vida 0 encerra a partida e letal simultâneo empata. Não especifica valores de dano, incremento, teto ou timing exato.

A alpha atual distribui seis cartas e compra até duas em `_close_round` para a próxima rodada (`draw_per_round=2`); deck vazio apenas interrompe o loop de compra. Isso não é equivalente a dano crescente por turno. A tranche registra o conflito e não muda o ruleset.

Artefatos:
- `docs/card-engine-v2-lifecycle-audit-v0.1.md` — auditoria das transições de remoção e fronteira entre remoção e morte.
- `docs/card-engine-v2-deck-fatigue-contract-v0.1.md` — semântica candidata e decisões pendentes.
- `data/card_game/card-engine-v2-deck-fatigue-policy-candidate.v0.1.json` — policy candidate com parâmetros não decididos em `null`.
- `sistemas/card_engine_v2/deck_fatigue_candidate.py` — referência aritmética pura, não importada pelo controlador.
- `tests/card_engine_v2/test_deck_fatigue_candidate.py` — seis testes do modelo matemático e dos guardrails.

## Decisões necessárias antes da integração

1. Cadência: compra/fatigue por turno individual ou por nova rodada.
2. Dano inicial, incremento e teto (ou ausência de teto).
3. Compra parcial: se restar uma carta e a fase pedir duas, fatigue aplica já ou só na próxima fase.
4. Política do contador se cartas retornarem ao deck.
5. Aplicação letal imediata antes de permitir a ação do jogador.
6. Se uma fase compartilhada dos dois jogadores deve aplicar fatigue simultaneamente.

Os testes `1, 3, 5, 7` são fixtures para validar a fórmula parametrizada, não valores de balanceamento propostos. Nenhum valor foi adicionado ao ruleset ou runtime.

## Comandos de validação

```bash
python -m py_compile sistemas/card_engine_v2/*.py docs/scripts/*.py tests/card_engine_v2/*.py
python -m unittest discover -s tests/card_engine_v2 -v
python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

## Próxima etapa

Fechar as decisões de cadence e balanceamento de deck fatigue antes de integrar a lógica. Em paralelo, podem ser implementados apenas os contratos de draw/turno sem efeito de vida, desde que não alterem o ruleset ou o comportamento ativo sem autorização. Manter a allowlist 27/110 e os cinco arquivos centrais do motor legado preservados.

---

# Handoff histórico — sacrifício normal no Card Engine v2 alpha (rev. 21)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev20.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-28-rev21.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset:** `alpha-test-only.ruleset.v0.2` (sem alteração).  
**Validação:** 120/120 testes; staging 137/27/110; simulação Bo3 A 2–1 B, 16 operações/60 eventos; demo combo/passiva/líder 25 eventos, SQLite íntegro.

## O que mudou nesta revisão

- `AlphaMatchController._build_resolver()` registra `unit.sacrifice` com a policy server-side de seleção manual de uma unidade aliada no campo e causa canônica `sacrifice`.
- `AlphaMatchController.sacrifice_target_offer()` cria oferta de alvos para o jogador ativo, inclui métricas/nome de exibição e vincula a oferta a `state_revision`.
- `AlphaMatchController.sacrifice_unit()` exige `target_instance_id` UUIDv4 e `expected_revision` obtida da oferta; revalida seleção/propriedade dentro de `SQLiteMatchRepository.execute_operation`.
- A operação externa `match.sacrifice_unit` é encaminhada ao `GameplayResolver` existente (`unit.sacrifice`), evitando duplicar transição de zona, validação de proteção, contadores ou Vingança.
- O sacrifício consome a ação do turno alpha. O commit grava `unit_removed`, o evento reativo de Vingança quando elegível e `turn_action_completed` no mesmo limite transacional.
- `operation_id` conserva replay idempotente; uma oferta desatualizada é rejeitada por `revision_conflict` sem remover a unidade.
- A documentação do motor e o changelog registram que o custo desta fatia é somente o turno; energia/recursos e limites específicos de sacrifício continuam pendentes.

## Validação reproduzida

```bash
python -m py_compile sistemas/card_engine_v2/*.py docs/scripts/*.py tests/card_engine_v2/*.py
python -m unittest discover -s tests/card_engine_v2 -v
python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

Relatórios desta tranche: `docs/card-engine-v2-sacrifice-match-alpha-v0.1.md` e `docs/card-engine-v2-sacrifice-match-alpha-v0.1-validation.json`. A validação geral foi regenerada em `docs/card-engine-v2-playable-alpha-validation-v0.4.md/.json` (120/120).

## Guardrails e limites

- Sacrifício ignora Égide/escudo e não consome a carga; incrementa `sacrifice_count`, não `board_removal_count`; dispara Vingança somente após remoção bem-sucedida, contra aliados sobreviventes na fileira original.
- O alvo deve ser obtido pela oferta gerada pelo servidor. Não aceitar alvo fora da oferta nem executar a partir de uma revisão obsoleta.
- O custo desta ação na alpha é `turn_consumed=true`; não há energia, moeda, custo de carta ou limite por rodada definido nesta fatia.
- A ação é um primitive alpha independente; não libera os 110 modelos históricos bloqueados nem infere handlers para efeitos candidatos de sacrifício.
- Combate por fileira continua causando dano à vida do jogador; ataque, armadura, defesa física e HP de unidade não estão definidos no contrato atual.
- Sem integração Discord/HTTP/frontend, sem acesso ao banco publicado e sem migração/cutover.
- Os cinco arquivos centrais do legado permanecem byte a byte idênticos ao baseline rev. 20.

## Próxima prioridade de implementação

Consolidar o ciclo de dano/remoção e ciclo de vida de morte com regras aprovadas; depois avançar em custos/recursos e efeitos restantes em fatias pequenas. Não ampliar o catálogo nem criar atributos físicos por unidade sem fonte normativa. O próximo bloco deve avaliar a regra de esgotamento do deck (`deck fatigue`) já descrita no redesign e convertê-la em contrato testável antes da implementação.

---

# Handoff histórico — combate por fileira Card Engine v2 alpha (rev. 20)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev19.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-28-rev20.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset:** `alpha-test-only.ruleset.v0.2`; 20 de vida inicial por jogador.  
**Validação:** 117/117 testes; staging 137/27/110; regressão Bo3 A 2–1 B, 16 operações/60 eventos; demonstração combo/passiva/líder aprovada, 25 eventos.

## O que mudou nesta revisão

- `sistemas/card_engine_v2/combat.py` implementa cálculo de poder total por fileira e dano pela diferença positiva entre os dois jogadores.
- O combate é resolvido no fechamento de cada rodada dentro de `AlphaMatchController._close_round`, utilizando `effective_power`: bônus, clima, resistência climática e estados de controle são contabilizados antes do dano.
- Vida por jogador é persistida no runtime e exposta na view; cada jogador inicia com 20 pontos.
- Eventos `combat_row_resolved`, `player_damage_applied` e `player_defeated` registram a resolução por fileira e a cadeia causal. `match_finished` identifica vitória letal ou empate por letal simultâneo.
- A série Bo3 continua como fallback da alpha quando ninguém chega a zero até o limite de rodadas.
- O ruleset foi promovido para `alpha-test-only.ruleset.v0.2` e seu hash/release é registrado no `DefinitionManifest`.

## Validação reproduzida

```bash
python -m py_compile sistemas/card_engine_v2/*.py docs/scripts/*.py tests/card_engine_v2/*.py
python -m unittest discover -s tests/card_engine_v2 -v
python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

Relatórios desta tranche: `docs/card-engine-v2-combat-alpha-v0.1.md` e `docs/card-engine-v2-combat-alpha-v0.1-validation.json`.

## Limites atuais

- O combate implementado causa dano à vida do jogador por fileira; não destrói automaticamente unidades.
- O contrato não define ataque, armadura, defesa física ou HP por unidade. A resistência presente é somente climática.
- Remoção, Execução, proteção e Vingança permanecem no resolvedor; sacrifício normal ainda não está conectado ao controlador.
- Dano por esgotamento de deck e sistema completo de custos/energia continuam pendentes.
- 27 cartas permanecem alpha-only; 110 modelos históricos continuam bloqueados. Dos 27 combos registrados, nove são alcançáveis e 18 permanecem inertes.
- Sem integração Discord/HTTP/frontend, sem acesso ao banco publicado e sem migração/cutover.
- Os cinco arquivos centrais do legado permanecem byte a byte idênticos ao baseline rev. 19.

## Próxima prioridade de implementação

Integrar sacrifício como ação normal do `AlphaMatchController`, com custo, seleção autoritativa e eventos, e depois consolidar regras de dano/remoção e o ciclo de vida de morte sem inventar atributos por unidade ausentes do contrato. Em seguida, avançar em custos/recursos e expansão controlada do catálogo.

---

# Handoff histórico — combos, passivas e líderes Card Engine v2 alpha (rev. 19)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev18.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-27-rev19.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Decisões:** Grupos A–F aprovados nos registros formais.  
**Validação:** 109/109 testes; staging 137/27/110; partida Bo3 A 2–1 B; demonstração combo/passiva/líder A 20–10 B.

## O que mudou nesta revisão

- O catálogo allowlist alpha atual é `data/card_game/card-engine-v2-alpha-catalog.v0.3.json`: 27 identidades explícitas. `AlphaCatalog` valida os novos artefatos e inclui os hashes dos combos, passivas e líderes no `DefinitionManifest`.
- `data/card_game/card-engine-v2-alpha-combos.v0.1.json` contém 27 combos. Nove são alcançáveis com tags existentes nas 27 cartas; 18 permanecem registrados, mas inertes até que cartas fornecedoras das tags sejam incluídas.
- `data/card_game/card-engine-v2-alpha-faction-passives.v0.1.json` contém quatro passivas de facção. A primeira unidade da facção escolhida, jogada em cada rodada, recebe +1; a ativação reinicia no fechamento da rodada.
- `data/card_game/card-engine-v2-alpha-leaders.v0.1.json` contém dez líderes alpha. Cada jogador seleciona um no setup e pode ativá-lo uma vez por partida; a facção do líder precisa corresponder à facção escolhida.
- `sistemas/card_engine_v2/synergies.py` resolve combos e passivas; `sistemas/card_engine_v2/leaders.py` implementa os dez handlers; `match.py` integra os efeitos ao fluxo de partida e ao fechamento de rodada.
- O staging histórico atualizado é `data/card_game/card-engine-v2-legacy-catalog-staging.v0.2.json`: 137 modelos, 27 alpha-only, 110 bloqueados. O staging v0.1 e o catálogo alpha v0.2 são históricos da revisão anterior.
- O schema `docs/schemas/card-game-card-instance-match.schema.v7.json` e `validation.py` aceitam os campos opcionais de facção/líder e estado de ativação por rodada, preservando compatibilidade de leitura para snapshots anteriores.

## Comandos de validação e demonstração

```bash
python -m py_compile sistemas/card_engine_v2/*.py docs/scripts/*.py tests/card_engine_v2/*.py
python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

Relatórios principais:
- `docs/card-engine-v2-playable-alpha-validation-v0.4.md/.json` — 109/109.
- `docs/card-engine-v2-combos-faction-passives-leaders-alpha-v0.1.md` — escopo e limitações.
- `docs/card-engine-v2-combo-faction-leader-alpha-run.v0.1.json` — demo A 20–10 B, 21 eventos, SQLite íntegro.
- `docs/card-engine-v2-playable-match-alpha-run.v0.3.json` — Bo3 A 2–1 B, 16 operações e 48 eventos.

## Estado e limites

- 27 cartas alpha; 110 modelos históricos continuam bloqueados.
- 27 combos registrados; nove alcançáveis, 18 inertes no allowlist atual.
- Quatro passivas e dez handlers de líderes no ambiente alpha; não equivalem a publicação/aprovação do catálogo completo.
- Testes sintéticos/isolados; não é playtest por UI humana. O jogo ainda não inclui combate/dano completo, todas as ações/custos, o fluxo normal de sacrifício no controlador, ou integração com Discord/HTTP/frontend.
- Sem acesso ou alteração do banco publicado, sem migração e sem cutover.
- Os cinco arquivos centrais do legado (`sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`) permanecem byte a byte idênticos ao baseline rev. 18.

## Próxima prioridade de implementação

Fechar o caminho normal de combate/dano e de sacrifício no controlador de partida, ampliar a cobertura de combos que hoje estão inertes por falta de tags-fonte e conectar os demais efeitos reais em fatias pequenas. Manter a allowlist alpha explícita e continuar sem integrar o runtime legado.

---

# Handoff histórico — expansão de catálogo Card Engine v2 alpha (rev. 18, 2026-11-27)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev17.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-27-rev18.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Decisões:** Grupos A–F aprovados.  
**Validação:** 97/97 testes; staging 8/8; partida Bo3 de regressão Player A 2–1 Player B.

## Expansão entregue

- `AlphaCatalog` agora carrega `data/card_game/card-engine-v2-alpha-catalog.v0.2.json`, verifica artifact type/status/version, IDs duplicados, `card_count`, igualdade com a allowlist revisada no código e presença no snapshot histórico. O SHA-256 do allowlist integra o `DefinitionManifest`.
- Allowlist alpha: 24 cartas; 14 novas entradas adicionadas ao conjunto anterior de dez.
- `card-engine-v2-alpha-effects.v0.2.json` e `entry_effects.py` ligam 12 famílias de efeitos de entrada: descarte, presságio/ruína, redução de bônus inimigo, presença em outra fileira, suporte e afinidade climática, bônus positivo inimigo, comeback, fileira solitária, vantagem no placar, sequência e caçador arcano.
- As novas famílias são resolvidas no `AlphaMatchController.play_unit`, com parâmetros vindos do snapshot de definição. Eventos de efeito citam o evento `unit_played` como causa.
- `card-engine-v2-legacy-catalog-staging.v0.1.json` preserva os 137 modelos do snapshot histórico para revisão; 24 constam como alpha-only, 113 como blocked. Nenhum dos 137 foi promovido a catálogo publicado.
- Testes de integração em `tests/card_engine_v2/test_expanded_entry_effects.py` cobrem os novos handlers, artefato allowlist, hash do manifesto e contagem/status do staging.

## Comandos atuais

```bash
python docs/scripts/test-card-engine-v2-playable-alpha-v0.3.py
python docs/scripts/compile-card-engine-v2-legacy-catalog-staging-v0.1.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.1.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.2.py
python docs/scripts/build-card-engine-v2-catalog-expansion-report-v0.2.py
```

## Limites e guardrails

- Os 24 modelos são fixtures alpha derivadas do snapshot histórico. A seleção não aprova custos, facções, textos, arte, combos ou publicação.
- Os 113 IDs restantes permanecem bloqueados; não inferir handlers a partir de texto legado.
- O staging declara 137/137 não reconstruídos, 137/137 sem revisão de facção e 19 divergências históricas de custo.
- A expansão implementa 12 famílias de efeitos de entrada selecionadas, não o registry candidato completo de 54 famílias nem os 27 combos.
- Líderes, passivas de facção, combate/dano, custos integrais, conexão Discord/HTTP/frontend, adapter assíncrono, multi-host e migração de partidas reais permanecem pendentes.
- Os arquivos centrais do legado (`sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`) não foram alterados nesta revisão.

## Próxima prioridade

Ampliar efeitos adicionais somente após revisão semântica e parâmetros server-side explícitos; depois implementar combos/passivas/líderes, custos/turnos integrais e o ciclo de combate. Manter o allowlist alpha fechado até aprovação de cada nova tranche.

---

# Histórico — partida jogável Card Engine v2 alpha (rev. 17, 2026-11-27)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev16.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-27-rev17.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado e não congelado.  
**Decisões:** Grupos A, B, C, D, E e F aprovados.  
**Validação:** 78/78 testes; partida sandbox completa Player A 2–1 Player B.

## O que já está construído

- `SQLiteMatchRepository`: base dedicada com marcador; migrations checksummed; transações `BEGIN IMMEDIATE`; CAS por `state_revision`; ledger idempotente; journal append-only; snapshot/runtime/eventos/rewards/outbox no mesmo commit; backup e verificação.
- `GameplayResolver`: seleção revision-bound, remoção, sacrifício, proteção, bônus, movimentação e Vingança reativa; oferece apenas políticas/ações registradas em configuração confiável do servidor.
- `AlphaCatalog`: allowlist rígida de dez modelos do snapshot histórico; manifesto e digest; recusa cartas fora da allowlist; raridade não modifica os resultados mecânicos.
- `power.py`: poder efetivo com base, bônus, clima, resistência e Frost/estados de controle, com piso de 1.
- `AlphaMatchController`: criação de partida, seis cartas iniciais, turnos de dois jogadores, unidade e especiais alpha, target offer e revisão obrigatória, rodada/pontuação/arquivo/expiração/compra e série melhor de três.

## Demonstração reproduzível

Executar na raiz do repositório:

```bash
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.1.py
```

Saída esperada: estado `finished`; Player A vence por 2–1. Resultados por rodada: 1ª Player A 9–4; 2ª Player B 6–0; 3ª Player A 6–0. A sequência gera 16 operações e 48 eventos. O fluxo inclui buff de entrada do Veterano, Tempestade, Frost, Execução de Godwyn, Vingança causal no sobrevivente, Égide, round-close e encerramento. O script usa SQLite temporário e falha se as verificações de integridade não passarem. O relatório JSON pode ser salvo com `--json-out caminho.json`.

## Catálogo e regras da demo

A allowlist contém `arma_lanca_fornalha`, `arma_cajado_marulho`, `arma_martelo_fornalha`, `chefe_vigia_cinzento`, `gwent_v75_ordem_veterano_juramento`, `gwent_unidade_herdeiro_portao`, `gwent_especial_egide`, `gwent_especial_execucao`, `gwent_especial_tempestade` e `elden_especial_geada`. São fixtures alpha extraídas do baseline histórico; não constituem catálogo ativo ou release aprovada.

Ofertas de Égide e Execução são calculadas pelo servidor. O request precisa repetir o `expected_revision` da oferta. O controlador rejeita oferta obsoleta mesmo quando o jogador voltou a ser o jogador ativo.

## Testes

```bash
python docs/scripts/test-card-engine-v2-playable-alpha-v0.2.py
python -m unittest discover -s tests/card_engine_v2 -v
```

Resultado atual: 78/78. Relatórios: `docs/card-engine-v2-playable-alpha-validation-v0.2.md/.json`. Testes utilizam arquivos SQLite temporários e conexões locais; não são teste de produção.

## Limites e guardrails

Ainda não há catálogo completo, todos os efeitos, combos, líderes, combate/dano, sistema completo de custos/recursos nem sacrifício exposto pelo controlador da partida. O `GameplayResolver` tem testes isolados para sacrifício, mas a partida demonstrativa não o oferece como ação de UI. Não há adapter `aiosqlite`, worker, integração Discord/HTTP/frontend, leitura/escrita do banco publicado, multi-host ou migração real.

Não alterar nem substituir `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` nesta etapa. A partida alpha usa seu próprio SQLite temporário. Qualquer integração deve vir depois, em adapter separado e staging, com comparação e rollback; partidas atuais permanecem no motor antigo.

## Próximo bloco de implementação

Expandir o controlador com turnos/custos completos e contratos de combate, depois conectar progressivamente os registries candidatos para combos, líderes e efeitos adicionais. Fazer testes de regressão por família. Somente depois implementar adapter assíncrono e staging; ainda não iniciar cutover.

---

# Histórico — handoff rev. 13 antes da aprovação do Grupo F e da auditoria E (2026-11-27)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev12.zip`.  
**Revisão atual:** `soulsbo-main-continuity-2026-11-27-rev13.zip`.  
**Contrato:** `CardInstance v0.5` draft, não congelado; incorpora Grupos A/B/C/D aprovados.  
**Runtime:** nenhuma alteração; sem migração, API, DB, catálogo ativo ou frontend.

## Aprovações preservadas

- **Grupo A:** identidade física por `instance_id`, unicidade global, `card_id` repetível, `exemplar_id` global, seleção exata e desempate determinístico.
- **Grupo B:** manifesto/snapshot imutável, causalidade append-only, `operation_id` separado de `event_id`, raridade apenas classificatória e fontes reativas próprias.
- **Grupo C:** políticas explícitas de grants/estados/transições, `round_close` após snapshot, resistência intrínseca separada de modificadores, proteção/custos e políticas de retorno; `vigil_seal` expira em `board_exit`.
- **Grupo D:** as 12 decisões DSEL-DEC-001..012 estão aprovadas; request/offer/policy/result e custos/outcomes são contratos candidatos, não endpoints implementados. CI-014/CAS real continua Grupo E.

## CardInstance v0.5

- Contrato: `docs/card-game-card-instance-contract-v0.5.md`.
- Schema/exemplo: `docs/schemas/card-game-card-instance-match.schema.v5.json` e `docs/examples/card-instance-match.example.v5.json`.
- Schemas D: `card-game-action-request.schema.v1.json`, `card-game-target-offer.schema.v1.json`, `card-game-effect-target-policy.schema.v1.json` e `card-game-action-result.schema.v1.json` em `docs/schemas/`.
- Validador: `docs/scripts/validate-card-game-card-instance-v0.5.py` — 28/28 verificações neste draft.

## Grupo F — auditoria concluída; decisões aguardam aprovação

- Parecer: `docs/card-game-removal-causes-group-F-review-v0.1.md`.
- Matriz de cinco propostas: `docs/card-game-removal-causes-group-F-decisions-v0.1.json` (FCAUSE-001..005, `PENDING_OWNER_APPROVAL`).
- Evidência: `docs/card-game-removal-causes-group-F-audit-v0.1.json` — 29/29.
- Validação: `docs/card-game-removal-causes-group-F-validation-v0.1.md/.json`.
- Harness: `docs/scripts/audit-card-game-removal-causes-group-F-v0.1.py`.

**Achados F:** Vingança ocorre após remoção bem-sucedida por remoção comum, execução ou sacrifício; escudo bloqueia remoção comum/execução e suprime Vingança, sacrifício ignora escudo. `baixas` mistura remoções, execuções e sacrifícios, não mortes. Rykard gera no legado Vingança +1 e bônus direto +2 como outputs sequenciais. Arquivamento de fim de rodada não chama o resolvedor de remoção e não dispara Vingança; o ramo terminal retorna sem arquivar o campo. Causa desconhecida não é rejeitada no legado. O registry usa `effect.vengeance_on_removal`, mas o exemplo v4 usa `unit.vengeance_on_removal`.

**Recomendações ainda não aprovadas:** (1) Vingança após sucesso nas três causas canônicas; (2) contadores derivados separados para `board_removal_count` e `sacrifice_count`, com `baixas` apenas como adaptador; (3) outputs de Vingança/Rykard separados e aditivos, com valores parametrizados por release; (4) enum fechado de causas e `round_archive` como evento distinto; (5) ID canônico `effect.vengeance_on_removal`.

## Próximos gates

- **F:** aguardar aprovação/ajuste das cinco decisões FCAUSE. O audit não aprova as regras.
- **E:** CAS/serialização por partida, ledger/fingerprint duráveis, replay idempotente, rollback e migração/testes reais. Continua aberto.
- Só depois de F aprovado, atualizar `CardInstance v0.6` como draft. Nenhuma integração com o runtime é autorizada por estas aprovações documentais.

## Regressões desta revisão

Grupo F 29/29; CardInstance v0.5 28/28; Grupo D validator 13/13; Grupo D audit 23/23; Grupo A 30/30; Grupo B 20/20; Grupo C 43/43; matriz cruzada 272/272; remoção/ressurreição candidato 49/49. As suítes têm escopos independentes e não são cobertura integrada nem testes de produção.

**Integridade:** apenas arquivos de `docs/` foram adicionados/atualizados. Arquivos funcionais e runtime permanecem idênticos ao pacote rev. 12.

---

# Histórico de continuidade

# Handoff histórico — `CardInstance v0.4` draft; Grupos A/B/C aprovados (2026-11-27)

**Baseline de continuidade:** `soulsbo-main-continuity-2026-11-27-rev10.zip`.  
**Pacote atualizado:** `soulsbo-main-continuity-2026-11-27-rev11.zip`.  
**Status:** `DRAFT_AFTER_GROUP_A_B_C_APPROVAL_NOT_FROZEN`.  
**Integração:** nenhuma; runtime e DB de produção intocados.

## Aprovações

- **Grupo A:** identidade por ocorrência; UUIDv4; unicidade global na partida; cópias de `card_id`; `exemplar_id` global e validado; tokens com instância; alvo físico por `instance_id`; ordem/desempate determinístico; operações exatas sobre instância.
- **Grupo B:** manifesto imutável e snapshots resolvidos; `operation_id` separado de `event_id`; ledger causal append-only; raridade exclusivamente classificatória; efeitos reativos com fonte/eventos próprios; apenas bindings ativos; remoção/Vingança e Rykard separados causalmente.
- **Grupo C:** limpeza explícita por transição; `round_close` global após snapshot, em todas as zonas e inclusive terminal; resistência intrínseca separada de modificadores; `printed_row/current_row/last_board_row/last_unit_play_row` separados; proteção por categoria e custo de ação independente; `vigil_seal` expira em `board_exit`; bônus por grants e clamp explícito; políticas específicas de bônus/fileira/normalização para Ressurgir, Réquiem, Esgar e Lágrima Sagrada.

Registros formais: `card-game-identity-group-A-approval-v0.1.md`, `card-game-snapshot-causality-group-B-approval-v0.1.md` e `card-game-state-lifecycle-group-C-approval-v0.1.md`. O aceite de C foi a resposta explícita “aprovo” à pergunta que abrangia as dez resoluções recomendadas.

## Contrato v0.4

- `docs/card-game-card-instance-contract-v0.4.md` é o draft consolidado; não está congelado.
- `docs/schemas/card-game-card-instance-match.schema.v4.json` define a estrutura do envelope v4.
- `docs/examples/card-instance-match.example.v4.json` demonstra estado com grants/aplicações e referência a eventos.
- `docs/card-game-card-instance-contract-validation-v0.4.json/.md` registra 72/72 verificações; reproduzir com `python docs/scripts/validate-card-game-card-instance-v0.4.py`.

O estado canônico v4 remove os escalares agregados `bonus`, `shield_charges`, `statuses` e `weather_resistance`. Em seu lugar usa `bonus_grants[]`, `protection_grants[]`, `status_applications[]` e `weather_resistance_modifiers[]`. Totais para cálculo/UI são projeções derivadas. A resistência intrínseca fica no `DefinitionSnapshot`. `current_row=null` fora do board; `last_board_row` é projeção persistida; `last_unit_play_row` fica no estado de rodada do participante.

## Pendências e bloqueios

- **Grupo D:** selecionar e desempatar grants compatíveis; definir fallback/target parcial; outcomes completos de operação; custo/consumo por família de efeito.
- **Grupo F:** lista final de causas elegíveis para Vingança, inclusive tratamento de sacrifício e remoção forçada.
- **Grupo E:** CAS/serialização, lock por partida, constraints e ledger no banco, idempotência sob concorrência real, migração de snapshots antigos e rollback.
- Estados negativos: caps/limiares e repetição de triggers permanecem dependentes do registry/ruleset; a aprovação C não congela esses números.
- Balanceamento: `clamp_policy_id` está no contrato, mas as políticas numéricas e seus releases ainda precisam ser fechados.

## Guardrails e próximo passo

Não alterar `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, catálogo ativo, resolvedores ou schema de produção. Não iniciar migrador nem integrar o CardInstance ao motor enquanto D/F/E e os testes de persistência real não forem fechados.

**Próximo gate:** auditar/definir o Grupo D, sem antecipar decisões do Grupo F ou E. A matriz de revisão CI/BUF/RSRX e os relatórios dos grupos devem ser tratados como histórico de análise; os três registros de aprovação acima prevalecem quanto ao status decisório.

---

# Histórico — Grupo C auditado antes da aprovação (2026-11-27)

## Estado oficial

- Grupo A: aprovado (CI-001/002/003/004/006/010, BUF-013, RSRX-09).
- Grupo B: aprovado (CI-005, CI-011, BUF-001 Alternativa A, BUF-002, BUF-012, RSRX-03 com causas finais no Grupo F, RSRX-05 somente separação causal).
- Raridade: exclusivamente classificatória no novo sistema; não altera outputs mecânicos; `RARITY_EFFECT_BUDGET` não será usado no novo engine.
- Grupo C: auditoria concluída; as 10 decisões CI-008/009, BUF-008/009/010/011/014 e RSRX-07/08/10 aguardam aprovação.
- Contrato: `CardInstance v0.3` permanece `CONTRACT_DRAFT_NOT_FROZEN`; Grupo C não atualizou schema nem runtime.

## Achados do Grupo C

- `_remover_unidade()` limpa escudo e quatro estados em remoção bem-sucedida, mas preserva bônus, resistência climática e marcador de combo; remoção bloqueada consome escudo e retorna antes da limpeza.
- No encerramento não terminal, limpeza percorre somente unidades no campo. Unidades anteriormente removidas e guardadas no descarte podem reter bônus. No encerramento terminal, a função retorna antes da limpeza de rodada.
- `weather_resist` é escalar; `vigil_seal` atribui 1. A duração não pode ser inferida pela persistência observada no legado.
- Escudo não é imunidade universal: bloqueia remoção/execução centralmente, sacrifício passa direto, status/debuffs normalmente ignoram proteção e duas relíquias fazem checagens locais com custos de ação diferentes.
- Ressurgir/Réquiem zeram bônus, Esgar acrescenta +1 ao bônus anterior, Lágrima Sagrada recupera para a mão sem normalização adicional; os hooks de entrada não são repetidos.

## Política proposta (não aprovada)

Evento `round_close` após snapshot imutável de pontuação; expirar concessões marcadas `round_close` em todas as zonas, também na última rodada. Bônus, proteção e marcas são projeções de grants/applications com fonte, evento de aplicação, política e expiração. Resistência intrínseca fica no `DefinitionSnapshot`; modificadores climáticos temporários ficam no estado da instância. Políticas de bônus/fileira/normalização continuam por efeito de retorno. Não congelar schema nem integrar ainda.

## Artefatos do Grupo C

- `docs/card-game-state-lifecycle-group-C-review-v0.1.md`
- `docs/card-game-state-lifecycle-group-C-decisions-v0.1.json`
- `docs/examples/card-game-state-lifecycle-group-C.example.v0.1.json`
- `docs/card-game-state-lifecycle-group-C-validation-v0.1.json`
- `docs/scripts/validate-card-game-state-lifecycle-group-C-v0.1.py`

**Validação:** Grupo C 43/43; Grupo B 20/20; CardInstance v0.3 + B 42/42; matriz CI/BUF/RSRX 272/272; Grupo A 30/30; status candidato 41/41; remoção/ressurreição 49/49. Suites independentes, estáticas/sintéticas quando indicado, sem integração de produção.

**Integridade:** baseline rev. 9; somente `docs/` atualizado. Runtime, catálogo ativo, registries candidatos, DB, API, frontend e bot não foram alterados. Próximo gate é a aprovação do Grupo C; depois, `CardInstance v0.4` como draft. Grupos D, F e E permanecem abertos.

---

# Handoff atual — Grupo B aprovado / CardInstance v0.3 (2026-11-27)

## Estado oficial

- Grupo A: aprovado (CI-001/002/003/004/006/010, BUF-013, RSRX-09).
- Grupo B: aprovado pelo proprietário no pacote rev. 8.
- Decisões B: CI-005, CI-011, BUF-001 Alternativa A, BUF-002, BUF-012, RSRX-03 com dependência do Grupo F e RSRX-05 limitado à separação causal.
- Contrato atual: `docs/card-game-card-instance-contract-v0.3.md`; ainda `CONTRACT_DRAFT_NOT_FROZEN`.

## Regra de raridade aprovada

Raridade é metadado classificatório, nunca input mecânico. O novo sistema não pode usar raridade para alterar magnitude, elegibilidade/threshold, quantidade ou seleção de alvos, duração nem outros outputs. `RARITY_EFFECT_BUDGET` não será usado no novo sistema. Isso não altera o runtime legado nesta fase e não aprova EFP/custo/cortes de raridade.

## Modelo causal aprovado

- Manifesto imutável por partida com releases de catálogo, efeitos, balanceamento e ruleset + digest.
- Snapshot mecânico resolvido e digest por `CardInstance`.
- `operation_id` UUIDv4 para idempotência; `event_id` UUIDv4 para cada evento.
- Eventos ordenados, append-only, com fonte e pais causais; operação/estado/revisão/eventos são commit atômico no futuro serviço.
- Efeito reativo usa sua própria fonte e nunca herda raridade/params externos.
- Remoção bem-sucedida e Vingança são eventos distintos; shield-block não dispara Vingança. As causas permitidas finais dependem do Grupo F.
- Rykard: Vingança e output direto do líder ficam separados; +3 legado não é valor definitivo.

## Próxima etapa

Grupo C — políticas de estado/duração: origem, acúmulo, expiração e limpeza de bônus, escudos, estados e resistência climática, com cruzamento explícito para recuperação/ressurreição. Não migrar nem integrar ainda.

## Artefatos recentes

- `docs/card-game-snapshot-causality-group-B-approval-v0.1.md/.json`
- `docs/card-game-card-instance-contract-v0.3.md`
- `docs/schemas/card-game-card-instance-match.schema.v3.json`
- `docs/schemas/card-game-definition-manifest.schema.v1.json`
- `docs/schemas/card-game-domain-event.schema.v1.json`
- `docs/examples/card-instance-match.example.v3.json`
- `docs/card-game-card-instance-contract-validation-v0.3.json` e `docs/card-game-card-instance-contract-validation-v0.3.md`
- `docs/scripts/validate-card-game-card-instance-v0.3.py`

**Integridade desta etapa:** documentação/validação somente em `docs/`; runtime, DB, API, catálogo ativo, bot e frontend não mudaram.

---

# Handoff — Grupo B auditado; aprovação pendente (2026-11-27)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev7.zip`  
**Status:** `GROUP_A_APPROVED; GROUP_B_AUDITED_NOT_APPROVED; CARD_INSTANCE_DRAFT_NOT_FROZEN`  
**Integração:** nenhuma. Código funcional e DB permanecem intactos.

## Resultado do Grupo B

A auditoria de snapshot e causalidade concluiu 20/20 verificações. As regressões reexecutadas também passaram: Grupo A 30/30, CardInstance v0.2 30/30, matriz cruzada 272/272, buffs cross 9/9, buffs/proteção 14/14, líderes 22/22, estados 41/41, remoção/ressurreição 49/49, catálogo candidato 23/23, contrato canônico 35/35, UI 12/12, sequência 10/10, seleção/fileiras 15/15, identidade/ciclo de vida 17/17 e comportamento de identidade 33/33. As suítes têm escopos independentes; não representam cobertura integral em produção. Leia `docs/card-game-snapshot-causality-group-B-audit-v0.1.md`, `docs/card-game-snapshot-causality-group-B-decisions-v0.1.json`, o JSON de resultados e o script em `docs/scripts/`.

Fatos principais: o baseline de catálogo é histórico e os hashes existentes são hashes de arquivos-fonte, não um manifesto de release; `effect-registry-candidate.v1.json` continua candidato sem release imutável; a versão de balanceamento ainda é prevista como saída futura; `novo_estado()` não congela manifesto nem `definition_snapshot`; `event_log` é uma lista curta de mensagens; o legado não fornece `operation_id` nem eventos causais.

### Cadeia causal observada

- Chama Negra chama `_remover_unidade()` e Vingança dispara sincronamente. A amplificação de raridade depois percorre diferenças globais de bônus. O teste reproduz Vingança +1 para os dois sobreviventes, mas +2 no primeiro quando a carta Chama Negra é Épica.
- Rykard sacrifica a unidade mais fraca, aciona Vingança +1 quando presente e depois concede +2 direto aos sobreviventes. O +3 é comportamento legado reproduzido, não design aprovado. A ação de líder não usa o amplificador de raridade.

### Decisão aberta prioritária

BUF-001 conflita entre (A) remover a amplificação por raridade, conforme `card-game-balance-spec-v0.1.md`, ou (B) mantê-la apenas nos outputs diretos, conforme o parecer cruzado anterior. O relatório recomenda A; ambas permanecem abertas até aprovação explícita. CI-005/011, BUF-001/002/012 e RSRX-03/05 também permanecem abertas.

**Não fazer ainda:** não editar `RARITY_EFFECT_BUDGET`, não congelar a versão de catálogo/balanceamento, não mudar schemas de produção, não implementar o event store, não criar migrador e não integrar ao motor.

---

# Handoff — última etapa: Grupo A aprovado e `CardInstance v0.2` (2026-11-27)

**Baseline de entrada:** `soulsbo-main-continuity-2026-11-27-rev6.zip`  
**Estado:** `GROUP_A_APPROVED; CONTRACT_DRAFT_NOT_FROZEN`  
**Integração:** nenhuma. O runtime legado, banco, catálogo ativo, API e frontend permanecem intactos.

## Aprovação do Grupo A

O proprietário respondeu `ok, continue` à pergunta explícita “Podemos seguir com a aprovação do Grupo A?”. O escopo aprovado é CI-001, CI-002, CI-003, CI-004, CI-006, CI-010, BUF-013 e RSRX-09, nos termos do parecer `docs/card-game-identity-group-A-decision-review-v0.1.md`. O registro formal está em `docs/card-game-identity-group-A-approval-v0.1.md` e `.json`.

A correção central de CI-004 permanece: `cartas_exemplares.id` é `INTEGER PRIMARY KEY AUTOINCREMENT`, global à tabela. Toda proveniência de exemplar tem de validar existência, `user_id == owner_player_id` e `card_id` coincidente. A mesma PK não pode ser atribuída a duas instâncias.

## Contrato v0.2

- `docs/card-game-card-instance-contract-v0.2.md` consolida apenas as oito decisões aprovadas e mantém os grupos B/C/D/F/E abertos.
- `docs/schemas/card-game-card-instance-match.schema.v2.json` valida a estrutura do envelope e UUIDv4 por ocorrência.
- `docs/schemas/card-game-target-selection.schema.v1.json` aceita seletor físico singular (`target_instance_id`) ou plural (`target_instance_ids` sem duplicatas), nunca `target_id` no protocolo novo.
- `docs/examples/card-instance-match.example.v2.json` demonstra cópias de modelo com identidades físicas diferentes, incluindo token sem exemplar.
- `docs/scripts/validate-card-game-card-instance-v0.2.py` e `docs/card-game-card-instance-contract-validation-v0.2.json` registram 30 verificações sintéticas/estruturais.

### Decisões aprovadas

CI-001/002/003/004/006/010, BUF-013 e RSRX-09. O adaptador legado por `card_id` só pode resolver exatamente uma correspondência elegível; zero ou várias são rejeitadas. A regra do deck builder de 12 `card_id` distintos permanece inalterada. Tokens materializados recebem instância; relíquia equipada fica fora das zonas e sua ativação é preferencialmente evento.

### Decisões ainda abertas

CI-005/007/008/009/011/012/013/014; BUF-001…BUF-012 e BUF-014; RSRX-01…08 e RSRX-10. RSRX-01…10 são chaves locais do parecer cruzado. `weather_resistance`, `policy.identity_only` e `result=applied` permanecem placeholders provisórios, marcados como deprecated no schema v2.

## Validação e guardrails

O harness v0.2 verifica schemas Draft 2020-12, invariantes semânticos de instância/zonas/proveniência, repetição de `card_id`, seleção alvo e evidência estática do DDL. Ele não valida DB real, concorrência, HTTP, Discord, browser ou runtime novo.

Não iniciar migrador, não alterar o schema de produção e não integrar ao motor legado antes de fechar B/C/D/F/E. Os arquivos funcionais permanecem sob baseline e devem ser comparados por hash em cada pacote.

## Próxima etapa recomendada

Grupo B — snapshot e causalidade: congelamento de definição/versões, contexto de origem de evento, distinção entre efeito direto e efeito reativo (ex.: raridade e Vingança), e proveniência de buffs/passivas. Preservar a separação entre evidência observada no legado e regra nova aprovada.

---

# Estado mais recente — Grupo A: identidade física v0.1 (2026-11-27)

A revisão do pacote rev. 5 abriu o Grupo A de CI/BUF/RSRX. O documento `docs/card-game-identity-group-A-decision-review-v0.1.md` apresenta recomendações para CI-001/002/003/004/006/010, BUF-013 e RSRX-09. **Todas permanecem abertas e não aprovadas.**

**Correção importante:** o DDL atual declara `cartas_exemplares.id` como PK `AUTOINCREMENT` global. Portanto, `exemplar_id` não pode ser tratado como identificador local repetível entre proprietários; a validação exige correspondência com `user_id`/`owner_player_id` e `card_id`. O exemplo CardInstance foi corrigido e a errata foi acrescentada ao contrato v0.1.

**Resultado do harness do Grupo A:** 30/30 casos sintéticos/estáticos passaram. Isso valida os invariantes da proposta e as evidências do código, não aprova regras, nem testa DB real, HTTP ou integração.

Leia nesta ordem:
1. `docs/card-game-identity-group-A-decision-review-v0.1.md` e `docs/card-game-identity-group-A-decisions-v0.1.json` — resoluções propostas e matriz estruturada com correção de CI-004.
2. `docs/card-game-identity-group-A-validation-v0.1.json` e `docs/scripts/validate-card-game-identity-group-A-v0.1.py` — 30 casos reproduzíveis.
3. `docs/card-game-card-instance-contract-v0.1.md` e `docs/card-game-card-instance-match.schema.v1.json` — contrato histórico candidato, com errata.
4. `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.md` — dependências de BUF e RSRX.

**Próximo gate:** aprovação ou ajuste explícito das oito decisões listadas na matriz do Grupo A. Depois disso, revisar CardInstance v0.2; ainda não iniciar migrador nem integração. Runtime preservado.

---

# Estado mais recente — revisão cruzada CI/BUF/RSRX v0.1 (2026-11-27)

A revisão do pacote rev. 4 consolidou **14 decisões CI, 14 decisões BUF e 10 decisões de remoção/ressurreição (chaves RSRX locais deste parecer)**. Foram registradas recomendações técnicas e dependências; **nenhuma decisão foi aprovada**. O status permanece `TECHNICAL_RECOMMENDATIONS_FOR_OWNER_REVIEW_NOT_APPROVED`.

Leia nesta ordem:

1. `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.md` — parecer completo, resoluções recomendadas, conflitos, grupos de dependência e gates de implementação.
2. `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.json` — matriz estruturada das 38 decisões/referências, gaps de schema e resultados de regressão.
3. `docs/scripts/validate-card-game-cross-decision-review-v0.1.py` — valida a integridade estrutural da matriz; não valida regras de jogo.
4. `docs/card-game-card-instance-contract-v0.1.md` — contrato candidato atual, ainda não congelado.
5. `docs/card-game-buffs-decision-register-v0.1.md` — fonte original das decisões BUF.
6. `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` e `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — evidência e pendências RSRX.
7. `docs/card-game-handoff.md` — histórico e restrições de continuidade.

**Conclusão técnica:** não congelar ainda o schema CardInstance v1 nem iniciar o migrador. O campo escalar `weather_resistance`, a policy única `policy.identity_only` e o resultado único `applied` não cobrem as políticas BUF/RSRX necessárias. A persistência atual em `database.py` também não tem revisão/ledger dedicados; CI-014 exige decisão e teste real de transação.

**Validações reexecutadas:** CardInstance 30/30; RSRX 49/49; buffs/proteção 14/14; interações cruzadas 9/9; sequência 10/10; seleção TGT 15/15; paridade TUI 12/12; identidade/ciclo de vida 17/17. Suites independentes, não somáveis.

**Integridade:** somente documentação/scripts de validação sob `docs/` foram acrescentados ou atualizados nesta etapa. Nenhum runtime, catálogo ativo, schema de produção, DB, API, resolvedor, bot ou frontend foi modificado. O motor antigo permanece intacto.

**Próximo passo:** obter aprovação/ajuste dos grupos A (identidade), B (snapshot/causalidade) e C (estado/duração) antes de desenhar CardInstance v0.2. A migração fica bloqueada até fechar as dependências.

---

# Handoff técnico — contrato candidato `CardInstance` e transições de zona v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev3.zip`  
**Pacote desta revisão:** `soulsbo-main-continuity-2026-11-27-rev4.zip`  
**Status:** `CANDIDATE_FOR_REVIEW_NOT_APPROVED`  
**Validação:** 30/30 assertions do harness candidato; schema Draft 2020-12 válido; exemplo sem erros de schema.  
**Integração:** nenhuma. O runtime legado, resolvedor de remoção/ressurreição, banco, API, catálogo ativo e frontend permanecem intocados.

## Última etapa concluída

Foi formalizado o contrato `CardInstance` em três artefatos principais: spec, JSON Schema e exemplo de envelope. Também foi criado um harness isolado com protótipo em memória de transição de zona, sem importar o runtime.

### Regras estruturais propostas

- `card_id` identifica o modelo; `exemplar_id` identifica o registro de coleção no escopo de um jogador; `instance_id` identifica uma ocorrência única em uma partida inteira.
- `instance_id` é UUIDv4 gerado pelo servidor uma única vez, antes da distribuição entre mão e pilha. É imutável durante movimento, remoção, retorno, ressurreição e serialização.
- `definition_snapshot` congela versões de catálogo/balanceamento e atributos mecânicos usados na partida. `state` guarda posição e valores dinâmicos.
- `instances` contém um único registro por ocorrência; as zonas dos dois jogadores contêm apenas referências. Cada instância precisa aparecer em exatamente uma das zonas `hand`, `draw_pile`, `board` ou `discard`.
- `board` aceita apenas `kind=unit`. O mesmo `card_id` pode aparecer em várias instâncias; isso não modifica a regra atual do endpoint de deck, que ainda exige modelos distintos.
- `owner_player_id` deve corresponder ao dono das zonas. Transferência de controle entre participantes não faz parte do contrato v0.1.
- O protótipo `policy.identity_only` move uma ocorrência sem clonar nem normalizar `state`; a operação confere zona de origem e `expected_revision`, faz cópia transacional, revalida invariantes e registra `operation_id` com fingerprint SHA-256. O ledger persiste `expected_revision`, `revision_before` e `revision_after`. Repetição idêntica não executa de novo; reutilização conflitante ou revisão obsoleta falha. Persistência real ainda requer CAS ou serialização equivalente (CI-014).
- `target_instance_id` substitui a identidade física baseada em `target_id`/`card_id` no protocolo futuro. Compatibilidade antiga só poderá resolver quando houver exatamente um candidato.
- Snapshots antigos devem ser migrados uma vez e persistidos atomicamente antes de aceitar ações; nunca gerar novas identidades em cada carregamento.

### Artefatos desta etapa

- `docs/card-game-card-instance-contract-v0.1.md` — contrato, evidências, invariantes, transições, migração e 14 decisões abertas.
- `docs/card-game-card-instance-match.schema.v1.json` — estrutura Draft 2020-12.
- `docs/examples/card-instance-match.example.v1.json` — exemplo com instâncias do mesmo modelo e proprietários diferentes.
- `docs/card-game-card-instance-contract-validation-v0.1.json` — resultado 30/30.
- `docs/scripts/test-card-instance-contract-v0.1.py` — harness de validação e transição de referência.

### Regressões reexecutadas

| Suite | Resultado |
|---|---:|
| Contrato candidato CardInstance | 30/30 |
| Auditoria de identidade/ciclo de vida | 17/17 |
| Paridade manual/UI/alvo | 12/12 |
| Remoção/ressurreição candidato + evidência legada | 49/49 |
| Contrato canônico de cartas | 35/35 |

Escopos diferentes; não somar como cobertura única. O harness CardInstance valida um modelo sintético em memória. Não testa persistência real, isolamento SQLite, HTTP, navegador, concorrência, Discord, R2 ou produção.

### Decisões ainda abertas

CI-001…CI-014 permanecem abertas: formato/escopo de `instance_id`; suporte a cópias de modelo; vínculo de exemplar; versionamento do snapshot; tokens e relíquias temporárias; transferência de controle; políticas de limpeza; duração de resistência climática; seleção manual; idempotência; migração de snapshots; e conjunto de zonas. Nenhuma proposta foi aprovada pelo proprietário nesta entrega.

### Integridade

Somente arquivos de `docs/` foram adicionados ou atualizados. Não houve mudança em `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, dados do catálogo ativo ou módulos candidatos.

## Próxima etapa recomendada

Revisar CI-001…CI-014 e, em paralelo, fechar as políticas de ciclo de vida RSRX e as decisões BUF que dependem da duração de bônus, escudos, estados e resistência climática. Após aprovação explícita, implementar migrador persistente e adaptar o resolvedor candidato em branch isolada. Não integrar diretamente ao motor antigo.

**Restrição invariável:** não apagar nem substituir o motor antigo antes do fechamento e aprovação das especificações.

---

# Handoff técnico — identidade física e ciclo de vida de unidades v0.1

**Data:** 2026-11-27  
**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`  
**Resultado novo:** 17/17 assertions aprovadas; nenhuma regra de design aprovada e nenhum resolvedor integrado.

## Última etapa concluída

Auditoria da identidade física e do ciclo de vida de unidades entre mão, campo e descarte. Foram analisados `_api_gwent_deck_save()`, `_gwent_deck_snapshots()`, `preparar_carta()`, `preparar_carta_pessoal()`, `novo_estado()`, `_resumo_alvo()`, `_remover_unidade()`, `_resolve_round()` e os caminhos de Lágrima Sagrada, Réquiem, Ressurgir e Esgar, além do resolvedor candidato isolado.

### Achados que precisam permanecer no contexto

- **Modelo, exemplar e instância são conceitos separados.** `card_id` identifica o modelo; `exemplar_id` vincula à coleção; `instance_id` deve identificar a ocorrência única durante a partida. O motor legado não gera `instance_id`.
- A rota atual de gravação exige 12 `card_id` distintos e mantém `exemplar_ids_json` alinhado. O snapshot loader só verifica se recebeu 12 cartas; não revalida a unicidade dos modelos. Isso abre caminho para dados antigos/malformados, mas nenhuma base real foi consultada.
- O caminho padrão injeta `exemplar_id` em `payload` e em seguida chama `preparar_carta()`, que não o devolve no snapshot de batalha. O caminho de carta pessoal mantém `exemplar_id` e usa `id` composto `card_id::exemplar_id`, mas ainda não atribui `instance_id` por partida.
- `novo_estado()` faz cópia profunda do deck, sem atribuir identificadores físicos. `_resumo_alvo()` e o frontend usam `id`/`target_id`; cópias iguais não podem ser escolhidas individualmente.
- `_remover_unidade()` consulta e remove com igualdade estrutural de dicionários. A fixture reproduziu que, com duas cartas iguais mas objetos distintos, o objeto solicitado pode continuar no campo e ser anexado também ao descarte, enquanto o outro objeto é removido.
- A remoção central bem-sucedida limpa escudo e quatro estados, mas preserva bônus, `weather_resist` e `combo_ativado`. O fim da rodada limpa bônus, escudo, estados e `combo_ativado`, mas preserva `weather_resist`.
- Lágrima Sagrada move a unidade elegível do descarte para a mão sem normalização adicional; após remoção central, ela preserva bônus e resistência climática, enquanto escudo/estados já foram limpos.
- Réquiem e Ressurgir zeram bônus/removem escudo, mas não limpam explicitamente os quatro estados nem `weather_resist`. O carry-over de estado foi reproduzido apenas em registros obsoletos sintéticos; remoção central e fechamento normal de rodada já limpam esses estados.
- Esgar escolhe uma unidade de poder-base até 5, força a fileira, soma +1 ao bônus preexistente, limpa escudo/estados e remove todas as entradas no descarte com o mesmo `id`.
- O resolvedor candidato melhora remoção por identidade de objeto e seleção por `target_instance_id`, mas ainda permite colisões globais de `instance_id` no campo/descarte e entre zonas na ressurreição. Ele continua isolado.

### Arquivos novos/atualizados

- `docs/card-game-identity-lifecycle-audit-v0.1.md` e `.json`.
- `docs/scripts/audit-card-identity-lifecycle-v0.1.py`.
- `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md` e `docs/PACOTE-MANIFESTO.md` — ponto de continuidade atualizado.

### Regressões direcionadas reexecutadas nesta etapa

| Suite | Resultado |
|---|---:|
| Identidade/ciclo de vida | 17/17 |
| Paridade manual/UI/alvo | 12/12 |
| Seleção de alvos/fileira | 15/15 |
| Buffs/movimentação/proteção | 14/14 |
| Sequência `last_row` | 10/10 |
| Remoção/ressurreição candidata + evidência legada | 49/49 |
| Mapeamento de identidade | 33/33 |
| Efeitos de ciclo de vida | 7/7 |
| Estados negativos candidato | 41/41 |
| Catálogo de efeitos candidato | 23/23 |

As suítes têm escopos distintos e não são uma medida de cobertura única. Todas as auditorias focadas usam fixtures sintéticas ou análise estática; não validam DB real, HTTP, Discord, navegador, R2 ou partidas de produção.

### Próximo passo recomendado (concluído pela revisão seguinte)

A especificação candidata de `CardInstance`, unicidade global, transições de zona e payload `target_instance_id` foi produzida em `docs/card-game-card-instance-contract-v0.1.md`. A próxima ação é revisar CI-001…CI-014 e fechar as políticas BUF/RSRX de preservação/limpeza antes de qualquer integração.

**Restrição invariável:** nenhuma alteração no motor legado, catálogo ativo, banco, API ou frontend nesta fase. Não apagar nem substituir o motor antigo antes do fechamento e aprovação explícita das especificações.

---

# Handoff técnico — auditoria de paridade UI/alvo v0.1

**Data:** 2026-11-27  
**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`  
**Resultado novo:** 12/12 verificações aprovadas; nenhuma regra de design aprovada.

## Última etapa concluída

Auditoria de paridade entre `opcoes_de_alvo()`, `opcoes_de_reliquia()`, seletor do frontend e validação real em `aplicar_jogada()`. Os 12 casos cobrem identidade enviada, filtro por fileira, métricas de poder mostradas versus usadas, fallbacks automáticos, seleção secundária de Égide/Passo e seleção de alvos para relíquias.

### Achados que precisam permanecer no contexto

- `_resumo_alvo()` envia `id`, não `instance_id`; o servidor resolve o primeiro item com `id` correspondente. Duplicatas com ID igual não são selecionáveis individualmente por meio do payload atual. A demonstração foi feita com fixture; não concluir sem auditoria adicional que o fluxo normal de deck cria tais duplicatas.
- Execução usa `effective_power`; Lágrima Sagrada e Réquiem usam `base_power`; o seletor genérico mostra `poder + bonus`. A métrica exibida pode não ser a usada para elegibilidade.
- “Automático” não tem semântica única: Lágrima Sagrada escolhe o último candidato no descarte; Réquiem escolhe maior poder-base; Execução escolhe menor poder efetivo; Égide escolhe maior poder efetivo; Passo escolhe menor poder efetivo.
- Égide Rara: alvo manual primeiro, depois maior poder efetivo entre os restantes. Passo Raro: alvo manual primeiro, depois primeira unidade elegível na ordem do tabuleiro. Ambos pedem somente um alvo primário na interface.
- `relic_options` é retornado pela API, mas não é lido por `app.js`; o modal recompõe as opções a partir de `opponent.board`.
- Lâmina Negra: escudo consome bloqueio, mas preserva o uso da relíquia. Algemas pode atingir bônus 0 e consumir a relíquia sem mudança de estado.

### Arquivos novos/atualizados

- `docs/card-game-manual-target-ui-parity-audit-v0.1.md` e `.json`.
- `docs/scripts/audit-manual-target-ui-parity-v0.1.py`.
- `docs/card-game-buffs-decision-register-v0.1.md` — adendo TUI; BUF-001…BUF-014 continuam abertos.
- `docs/README-PACOTE-CONTINUIDADE.md` e `docs/card-game-handoff.md` — estado mais recente.

### Regressões e integridade nesta continuidade

| Suite | Resultado |
|---|---:|
| Paridade manual/UI/alvo (TUI) | 12/12 |
| Seleção de alvos e escopo de fileira (TGT) | 15/15 |
| Buffs/movimentação/proteção | 14/14 |
| Interações cruzadas de buffs | 9/9 |
| Estado de sequência (`last_row`) | 10/10 |
| Estados negativos | 41/41 |
| Remoção/ressurreição | 49/49 |
| Combos/passivas | 87/87 |
| Líderes | 22/22 |
| Comportamento de cartas | 13/13 |
| Efeitos genéricos | 39/39 |
| Contrato canônico | 35/35 |
| Catálogo candidato | 23/23 |
| Auditoria semântica | 11/11 |

As suites têm escopos distintos e não são uma medida de cobertura única. Todas as auditorias focadas usam fixtures sintéticas; não validam partida de produção, banco, HTTP, Discord, navegador ou R2.

Comparação com o ZIP de continuidade anterior: zero arquivos não-documentais ausentes, adicionados ou alterados. SHA-256 dos arquivos centrais coincide com o pacote anterior: `sistemas/gwent.py` (`f69e8865759862dd`), `sistemas/cartas.py` (`3bed48cbd496de43`), `bot.py` (`a735b2380176a587`), `database.py` (`ead936a2813335e5`) e `site/app.js` (`9aafa6ba1ef2641f`).

### Próximo passo recomendado

Auditar a validação de alvo e o ciclo de vida de cartas que retornam à mão/campo (Lágrima Sagrada, Réquiem e remoção/ressurreição), com foco em identidade de instância, preservação/reset de bônus/escudo/estados, e colisões de IDs. Depois, consolidar os contratos de `target_identity`, métricas, fallbacks e efeitos secundários com as decisões BUF já abertas.

**Restrição invariável:** nenhuma alteração no motor legado, no catálogo ativo, no banco, API ou frontend nesta fase. Não apagar nem substituir o motor antigo antes de fechar e aprovar explicitamente as especificações.

---

# Handoff técnico — Soulsbo Card Game

## Estado mais recente — seleção de alvos e escopo de fileira v0.1 (2026-11-27)

**Status:** auditoria read-only do runtime legado; diagnóstica e não aprovada. Nenhum handler, catálogo, DB, API ou frontend foi alterado.

### Resultado desta etapa

- Criados `docs/card-game-target-selection-row-scope-audit-v0.1.md/.json` e `docs/scripts/audit-target-selection-row-scope-v0.1.py`.
- **15/15** verificações passaram. Foram exercitados `_poder_efetivo()`, `_aplicar_habilidade_identidade()` e `aplicar_jogada(..., action="leader")` com fixtures sintéticas.
- Métricas encontradas: diversos efeitos e líderes selecionam por poder efetivo; Cisalhamento Gravitacional filtra bônus positivo e ordena pelo bônus bruto.
- Escopos variam: campo inimigo global, fileira escolhida, fileira fixa e fileira corrente de aliados. Os filtros em campo consultam `row`, não `fileira`.
- Regressão: Gravidade do Flagelo seleciona o maior poder efetivo global, move a unidade para `row` da carta e preserva `fileira` original.
- Fallback: Regressão Serena tenta alvos com status, depois aliado mais fraco na fileira e, sem aliado, fortalece a própria carta.
- Proteção: Morgott exclui aliados com escudo antes de selecionar até dois alvos mais fortes.
- Empate: `max()` e `sorted()` preservam a ordem atual do tabuleiro entre valores iguais. Isso é comportamento legado, não política aprovada para o novo motor.
- Vínculos filtrados/inativos: Tiro de Cobertura e Contrafogo não estão ativos após V18; `v75_blood_pursuit` e `v75_moon_ward` não possuem atribuições individuais ativas. Não os contar como efeitos disponíveis.
- O registro de decisões ganhou adendo TGT para BUF-006, BUF-008 e BUF-013; as 14 decisões BUF continuam abertas.

### Artefatos

- `docs/card-game-target-selection-row-scope-audit-v0.1.md` — evidências, matriz de escopo/métrica, ramos ativos versus arquivados e requisitos candidatos.
- `docs/card-game-target-selection-row-scope-audit-v0.1.json` — 15 resultados estruturados.
- `docs/scripts/audit-target-selection-row-scope-v0.1.py` — harness read-only reproduzível.
- `docs/card-game-buffs-decision-register-v0.1.md` — adendo TGT; sem aprovação de design.

### Limites e continuidade

- Não cobre exaustivamente todas as cartas, relíquias, opções apresentadas pela UI ou colisões de IDs de cópias físicas.
- Não prova estabilidade do desempate após uma serialização/reordenação real; apenas comprova a regra atual da lista em memória.
- As regras observadas continuam candidatas à avaliação. O runtime antigo deve permanecer preservado.
- Próximo passo: auditar a correspondência entre opções de alvo expostas pela UI, filtro de fileira, `target_id`, validação do handler e alvo realmente resolvido em cartas especiais e relíquias.

---


## Estado mais recente — família de sequência e histórico `last_row` v0.1 (2026-11-27)

**Status:** auditoria read-only do runtime legado, diagnóstica e não aprovada. Nenhum handler foi alterado; nenhuma regra foi integrada. O objetivo desta etapa é distinguir posição atual de unidade e histórico de jogada do jogador antes da reconstrução.

### Resultado desta etapa

- Criados `docs/card-game-sequence-power-state-audit-v0.1.md/.json` e `docs/scripts/audit-sequence-power-state-v0.1.py`.
- **10/10** assertions aprovadas, usando `aplicar_jogada()`, `_remover_unidade()` e `_resolve_round()` em fixtures sintéticas.
- `encadeamento` compara a fileira da nova unidade com a última fileira em que o jogador jogou uma unidade; concede +2 se igual.
- `adaptacao` exige `last_row` anterior não nulo e diferente da fileira da unidade atual; concede +1.
- `quebra_ritmo` compara a fileira da nova unidade com a última fileira em que o adversário jogou uma unidade; concede +1 se igual.
- O snapshot de `last_row` é lido antes de resolver a nova unidade; o valor só é atualizado após a jogada de unidade ser resolvida e anexada ao campo.
- `gwent_passo` muda `unit.row`, mas não altera `player.last_row`. Uma unidade pode sair da fileira que originou o último evento de jogada e ainda assim essa fileira continuar acionando `adaptacao`/`encadeamento`.
- Carta especial e remoção não atualizam/limpam `last_row`; a transição para uma nova rodada o redefine para `None` nos dois jogadores.
- O registro BUF-008 foi atualizado com a recomendação candidata de um estado por jogador (`last_unit_play_row`) distinto da posição e do histórico de movimento.
- Regressões reexecutadas: buffs 14/14; matriz cruzada 9/9; estados 41/41; remoção/ressurreição 49/49; combos/passivas 87/87; líderes 22/22; comportamento genérico 13/13; contrato 35/35; catálogo 23/23; semântica 11/11. São suites com escopos distintos, não uma contagem agregada.

### Artefatos desta etapa

- `docs/card-game-sequence-power-state-audit-v0.1.md` — semântica observada, dez casos, requisitos candidatos e decisões abertas.
- `docs/card-game-sequence-power-state-audit-v0.1.json` — evidências estruturadas.
- `docs/scripts/audit-sequence-power-state-v0.1.py` — harness de repetição.
- `docs/card-game-buffs-decision-register-v0.1.md` — BUF-008 atualizado; sem aprovação da recomendação.

### Limites e continuidade

- `veil_shift`, `pilgrim_duel` e `mist_trail` permanecem apenas aliases/branches históricos filtrados ou inativos conforme a auditoria semântica; não foram reativados.
- As fixtures não avaliam partidas completas, persistência, UI, equilíbrio ou produção.
- Nenhuma regra BUF foi aprovada. O runtime antigo permanece preservado.
- Próximo passo: auditar outras famílias de alta prioridade que dependem de estado/seleção; depois revisar as decisões BUF em conjunto. A reconstrução continua bloqueada até especificações aprovadas.

---

## Etapa anterior — matriz cruzada de buffs, movimentação, proteção, clima, estados e combos v0.1 (2026-11-27)

**Status:** auditoria read-only do motor legado; diagnóstica, não aprovada e não integrada. O objetivo é registrar a interação das famílias antes de fechar contratos canônicos. O runtime antigo continua preservado.

### Resultado desta etapa

- Nova matriz: `docs/card-game-buffs-cross-interactions-v0.1.md` com nove interações reproduzidas; resultado JSON em `docs/card-game-buffs-cross-interactions-v0.1.json`; script em `docs/scripts/audit-buffs-cross-interactions-v0.1.py`.
- Criado `docs/card-game-buffs-decision-register-v0.1.md`, que consolida BUF-001…BUF-014 com evidências, alternativas, recomendação candidata e dependências. O registro deixa todas as 14 decisões como abertas; não substitui aprovação do proprietário.
- **9/9** casos cruzados passaram. A seleção de alvos usa poder efetivo nos handlers testados, portanto clima e estados mudam qual unidade é considerada mais fraca/forte.
- `star_gravity` seleciona pela força efetiva na fileira de origem, muda `row`, preserva `fileira` e recalcula a penalidade climática na fileira de destino, descontando `weather_resist`.
- Combos usam `row` corrente para `team_bonus`. Uma unidade movida continua elegível na fileira atual, ainda que sua `fileira` original seja diferente.
- Ordem observada de unidade: identidade → combo/team bonus → raridade → passiva de facção → anexação. No teste Raro, a carta ganhou +2 do combo, +1 da raridade e +1 da passiva; `team_bonus` concedeu +1 ao aliado preexistente.
- `gwent_passo` muda a posição corrente, mas não reescreve `player.last_row`; um buff de fileira subsequente consulta a nova `row`.
- Preço em Sangue escolhe vítima e calcula ganho com poder efetivo; o sacrifício ignora escudo e a remoção central limpa escudo e estados. Vingança não dispara quando remoção/execução é bloqueada por escudo.
- Purificação de Regressão Serena não consome escudo; elegibilidade depende de existir estado negativo, e a ordenação usa poder efetivo.

### Artefatos desta etapa

- `docs/card-game-buffs-cross-interactions-v0.1.md/.json` — matriz e resultado de nove cruzamentos.
- `docs/scripts/audit-buffs-cross-interactions-v0.1.py` — harness reproduzível read-only.
- `docs/card-game-buffs-decision-register-v0.1.md` — consolidação das 14 decisões BUF com alternativas e recomendações candidatas ainda abertas.
- `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md` — continuidade e histórico atualizados.

### Validação repetida nesta continuidade

| Suite | Resultado |
|---|---:|
| Auditoria base de buffs/movimento/proteção | 14/14 |
| Matriz cruzada de buffs | 9/9 |
| Estados candidatos | 41/41 |
| Remoção/ressurreição | 49/49 |
| Combos e passivas | 87/87 |
| Líderes | 22/22 |
| Comportamento genérico | 13/13 |
| Contrato de cartas | 35/35 |
| Catálogo de efeitos | 23/23 |
| Auditoria semântica | 11/11 |

Essas suites têm escopos próprios e não medem a mesma cobertura. `test-effect-semantic-audit-v0.1.py` foi reexecutado isoladamente e passou 11/11; a tentativa combinada anterior excedeu o limite de tempo, mas a execução isolada confirmou o resultado.

### Estado técnico e limites

- Nenhuma regra BUF-001…BUF-014 foi aprovada por esta matriz; as decisões permanecem em aberto.
- Não houve alteração em `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, schemas, dados do catálogo ou persistência.
- Testes usam fixtures sintéticas em memória e chamadas a funções do motor; sem DB de produção, HTTP, Discord, navegador, R2 ou simulação competitiva.
- O achado anterior de raridade amplificando Vingança reativa continua registrado em BUF-001/002; não foi redefinido aqui.

### Próximo passo recomendado

Revisar e fechar BUF-001 a BUF-014 com o proprietário, em especial os grupos dependentes BUF-001/002/013, BUF-006/008 e BUF-009/010/011. O registro de decisão já foi preparado. Separar fatos observados no legado de decisões de design do novo motor; não conectar resolvedores nem apagar handlers antes da aprovação.

---

## Etapa anterior — auditoria de buffs, movimentação, proteção e clima v0.1 (2026-11-27)

**Status:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`. Auditoria documental e testes diagnósticos foram adicionados; não houve alteração de handlers, catálogo de cartas, banco, API, frontend ou motor antigo. O objetivo continua sendo fechar especificações antes de substituir qualquer parte do runtime.

### Resultado comprovado

- `gwent_chifre`: concede +2 aos aliados pré-existentes da fileira escolhida; raridade pode acrescentar +1 a alvos na ordem do tabuleiro.
- `gwent_muralha`: concede +1 aos aliados da fileira; se a fileira estiver vazia, a carta é consumida sem efeito.
- `gwent_vinculo`: exige pelo menos dois aliados na fileira; abaixo disso a jogada é recusada.
- `gwent_egide` Rara protege duas unidades sem escudo, embora a descrição estática diga “uma unidade”.
- `gwent_passo` Raro move até duas unidades; o alvo escolhido ou o mais fraco é movido primeiro e os demais seguem a ordem do tabuleiro.
- `star_gravity` muda a `row` corrente do inimigo mais forte e aplica -2 ao bônus (piso -2); `fileira` permanece original e o clima da nova posição incide imediatamente.
- Escudo bloqueia remoção comum e consome uma carga; sacrifício ignora escudo. Debuffs/status não são bloqueados universalmente.
- A identidade ativa `vigil_seal` concede `weather_resist=1`; essa resistência reduz apenas clima na fileira atual, não estados negativos.
- `weather_resist` permanece na cópia arquivada ao fim da rodada, ao contrário de bônus, escudo e estados, que são limpos.
- Combo é aplicado antes de anexar a nova unidade; `team_bonus` alcança aliados já presentes na mesma fileira. A passiva de facção é aplicada após raridade e não é amplificada por ela.
- Não foi localizada operação genérica de transferência de bônus. Efeitos que combinam redução inimiga e ganho próprio são operações compostas, cada qual com sua condição.

### Interação crítica reproduzida

A Chama Negra é Épica e remove a unidade mais forte de cada lado. Quando a unidade aliada removida tem Vingança, `_remover_unidade()` concede +1 aos aliados sobreviventes da mesma fileira. O snapshot global usado pela potência de raridade inclui esse delta reativo e acrescenta outro +1 ao primeiro aliado na ordem do tabuleiro. Resultado observado: sobreviventes ficam com bônus +2 e +1, em vez de +1 e +1 que viriam somente da Vingança. O novo contrato deve decidir se gatilhos reativos podem consumir orçamento de raridade; recomendação candidata é que não o façam implicitamente.

### Artefatos adicionados

- `docs/card-game-buffs-movement-protection-audit-v0.1.md` — auditoria completa, tabela de mecânicas, achados e decisões BUF-001 a BUF-014.
- `docs/card-game-buffs-movement-protection-audit-v0.1.json` — resultado estruturado e 14 casos.
- `docs/scripts/audit-buffs-movement-protection-v0.1.py` — 14 verificações sintéticas reproduzíveis.

### Validação e limites

- Auditoria direcionada: **14/14**.
- Suites complementares executadas nesta continuidade: comportamento de efeitos **13/13**, combos e passiva de facção **87/87**, líderes **22/22**. Manter escopos separados; não somar como uma única cobertura.
- Testes controlados não são simulação competitiva, teste de produção, HTTP, Discord, navegador, banco ou R2.
- Não foram implementadas as propostas de transferência, limites de bônus, política universal de escudo, duração de resistência climática, alvo/desempate por `instance_id` ou modelo explícito `base_row/current_row`.
- Nenhum handler funcional foi alterado nesta etapa; os artefatos novos são documentação e diagnóstico.

### Próximo passo recomendado

A matriz cruzada e o registro de decisões estão prontos. Revisar e fechar explicitamente BUF-001 a BUF-014 (especialmente os grupos de dependência indicados no registro); depois congelar contratos e somente então iniciar a reconstrução. **Não apagar nem substituir o motor antigo nesta fase.**

---

# Etapa anterior — auditoria cruzada de remoção, sacrifício e retorno v0.1 (2026-11-27)

**Status:** auditoria do motor legado e resolvedor candidato independentes concluídos; `CANDIDATE_FOR_REVIEW_NOT_APPROVED`; **não integrado ao runtime**. Esta etapa ampliou a validação de 43 para 49 testes e criou uma matriz de 12 interações cruzadas. Nenhuma regra de remoção/ressurreição foi aprovada pelo proprietário nesta etapa.

## Resultado comprovado no motor legado

- Nove atribuições rastreadas: Chama Negra (`gwent_queima`), Lâmina da Morte Destinada (`gwent_execucao`), Devorar (`devorar`), Preço em Sangue (`v75_blood_price`), Rykard (`rykard_devour`), Ressurgir (`ressurgir`), Chamado dos Mortos (`gwent_requiem`), Esgar (`esgar_blood_priest`) e Lágrima Sagrada (`gwent_medico`). Lágrima Sagrada devolve para a mão, não ao campo.
- Escudo bloqueia remoção comum e execução, consumindo uma carga; sacrifício ignora escudo. Tentativa bloqueada não descarta, não soma `baixas` nem dispara Vingança.
- Remoção bem-sucedida limpa escudo e Geada/Podridão/Sangramento/Loucura, move a unidade ao descarte, incrementa `baixas` (inclusive sacrifício) e dispara Vingança para aliados restantes da mesma fileira quando o campo legado é `habilidade == "vinganca"`.
- `_remover_unidade()` usa membership e `list.remove()` por igualdade de dicionários. Cópias físicas com payload igual podem fazer o objeto errado sair do tabuleiro, enquanto o objeto passado é anexado ao descarte; a mesma referência pode permanecer no tabuleiro e no descarte.
- A expressão de limite da Execução `min(6, 6 + potencia_raridade)` é sempre 6 para os orçamentos atuais. A raridade não aumenta o limite.
- Devorar escolhe o aliado mais fraco na fileira da carta e ganha `min(4, max(1, poder_efetivo))`; sem alvo faz no-op silencioso e a carta ainda entra. Preço em Sangue sacrifica o aliado mais fraco na mesma fileira, ganha até +3 e recebe +1 sem alvo.
- Rykard exige dois aliados na fileira, sacrifica o mais fraco e concede +2 aos sobreviventes. Se a vítima tiver Vingança, a ordem atual aplica +1 da Vingança e depois +2 de Rykard: +3 por sobrevivente.
- Ressurgir e Réquiem zeram o bônus e retiram escudo, mas não limpam explicitamente os quatro estados na chegada. O caminho central de remoção já limpa esses estados antes do descarte; o risco de retorno contaminado concentra-se em snapshots antigos/malformados ou outras origens.
- Esgar limpa status, força a fileira escolhida e soma +1 ao bônus pré-existente; seu handler remove do descarte todas as cópias com o mesmo `card_id`, mesmo ressuscitando apenas uma.
- O retorno por efeito de entrada é resolvido antes do combo; a carta jogada é anexada ao campo e depois a unidade ressuscitada. A ressuscitada não ativa combo na jogada em que chega, mas pode participar de checagens futuras.

## Artefatos atuais

- `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` — evidência linha a linha, nove defeitos, decisões e recomendação candidata.
- `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — 12 interações cruzadas, ordem de execução e recomendação.
- `data/card_game/removal-resurrection-registry-candidate.v1.json` + schema — nove atribuições, política de remoção, `instance_id` e normalização propostas.
- `sistemas/card_removal_resurrection_candidate.py` — `attempt_removal`, `resurrect_from_discard`, `recover_unit_to_hand`; módulo isolado.
- `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` — 49 testes reproduzíveis.
- `docs/card-game-removal-resurrection-validation-v0.1.md/.json` — resultado, hashes e limites.

## Interações cruzadas verificadas

1. Vingança em Devorar: Vingança fortalece aliados que já estavam no campo; a carta Devorar recebe depois o ganho do sacrifício, sem receber o +1 da vítima.
2. Vingança em Rykard: a acumulação atual é +1 seguida de +2, resultando em +3 para cada sobrevivente da fileira.
3. Unidade ressuscitada: não entra na verificação do combo da jogada atual, mas suas tags podem contribuir para uma jogada posterior.
4. Remoção seguida de ressurreição no resolvedor candidato: uma instância exata retorna com escudo/status limpos; o contador de remoções não é decrementado.
5. O protótipo agora reconhece `effect_id == "effect.vengeance_on_removal"`; `effect_ids` e `habilidade == "vinganca"` são apenas aliases de compatibilidade.

## Validação e limites

- Suite específica atual: **49/49**.
- Motor legado agregado: **251/251 em oito suites**; partidas stateful/snapshots: **12/12**.
- Contrato/schema de carta: **35/35**; estados candidatos: **41/41**; catálogo candidato de efeitos: **23/23**; auditoria semântica: **11/11**; ferramentas de auditoria de produção em fixtures: **7/7**.
- Esses totais são conjuntos separados e parcialmente sobrepostos; não devem ser somados como casos únicos nem interpretados como equilíbrio competitivo.
- Os testes de legado usam estados sintéticos em memória. Não são testes HTTP, Discord, navegador, banco de produção ou R2.
- `sistemas/card_removal_resurrection_candidate.py` não é importado por `sistemas.gwent`; não houve migração de `instance_id`, DB, APIs, frontend, cartas ou imagens.
- Os hashes dos cinco arquivos funcionais centrais (`sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`) coincidem com o ZIP de entrada desta etapa; runtime preservado.

## Histórico por arquivo nesta etapa

| Arquivo | Função/campo | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `sistemas/card_removal_resurrection_candidate.py` | `_has_vengeance()` | Lia `effect_ids` plural e alias de `habilidade` | Reconhece `effect_id` canônico singular, mantendo aliases só para compatibilidade | Alinhar à definição de carta canônica | Só módulo candidato; runtime não importa | 49/49 + `py_compile` |
| `data/card_game/removal-resurrection-registry-candidate.v1.json` | `on_remove_effects` | Só declarava condição de campo legado | Adiciona `canonical_check` e `compatibility_check` | Documentar a migração de alias para `effect_id` | Dados candidatos | Schema + 49/49 |
| `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` | seis testes cruzados novos | 43 asserts | 49 testes; inclui ID canônico, retorno round-trip, combo futuro, Devorar+Vingança, Rykard+Vingança e ordem de resolução | Cobrir interações que isoladamente não apareciam | Ferramenta de teste; não é chamada pelo jogo | 49/49 |
| `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` | documento inteiro | Sem matriz de interações cruzadas | 12 interações e ordem exata da jogada/retorno | Explicitar dependências entre efeitos | Documentação | Conferência com fonte + testes |
| `docs/card-game-removal-resurrection-validation-v0.1.md/.json` | contagem, escopo e hashes | 43/43 | 49/49 e seis casos novos | Manter resultado reproduzível | Relatório | JSON + 49/49 |
| `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` | seção 4.1 | Sem explicação de interações cruzadas | Liga Devorar/Vingança, Rykard, combo/ressurreição e `effect_id` | Contextualizar as decisões pendentes | Documentação | Revisão cruzada |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md` | estado, entrada e histórico | Estágio indicava 43 testes e não priorizava matriz | Estado atual atualizado para 49, matriz priorizada e histórico por arquivo | Permitir novo chat assumir sem contexto externo | Documentação | Conferência de links e pacote |

## Decisões ainda pendentes

1. Limite de poder da Lâmina da Morte Destinada na nova escala 1–15; o 6 legado não é aprovado automaticamente.
2. Devorar sem alvo: rejeitar jogada antes de consumir a carta ou definir fallback explicitamente.
3. Vingança após sacrifício: preservar ou restringir as causas que disparam.
4. Semântica do contador legado `baixas`: renomear para `board_removals`/`removed_units` ou eliminá-lo do modelo novo.
5. Acúmulo Vingança + Rykard: manter o +3 ou estabelecer não acumulação.
6. Limites de poder de Ressurgir (5), Réquiem (até 9 no motor atual), Esgar (5) e Lágrima Sagrada (até 7 no motor atual).
7. Bônus de chegada de Esgar: definir exatamente +1, somar +1 ao bônus anterior ou outra regra.
8. Política de fileira de chegada por efeito.
9. `instance_id` único por exemplar e sua propagação por coleção, deck, alvo, descarte e snapshot.
10. Normalização de estados no retorno ao campo; retorno à mão continua uma operação diferente.

## Próximo passo recomendado

Auditar buffs, movimento e efeitos de fileira com a mesma matriz de código-fonte, incluindo sobreposição com remoção/sacrifício, antes de fechar decisões finais e integrar qualquer resolvedor. A reconstrução das 137 cartas, o novo registry oficial e as fórmulas EFP/custo/raridade ainda não começaram; EFP, custo, raridade e limite de deck seguem propostas não aprovadas.

---
# Handoff técnico — Soulsbo Card Game

## Etapa anterior — auditoria dos estados negativos v0.1 (2026-11-27)

**Status:** mapeamento do motor legado concluído para Geada, Podridão Escarlate, Sangramento e Loucura Frenética. Registry e resolvedor de referência criados, testados e ainda **CANDIDATOS, NÃO APROVADOS e NÃO CONECTADOS AO RUNTIME**. Nenhum handler legado foi apagado ou alterado nesta etapa.

### Resultado comprovado

- Quatro perfis de estado e regras de contador/limiar documentados.
- 15 aplicações mapeadas: sete especiais, cinco identidades, dois líderes e uma relíquia.
- Cinco caminhos de purificação mapeados: dois líderes, uma identidade, um especial e uma relíquia.
- Geada, Podridão e Loucura reduzem poder efetivo por marca, com limite agregado de três pontos; Sangramento não reduz poder efetivo diretamente.
- Podridão corrói um bônus positivo ao cruzar para duas marcas; Sangramento reduz dois pontos de bônus (piso -2) e consome as marcas ao cruzar para duas; Loucura zera bônus positivo ao cruzar para duas; Geada não tem consequência secundária.
- As consequências de limiar na proposta são acionadas somente em transição para duas marcas; raridade não aplica amplificação automática; estados expiram no fechamento de toda rodada, inclusive a final.

### Defeitos/diferenças legadas comprovadas

1. Malenia (`scarlet_bloom`) pode repetir corrosão de bônus quando o alvo já está em duas marcas de Podridão.
2. Oráculo da Geada (`v75_frost_oracle`) pode ganhar bônus novamente mesmo quando o alvo já está no limite de Geada.
3. `_aplicar_potencia_raridade()` pode acrescentar outra alteração ao bônus depois da consequência de estado.
4. Alguns especiais com amplificação de raridade adicionam marcas a alvos pela ordem do tabuleiro, não por critério de força explícito.
5. `_resolve_round()` termina a partida antes do bloco comum de limpeza na rodada final, podendo conservar os contadores negativos no snapshot terminal.

### Artefatos adicionados

- `data/card_game/status-registry-candidate.v1.json` — quatro perfis, regras agregadas, 15 aplicações e cinco purificadores.
- `data/card_game/status-registry.schema.v1.json` — JSON Schema Draft 2020-12.
- `sistemas/card_status_candidate.py` — resolvedor de referência puro para aplicação de marcas, limiar, poder efetivo, purificação e fechamento de rodada; não importado pelo runtime legado.
- `docs/scripts/test-card-status-candidate-v0.1.py` — 41 testes, incluindo regressões que reproduzem bugs do legado.
- `docs/card-game-status-effects-review-v0.1.md` e `docs/card-game-status-effects-validation-v0.1.md/.json` — evidência, proposta, testes e limitações.

### Validação executada

- Estados candidatos: 4/4; aplicações: 15; purificadores: 5.
- Testes do resolvedor candidato: **41/41**.
- Contrato: **35/35**; catálogo: **23/23**; auditoria semântica: **11/11**.
- Motor legado: **251/251 asserts em oito suites**; partidas stateful: **12/12 cenários**.
- Schema Draft 2020-12 e instância do registry aprovados; `py_compile` passou.
- Os hashes de `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` coincidem com as mesmas entradas do ZIP mestre no início desta revisão. Nenhum desses arquivos foi alterado.

Os totais de suites pertencem a escopos distintos e não equivalem a 333 efeitos únicos testados. As suites legadas continuam exercitando o motor antigo; parte dos testes demonstra explicitamente os comportamentos que a proposta candidata pretende corrigir. Isso não os torna regra aprovada. O resolvedor novo cobre transições de estado, não os seletores completos de alvo/handler de cada carta.

### Próximo passo autorizado

Obter a decisão do proprietário sobre os perfis de estado (ou ajustar a proposta); depois revisar remoção/execução, sacrifício e ressurreição. Somente após aprovação será criada uma versão de registry aprovada e planejada a integração a unidades, especiais, líderes, relíquias, purificadores, descrições e UI. Não conectar o módulo candidato nem alterar o motor legado antes disso.

### Histórico detalhado desta etapa

| Arquivo | Função/campo | Antes | Depois | Motivo | Impacto no restante | Validação |
|---|---|---|---|---|---|---|
| `data/card_game/status-registry-candidate.v1.json` | `statuses`, `global_rules`, `applications`, `cleansers` | As quatro regras estavam espalhadas no motor; sem registry tipado | Declara quatro estados, transições de limiar, cap agregado, 15 aplicadores e cinco purificadores | Criar fonte candidata explícita e auditável sem afirmar equivalência automática | Dados candidatos apenas; não importados pelo runtime | Schema Draft 2020-12, validação estrutural e 41/41 testes |
| `data/card_game/status-registry.schema.v1.json` | Schema raiz e definições de estado/aplicação/purificação | Não havia schema específico | Define campos, enums, escopos, parâmetros e mapeamentos de estado | Impedir metadata de estado inconsistente | Apenas validação do JSON | `Draft202012Validator.check_schema` e instância passaram |
| `sistemas/card_status_candidate.py` | `load_registry`, `validate_registry`, `apply_status_marks`, `combined_control_penalty`, `effective_power`, `clear_statuses`, `close_round_statuses` | Sem resolvedor isolado para testar a proposta | Implementa transições de marca, consequência de limiar, cap de poder, limpeza e expiração | Permitir testar a regra candidata independentemente do motor antigo | Novo módulo isolado; não importado por `sistemas.gwent` | 41/41 testes e `py_compile` |
| `docs/scripts/test-card-status-candidate-v0.1.py` | 41 testes `unittest` | Sem regressão específica dos quatro estados | Testa schema, mappings, fontes, purificadores, transições, cap, limpeza e reprodução de três defeitos legados | Fazer a proposta reproduzível e distinguir regressão de legado de regra nova | Ferramenta de teste; sem runtime | 41/41 |
| `docs/card-game-status-effects-review-v0.1.md` | Seções 2–11 | Estados dispersos sem análise de transição consolidada | Documenta semântica antiga, aplicadores, purificadores, raridade, riscos, proposta e pendências | Preservar a evidência antes de refatorar | Documentação somente | Conferência com `sistemas/gwent.py`, JSON e suites |
| `docs/card-game-status-effects-validation-v0.1.md/.json` | Relatório de resultado | Sem relatório consolidado desta etapa | Registra contagens, comandos, testes, hashes e limites | Permitir handoff verificável | Documentação/relatório somente | JSON revisado; hashes comparados ao ZIP de entrada |
| `docs/README-PACOTE-CONTINUIDADE.md` | Estado mais recente e ordem de leitura | Iniciava pela família genérica de efeitos | Prioriza revisão de estados, schema, resolvedor e teste antes do catálogo amplo | Fazer o próximo chat partir do estado real mais recente | Documentação somente | Links/caminhos conferidos |
| `data/card_game/README.md` | Registry de estados | Não documentava perfis de estado | Lista os novos arquivos e reforça que são candidatos isolados | Evitar importação prematura | Documentação somente | Revisão cruzada |
| `docs/PACOTE-MANIFESTO.md` | Estado, hashes e histórico | Refletia a revisão semântica anterior | Registra 41/41, hashes e arquivos da etapa | Atualizar a fonte principal de continuidade | Documentação somente | Comparação de hashes/ZIP |

---

## Estado anterior — catálogo candidato e auditoria semântica AST v0.1 (2026-11-27)

**Status:** etapa documental/estrutural concluída; o catálogo ainda é uma PROPOSTA e não foi conectado ao motor. O projeto agora tem uma matriz de migração que liga cada ID legado a uma família canônica candidata, parâmetros, descrição original e cartas atualmente atribuídas.

## Resultado comprovado na fonte atual

- `sistemas/cartas.py`: 59 definições em `HABILIDADES`: 32 efeitos de unidade, 21 especiais táticas e seis relíquias.
- `sistemas/gwent.py`: 22 identidades ativas, 27 combos, 10 líderes, quatro passivas de facção e 72 chaves em `CARD_SYNERGY_TAGS`.
- A proposta agrupa esses comportamentos em **54 famílias de efeito candidatas (36 unidade, 12 especiais e seis relíquias)**; os 59 IDs de `HABILIDADES` têm alias de migração único e preservam nome, descrição, parâmetros default e lista de cartas atualmente associadas.
- As 22 identidades ativas têm override por `card_id`; 16 cartas também carregam um campo genérico que o motor suprime ao resolver a identidade. Na nova definição, somente o `effect_id` da identidade é migrado; o campo genérico suprimido fica arquivado, não acumulado.
- 11 definições de habilidade de unidade não estão atribuídas a nenhuma carta atual: `circulo_arcano`, `contragolpe`, `dupla_fornalha`, `eco_arcano`, `escudo_ferro`, `espolios`, `guardiao_fileira`, `irmandade_veu`, `resistencia_climatica`, `sangue_frio`, `sobrevivente`. Permanecem no mapa de migração, mas não serão atribuídas automaticamente.
- Foram classificados 18 ramos filtrados pela V18, seis ramos V75 sem associação ativa e quatro valores de campo sem metadado canônico (`devoto`, `legado`, `escolha_ritmo`, `sinergia_faccao`). Eles não foram apagados do runtime.
- `gloria` está fora de `HABILIDADES`, aparece em três cartas e possui hook em `_resolve_round()`; `sobrevivente` está declarado em `HABILIDADES`, sem carta atribuída no snapshot e sem handler identificado. **Não são comportamentos equivalentes comprovados.** O alias `sobrevivente` fica arquivado como texto não implementado, sem migração automática. Qualquer nova regra de sobrevivência exige decisão explícita e novo handler/teste.
- Os 27 combos foram importados da política já aprovada: mínimo de duas cartas distintas, prioridades únicas, carta que recebe bônus individual participa por tag, um combo por jogada e participante válido para combos pendentes. Cinco IDs de carta presentes no mapa de tags são órfãos e ficam excluídos até existir uma carta real.
- Líderes e passivas foram separados: 10 líderes em slot próprio e quatro passivas globais, sem fazer a passiva da facção invalidar a pureza da carta.

## Validação desta etapa

- **23/23 testes estruturais** em `docs/scripts/test-effect-catalog-candidate-v0.1.py`; **11/11 testes semânticos** em `docs/scripts/test-effect-semantic-audit-v0.1.py`.
- O registry candidato passou o JSON Schema Draft 2020-12 e `validate_effect_registry()`.
- Os parâmetros default de todos os 59 aliases genéricos/especiais/relíquias e das 22 identidades foram validados contra o schema dos respectivos efeitos. `effect.sequence_power` exige agora `requires_previous_play:boolean` explícito e verdadeiro em todos os seis aliases porque o legado não concede bônus sem jogada anterior válida.
- Todos os 27 combos têm ao menos um exemplo de par com IDs distintos que cobre suas tags exigidas.
- Os testes antigos continuam separados: contrato estrutural **35/35**, comportamento do motor legado **251/251**, stateful **12/12** e política de combos **32/32**. Não somar esses conjuntos como se fossem 317 comportamentos exclusivos; cobrem escopos diferentes e têm sobreposição.

## Artefatos novos

- `data/card_game/effect-registry-candidate.v1.json` — 54 famílias candidatas e 27 combos; não aprovado.
- `data/card_game/legacy-effect-aliases-v0.1.json` — 59 aliases, 22 overrides por identidade, parâmetros, textos originais, cartas atribuídas e ramos arquivados.
- `data/card_game/leader-registry-candidate.v1.json` — 10 líderes em estrutura separada.
- `data/card_game/faction-passives-candidate.v1.json` — quatro passivas globais separadas dos efeitos individuais.
- `docs/card-game-effect-catalog-decision-v0.1.md/.json` — tabela de famílias, atribuições atuais, combos, órfãos e decisões candidatas.
- `docs/card-game-effect-catalog-validation-v0.1.md/.json` — evidências, hashes, contagens, testes e limitações (23/23 estrutural, 11/11 semântico).
- `docs/card-game-effect-semantic-audit-v0.1.md/.json` — auditoria AST por família, branch/hook, divergências semânticas, quatro campos sem binding ativo e triagem de risco.
- `docs/scripts/build-effect-catalog-candidate-v0.1.py` — extrai os dados reais do catálogo/motor legado e recria os candidatos.
- `docs/scripts/test-effect-catalog-candidate-v0.1.py` — valida schemas, aliases, parâmetros, identidades, combos, líderes e passivas.
- `docs/scripts/audit-effect-semantic-groups-v0.1.py` — liga famílias e aliases aos branches, hooks e locais de código.
- `docs/scripts/test-effect-semantic-audit-v0.1.py` — 10 regressões do relatório semântico.
- `docs/scripts/summarize-effect-catalog-candidate-v0.1.py` — executa as duas suites e gera relatório agregado.

## Limites: o que ainda NÃO está aprovado ou implementado

- `resolution_handler` no registry é apenas o nome proposto de uma futura função; nenhum dos 54 handlers novos foi implementado.
- O mapa de alias é uma proposta de migração, não uma decisão definitiva de manter todos os efeitos. Os grupos compostos precisam de revisão semântica, especialmente `row_status_pressure`, `enemy_bonus_reduction`, `sequence_power`, `ally_sacrifice_power`, `gravity_reposition`, `frost_storm_momentum`, `ruin_omen` e efeitos de compra/ressurreição.
- Os 27 combos vieram do catálogo atual, mas suas tags e nomes devem ser reavaliados quando as quatro facções e o catálogo de cartas forem reconstruídos.
- EFP, custo, orçamento do deck, fórmula/faixas de raridade, distribuição dos efeitos e atribuição dos efeitos a cartas continuam não aprovados.
- Não foi criado ainda o manifesto das 137 cartas novas; nomes, títulos, lore, facções e arte permanecem no baseline histórico.
- Nenhum handler, módulo de runtime, banco, API, frontend, deck builder ou renderizador foi alterado nesta etapa.

## Próximo passo autorizado

Revisar primeiro as 18 famílias classificadas HIGH e as seis MEDIUM no relatório semântico (classificação heurística de prioridade, não medida de poder). Para cada família candidata, comparar aliases quanto a condição, alvo, magnitude, duração, stack, limite, bloqueios, persistência e resultado do motor legado. Dividir famílias que não são realmente equivalentes; só depois emitir uma versão v0.2 do registry e atribuir decisões finais `keep/merge/redesign/remove`. Não implementar nem apagar handlers até essa revisão e os testes novos estarem definidos.

## Histórico detalhado desta etapa

| Arquivo | Função/campo | Antes | Depois | Motivo | Impacto no restante | Validação |
|---|---|---|---|---|---|---|
| `docs/scripts/build-effect-catalog-candidate-v0.1.py` | `FAMILIES`, `build()` | Sem mapa integral entre aliases legados e famílias parametrizadas | Cria 54 famílias, 59 aliases, 22 overrides, combos, líderes e passivas; declara `requires_previous_play=true` em `sequence_power`; separa `gloria` funcional de `sobrevivente` não implementado | Transformar inventário em proposta de migração sem presumir equivalência | Só produz JSON/Markdown candidato; não altera runtime | Registry válido; 23/23 testes estruturais e 11/11 semânticos |
| `docs/scripts/audit-effect-semantic-groups-v0.1.py`, `docs/card-game-effect-semantic-audit-v0.1.md/.json` | AST de `aplicar_jogada`, `_aplicar_habilidade_identidade`, `_resolve_round`, `_remover_unidade`; famílias e aliases | Não havia ligação semântica de cada família ao branch/hook e evidência por linha | Mapeia 59 aliases (56 branches diretos, 2 hooks, 1 sem handler), 22/22 identidades, quatro campos não vinculados e divergências; prioridade heurística 18 HIGH/6 MEDIUM/30 LOW | Evitar que nome/descrição sejam confundidos com equivalência de comportamento | Auditoria somente leitura; não modifica runtime | Relatório reproduzido e 11/11 testes semânticos |
| `docs/scripts/test-effect-semantic-audit-v0.1.py` | 11 testes | Nenhuma regressão para o mapa AST | Verifica cobertura, branches, aliases arquivados, quatro campos, `gloria`/`sobrevivente`, precondição de sequência, níveis de revisão consistentes e hashes de fonte | Detectar deriva do relatório em relação ao código | Ferramenta de teste apenas | 11/11 aprovados |
| `docs/scripts/summarize-effect-catalog-candidate-v0.1.py`, `docs/card-game-effect-catalog-validation-v0.1.md/.json` | Agregador estrutural + semântico | Relatório apenas rodava 21 testes de estrutura | Agora executa 23 testes estruturais, gera a auditoria AST e executa 11 testes semânticos; registra contagens, prioridade de revisão e hashes | Impedir que o handoff exiba resultado parcial/obsoleto | Documentação e tooling somente | Todos os checks passaram |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `data/card_game/README.md`, `docs/PACOTE-MANIFESTO.md` | Entrada do chat, arquitetura, dados e manifesto | Estado e evidência semântica não estavam refletidos em todos os pontos de entrada | Atualiza ordem de leitura, contagens 23/23 + 11/11, riscos 18/6/30, precondição de sequência e distinção de ciclo de vida | Garantir contexto uniforme no próximo chat | Documentação somente | Revisão cruzada com JSONs e scripts |
| `data/card_game/effect-registry-candidate.v1.json` | `effects`, `combos` | Não existia candidato consolidado | 54 famílias parametrizadas e 27 combos com mínimo/prioridade | Criar fonte candidata de metadados de efeito | Ainda não consumido pelo jogo | Draft 2020-12 e `validate_effect_registry()` aprovados |
| `data/card_game/legacy-effect-aliases-v0.1.json` | aliases, overrides, ramos arquivados | Dados dispersos em catálogo, mapas por ID e hooks | Preserva 59 IDs, 22 identidades, supressões genéricas, textos originais, cartas atribuídas, `gloria`/`sobrevivente`, 18 V18, seis V75, quatro IDs de campo e cinco órfãos de tags | Evitar perda de dados e tornar explícita a origem da migração | Sem impacto no motor; ponte para auditoria/reconstrução | IDs/params cruzados contra código e testes |
| `data/card_game/leader-registry-candidate.v1.json`, `faction-passives-candidate.v1.json` | catálogos separados | Líderes/passivas no módulo do motor | 10 líderes e quatro passivas em registros separados | Não misturar slot de líder com efeito da unidade ou passiva global com pureza | Estrutural; ainda não ligado ao deck/runtime novo | 10/10 líderes, 4/4 facções |
| `docs/card-game-effect-catalog-decision-v0.1.md/.json` | relatório e decisões | Inventário apenas por camada, sem agrupamento parametrizado completo | Lista 54 famílias, 59 atribuições, 16 supressões, combos e ramos antigos | Dar base técnica à revisão de keep/merge/redesign/remove | Documentação de decisão; candidata, não aprovada | Gerada pelo builder e revisada |
| `docs/scripts/test-effect-catalog-candidate-v0.1.py` | 23 testes | Sem regressões do novo mapa | Testa schema, params, atribuições, identidades, decisões, combos, líderes, passivas e a não equivalência `gloria`/`sobrevivente` | Detectar falhas de extração antes de rever semântica | Ferramenta de teste apenas | 23/23 aprovados |
| `docs/scripts/summarize-effect-catalog-candidate-v0.1.py`, `docs/card-game-effect-catalog-validation-v0.1.md/.json` | relatório de validação | Sem resumo reproduzível | Executa testes, calcula contagens e hashes SHA-256 | Registrar evidência e limites no handoff | Ferramenta/docs apenas | Todos os checks passaram |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `data/card_game/README.md`, `docs/PACOTE-MANIFESTO.md` | estado, ordem de leitura, mapa, inventário | A etapa atual ainda dizia que o registry estava por consolidar | Atualizados para candidato v0.1, com limites, arquivos e próximo passo sem fingir aprovação | Continuidade autossuficiente | Documentação apenas | Revisão cruzada, testes e ZIP conferidos |

---

## Histórico anterior — contrato canônico v1.1 e validação do registry (2026-11-27)

**Status:** a fundação estrutural v1 foi reforçada para v1.1. Além do schema da carta, existe schema do registry de efeitos/combos; o validador verifica os parâmetros efetivamente usados por cada carta e rejeita parâmetros ausentes, fora de faixa, de tipo incorreto ou não declarados. Combos do novo registry precisam de dois participantes distintos e prioridades positivas únicas. Isso continua isolado do runtime legado; não existe ainda um catálogo autoral novo.

- **35/35 testes** `unittest`, incluindo CLI válido/inválido e validação de parâmetros.
- Os dois JSON Schemas Draft 2020-12 passaram `check_schema`; os exemplos de carta e registry foram aprovados.
- CLI passou com catálogo sintético de quatro modelos e 75% unidades puras; rejeitou o fixture negativo com `ally_bonus` fora do máximo.
- Snapshot legado reproduzido duas vezes; SHA-256 continua `df383e6aa10634cf4a0c5d00594e2cbc9f1edb071c95da2ce3119096375297c2`.
- Os hashes de `sistemas/cartas.py`, `sistemas/gwent.py`, `bot.py`, `database.py` e `site/app.js` continuam idênticos ao baseline. Nenhuma regra funcional do jogo foi alterada nesta etapa.

Leia `docs/card-game-contract-validation-v1.1.md/.json` para os comandos e limites. A fórmula EFP/custo/raridade e teto de deck permanecem não aprovados; o contrato estrutural não inventa esses números.


## Registro da implementação estrutural inicial v1 (histórico, ampliado pela v1.1)

**Status na primeira entrega:** o contrato canônico estrutural, JSON Schema da carta, snapshot do catálogo legado e validador inicial foram adicionados. A v1.1, documentada acima, agora também cobre o schema do registry e a validação de parâmetros. O catálogo novo ainda não foi ligado ao runtime: `sistemas/cartas.py`, `sistemas/gwent.py`, `bot.py`, `database.py`, `site/app.js` e renderizadores permanecem como baseline funcional, exceto pela presença do módulo isolado `sistemas/card_contract.py`.

## Resultado da implementação inicial v1

- Snapshot reprodutível: `data/card_game/catalog-legacy-baseline-v0.1.json` contém 137 modelos atuais e os registries legados de 59 efeitos genéricos, 22 identidades ativas, 27 combos, dez líderes e quatro passivas de facção.
- Tipos reclassificados para a nova arquitetura: 110 unidades, 21 especiais táticas e seis relíquias. Relíquias ocupam slot separado; não fazem parte das 12 cartas normais.
- Pureza estrita do baseline: 15 de 137 modelos (10,95%). A quota mínima confirmada é `ceil(30% × 137) = 42` unidades puras. Faltam pelo menos 27 modelos puros no denominador atual, antes de expansão/revisão.
- Alertas preservados: 19 custos legados divergentes da tabela por raridade; seis cartas `luterano_*` com facção a revisar; 43 registros atingidos pela transformação V18; 67 cartas com tags de combo.
- Novo contrato: `data/card_game/card-definition.schema.v1.json`, `sistemas/card_contract.py`, exemplo de definição e registry; regras estruturais cobrem ID estável, facção, tipo, fileira, poder, efeito único, parâmetros, tags, lore, versão de arte e quota de pureza.
- Testes da primeira iteração: **25/25** testes unitários passaram; a revisão v1.1 ampliou a suíte para 35/35, conforme o estado mais recente no topo deste handoff. O baseline foi gerado duas vezes com SHA-256 idêntico (`df383e6aa10634cf4a0c5d00594e2cbc9f1edb071c95da2ce3119096375297c2`).

## Decisões estruturais desta versão

1. Unidade tem `power_base` inteiro de 1 a 15. Especial tática e relíquia não são corpos de combate: têm `row=null` e `power_base=null`, nunca `0`.
2. `kind` distingue `unit`, `special` e `relic`; o slot do deck distingue cartas normais de relíquias equipadas.
3. A carta aponta para no máximo um `effect_id` individual. Efeitos por identidade serão migrados para o mesmo registry, não poderão continuar escondidos em associação paralela por `card_id`.
4. Combos ficam em registry próprio; `combo_tags` são links explícitos e tornam a unidade não pura.
5. Carta pura: `effect_id=null`, `effect_params={}` e `combo_tags=[]`. Passiva global de facção não elimina pureza.
6. Custo e raridade serão derivados por compilador a partir de poder/efeito e regras versionadas; não se gravam valores escolhidos manualmente no manifesto autoral. As fórmulas, EFP, faixas de raridade, teto de deck e leader load continuam sem aprovação.
7. Lore é narrativa apenas. Texto de regra vem do registry de efeito/parâmetros e não de `descricao`.

A interpretação de 30% usa todos os 137 modelos jogáveis como denominador, incluindo especiais e relíquias (que não podem ser puras). O alvo exato para esse baseline é 42. A meta opcional de 35% sugerida na proposta anterior não está aprovada.

## Arquivos adicionados nesta etapa

- `sistemas/card_contract.py` — validador independente do motor antigo, incluindo registry de efeitos/combos e parâmetros; não é importado pelo runtime atual.
- `data/card_game/card-definition.schema.v1.json` — schema JSON para definições autorais.
- `data/card_game/effect-registry.schema.v1.json` — schema do registry de efeitos e combos.
- `data/card_game/card-definition.example.v1.json` — exemplo ilustrativo, não uma carta aprovada.
- `data/card_game/effect-registry.example.v1.json` — exemplo ilustrativo do registry, não catálogo aprovado.
- `data/card_game/catalog-legacy-baseline-v0.1.json` — snapshot de 137 modelos, links legados e registry antigo; não usar como runtime novo.
- `data/card_game/README.md` — descrição dos dados.
- `docs/card-game-canonical-model-v1.md` — contrato, semântica e decisões estruturais.
- `docs/card-game-legacy-baseline-v0.1.md` — inventário e alertas do baseline.
- `docs/scripts/build-card-catalog-baseline-v0.1.py` — gerador reprodutível do snapshot.
- `docs/scripts/test-card-contract-v1.py` — 35 testes `unittest` sem dependências externas.
- `docs/scripts/validate-card-catalog-v1.py` — CLI valida registry, parâmetros e catálogo sintético/autoral.
- `docs/scripts/validate-card-json-schemas-v1.1.py` — valida os dois schemas e exemplos; `jsonschema` é ferramenta opcional de desenvolvimento.
- `docs/card-game-contract-validation-v1.1.md/.json` — relatório reproduzível desta etapa.

## Pendências da reconstrução

- Não existe ainda `catalog-v1.json` com as 137 cartas reconstruídas; os nomes, lore, facções, poderes e efeitos permanecem os legados.
- Ainda precisamos normalizar os 59 IDs genéricos, 22 identidades, efeitos de ciclo de vida, 27 combos, dez líderes e seis efeitos de relíquia num registry com parâmetros e handlers únicos.
- `sobrevivente`, `gloria`, `legado`, `devoto`, `sinergia_faccao` e ramos antigos precisam de decisão `keep/merge/redesign/remove`; snapshot preserva o estado sem declarar que todos são válidos.
- Custo, EFP, raridade, teto de deck e custo de líder precisam de calibração/simulação e aprovação antes de entrar no runtime.
- A nova quota de 42 cartas puras ainda não foi aplicada; o baseline atual tem 15.
- A camada `card_contract.py` ainda não está integrada a `cartas.py`, motor, APIs, deck builder, banco nem renderização.

## Próximo passo autorizado

Construir a matriz de consolidação do registry de efeitos: para cada mecânica antiga, ligar ID de catálogo → handler real → timing/condição/alvos/duração → parâmetros → teste comportamental → texto proposto → decisão `keep/merge/redesign/remove`. Não remover os ramos ainda. Depois disso, calibrar os parâmetros EFP e custo, simular facções e produzir o catálogo autoral final com nomes/lore/pureza. Só então integrar o manifesto ao runtime e remover a fonte antiga.

## Histórico desta etapa — arquivo/função/campo/motivo/impacto/validação

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `sistemas/card_contract.py` | `validate_card_definition()`, `validate_catalog()`, `validate_effect_registry()`, `_validate_effect_params()`, `is_pure_unit()`, `minimum_pure_cards()` | Amplia contrato para validar registry, parâmetros obrigatórios/tipados/limitados e combos com mínimo de dois participantes e prioridades únicas | Impedir efeitos com payload incoerente e metadados de combo incompatíveis com a política aprovada | Continua isolado; sem impacto no runtime antigo | 35/35 testes, incluindo CLI e parâmetros negativos |
| `data/card_game/card-definition.schema.v1.json` | JSON Schema da carta | Formaliza campos e condicionais por `kind` | Compartilhar o contrato com tooling externo e outros agentes | Estrutural; não calcula EFP/custo/raridade | Draft 2020-12 válido; exemplo válido |
| `data/card_game/effect-registry.schema.v1.json` | Novo JSON Schema do registry | Define efeitos, parâmetros, obrigatórios, handlers, timing e combos | Garantir forma consistente dos registries | Estrutural; unicidade e validações cruzadas são reforçadas pelo Python | Draft 2020-12 válido; exemplo válido |
| `data/card_game/card-definition.example.v1.json` | Exemplo | Demonstra unidade com `effect_id`, parâmetros e tags | Tornar o contrato concreto | Exemplo, não carta aprovada | Schema Draft 2020-12 válido |
| `data/card_game/effect-registry.example.v1.json` | Exemplo revisado | Inclui `required_parameters` e `allow_additional_parameters` | Demonstrar validação de payload fechado | Exemplo, não registry oficial | Schema e validador Python aprovados |
| `docs/card-game-contract-validation-v1.1.md/.json` | Novo relatório | Registra 35 testes, schemas, CLI, hashes e limites | Manter evidência para handoff | Documentação apenas | Dados reproduzidos em execução local |
| `data/card_game/catalog-legacy-baseline-v0.1.json` | Novo snapshot | Captura 137 cartas, campos antigos, identidade, tags, origem, alerta de facção, custos, lore bruta e registries | Não perder informação antes da reconstrução | Fonte de auditoria/migração; explicitamente proibido importar no runtime novo | 137 IDs, 110 unidades, 21 especiais, seis relíquias; duas gerações com SHA-256 idêntico |
| `docs/scripts/build-card-catalog-baseline-v0.1.py` | Novo gerador | Importa dados em runtime e gera o snapshot de forma determinística com hashes das fontes | Reproduzir baseline | Somente documentação/dados | Saída idêntica em duas execuções |
| `docs/scripts/test-card-contract-v1.py` | 35 casos `unittest` | Valida poder 1/15, pureza, quota, IDs, registry, parâmetros, prioridades, CLI válido/inválido e referências | Travar invariantes estruturais e contratos de efeito | Harness local, sem mudança de jogo | 35/35 aprovados |
| `docs/scripts/validate-card-catalog-v1.py` | CLI | Valida primeiro registry, depois parâmetros e catálogo | Evitar que catálogo autoral referencie efeito com params inválidos | Ferramenta local, sem alteração de dados | Fixture de 4 cartas aceito; parâmetro fora de faixa rejeitado |
| `docs/scripts/validate-card-json-schemas-v1.1.py` | Novo validador opcional | Executa Draft 2020-12 contra ambos os schemas/exemplos | Tornar a validação compartilhável | Usa pacote opcional `jsonschema`, não runtime | Dois schemas e exemplos aprovados |
| `docs/scripts/validate-card-catalog-v1.py` | Novo CLI | Valida manifesto e referências ao registry | Permitir validação repetível do novo catálogo | Ferramenta local; não altera arquivos | `py_compile`; execução sintética documentada |
| `docs/card-game-canonical-model-v1.md`, `docs/card-game-legacy-baseline-v0.1.md`, `data/card_game/README.md` | Novos documentos | Definem contrato, semântica, baseline e limites | Handoff autossuficiente | Documentação apenas | Revisão cruzada |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md`, `docs/PROJECT-OPERATING-CONTEXT.md`, `docs/card-game-balance-spec-v0.1.md` | Estado, ordem de leitura, manifesto, contexto e proposta de balanceamento | Atualizam estado, distinguem requisitos confirmados de propostas e registram próximos passos | Permitir novo chat assumir com contexto correto | Documentação apenas | Conferência dos links/contagens e integridade do pacote |

---

## Atualização operacional mais recente — jogo ainda em fase de teste (2026-11-27)

**Informação declarada pelo proprietário:** o jogo ainda não tem jogadores reais; quaisquer contas/registros existentes são testes realizados pelo próprio proprietário. A declaração não foi verificada no banco, hospedagem, Discord ou R2, porque esses ambientes não vieram no pacote. Consulte `PROJECT-OPERATING-CONTEXT.md` para as consequências e os limites.

**Impacto na estratégia:** não precisamos preservar coleções, rankings, decks, recompensas ou progresso de uma base de jogadores. A reconstrução pode favorecer schema limpo, seed controlado e reset/reseed de dados de teste, sem criar migrações complexas para suportar usuários inexistentes. O runbook SQLite/R2 preparado na seção seguinte é opcional, não uma dependência para continuar o motor e o novo catálogo. Executá-lo apenas quando for importante recuperar/reutilizar artes aprovadas, submissões ou registros específicos. Não apagar automaticamente o R2, anexos Discord ou arte aprovada; isso pode representar trabalho do proprietário. Segredos e credenciais continuam fora do ZIP e do chat.

**Próximo passo técnico recomendado:** retomar a validação integrada de APIs/deck/partidas e definir o schema canônico; depois decidir se o banco de teste será recriado do zero. Antes de qualquer reset no host, identificar o caminho ativo do banco e delimitar precisamente o que será apagado.

### Histórico desta revisão — contexto operacional

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/PROJECT-OPERATING-CONTEXT.md` | Novo documento | Registra que o proprietário informou não haver jogadores reais; contas/dados existentes são testes; define impacto na estratégia e salvaguardas | Evitar planejar migração complexa ou preservação de progresso de jogadores inexistentes | Permite reconstrução/reseed mais direto; não autoriza apagar arte, credenciais ou ativos sem escopo definido | Informação identificada como declaração do proprietário, não como dado verificado de produção |
| `docs/README-PACOTE-CONTINUIDADE.md` | Aviso de entrada e ordem de leitura | Inclui o contexto operacional e rebaixa o runbook de produção a ferramenta opcional para recuperação de ativos | Orientar chats novos corretamente | Evita bloquear a reconstrução esperando inventário real de produção | Links e ordem conferidos |
| `docs/card-game-handoff.md` | Estado atual e próximos passos | Registra a ausência de jogadores reais e reordena próximos passos para integração/modelo canônico | Ajustar prioridades à realidade do projeto | Documentação somente; nenhum runtime alterado | Revisão cruzada com o documento de contexto |
| `docs/card-game-production-audit-runbook-v0.1.md` | Aviso de escopo | Explicita que o runbook é opcional e destinado à preservação/reutilização de dados e artes | Não tratar inventário de produção como bloqueio obrigatório | Ferramenta continua somente leitura e disponível quando necessária | Revisão documental |
| `docs/PACOTE-MANIFESTO.md` | Estado e contagem do pacote | Atualiza conteúdo, próxima etapa e histórico desta revisão | Manter o pacote autossuficiente | Somente documentação | Contagem e integridade do ZIP verificadas |

---

## Registro anterior — preparação para auditoria de produção somente leitura (2026-11-27)

**STATUS: runbook e quatro utilitários read-only preparados; 7/7 testes locais passaram; nenhuma fonte real foi acessada.** Esta seção registra a etapa em que as ferramentas foram preparadas. A ordem original de executar o runbook foi posteriormente reclassificada: após a informação operacional do proprietário, o inventário é opcional e só deve ser usado para recuperar/preservar ativos. Não interpretar testes de fixture como inventário real.

- Runbook operacional: [`card-game-production-audit-runbook-v0.1.md`](card-game-production-audit-runbook-v0.1.md).
- Snapshot consistente, sem abrir a origem para escrita: `docs/scripts/snapshot-sqlite-readonly-v0.1.py` (SQLite `mode=ro`, `query_only`, `Connection.backup`, `quick_check`).
- Relatório DB agregado e sanitizado: `docs/scripts/audit-production-card-db-v0.1.py` (sem valores de user/reviewer IDs, prompts, razões de rejeição, BLOBs, imagens ou `state_json`; `image_key` só como SHA-256/namespace). Opção `--verify-local-generated-art` verifica existência/hash dos arquivos do Laboratório sem exportar caminhos.
- Inventário R2: `docs/scripts/inventory-r2-readonly-v0.1.py` (apenas `ListObjectsV2`; não chama `GetObject`, `PutObject`, `DeleteObject`, `CopyObject` ou ACL; as chaves são representadas por SHA-256).
- Reconciliação: `docs/scripts/reconcile-production-card-assets-v0.1.py` cruza as chaves DB com o bucket primário e separa cache `cards/`; recusa inventário filtrado/truncado e não apaga objetos.
- Testes: `docs/scripts/test-production-audit-tooling-v0.1.py` — **7/7** em SQLite temporário e cliente S3 simulado, incluindo leitura de linha ainda não checkpointada em WAL sem alterar o arquivo WAL; `py_compile` dos cinco scripts passou. Não houve chamadas de rede nem acesso a produção.

### Quatro pipelines de arte — não confundir

1. `cartas_atelie_submissoes`: submissões completas novas usam `image_key` para o objeto original R2 em `atelier/submissions/<user_id>/<card-hash>/exemplar-<id>/...`; registros antigos podem usar `image_data` BLOB.
2. `cartas_atelie_artes`: fluxo legado de pedido/revisão via Discord; guarda referências `channel_id`/`message_id`/`attachment_id`, não é um objeto R2. A existência efetiva do anexo exige consulta separada ao Discord.
3. `cartas_gwent_lideres_artes`: arte do líder guardada em BLOB no SQLite.
4. `cartas_geradas` + `cartas_geradas_artes`: PNG do Laboratório guardado localmente em `DATA_DIR/cartas_geradas/<owner_id>/<card_id>.png`, com hash de integridade. O inventário pode conferir caminho/hash sem revelar o path.

O prefixo R2 `cards/<card-hash>/<etag>.<ext>` representa variantes de cache/CDN imutáveis; não é um arquivo original do Ateliê e não deve ser marcado como órfão só porque não existe uma linha direta de submissão. `cartas_cache` local é outro nível da mesma cadeia de renderização.

### O que continua indisponível e próximo passo autorizado

O ZIP continua sem banco de produção, `.env` preenchido, credenciais, acesso ao bucket R2, volume `DATA_DIR` ou sessão/canal privado do Discord. Portanto não há números reais de aprovações, BLOBs, chaves ausentes, objetos R2 órfãos candidatos ou arquivos locais ausentes.

**Instrução histórica substituída:** não é necessário executar o runbook como condição para continuar o desenvolvimento. Caso o proprietário decida preservar/reutilizar artes ou registros específicos, executar o procedimento no host e compartilhar apenas `card-game-production-assets-reconciliation.json` e, se necessário, o relatório DB sanitizado. Nunca enviar snapshot SQLite, `.env`, tokens, access keys, imagens, prompts ou chaves de objetos brutas. Não realizar limpeza automática a partir dos contadores.

A integração HTTP real (`aiohttp.TestClient`, `bot.py`, `Database`/`aiosqlite`) permanece pendente, assim como o browser e o ambiente publicado. A execução desses testes continua separada da coleta DB/R2; não foi tentada novamente nesta etapa porque as dependências ainda não foram providenciadas.

### Histórico desta etapa — preparação da auditoria de produção

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/snapshot-sqlite-readonly-v0.1.py` | `create_snapshot()` | Abre a origem com `mode=ro` e `query_only`, executa `quick_check` e backup API para destino novo fora do repo, permissão 0600 | Obter cópia consistente com WAL sem usar `Database.connect()` que aplica schema/migrações | Ferramenta operacional; sem mutação da origem | Fixture temporária; origem com hash inalterado; snapshot quick_check ok |
| `docs/scripts/audit-production-card-db-v0.1.py` | `build_report()` e filtros de tabela/coluna | Exporta contagens/agrupamentos e metadados das quatro pipelines; hash `image_key`; opcionalmente verifica path/hash de arte local sem divulgar caminho | Inventariar DB sem exportar dados pessoais, prompts, BLOBs ou estados privados | Ferramenta operacional; não modifica DB | Fixture sintética; privacidade, agregações e path check validados |
| `docs/scripts/inventory-r2-readonly-v0.1.py` | `_bucket_configs()`, `_client()`, `write_inventory()` | Lista buckets primary e public-cards se distintos com apenas `ListObjectsV2`; grava hash de key e metadados; marca escopo completo/filtrado | Inventariar R2 com privilégio mínimo e sem divulgar chaves | Leitura do bucket apenas quando executado pelo operador; nenhuma operação de escrita | Cliente S3 simulado confirmou somente `list_objects_v2`; JSON e scope validados |
| `docs/scripts/reconcile-production-card-assets-v0.1.py` | `reconcile()` | Compara hashes de `image_key` apenas contra bucket `primary`, classifica pendências e candidatos; recusa R2 parcial | Evitar falso positivo por bucket de CDN separado ou inventário truncado | Relatório somente; sem limpeza | Cenários match/missing/orphan/scope inválido |
| `docs/scripts/test-production-audit-tooling-v0.1.py` | Sete testes `unittest` | Fixture SQLite (journal padrão e WAL) e cliente S3 simulado | Reproduzir operações sem rede/produção e verificar backup com linha ainda no WAL | Harness somente | 7/7 aprovados |
| `docs/card-game-production-audit-runbook-v0.1.md` | Documento novo | Caminhos, permissões, comandos, interpretação e limites | Permitir execução segura pelo operador de produção | Documentação | Comandos cruzados com `config.py`, `database.py`, `bot.py` e `storage_r2.py` |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/card-game-mapping-audit.md`, `docs/CLOUDFLARE_R2.md`, `docs/PACOTE-MANIFESTO.md` | Estado, arquitetura, ordem e histórico | Etapa read-only e ausência de evidência real registradas | Preservar continuidade e separar testes locais de produção | Documentação somente | Revisão cruzada; nenhuma fonte de runtime alterada |

---

# Card Game — Handoff de continuidade

> Documento operacional vivo. Leia primeiro este arquivo e depois o inventário técnico em [`card-game-mapping-audit.md`](card-game-mapping-audit.md).

## Estado anterior — mapa estático dos contratos HTTP Gwent v0.1 (2026-11-27)

**STATUS: mapa das 12 rotas Gwent produzido e reproduzido por AST; execução HTTP real continua pendente.** Esta é a revisão documental mais recente.

- Script: `docs/scripts/audit-gwent-http-contracts-v0.1.py`; relatórios: `docs/card-game-http-contract-map-v0.1.md` e `.json`.
- Foram identificadas 12 rotas: catálogo, imagem privada/pública, deck (GET/POST/reset), lista/criação de partidas, criação solo, resposta a convite, detalhe e ação.
- O mapa registra linha de registro, handler, linhas da função, sinais estáticos de autenticação/origem, campos de body, parâmetros de rota, chamadas de banco/motor e literais de consumo no `site/app.js`. O AST localiza `preparar_carta()`, `aplicar_jogada()`, `novo_estado()` e `executar_turno_ia()` nos handlers correspondentes.
- **Falha relevante para custo:** `POST /api/gwent/deck` valida 12 cartas-modelo únicas, pelo menos 8 unidades, no máximo 4 especiais, facção predominante, líder/facção, relíquia e propriedade de exemplares; não soma custos nem impõe orçamento.
- **Falha de payload:** `/api/gwent/cards` e `/api/gwent/deck` atribuem `payload['custo']` antes de chamar `preparar_carta()`, mas o dicionário de retorno explícito dessa função não inclui `custo`; portanto o campo é descartado no payload preparado.
- O frontend envia cartas como `{card_id, exemplar_id}` e configuração `{faction, leader_id, relic_id}`; ações de partida enviam `action`, `card_id`, `row`, `card_ids` e `target_id`. A ação retorna `{ok: true}` e o frontend refaz GET do detalhe.
- Convites guardam snapshots de deck/config como `pending`; aceite revalida relíquia, embaralha snapshots e chama `novo_estado()`. Solo espelha a configuração do jogador para NARA; a ação pode executar `executar_turno_ia()` no servidor, com fallback `pass` se a IA falhar.
- **Limite obrigatório:** isto é auditoria estática. `discord.py` e `aiosqlite` não estão instalados e a instalação por `pip` foi bloqueada por falha de DNS/rede. Não houve `aiohttp.TestClient`, import/dispatch real de `bot.py`, instância da classe `Database`, browser, convite, solo/IA ou produção. Não interpretar sinais AST como prova de status HTTP ou autorização em runtime.
- O restante do estado validado continua: 251/251 asserts em oito suites e 12/12 cenários stateful (contagens separadas). Política de combos aprovada continua sendo a única alteração funcional aprovada nesta trilha.

### Próximo passo autorizado naquela etapa (reordenado pela auditoria de produção)

Obter ambiente/wheels compatíveis com `requirements.txt` e executar `aiohttp.TestClient` contra as 12 rotas, cobrindo autenticação, origem, ownership, status, transações/rollback, convites, solo/IA, recompensas e refetch. Depois, corrigir o contrato de custo somente quando o schema/custo oficial for aprovado. Não modificar ainda poder, raridade, habilidade, DB, frontend ou imagens.



## Estado imediatamente anterior — integração stateful de partidas v0.1 (2026-11-27) — preservado como referência

**STATUS: 12/12 cenários stateful aprovados.** Esta é a etapa imediatamente anterior ao mapa HTTP estático; fica preservada como evidência de partidas/snapshots. Os oito conjuntos de testes anteriores continuam válidos em seus limites próprios (251/251 asserts); a nova suíte não soma seus 12 cenários aos 251 asserts como se fossem a mesma unidade de contagem.

- Novo script: `docs/scripts/assert-full-match-stateful-v0.1.py`; relatório: `docs/card-game-match-snapshot-integration-v0.1.json`; explicação e limitações: `docs/card-game-match-snapshot-integration-v0.1.md`.
- Quatro partidas completas de três rodadas foram conduzidas pelo motor em memória, cobrindo as quatro facções em pares cruzados, mulligan, turnos, jogadas, passes, encerramento de rodada, coroas e estado final. O estado foi serializado/desserializado por JSON durante os fluxos.
- `preparar_carta()` foi exercitada em todos os 137 modelos do catálogo. Um combo real foi ativado via jogadas normais. Também foram testados líder + carta especial climática + reset de rodada, relíquia de uso único, clima manual de uso único, snapshot legado e rejeição sem mutação do estado de entrada.
- O SQLite em memória executou as constantes `SCHEMA` e `SCHEMA_CARTAS` extraídas de `database.py` e testou insert/select/update da tabela `cartas_gwent_matches` com FK ativada. Isso não usa o wrapper `Database`/`aiosqlite` nem o DB de produção.
- Verificação estática do contrato `bot.py` ↔ `site/app.js` confirmou rotas e campos usados. `compileall` dos módulos-alvo e `node --check site/app.js` passaram.
- **Limite HTTP:** a camada HTTP não foi executada. `bot.py` não pôde ser importado porque `discord.py` não está instalado no ambiente de análise; `database.py` não pôde ser importado porque `aiosqlite` não está instalado. Ambos estão fixados em `requirements.txt`; tentei instalá-los com `pip`, mas a resolução DNS/rede do ambiente bloqueou o acesso ao índice. Não usei stubs. Portanto não houve `aiohttp.TestClient`, execução dos handlers reais, gateway Discord ou transação assíncrona do wrapper.
- As partidas completas usam 12 fixtures unitárias sintéticas por jogador para controlar poder/resultado; não são decks publicados validados pelo deck builder. O teste com cartas reais cobre o combo e a preparação de todos os modelos, não uma partida competitiva com decks reais.
- Runtime funcional não foi alterado nesta etapa. A alteração funcional aprovada permanece exclusivamente a política de combos em `sistemas/gwent.py`.

### Próximo passo autorizado naquela etapa (substituído pelo estado HTTP no início do handoff)

Continuar com integração HTTP real quando `discord.py` e `aiosqlite` estiverem disponíveis: testar criação/aceitação de convite, criação solo/IA, `GET /api/gwent/cards`, detalhe de partida, `POST /action`, autenticação, persistência transacional e recompensas. Em seguida validar no browser as respostas, imagens/R2 e só então avançar para testes de IA e simulação competitiva. Não recalibrar EFP/custo/raridade ainda.

## Estado anterior — política oficial de combos v0.1 (2026-11-27)

**STATUS: aprovada pelo usuário, implementada em runtime e coberta por regressões sintéticas.** Esta seção é a referência de estado mais recente; as seções intituladas v0.1/v0.2 abaixo preservam o histórico do baseline e devem ser lidas como registros históricos quando indicadas.

- Único arquivo funcional alterado nesta etapa: `sistemas/gwent.py` (`SYNERGY_COMBOS` e `_aplicar_combo_de_cartas()`).
- Regras: todos os 27 combos exigem duas instâncias distintas; a carta atual precisa contribuir com tag exigida; há no máximo um combo por jogada; `priority` único e explícito decide precedência (menor primeiro); combos pendentes só podem ser ativados por uma carta posterior que também contribua com tag exigida; o bônus individual vai para essa carta participante; `team_bonus` e reset de `synergy_used` foram preservados.
- Partidas persistidas antes do deploy mantêm bônus já concedidos no `state_json`; não há DB de produção no ZIP para uma migração/encerramento controlado. A política nova rege as jogadas resolvidas pelo processo atualizado.
- Os três combos anteriormente sem `minimum` (`cinzas_fornalha`, `vazio_astral`, `eco_convergente`) agora declaram `minimum: 2`.
- Validação: oito suites, **251/251 asserts**; auditoria pós-política em 4.422 pares e 287.430 trincas, zero ativações solo e todos os 2.582 eventos de combo posteriores examinados com carta que contribui com tag exigida.
- Documentos de autoridade: `card-game-combo-policy-v0.1.md`, `card-game-behavior-validation-v0.3.md/.json` e `card-game-combo-overlap-v0.2.md/.json`.
- Compatibilidade: sem migração de schema/DB; snapshots de partidas ativas mantêm bônus já concedidos pela política antiga. A nova regra se aplica às próximas jogadas resolvidas após atualizar o processo. O DB de produção não foi fornecido.
- EFP, custo, raridade, limite de deck e redistribuição das cartas continuam sem aprovação e sem implementação.

## Verificação dos quatro blocos obrigatórios da Regra 8 (revisão de continuidade)

Esta seção responde se o handoff, **isoladamente**, já satisfaz os quatro blocos pedidos. A resposta correta nesta revisão é: **há cobertura significativa, mas ainda não está 100% autossuficiente nem integralmente fechado**. O pacote completo complementa o handoff com a auditoria, matriz e proposta v0.1; o próximo chat deve ler os documentos na ordem definida em `README-PACOTE-CONTINUIDADE.md`.

| Bloco exigido | Estado | Onde está documentado | Pendências/defasagens conhecidas |
|---|---|---|---|
| 1. Mapa completo do sistema | **Parcialmente coberto no handoff; complementado pela auditoria** | `card-game-mapping-audit.md`, seções 2–3, 11–14 e 23 (contratos HTTP); handoff, seção “Problemas prioritários”. | O mapa lista módulos centrais/auxiliares, APIs principais, fluxo catálogo→DB/API→motor→frontend/imagem e alguns comandos/funções. Ainda não é um inventário de cada evento/handler de Discord, cada função chamada em todos os caminhos auxiliares, todos os comandos operacionais de execução/deploy nem um runbook testado. O DB de produção e configuração publicada não vieram no baseline; schema/runtime de produção não foi validado. |
| 2. Dados e regras oficiais | **Parcial; contrato estrutural v1.1 criado, catálogo novo e números de balanceamento pendentes** | `card-game-canonical-model-v1.md`, schemas de carta/registry e `sistemas/card_contract.py`; `card-game-combo-policy-v0.1.md` para a política de combos; matriz/snapshot para o baseline; `card-game-balance-spec-v0.1.md` como proposta numérica. | Requisitos confirmados incluem poder-base 1–15 para unidades, ≥30% de cartas puras, efeitos deliberados/determinísticos, custo real de deck, raridade derivada e lore/facção coerentes. O contrato v1.1 separa unit/special/relic, valida parâmetros do registry e define efeito único, mas ainda não está ligado ao runtime. Fórmulas EFP/custo/raridade, teto 32, meta 35%, leader_load e faixas numéricas seguem propostas. Faltam decisões carta a carta `keep/merge/redesign/remove`, registry completo, facções das seis cartas `luterano_*` e o novo catálogo. `CARD_GAME_REDESIGN.md` continua defasado e não é autoridade. |
| 3. Histórico detalhado por arquivo/função/campo/motivo/impacto | **Parcial, com histórico desta etapa acrescentado; histórico original do código não veio no ZIP** | Handoff (seções de histórico), `PACOTE-MANIFESTO.md`, `card-game-canonical-model-v1.md` e auditorias. | Além da política de combos em `sistemas/gwent.py`, agora há registro dos novos módulos/schema/snapshot/validador e de seu impacto isolado. O ZIP baseline não fornece histórico Git/commits; não há como reconstruir a história anterior do código. Para cada mudança futura, registrar caminho, função/campo/trecho, antes/depois, motivo, impacto em DB/API/frontend/arte, testes, migração e rollback. |
| 4. Estado exato, dependências e próximos passos | **Majoritariamente coberto; integração operacional pendente** | Este handoff; `card-game-behavior-validation-v0.3.md/.json`; `card-game-match-snapshot-integration-v0.1.md/.json`; `card-game-http-contract-map-v0.1.md/.json`; `card-game-combo-overlap-v0.2.md/.json`; README e manifesto. | Além dos 251/251 asserts em oito suites e da enumeração pós-política, a suíte stateful passou 12/12 cenários: quatro partidas de três rodadas em memória, JSON snapshots, payloads dos 137 modelos, combo por turno, líder/especial/clima, relíquia, legado e SQLite com DDL real extraído de `database.py`. O mapa estático agora cobre as 12 rotas Gwent e detecta o contrato de custo ausente. Faltam dispatch HTTP real, wrapper `Database`/aiosqlite, browser, IA/recompensas no fluxo real, DB/ambiente de produção, R2/artes e runbook de deploy reproduzido. |

### Interpretação obrigatória para um chat novo

- O **pacote ZIP completo** é a unidade de handoff; `card-game-handoff.md` é o índice operacional, não substitui a leitura da auditoria, matriz, especificação e manifesto.
- A existência de uma fórmula no documento v0.1 não significa aprovação. Apenas os requisitos listados em “Decisões já confirmadas pelo usuário” são requisitos confirmados; valores numéricos adicionais continuam como propostas.
- A auditoria descreve o baseline estático do ZIP de origem, não o estado do servidor/DB em produção.
- A política de combos v0.1 foi aprovada pelo usuário e aplicada em `sistemas/gwent.py`. A fundação estrutural do modelo canônico v1 foi criada em `sistemas/card_contract.py` e `data/card_game/`, mas ainda não substitui o catálogo/runtime legado. O redesenho das cartas, integração do registry, EFP/custo/raridade, DB/API/frontend/imagens e limpeza geral estão pendentes.

## Matriz de rastreabilidade carta por carta (etapa concluída)

A matriz foi adicionada em três formatos, todos gerados a partir do catálogo runtime importado do ZIP baseline:

- [`card-game-card-traceability.md`](card-game-card-traceability.md): relatório legível com tabela de todas as 137 cartas e detalhe individual de cada definição.
- [`card-game-card-traceability.csv`](card-game-card-traceability.csv): uma linha por carta para filtragem e comparação.
- [`card-game-card-traceability.json`](card-game-card-traceability.json): dados estruturados para scripts e futuras migrações.

A matriz distingue habilidade genérica, identidade ativa, identidade histórica filtrada, tags/combos, pureza estrita, custo cadastrado, custo tabelado, texto efetivamente preparado e cobertura de aura/emblema.

**Correção técnica da auditoria:** quando uma carta tem `Carta.habilidade` preenchida e entrada ativa em `CARD_IDENTITY_ABILITIES`, `aplicar_jogada()` define `skill = ""` e suprime o efeito genérico antes da resolução. Só a identidade é executada. A inconsistência real está no payload de `preparar_carta()`: `habilidade` continua contendo o ID genérico, enquanto `habilidade_nome` e `habilidade_texto` apresentam a identidade. Não há dupla execução nesses 16 casos; há ambiguidade de contrato. A matriz JSON/CSV marca os 16 registros.

Achados quantitativos adicionais desta matriz:

- 16 cartas têm campo genérico preenchido e identidade ativa; o motor suprime o efeito genérico e executa somente a identidade. O payload ainda mantém o ID genérico em `habilidade`, enquanto nome/texto usam a identidade.
- 9 cartas carregam IDs ausentes de `HABILIDADES`: três `gloria`, executadas em `_resolve_round()` mas sem metadado/texto no catálogo; e seis `legado`, `devoto` ou `sinergia_faccao`, cujos valores no campo genérico não acionam os ramos homônimos porque esses ramos estão no resolvedor de identidade, sem associação ativa correspondente.
- 43 declarações literais de carta são modificadas pela transformação V18 durante o import: a habilidade é apagada e o poder pode aumentar em +1, limitado pelo teto da raridade. A matriz preserva os valores anteriores e runtime.
- 19 cartas divergem entre `Carta.custo` e `CUSTO_RARIDADE[raridade]`.
- A pureza estrita atual é 15/110 unidades (13,64%); 67 cartas têm tags de combo.
- Cinco IDs têm tags de sinergia sem carta correspondente no catálogo: `gwent_unidade_cruzado`, `gwent_unidade_evangelista`, `gwent_unidade_missionario`, `gwent_unidade_protetor`, `gwent_unidade_sacerdote`.

A geração da matriz não alterou código de jogo nem dados persistidos.


## Especificação de balanceamento — proposta v0.1

- [`card-game-balance-spec-v0.1.md`](card-game-balance-spec-v0.1.md): regras confirmadas separadas de propostas numéricas de EFP, poder, custo, budget de deck, raridade, pureza, distribuição e lore por facção. **Não implementar valores propostos antes de simulação e aprovação.**
- [`card-game-deck-cost-sampling-v0.1.json`](card-game-deck-cost-sampling-v0.1.json): resultado histórico/superado; método tinha crédito de combo parcial e não incluía relíquia/líder.
- [`card-game-deck-cost-sampling-v0.2.json`](card-game-deck-cost-sampling-v0.2.json): amostragem corrigida, separada em cenários com/sem relíquia equipada.
- [`scripts/sample-deck-cost-v0.1.py`](scripts/sample-deck-cost-v0.1.py): reprodução histórica/superada; não usar para recomendar teto.
- [`scripts/sample-deck-cost-v0.2.py`](scripts/sample-deck-cost-v0.2.py): script atual da amostragem de custo.
- [`card-game-effect-score-catalog.json`](card-game-effect-score-catalog.json): catálogo estruturado com os metadados atuais e estimativas provisórias para habilidades genéricas, identidades, combos e líderes. `null` indica definição não executável/incompleta, não carta pura.

A fórmula de custo proposta é `ceil((P + 2E)/3,5)` para unidades; raridade proposta `R = 2P + 3E + 0,5(10-C)`. O teto 32 foi uma hipótese preliminar, **não aprovado**. A amostragem v0.1 foi identificada como metodologicamente incompleta (crédito de combo por interseção parcial de tags e ausência de custo de líder/relíquia); consulte `card-game-balance-validation-v0.1.md` e a amostragem v0.2. Os dados revistos aceitam 68,8% dos decks sem relíquia e 45,4% com relíquia equipada no teto 32, sob premissas aleatórias. Isso não demonstra equilíbrio de partidas. Nenhum valor de custo, EFP, teto ou raridade foi implementado.

## Estado do repositório após política de combos — referência histórica (ver estado stateful no início e no fim do handoff)

- Data do baseline: 2026-11-27; pacote de continuidade recebido: `soulsbo-main-handoff.zip`.
- Código-base original: `soulsbo-main(1).zip`, SHA-256 documentado no manifesto anterior.
- **Uma alteração funcional foi aplicada:** `sistemas/gwent.py`, catálogo `SYNERGY_COMBOS` e `_aplicar_combo_de_cartas()`. Os demais endpoints, schema, frontend, arte e dados persistidos não foram modificados.
- Documentação adicionada/atualizada: regra oficial dos combos v0.1, suite de 32 regressões, auditoria pós-política v0.2, mapa AST pós-política v0.2 e relatório agregado v0.3.
- Validação daquela etapa: oito suites, 251/251 asserts; auditoria enumerativa pós-correção em 4.422 pares e 287.430 trincas. A validação stateful posterior está no bloco inicial e em ‘Estado exato ao encerrar esta entrega — integração stateful v0.1’.
- O DB de produção não veio no ZIP. O inventário não atesta dados de produção nem permite limpar bônus antigos de partidas ativas.

## Decisões já confirmadas pelo usuário

### Requisitos de produto confirmados

1. Poder-base das unidades estritamente entre 1 e 15.
2. Distribuição de efeitos intencional, não aleatória.
3. Pelo menos 30% dos modelos de carta do jogo devem ser puros, sem habilidade/efeito individual.
4. Deve existir custo por carta aplicado como limite na montagem de decks.
5. Raridade deve decorrer matematicamente de poder-base, força do efeito e custo; maior poder/efeito e menor custo devem elevar raridade.
6. Nomes, títulos, lore e facção devem ser coerentes com Elden Ring/Dark Souls e com a identidade da facção.
7. O pacote ZIP mestre e os documentos de handoff devem ser atualizados a cada etapa.
8. O proprietário informou que não há jogadores reais ativos; contas/dados existentes são testes. Isso permite reset/reseed de dados de jogo após delimitar o escopo, mas não é autorização para apagar artes/segredos/ativos automaticamente.
9. A regra de combos com prioridade explícita, duas instâncias distintas e participação da carta que recebe bônus foi aprovada e implementada.

### Decisões estruturais de engenharia adotadas para o contrato v1

- `kind` separa unidade, especial tática e relíquia; relíquia ocupa slot próprio e não uma das 12 cartas normais.
- Unidade usa `power_base` 1–15; especial/relíquia não combatente usa `power_base=null` e `row=null` (em vez de usar 0).
- Uma carta tem no máximo um `effect_id` individual canônico; as identidades antigas serão migradas ao mesmo registry. Combos continuam em registry separado.
- Pureza estrita exige `effect_id=null`, `effect_params={}` e `combo_tags=[]`; passiva global de facção não retira pureza.
- Custo e raridade são campos derivados pelo compilador depois de aprovadas as regras quantitativas; a fórmula não é decidida por este contrato.

1. Fazer limpeza de versões antigas, mas somente depois de mapear o comportamento atual.
2. Poder-base futuro estritamente entre 1 e 15.
3. Distribuição de efeitos não aleatória.
4. Pelo menos 30% do jogo deve ser composto por cartas puras, sem habilidade/efeito.
5. Implementar custo como regra efetiva para limitar deck.
6. Raridade deve derivar do equilíbrio entre poder-base, efeito e custo, não de escolha arbitrária.
7. Refazer nomes e lore no universo Elden Ring / Dark Souls, mantendo coerência de facção.
8. Manter handoff autossuficiente com mapa técnico, regras, histórico e próximos passos.
9. Política de combos aprovada: duas instâncias distintas de unidade participantes; carta atual contribui com tag requerida; um combo por jogada; prioridade explícita (menor número primeiro); combo pendente só é ativado por participante posterior; bônus individual vai à carta participante que ativa, com bônus de equipe existente preservado.

## Evidências quantitativas do baseline

- 137 modelos: 110 unidades e 27 especiais.
- 59 definições em `HABILIDADES`.
- 22 identidades ativas; 40 antes do filtro (18 filtradas).
- 72 associações de tag; 5 IDs órfãos.
- 27 combos; 10 líderes; 6 relíquias.
- 15 unidades puras estritas (13,64% das unidades; 10,95% do catálogo total).
- 19 modelos com custo cadastrado diferente do custo tabelado pela raridade.
- Deck atual: 12 cartas diferentes, mínimo 8 unidades e máximo 4 especiais; sem orçamento de custo.

Os detalhes e listas completas são mantidos no inventário ligado acima. Não confiar em uma contagem resumida sem consultar as tabelas do inventário.

## Problemas prioritários ainda abertos

1. Duas rotas fornecem descrição de habilidade diferente: `/api/gwent/cards` usa `preparar_carta()`; `/api/gwent/catalogo-cartas` usa `Carta.para_dict()` + `HABILIDADES`, sem consultar identidades ativas.
2. `sobrevivente` está no catálogo e na aura visual, mas não tem resolução no motor.
3. `legado`, `devoto`, `sinergia_faccao` e `escolha_ritmo` têm ramos nominais no resolver de identidade, mas não uma associação ativa por ID; cartas que possuem esses valores no campo genérico não disparam os ramos.
4. `espolios` está implementado no fechamento de rodada, mas não está atribuído a carta atual.
5. Identidades genéricas de cartas ativas são suprimidas por ID; o campo `habilidade` ainda contém um valor diferente que pode confundir consumidores.
6. Tags de combo incluem cinco card IDs ausentes do catálogo.
7. O campo de facção das seis cartas `luterano_*` da seção dos Esquecidos conflita com o comentário/grupo de tags; validar intenção antes de ajustar.
8. Custo não é aplicado como orçamento no deck. Há 19 divergências entre `Carta.custo` e `CUSTO_RARIDADE`; `preparar_carta()` não devolve `custo`.
9. A geração procedural usa `rng.random()`/`rng.choice()` para decidir se uma carta terá habilidade; monitoramento 50/50 só mede, não força uma regra de distribuição.
10. Arte oficial integral antiga não é reescrita; imagem é devolvida como composição completa sem texto dinâmico sobreposto.
11. A aura usa `card['habilidade']`, não o effect ID de identidade; cobertura visual parcial.
12. **RESOLVIDO:** o resolver de combos agora usa prioridades explícitas, exige contribuição da carta atual com tag do combo, exige duas instâncias participantes e bloqueia ativação solo. Ver `card-game-combo-policy-v0.1.md` e auditoria pós-correção `card-game-combo-overlap-v0.2.md`.
13. `docs/CARD_GAME_REDESIGN.md` descreve mecânicas que não são as do motor atual; deve ser reconciliado, não usado como autoridade sem revisão.

## Ordem recomendada para continuar

### Fase A — auditoria e matriz (concluída)

1. [x] Ler e mapear `card-game-mapping-audit.md`.
2. [x] Construir a matriz canônica de referência para os 137 modelos, com dados, habilidades, identidades, tags, combos, texto e arte.
3. [x] Documentar a definição proposta de carta pura: unidade sem habilidade individual, identidade, tag de combo ativo ou trigger próprio; passiva global de facção separada.
4. [x] Fixar como proposta o denominador de todos os modelos: 137 no baseline, exigindo 42 puras; confirmar/rever antes da implementação.
5. [x] Criar escala EFP e catálogo estruturado de habilidades, identidades, combos e líderes; estimativas ainda não validadas.

### Fase B — especificação quantitativa v0.1 (rascunho concluído; aprovação pendente)

6. [x] Propor poder 1–15 para unidades e `power_base=null` para especiais; confirmar a interpretação de especiais antes de migrar.
7. [x] Propor função de custo `ceil((P + 2E)/3,5)` para unidades e `ceil((2E)/3,5)` para especiais.
8. [x] Registrar teto experimental inicial de 32 com custo da relíquia e carga do líder como hipóteses; a validação v0.2 mostrou resultados distintos com/sem relíquia e não sustenta nem aprova esse teto.
9. [x] Propor raridade `R = 2P + 3E + 0,5(10-C)` com faixas Comum a Singular.
10. [x] Definir política proposta de distribuição por manifesto determinístico e meta mínima de 30% de cartas puras.

**Atenção:** `[x]` nesta fase significa que há uma proposta escrita, não que o usuário aprovou os números. Nenhum dos parâmetros de custo, EFP ou raridade foi implementado no motor.

### Fase C — reconstrução e migração

11. [x parcial] Criar o contrato estrutural v1, JSON Schema, validador e snapshot baseline; falta escrever o catálogo novo e conectá-lo ao runtime.
12. Refatorar motor para resolver por `effect_id` canônico; evitar lógica de identidade por ID separada de habilidade declarada. Se efeitos de assinatura forem mantidos, devem estar declarados na carta como efeito canônico explícito.
13. Corrigir facções, tags, combos e referências órfãs.
14. Unificar payload de carta para API de coleção, deck, catálogo público e arte.
15. Preparar migração compatível para exemplares e decks existentes; manter IDs estáveis ou produzir mapeamento antigo→novo.
16. Definir versão de schema/definição no snapshot de partida para que jogos já iniciados não mudem silenciosamente.
17. Definir política de imagem: invalidar cache, versionar arte oficial ou reaprová-la após alteração em nome/poder/raridade/efeito/lore.

### Fase D — validação e limpeza

18. Testar todas as habilidades individualmente com estados iniciais e resultados esperados.
19. Testar combos, passivas de facção, líderes, relíquias, clima, rodada, descarte e IA.
20. Testar invariantes: poder 1–15, percentual puro mínimo, custo total, raridade calculada, descrição = execução, arte = definição.
21. Só depois remover funções/atributos antigos e atualizar os docs antigos.
22. Registrar cada alteração por arquivo, linha/função/campo, antes/depois, motivo, impacto, testes e risco de migração.

## Validação exploratória do balanceamento v0.1 (concluída; sem aprovação)

A validação está consolidada em [`card-game-balance-validation-v0.1.md`](card-game-balance-validation-v0.1.md). A proposta v0.1 continua não aprovada e não implementada.

- A amostragem de custo v0.1 é histórica/superada: concedia EFP parcial se qualquer tag de combo coincidisse e não incluía líder nem relíquia. Não usar seus 56,3% de aceitação em 32 como justificativa.
- A amostragem v0.2 é reproduzível (100.000 decks por cenário, seed 42), sem combo parcial: 128 modelos pontuáveis, 9 excluídos. Teto 32 aceita 68,8% sem relíquia e 45,4% com relíquia; `leader_load` e inclusão de relíquia continuam sendo hipóteses de design.
- Simulação de combos: 100.000 decks, 57,19% com ao menos um combo, média de 0,956 combo ativado na mão de 10 assumida jogada na mesma rodada. Glória Divina atinge 15,87%; Eco das Pedras Cintilantes 9,31%. Frequência não equivale a valor de pontuação/partida.
- Auditoria de handlers: 59 habilidades genéricas; 56 referências diretas em `aplicar_jogada()`, dois hooks de ciclo de vida (`vinganca`, `espolios`) e `sobrevivente` sem handler encontrado. `gloria` é um hook oculto fora de `HABILIDADES`. Há 22 identidades ativas, todas com ramo, e 28 ramificações antigas sem mapeamento ativo.
- Testes de fumaça: 56 habilidades com ação direta concluída sem exceção; três IDs do catálogo com hooks de ciclo de vida testados separadamente (`vinganca`, `espolios`, `sobrevivente`); mais o hook oculto `gloria`; 22/22 identidades emitiram evento de ativação. Isso não equivale a cobertura de todos os ramos nem a teste competitivo.
- `CARD_SYNERGY_TAGS` mantém cinco IDs órfãos; todos os 27 combos têm provedor para cada tag exigida. A amostragem de ativação respeita a resolução real, mas assume ordem aleatória e todas as 10 cartas iniciais jogadas.

**Próximo passo autorizado após a política de combos:** ampliar os testes para sequências stateful de 12 cartas e pares sobrepostos adicionais; testar snapshots serializados e payload de `/api/gwent/cards`; decidir como tratar partidas ativas que conservam bônus legados; cobrir clima, transições, IA e interações cruzadas; revisar as 28 ramificações antigas e hooks `gloria`/`sobrevivente` sem removê-los antes de decisão. Depois construir simulador determinístico de partidas por facção. Não escolher nem implementar teto 32, pesos EFP ou raridade sem simulação e aprovação.

## Decomposição de efeitos e metodologia EFP v0.2 (proposta; sem aprovação)

A etapa seguinte à amostragem v0.1 produziu dois artefatos que ligam o catálogo à implementação real e retiram a pontuação agregada de uma posição de falsa precisão:

- `card-game-effect-source-map-v0.1.json` e `scripts/build-effect-source-map-v0.1.py`: mapa AST histórico congelado; o gerador v0.1 recusa sobrescrever o artefato no runtime atual. Para o código vigente, usar v0.2.
- [`card-game-effect-source-map-v0.2.json`](card-game-effect-source-map-v0.2.json) e [`scripts/build-effect-source-map-v0.2.py`](scripts/build-effect-source-map-v0.2.py): mapa AST regenerado a partir do runtime pós-política.
- [`card-game-efp-methodology-v0.2.md`](card-game-efp-methodology-v0.2.md): metodologia proposta para registrar componentes imediatos/atrasados, alvos, caps, precondições, bloqueios, duração, testes e valor esperado em partidas.

**Cobertura por referência no baseline:** 59 habilidades genéricas: 56 handlers de jogada, dois hooks de ciclo de vida (`vinganca`, `espolios`) e uma sem handler identificado (`sobrevivente`). `gloria` é um hook oculto em `_resolve_round()`, fora do catálogo `HABILIDADES`. As 22 identidades ativas e dez líderes possuem referências de execução. Os 27 combos são declarativos e compartilham `_aplicar_combo_de_cartas()`.

O mapa AST prova apenas onde o código menciona os IDs; não prova alcançabilidade em produção nem correção funcional. O smoke test v0.1 também não cobre todas as condições/branches. EFP v0.1 continua não aprovado: valores fixos para buff, remoção, compra, escudo etc. não estão calibrados por estado e frequência real. A metodologia v0.2 propõe medir um vetor de consequências e valor esperado por política/facção; até testes e simulações serem concluídos, manter `null`/intervalos não aprovados e não recalcular custo ou raridade em produção.

**Estado atualizado pós-política e pós-snapshot:** a validação de comportamento isolado continua em `card-game-behavior-validation-v0.3.md/.json`, com oito suites e 251/251 asserts; a validação stateful atual está em `card-game-match-snapshot-integration-v0.1.md/.json`, com 12/12 cenários. A auditoria atual de combos é `card-game-combo-overlap-v0.2.md/.json`: 4.422 pares, 287.430 trincas, zero ativações solo e 2.582/2.582 eventos posteriores com contribuição de tag exigida. A política foi aprovada e implementada; a seção abaixo com 219 asserts e a auditoria v0.1 são registros históricos pré-patch. Ainda faltam dispatch HTTP real, `Database`/aiosqlite, browser, IA e recompensas de partida, produção, R2/artes e decisão operacional sobre partidas ativas.

## Registro histórico pré-política: validação comportamental v0.2 — 219/219 asserts

> **Histórico pré-patch:** esta seção descreve a etapa anterior à aprovação e implementação da política de combos. O resultado atual é oito suites/251 asserts em `card-game-behavior-validation-v0.3.md`.

A expansão de testes desta etapa está consolidada em [`card-game-behavior-validation-v0.2.md`](card-game-behavior-validation-v0.2.md) e [`card-game-behavior-validation-v0.2.json`](card-game-behavior-validation-v0.2.json). O runner `scripts/summarize-card-game-behavior-v0.2.py` verifica os sete relatórios individuais e agrega suas contagens. Resultado repetido nesta revisão: **219 asserts, 219 aprovados, zero falhas**.

As sete suites são: 13 efeitos representativos iniciais; 33 cenários de identidade (22 positivos para as identidades ativas + 11 negativos/limite); 39 cenários de habilidades genéricas de unidade; sete de ciclo de vida; 18 de especiais/relíquias; 22 de líderes (dez handlers positivos + 12 negativos/limite); e 87 de combos/passiva (27 ativações positivas, 27 requisitos incompletos, 27 bloqueios de repetição do mesmo combo, um teste sem tags, quatro passivas de facção e um especial que não consome a passiva). As contagens são asserções e cenários, não 219 efeitos diferentes.

Os dez líderes verificados são Godfrey, Morgott, Radagon, Mohg, Rykard, Esgar, Papa Esquecido, Rennala, Astel e Loretta. Os testes chamam o `aplicar_jogada()` real com `action="leader"`, mas usam estados sintéticos em memória. Não validam integração HTTP, DB, frontend, Discord, R2, estados persistidos ou força competitiva.

A classificação de código legado foi detalhada em `card-game-stale-identity-disposition-v0.1.md/.json`: 28 ramos sem associação ativa = 18 identidades filtradas pelo V18 + quatro efeitos legados em campos sem dispatch ativo (`devoto`, `legado`, `escolha_ritmo`, `sinergia_faccao`) + seis ramos V75 antigos. A contagem não inclui os problemas separados de `gloria` (hook oculto em `_resolve_round()`, presente em três cartas) e `sobrevivente` (declarado sem handler localizado). **Nenhum ramo foi removido**; ainda falta decidir o destino de cada identidade/efeito legado e revisar as tags associadas especificamente a essas cartas antigas, sem confundir isso com a política de combos já aprovada.

A validação sintética não aprova EFP, custo, raridade, teto 32 ou distribuição. Naquele ponto histórico, a auditoria de sobreposição havia enumerado pares e trincas de IDs distintos, mas não simulava partidas completas. A decisão sobre participação/mínimos/precedência foi aprovada e implementada posteriormente; a sequência autorizada atual está no bloco “Estado exato ao encerrar esta entrega” e inclui testes stateful, snapshots, integração e simulação por facção.

## Histórico pré-patch: auditoria de sobreposição, precedência e participação dos combos

> **Histórico do defeito anterior à política aprovada.** Use `card-game-combo-overlap-v0.2.md` para o estado atual.

Documentos: [`card-game-combo-overlap-v0.1.md`](card-game-combo-overlap-v0.1.md) e JSON congelado. O script `scripts/audit-combo-overlap-v0.1.py` é arquivado: só reproduz o baseline em checkout pré-política e recusa execução no código atual. Para runtime vigente, use v0.2.

O script examina o resolvedor real `sistemas/gwent.py::_aplicar_combo_de_cartas()` com 67 unidades do catálogo que possuem tags, excluindo cinco IDs órfãos. Enumera 4.422 ordens de dois modelos distintos e 287.430 sequências ordenadas de três modelos distintos. Não valida um deck completo de 12 cartas, posse, partida, API ou vitória.

Achados objetivos:

- 154/4.422 ordens de pares (3,4826%) têm mais de um combo elegível ao mesmo tempo; correspondem a 77 pares não ordenados e envolvem 15 dos 27 combos. O resolvedor aplica o primeiro na ordem do dicionário e retorna; os demais ficam adiados.
- 11.780/287.430 trincas (4,0984%) ativam pelo menos dois combos diferentes em jogadas sucessivas; 1.088 dessas trincas pertencem à mesma facção.
- Em 8.096 de 11.784 eventos de combo posterior (68,7033%), a carta que recebeu o bônus não contribuiu com nenhuma tag exigida por aquele combo. A causa é que o resolvedor só testa se a carta atual tem qualquer tag não vazia; a condição do combo pode já estar completa no tabuleiro.
- Três combos não têm `minimum`: `cinzas_fornalha`, `vazio_astral` e `eco_convergente`. No catálogo atual, `gwent_unidade_eco` (`Erudito das Pedras Cintilantes`, tags `astral` + `eco`) ativa `eco_convergente` sozinho, embora a descrição cite o Erudito e outra unidade Astral.

Exemplo: `chefe_guardiao_cinzas` + `gwent_unidade_baluarte` completam tanto `cinzas_fornalha` quanto `juramento_erdtree`; o primeiro dispara por precedência. Em seguida `covenant_irmandade_ferro`, que só possui a tag `estandarte`, aciona o `juramento_erdtree` pendente e recebe o bônus individual apesar de não contribuir com `ordem_dourada`.

**Decisão posteriormente aprovada e implementada:** a carta atual precisa contribuir com tag exigida; os 27 combos exigem duas instâncias distintas; `priority` crescente decide a precedência; apenas um combo ativa por jogada; a carta participante atual recebe o bônus individual; `team_bonus` permanece. Consulte `card-game-combo-policy-v0.1.md` e a seção de estado atual no início deste handoff.

A auditoria é reproduzível e não altera o motor. Os detalhes, linhas, método, limitações e decisões estão no relatório completo.

## Regra permanente de pacote de continuidade

O usuário determinou que **toda entrega futura deste trabalho deve atualizar um único arquivo `.zip`** contendo os materiais necessários para outro chat/agente assumir sem depender do histórico da conversa. Esta é uma exigência recorrente, não uma ação opcional.

Em cada nova etapa que produza ou altere documentação, código, dados, testes ou decisões:

1. Atualizar este handoff e os documentos técnicos afetados.
2. Incluir no mesmo pacote o projeto-fonte disponível e todos os documentos de continuidade/auditoria, mantendo caminhos relativos.
3. Incluir um índice de leitura e um manifesto com o estado da entrega, arquivos adicionados/alterados, validações e limitações conhecidas.
4. Recriar o ZIP completo; não entregar documentos avulsos como substitutos do pacote.
5. Verificar a integridade do ZIP, a presença de todos os documentos e a ausência de segredos, arquivos temporários e artefatos locais desnecessários antes de fornecer o link.
6. Informar claramente se algum arquivo necessário não estava disponível para inclusão.

O arquivo ZIP mais recente deve ser tratado como o pacote de continuidade de referência da etapa atual. O handoff dentro do próprio pacote deve indicar o estado exato e a ordem de leitura.

## Regras de operação para a próxima IA

- Comece lendo este arquivo e `card-game-mapping-audit.md`.
- Não assumir que o código executável corresponde aos textos de descrição.
- Não apagar IDs de carta já persistidos sem migração/alias; verificar `cartas_colecao`, `cartas_exemplares`, `cartas_gwent_decks`, `cartas_gwent_matches`, Ateliê e artes pessoais.
- Não confiar em `HABILIDADES_UNIDADE_IMPLEMENTADAS` como prova suficiente de execução; conferir o caminho de chamada e simular partida.
- Não usar a lore como texto mecânico. A descrição mecânica deve derivar do mesmo `effect_id` que o motor executa.
- Não editar arte oficial integral como se fosse um layer; o renderer devolve o arquivo completo sem overlays.
- Não usar a tabela de raridade antiga como a fórmula nova; preservar os valores históricos até existir migração aprovada.
- Não tratar `docs/CARD_GAME_REDESIGN.md` como fonte de verdade sem conciliar com o motor real.
- Nunca atualizar apenas frontend para uma regra de deck/custo: validação autoritativa fica no servidor.

## Histórico de alterações desta continuidade

| Data | Arquivo | Trecho/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| 2026-11-27 | `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md` | Quadro de completude da Regra 8 e aviso de entrada para chat novo | Tornada explícita a finalidade de handoff do pacote, adicionada mensagem inicial sugerida e avaliada a cobertura dos quatro blocos com pendências/defasagens. | Evitar que um novo chat trate o pacote como 100% completo ou confunda propostas com regras aprovadas. | Sem impacto no runtime; clarifica limites e ordem de leitura. | Conteúdo comparado com auditoria, spec v0.1, matriz e inventário do ZIP; revisão documental. |
| 2026-11-27 | `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md` | Regra permanente de entrega | Registrada a exigência do usuário de manter todo o contexto necessário em um único ZIP atualizado a cada nova etapa, com índice, manifesto e verificação de integridade. | Garantir continuidade entre chats sem depender do histórico da conversa. | Nenhum impacto funcional; altera somente o processo documental/de entrega. | Regra incorporada ao handoff e incluída no pacote de continuidade. |
| 2026-11-27 | `docs/card-game-mapping-audit.md` | Novo documento | Criado inventário estático completo, incluindo catálogo de habilidades, identidades, combos, líderes, relíquias, dados, APIs e falhas encontradas. | Registrar o estado anterior antes de qualquer remoção. | Nenhum impacto funcional; referência técnica para a reconstrução. | Catálogos importados e contagens conferidas; sem teste de partida real. |
| 2026-11-27 | `docs/card-game-handoff.md` | Novo documento | Criado handoff operacional com regras confirmadas, estado, prioridades e próximos passos. | Permitir continuidade entre chats/agentes. | Nenhum impacto funcional. | Revisão estática do conteúdo e links relativos. |
| 2026-11-27 | `docs/card-game-card-traceability.md`, `.csv`, `.json` | Novos documentos | Criada matriz individual do catálogo runtime, incluindo efeitos, identidade, tags, custo, texto preparado e cobertura visual. | Permitir decidir carta por carta o que preservar, corrigir ou remover. | Nenhum impacto funcional; artefatos de auditoria para a reconstrução. | Import do catálogo e do motor; comparação estática de campos e mapeamentos; sem partidas reais/DB de produção. |
| 2026-11-27 | `docs/card-game-mapping-audit.md` | Seção 12 — Matriz de rastreabilidade individual | Adicionadas referências aos três formatos da matriz e os achados atualizados da auditoria carta por carta. | Manter o baseline técnico conectado à evidência individual. | Nenhum impacto funcional. | Conferência das 137 cartas e referências relativas. |
| 2026-11-27 | `docs/card-game-handoff.md` | Seção Matriz e Estado exato | Atualizados o ponto de continuidade, achados quantitativos, dependências e estado da implementação. | Garantir handoff atualizado após a nova etapa. | Nenhum impacto funcional. | Revisão dos links e cruzamento com a matriz JSON/CSV/Markdown. |

| 2026-11-27 | `docs/scripts/build-effect-source-map-v0.1.py`, `docs/card-game-effect-source-map-v0.1.json` | Novo índice AST de efeitos | Ligados 59 IDs genéricos, 22 identidades, 10 líderes e 27 combos às funções/linhas/condições do código. | Evitar inferir mecânica apenas de nome/descrição; localizar o handler exato. | Somente diagnóstico documental; nenhum módulo de runtime alterado. | Geração repetida; 56 handlers diretos, 2 hooks, `sobrevivente` sem handler, 22 identidades e 10 líderes com referências. |
| 2026-11-27 | `docs/card-game-efp-methodology-v0.2.md` | Novo método de avaliação | Substituída a recomendação de pontuação fixa por decomposição de vetor mecânico, cenários estratificados e valor esperado em simulações. | Pesos da v0.1 não têm calibração empírica. | Sem alteração funcional; metodologia permanece proposta não aprovada. | Revisão cruzada com resolver, handlers, smoke e frequência de combos. |
| 2026-11-27 | `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md`, `docs/card-game-balance-validation-v0.1.md` | Estado, ordem e próximos passos | Incluídos mapa de fonte, método EFP v0.2 e pendências de asserts/simulação. | Manter novo chat no estágio correto e evitar adoção prematura de pontuações. | Apenas documentação. | Conferência dos links relativos, contagens e saídas geradas. |

| 2026-11-27 | `docs/scripts/assert-card-effect-behavior-v0.1.py`, `docs/card-game-effect-behavior-assertions-v0.1.json` | Primeira bateria de comportamento | Adicionadas 13 asserções explícitas para buffs, debuffs, compra, escudo, ressurreição, movimento, invocação, remoção, clima/estado e identidade. | Verificar resultado esperado, não apenas ausência de exceção. | Ferramenta diagnóstica apenas; nenhuma alteração de runtime. | 13/13 passaram com raridade Comum e fixtures sintéticos. |
| 2026-11-27 | `docs/scripts/assert-leader-effects-v0.1.py`, `docs/card-game-leader-assertions-v0.1.json` | Novo harness; `state_for()`, `activate()`, dez handlers e condições de falha | Adicionadas 22 asserções: dez positivas (todos os líderes) e doze negativas/limite. | Completar a cobertura controlada da ação de líder que não estava nos testes anteriores. | Diagnóstico apenas; nenhum impacto no runtime. | 22/22 aprovadas por `aplicar_jogada(action="leader")` em fixtures sintéticos. |
| 2026-11-27 | `docs/scripts/summarize-card-game-behavior-v0.2.py`, `docs/card-game-behavior-validation-v0.2.json`, `.md` | Agregador e relatório de seis suites | Consolidadas 132 asserts, resultados, limitações, mapa dos 28 ramos antigos e próximos passos. | Criar um ponto único e reprodutível de leitura para o próximo chat. | Apenas documentação e ferramentas de diagnóstico. | Nove scripts executados novamente; 132/132 aprovados; agregador verifica presença/contagem/status. |
| 2026-11-27 | `docs/scripts/assert-combo-and-faction-passive-v0.1.py`, `docs/card-game-combo-faction-assertions-v0.1.json` | Novo teste de `_aplicar_combo_de_cartas()`, `aplicar_jogada()` e `_resolve_round()` | Incluídos 87 cenários: todos os 27 combos com um par ativador, requisito incompleto e bloqueio de repetição; quatro passivas de facção; carta sem tags; exclusão de especial. | Completar a validação controlada dos combos e passivas antes da simulação competitiva. | Apenas ferramenta/JSON diagnóstico; nenhum impacto no runtime. | 87/87 passaram. Cada combo testado com um par ativador concreto; outras combinações e precedências sobrepostas ainda não exaustivas. |
| 2026-11-27 | `docs/scripts/summarize-card-game-behavior-v0.2.py`, `docs/card-game-behavior-validation-v0.2.md/.json` | Agregador ampliado de seis para sete suites | Total atualizado de 132 para 219 cenários; novo bloco detalha combos e passivas. | Evitar handoff defasado após nova bateria. | Apenas documentação e ferramentas. | Sete relatórios JSON validados; 219/219 aprovados, zero falhas. |
| 2026-11-27 | `docs/card-game-stale-identity-disposition-v0.1.md`, `.json`, `docs/scripts/audit-stale-identity-branches-v0.1.py` | Classificação de 28 ramos sem associação ativa | Separados 18 ramos filtrados pelo V18, quatro campos legados e seis ramos V75; separados também `gloria`/`sobrevivente`. | Não classificar código como morto sem identificar carta, tag e dependência; evitar exclusão prematura. | Nenhuma remoção nem alteração funcional. | Auditoria AST/runtime: 28 = 18+4+6; três cartas com `gloria`; `sobrevivente` sem handler. |
| 2026-11-27 | `docs/card-game-handoff.md`, `README-PACOTE-CONTINUIDADE.md`, `PACOTE-MANIFESTO.md`, `card-game-mapping-audit.md`, `card-game-balance-validation-v0.1.md`, `card-game-efp-methodology-v0.2.md` | Estado, ordem de leitura, completude e próximos passos | Atualizada a fase de 13 asserts para seis suites/132 asserts; incluídos testes de líder e disposição dos ramos antigos. | Não deixar o próximo chat repetir trabalho concluído nem interpretar asserts como prova de balanceamento. | Apenas documentação. | Links e contagens cruzados com relatórios individuais e agregador. |

## Estado exato ao encerrar esta entrega — integração stateful v0.1

- **Concluído anteriormente:** política de combos aprovada e implementada em `sistemas/gwent.py`; 27 combos com `minimum: 2` e `priority` único; bônus individual limitado à carta participante; `team_bonus` preservado. Oito suites anteriores: 251/251 asserts; auditoria de 4.422 pares e 287.430 trincas, zero ativações solo e 2.582/2.582 eventos posteriores com carta participante.
- **Concluído nesta etapa:** 12/12 cenários stateful; quatro partidas em memória de três rodadas cobrindo as quatro facções; round-trip JSON em ações/resoluções; 137/137 modelos preparados com contrato de payload; combo real por jogadas; líder + especial climático + reset; relíquia de uso único; clima manual de uso único; defaults de snapshot legado; imutabilidade da entrada em ação rejeitada; `SCHEMA` + `SCHEMA_CARTAS` reais executados em SQLite `:memory:` e persistência `state_json` verificada; contrato bot/site inspecionado estaticamente; `compileall` e `node --check` aprovados.
- **Não confundir com integração de produção:** os quatro jogos stateful usam unidades sintéticas para controlar resultado; o teste SQLite usa DDL real mas conexão `:memory:` e não o wrapper `Database`. O HTTP foi analisado estaticamente, não despachado. `discord.py` e `aiosqlite` não estão instalados no ambiente de análise, impedindo import real do bot/wrapper nesta etapa.
- **Runtime funcional:** nenhuma mudança nesta etapa. A última mudança funcional continua em `sistemas/gwent.py` na implementação da política de combos. Nenhum schema, endpoint, frontend ou imagem foi alterado.
- **Pendente imediato:** obter ambiente com `discord.py==2.7.1` e `aiosqlite==0.22.1` (ou wheels locais; tentativa de instalação via pip bloqueada por DNS nesta sessão); executar testes reais de handlers HTTP; fluxo de convite e aceitação; criação solo/IA e fallback; persistência via classe `Database`; autenticação e respostas API; browser para catálogo, detalhes e jogadas; arte/R2.
- **Pendente de reconstrução:** destino de habilidades/identidades antigas, corrigir tags e facções apontadas, novo catálogo, lore, poder 1–15, pelo menos 30% de cartas puras, distribuição determinística, EFP/custo/raridade e orçamento de deck. Valores de `card-game-balance-spec-v0.1.md` continuam propostas não aprovadas e fora do runtime.
- **Dependências ausentes:** DB de produção, credenciais/configuração publicada, `discord.py` e `aiosqlite` neste ambiente de análise, estado R2 e artes aprovadas publicadas.
- **Referência de continuidade:** ler `README-PACOTE-CONTINUIDADE.md`, depois este handoff, `card-game-match-snapshot-integration-v0.1.md`, `card-game-behavior-validation-v0.3.md` e a política de combos. O ZIP mestre é atualizado a cada etapa.

## Histórico de alterações — etapa de especificação v0.1 (2026-11-27)

| Arquivo | Trecho/campo | Alteração | Motivo | Impacto/validação |
|---|---|---|---|---|
| `docs/card-game-card-traceability.json` | 16 registros; `status_resolucao`, `efeitos_efetivos_listados`, `divergencia_exibicao_vs_execucao`, novo `habilidade_generica_suprimida_por_identidade` | Corrigido para indicar supressão do genérico e execução única da identidade. | O resolver define `skill=""` quando há identidade ativa. | Somente documentação/dados de auditoria; origem conferida em `sistemas/gwent.py:1472` e chamada de identidade em `:1863`. |
| `docs/card-game-card-traceability.csv` | Todas as linhas/colunas | Regenerado do JSON corrigido. | Manter formatos tabular e JSON idênticos. | CSV conferido por contagem de 137 linhas de dados. |
| `docs/card-game-card-traceability.md` | Convenções, inconsistências e 16 fichas | Removida a alegação de dupla execução e documentada ambiguidade do payload. | Corrigir conclusão técnica anterior. | Comparação estática com o resolver e `preparar_carta()`. |
| `docs/card-game-mapping-audit.md` | Nova seção de retificação | Adicionada explicação de `skill=""` e do payload com ID genérico + texto de identidade. | Preservar o histórico sem ocultar a correção. | Nenhum impacto funcional. |
| `docs/card-game-balance-spec-v0.1.md` | Novo documento integral | Formalizada proposta de EFP, pureza, custo, orçamento (inicialmente 60, depois revisado para 32 por amostragem), raridade, distribuição determinística, schema e facções. | Estabelecer critérios mensuráveis antes da reconstrução. | Proposta não aprovada; pesos e limiares não testados em simulação. |
| `docs/card-game-effect-score-catalog.json` | Novo catálogo estruturado | Adicionados 59 metadados de habilidade, 22 identidades, 27 combos e 10 líderes, com scores estimados/estados. | Permitir revisão efeito a efeito sem confundir metadados com regras já implementadas. | EFP é hipótese; `null` marca definição sem handler/associação validada. |
| `docs/card-game-handoff.md` | Estado, links, achados e histórico | Corrigida conclusão de identidade e adicionada proposta v0.1/ordem de continuidade. | Próxima IA precisa receber contexto correto e status explícito. | Nenhum impacto funcional. |
| `docs/card-game-balance-spec-v0.1.md`, `docs/card-game-deck-cost-sampling-v0.1.json` | Seção 5 e teto experimental | Teto 60 rejeitado como permissivo; proposta passou a 32 após amostra reproduzível de 100.000 decks. | 100% dos decks amostrados ficaram ≤60 e só 56,3% ≤32. | Amostragem aleatória, não simulação de resultados de partida; orçamento permanece não aprovado. |

### Próximo passo autorizado na etapa v0.1 (histórico; concluído pela validação exploratória)

A instrução anterior para validar a proposta foi cumprida parcialmente sem alterar o runtime. Os achados e correções metodológicas estão em `card-game-balance-validation-v0.1.md`. A próxima etapa agora é construir EFP com memória de cálculo e testes por efeito; simulação competitiva ainda falta.


### Resultado histórico da amostragem de custo v0.1 (superado; não usar para aprovar orçamento)

- 128 modelos pontuáveis: 101 unidades e 27 especiais; 9 unidades com habilidade não resolvida foram excluídas da amostra.
- 100.000 decks aleatórios, 12 cartas únicas, 8–12 unidades, 0–4 especiais, seed 42.
- Média/mediana de custo: 32,08 / 32; p90 = 36.
- Teto 32: 56,3% dos decks amostrados caberiam; teto 36: 91,6%; teto 60: 100%.
- Raridade calculada nos 128 modelos pontuáveis: 8 Comuns, 36 Raras, 45 Épicas, 32 Lendárias, 7 Míticas, 0 Primordiais e 0 Singulares. Resultado estimado pelo score v0.1, sem distribuição de drop.
- O teto 32 substitui 60 como hipótese experimental. Amostra não simula jogabilidade, posse, facção, líder ou relíquia e não comprova equilíbrio.



## Histórico de alterações — validação exploratória v0.1 (2026-11-27)

| Arquivo | Trecho/função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/card-game-balance-validation-v0.1.md` | Novo relatório | Registradas as falhas de método v0.1, amostragem de custo v0.2, frequência de 27 combos, auditoria de handlers, testes de fumaça, limites de EFP e próximos passos. | Criar evidência para não aprovar parâmetros não sustentados. | Somente documentação. | Cruzado com scripts/JSON gerados e código estático; nenhuma regra do jogo alterada. |
| `docs/scripts/validate-card-effect-smoke-v0.1.py` | `fixture()`, `run_skill()` e agregações | Carta reserva evita auto-pass; condições de `encadeamento` e `sangue_frio` corrigidas; status não declara cobertura completa de ramo. | Corrigir fixtures e precisão do diagnóstico. | Ferramenta em `docs/scripts/`, sem chamada pelo runtime. | 59 ações sem exceção; `encadeamento` +2, `sangue_frio` +2; hooks verificados separadamente; 22/22 identidades com evento. |
| `docs/card-game-effect-runtime-smoke-v0.1.json` | Resultado regenerado | Atualizadas contagens e detalhes dos fixtures. | Refletir teste corrigido. | Evidência documental. | Script executado com sucesso. |
| `docs/scripts/audit-effect-handler-coverage-v0.1.py` | Novo script AST | Cruzamento estático de `HABILIDADES`, handlers genéricos, hooks, identidade e tags. | Encontrar ramos antigos e ligações ausentes. | Ferramenta diagnóstica, não altera runtime. | 59 genéricas, 58 com referência (1 sem), 22 identidades ativas (22 com ramo), 28 ramos antigos, 27 combos sem tag impossível. |
| `docs/card-game-handler-coverage-v0.1.json` | Novo relatório | Saída estruturada da auditoria estática. | Facilitar continuação automatizada. | Somente docs. | Reproduzido pelo script AST. |
| `docs/scripts/sample-deck-cost-v0.2.py` / `docs/card-game-deck-cost-sampling-v0.2.json` | Cálculo e hipóteses | Removida pontuação parcial de combo; adicionados cenários com/sem relíquia e `leader_load`; limitações atualizadas para reconhecer medição de combo separada. | Corrigir método da amostragem v0.1. | Estimativa analítica, não custo em produção. | Reexecução com seed 42 idêntica: 68,8% aceitação em 32 sem relíquia; 45,4% com relíquia. |
| `docs/scripts/sample-deck-cost-v0.1.py` | Docstring | Marcado como histórico/superado, preservando cálculo antigo para auditabilidade. | Evitar uso equivocado da fórmula antiga. | Nenhum impacto no runtime. | Inspeção estática. |
| `docs/scripts/simulate-combo-activation-v0.1.py` / `docs/card-game-combo-activation-v0.1.json` | Novo diagnóstico | Medida de ativação potencial/real dos 27 combos chamando o resolvedor atual. | Não imputar EFP por tag parcial; obter frequência preliminar realista. | Não altera jogo e não atribui EFP aos combos. | Segunda execução com seed 42 idêntica; 57,19% de decks com ao menos um combo. |
| `docs/card-game-balance-spec-v0.1.md` | Nota de revisão | Marcada a amostragem v0.1 como superada e teto 32 como sem sustentação/aprovação. | Evitar confundir dado antigo com decisão. | Apenas documentação. | Conferido com relatório v0.2. |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem e histórico | Atualizados para próxima fase EFP/testes/simulação e incluídos novos materiais. | Permitir que novo chat continue sem consultar esta conversa. | Apenas docs. | Links relativos, contagens e hashes revisados. |


## Histórico de alterações — implementação da política oficial de combos (2026-11-27)

| Arquivo | Trecho/função/campo | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `sistemas/gwent.py` | `SYNERGY_COMBOS` | 27 definições; três sem mínimo explícito; nenhuma prioridade própria | Todos os 27 têm `minimum: 2` e `priority` inteiro único de 10 a 270, em intervalos de dez | Formalizar duas unidades distintas e precedência determinística aprovada | Corrige combos solo e remove dependência da ordem do dicionário | Teste de contrato: 27 mínimos e 27 prioridades únicos |
| `sistemas/gwent.py` | `_aplicar_combo_de_cartas()` | Uma carta com qualquer tag podia receber combo já elegível; mínimo era opcional; primeira entrada do dict vencia | Exige tag atual intersectando tags do combo; conta instâncias distintas; ordena por priority ascendente; aplica um combo por chamada | Garantir participação efetiva e prioridade estável | Muda resolução de jogadas futuras; mantém `synergy_used`, `bonus`, `team_bonus` e reset de rodada | 32/32 regressões; 87/87 combo/facção; auditoria pós-patch |
| `sistemas/gwent.py` | Descrições em `SYNERGY_COMBOS` | Algumas diziam “carta que completa”; três descrições não deixavam o mínimo explícito | Texto diz “carta participante que ativa” e explicita cartas distintas nos três casos | Alinhar texto ao alvo real do bônus e mínimo | Texto de combo retornado pelo motor é atualizado; imagens integrais aprovadas não são regeneradas | Revisão estática das 27 definições e teste do contrato |
| `docs/scripts/assert-combo-policy-v0.1.py`, `docs/card-game-combo-policy-assertions-v0.1.json`, `docs/card-game-combo-policy-v0.1.md` | Nova suite e especificação oficial | Inexistentes | Adicionados contrato, prioridades, exemplos, impacto e 32 asserts, incluindo caminho público `aplicar_jogada(action="play")` | Tornar a política aprovada reproduzível | Diagnóstico/documentação, não chamado no runtime | 32/32 passaram |
| `docs/scripts/audit-combo-overlap-v0.2.py`, `docs/card-game-combo-overlap-v0.2.json/.md` | Nova auditoria pós-política | Relatório antigo era baseline pré-patch | Enumerados pares/trincas no resolver atualizado | Medir regressões e estado após correção | Diagnóstico apenas; sem mudança adicional no motor | 4.422 pares, 287.430 trincas; 0 solo; 2.582 eventos posteriores todos participantes |
| `docs/scripts/summarize-card-game-behavior-v0.3.py`, `docs/card-game-behavior-validation-v0.3.json/.md` | Novo agregador e relatório | v0.2 totalizava 219 asserts em sete suites antes da nova política | v0.3 inclui oitava suite e total de 251 asserts | Um resultado único pós-patch | Handoff tem contagem reprodutível | 8 suites, 251/251 aprovados |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/card-game-mapping-audit.md`, `docs/card-game-balance-validation-v0.1.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura, pendências e histórico | Diziam que decisão de combo era pendente e nenhuma alteração funcional existia | Registram decisão aprovada, patch, compatibilidade e próximos passos atuais | Evitar handoff incorreto ao chat novo | Documentação de continuidade | Links/contagens conferidos com scripts e JSONs |

## Histórico de alterações — auditoria de combos sobrepostos (2026-11-27)

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/audit-combo-overlap-v0.1.py` | Script arquivado de baseline pré-política | Rodava contra o resolvedor original antes da aprovação; agora o runtime mudou | Guardado com fail-fast no checkout pós-política; só pode ser reproduzido em checkout pré-política | Evitar sobrescrever ou confundir o relatório histórico | Ferramenta documental apenas; não é importada pelo runtime | JSON/Markdown v0.1 congelados; auditoria atual é v0.2 |
| `docs/scripts/build-effect-source-map-v0.1.py` | Gerador arquivado do mapa AST pré-política | Gerava o índice histórico a partir do runtime daquele baseline | Guardado com fail-fast no checkout pós-política; mapa atual é v0.2 | Evitar sobrescrever as referências históricas e misturar linhas/branches de versões distintas | Ferramenta documental apenas | JSON v0.1 congelado; script/JSON v0.2 são a fonte atual |
| `docs/card-game-combo-overlap-v0.1.json`, `.md` | Novos relatórios | Documentados combos simultaneamente elegíveis, ativações diferidas, 8.096/11.784 eventos sem contribuição da carta atual, `eco_convergente` solo e decisões de design pendentes. | Tornar explícito o comportamento escondido do resolver antes de qualquer alteração. | Apenas evidência e documentação; nenhuma regra de partida alterada. | JSON regenerado pelo script; exemplos conferidos com o catálogo e o resolver em `sistemas/gwent.py:916–946`. |
| `docs/card-game-handoff.md`, `README-PACOTE-CONTINUIDADE.md`, `PACOTE-MANIFESTO.md`, `card-game-mapping-audit.md`, `card-game-balance-validation-v0.1.md`, `card-game-behavior-validation-v0.2.md`, `card-game-efp-methodology-v0.2.md` | Estado, ordem de leitura, riscos e próximos passos | Atualizadas referências e pendências para exigir decisão explícita sobre participação, mínimo, precedência e alvo dos combos. | Evitar simular EFP/custo com semântica de combo ambígua. | Documentação/handoff somente. | Links, métricas e limitações cruzados com o JSON de auditoria. |


## Histórico de alterações — mapa estático de contratos HTTP v0.1 (2026-11-27)

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/audit-gwent-http-contracts-v0.1.py` | AST de registros de rota, funções handler, `preparar_carta()` e literais de `site/app.js` | Criado/ajustado gerador para inventariar as 12 rotas Gwent, os campos de requisição, sinais de autenticação/origem, chamadas DB/motor e sinais frontend; corrigido o acesso AST para reconhecer funções referenciadas por nome. | Fechar a lacuna entre mapa geral do sistema e contratos concretos entre bot, UI, motor e banco, sem fingir execução HTTP. | Apenas ferramenta documental; não é importada pelo runtime. | Script reproduz 12 rotas; identifica ausência de orçamento e ausência de `custo` no retorno preparado. |
| `docs/card-game-http-contract-map-v0.1.md/.json` | Novo relatório de contratos | Registradas as 12 rotas, linhas/handlers, campos do frontend, validações de deck, fluxo de convite/solo/ação e limites da análise estática. | Documentar as conexões exatas e a pendência real de integração. | Handoff/diagnóstico; sem impacto em APIs ou partidas. | Gerado pelo script e revisado contra `bot.py`, `site/app.js` e `sistemas/gwent.py`. |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura, mapa e histórico | Incluída a revisão HTTP estática como estado mais recente; etapa stateful preservada como referência anterior; registrada a perda do campo `custo` em `preparar_carta()` e falta de enforcement do orçamento no deck save. | Impedir que próximo chat confunda análise estática com integração executada e antecipar o contrato a corrigir quando as regras de custo forem aprovadas. | Apenas documentação e scripts em `docs/`; runtime intocado. | 12 rotas reproduzidas; testes comportamentais/stateful reexecutados separadamente. |

## Histórico de alterações — validação stateful v0.1 (2026-11-27)

| Arquivo | Trecho/função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/assert-full-match-stateful-v0.1.py` | Nova suíte: `novo_estado()`, `aplicar_jogada()`, `_resolve_round()`, `preparar_carta()`, snapshot JSON e DDL SQLite | Criados 12 cenários stateful para quatro jogos de três rodadas, catálogo 137 modelos, combo normal, líder/especial/clima, relíquia, clima manual, snapshot legado, ação rejeitada, SQLite e contrato estático bot/site. | A suíte anterior testava principalmente funções/condições isoladas; era necessário validar transições, serialização e o fluxo em várias rodadas. | Somente ferramenta de teste; nenhum import/call no runtime. | 12/12 cenários; relatório JSON associado. |
| `docs/card-game-match-snapshot-integration-v0.1.md/.json` | Novo relatório | Registrados escopo, evidências, comandos de reprodução e limitações, incluindo ausência de `discord.py`/`aiosqlite` no ambiente. | Evitar afirmar integração HTTP/produção que não foi executada. | Handoff e diagnóstico. | JSON gerado pelo runner; 12/12. |
| `docs/card-game-handoff.md` | Estado atual, tabela da Regra 8, estado exato e histórico | Atualizado de testes sintéticos isolados para 251 asserts + 12 cenários stateful separados; próximos passos HTTP explicitados. | Impedir que novo chat repita validação ou trate análise estática como integração executada. | Somente documentação. | Links e resultados cruzados com relatório. |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md`, `docs/card-game-mapping-audit.md` | Ordem de leitura, estado, mapa e manifesto | Incluídos testes stateful, resultados, tentativa de instalação de dependências e bloqueio de DNS/produção. | Manter pacote autossuficiente e atual. | Somente documentação. | Referências, contagens e validações conferidas. |




## Histórico de alterações — reforço do contrato e registry v1.1 (2026-11-27)

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `sistemas/card_contract.py` | `validate_effect_registry()`, `_validate_effect_params()`, `validate_card_definition()`, `validate_catalog()` | Adiciona validação de IDs duplicados, parâmetros declarados/obrigatórios, tipos, limites, enum, parâmetros extras, mínimo de dois participantes em combo e prioridade positiva única; passa a validar `effect_params` contra a definição real do efeito | Um `effect_id` conhecido ainda poderia receber parâmetros que o handler não reconhece ou valores fora da faixa | Continua módulo isolado; nenhuma chamada foi adicionada ao runtime legado | 35/35 testes; casos inválidos de parâmetro, combo solo, prioridade e IDs detectados |
| `data/card_game/effect-registry.schema.v1.json` | Novo JSON Schema Draft 2020-12 | Formaliza efeitos, parâmetros, timing, handler e combos | Dar contrato publicável ao registry, não apenas ao catálogo de cartas | Nenhum impacto funcional | `check_schema` aprovado e exemplo válido |
| `data/card_game/effect-registry.example.v1.json` | `required_parameters`, `allow_additional_parameters` | Torna explícitos parâmetros obrigatórios e bloqueio de parâmetros extras | Demonstrar payload estritamente tipado | Exemplo didático somente | Schema e validador Python aprovados |
| `docs/scripts/validate-card-catalog-v1.py` | `main()` | Valida registry antes do catálogo e compara os parâmetros de cada carta com sua definição de efeito | Evitar aceitar referências corretas com payload incompatível | Ferramenta de validação; não modifica arquivos | Fixture válido aceito; `ally_bonus` fora do máximo rejeitado |
| `docs/scripts/test-card-contract-v1.py` | Suite `unittest` | Expande 25 para 35 casos, incluindo registry e CLI | Cobrir falhas reais de consistência de dados | Harness local | 35/35 aprovados |
| `docs/scripts/validate-card-json-schemas-v1.1.py` | Novo script opcional | Valida dois schemas e dois exemplos com Draft 2020-12 | Reproduzir validação estrutural fora do teste unitário | Depende opcionalmente de `jsonschema`; não é requisito do bot | Dois schemas e exemplos válidos |
| `docs/card-game-canonical-model-v1.md`, `data/card_game/README.md`, `docs/card-game-contract-validation-v1.1.md/.json` | Contrato, leitura e relatório | Registra schema do registry, parâmetros e limites de validação, resultados e comandos | Manter handoff verificável | Documentação e ferramentas apenas | Revisão cruzada e artefatos reproduzíveis |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PROJECT-OPERATING-CONTEXT.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem, histórico e próximos passos | Atualiza validação para 35/35 e separa contrato estrutural de catálogo/runtime e fórmulas não aprovadas | Evitar que chat novo use status desatualizado ou trate proposta como aprovada | Apenas documentação | Links e contagens conferidos |

## Estado da reconstrução — contrato canônico v1.1

A fundação estrutural foi criada. Ler `card-game-canonical-model-v1.md` e `card-game-legacy-baseline-v0.1.md`. O snapshot contém 137 modelos (110 unidades, 21 especiais, seis relíquias), 59 habilidades genéricas, 22 identidades ativas, 27 combos e dez líderes. Baseline com 15/137 puras; quota de 30% = 42. Há 19 divergências de custo, seis facções a revisar e 43 modelos tocados pela transformação V18.

Validação atualizada: 35/35 testes do contrato; dois JSON Schemas Draft 2020-12 válidos e exemplos aprovados; CLI sintético positivo/negativo; snapshot determinístico. O runtime legado não foi alterado nesta etapa; `sistemas/card_contract.py` é isolado. Próximo passo é montar o registry consolidado `effect_id -> handler -> parâmetros -> timing -> testes -> texto`, sem remover ramos até classificar cada um.


## Continuidade rev. 14 — 27/11/2026

Grupos A/B/C/D/F aprovados. O Grupo F foi formalizado em `card-game-removal-causes-group-F-approval-v0.1.md` e integrado ao draft `CardInstance v0.6`. O Grupo E foi auditado em modo somente leitura: `BEGIN IMMEDIATE`, WAL e transações já protegem o caminho atual contra lost update sob SQLite; faltam revisão persistida, idempotência de ação, journal durável, outbox e migration ledger. Decisões E-001..E-010 aguardam aprovação. Não executar migração nem alterar o runtime antes do gate E.
