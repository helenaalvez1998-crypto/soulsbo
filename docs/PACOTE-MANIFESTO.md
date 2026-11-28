# Estado corrente V77 — paridade de facções e revisão de nomes (2026-11-28)

A revisão V77 está no código do pacote: 179 modelos no índice, 164 cartas no pacote jogável, 30 unidades + 11 especiais e três líderes por facção (41 cartas de coleção por facção; 12 líderes no total). Os Esquecidos têm dez novas cartas especiais nesta revisão, além dos dois líderes adicionais já introduzidos na V76. Os 17 especiais V77 usam aliases declarados e handlers canônicos testados; o site recebe o efeito efetivo para usar os controles corretos. Os títulos atuais são únicos e limitados a 27 caracteres; IDs anteriores foram preservados. A auditoria catálogo → motor → site reporta 179/179 e zero divergências; suíte completa: **340 testes + 109 subtestes aprovados**; `py_compile` e `node --check site/app.js` aprovados. A atualização ainda não foi implantada no host. Consulte `docs/v77-normalizacao-faccoes-e-nomes.md` e `docs/AUDITORIA-FIDELIDADE-CARTAS.md/.json`. As seções abaixo preservam registros históricos.

---

# Manifesto atual — revisão rev. 31 (2026-11-28)

- **Baseline:** `soulsbo-main-continuity-2026-11-28-rev30.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev31.zip`.
- **Estado:** Card Engine v2 segue isolado em alpha; `CardInstance v0.7`/schema 7 continua draft, não congelado.
- **Conquistas:** 6 metas rastreáveis por registros autoritativos do servidor; Apostador e Sobrevivente explicitamente pendentes. Persistência monotônica e GET read-only.
- **Segurança de progressão:** apostas e evolução com risco bloqueadas em fail-closed, sem débito/reserva/mutação enquanto escrow/ledger transacional não existirem. Forja de ascensão segue separada.
- **Operação:** Dockerfile/Compose, volume persistente, imagem non-root, rootfs read-only, healthcheck, env example sem secrets, preflight e backup SQLite adicionados.
- **CI:** workflow inclui pytest, compilação Python, verificação JavaScript, parse Compose e Docker build.
- **Validação:** 240 testes + 61 subtests; playable alpha; staging 137/27/110; simulações Bo3 97 eventos e combo/passiva/líder 49 eventos; integridade SQLite aprovada.
- **Preflight no host atual:** 9 pass, 0 warnings, 22 blockers; sem token/OAuth, dependências exatas instaladas, banco real, Docker CLI ou deploy conectado.
- **Limites do produto:** 110 modelos históricos bloqueados; 18 combos ainda inativos; custos provisórios sem playtests humanos; evolução com risco e apostas não disponíveis; no Discord real/staging executado.
- **Preservação:** `bot.py`, `database.py`, `site/app.js`, `sistemas/gwent.py`, `sistemas/cartas.py` mantidos byte a byte iguais ao baseline rev. 30.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-rev31-product-completion.md`, `docs/card-engine-v2-rev31-change-manifest.md` e `docs/card-engine-v2-rev31-validation.json`.

---

# Manifesto atual — revisão rev. 25 (2026-11-28)

- **Baseline:** `soulsbo-main-continuity-2026-11-28-rev24.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev25.zip`.
- **Estado:** Card Engine v2 permanece isolado em alpha; `CardInstance v0.7`/schema 7 continua draft não congelado.
- **Ruleset:** `alpha-test-only.ruleset.v0.5`; mantém combate por fileira, 20 de vida, fatigue por turno individual, mão inicial 4 e energia +1/turno com teto 5.
- **Custos:** 27 cartas e dez líderes têm custos explícitos por ID. Cartas 1–5; líderes 2–3. A tabela é provisória para playtest, não aprovada para release nem validada com jogadores humanos/telemetria. Raridade e `deck_cost_legacy` não são entradas.
- **Habilidades:** framework genérico server-side `activate_card_ability` implementado e testado com fixture sintética. Registry ativo vazio, pois as 27 cartas atuais não declaram habilidade manual; efeitos de entrada não se tornam reativáveis.
- **Validação:** 150/150 testes; cada um dos 27 custos de carta e dez custos de líder passa com saldo exato e rejeita com saldo inferior; staging 137/27/110 e simulações oficiais aprovados; ZIP rev. 25 extraído em diretório limpo e validado com 150/150 testes.
- **Simulações:** cenários gerais usam fixture de energia uniforme 1 para isolar outras mecânicas; não representam playtest nem aprovam a tabela provisória. Testes de economia usam os preços reais provisórios por ID.
- **Integração:** ainda sem Discord/HTTP/frontend/banco publicado/adapter assíncrono/migração/cutover. Cinco arquivos centrais do motor legado permanecem intactos.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-energy-economy-alpha-v0.2.md`, `docs/card-engine-v2-alpha-energy-cost-schedule-v0.1.md`, `docs/card-engine-v2-alpha-activated-abilities-v0.1.md` e `docs/card-engine-v2-playable-alpha-validation-v0.5.md`.

---

# Manifesto atual — revisão rev. 24 (2026-11-28)

- **Baseline:** `soulsbo-main-continuity-2026-11-28-rev23.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev24.zip`.
- **Estado:** Card Engine v2 segue isolado em alpha; `CardInstance v0.7`/schema 7 continua draft não congelado.
- **Ruleset:** `alpha-test-only.ruleset.v0.4`; mão inicial padrão quatro, vida inicial 20, combate por diferença de poder nas fileiras e deck fatigue no início de cada turno individual.
- **Energia:** +1 por início de turno, máximo 5, saldo persistente entre rodadas; persistida no runtime sidecar sob CAS. `view()` expõe o saldo e o máximo.
- **Custos:** mapas por `card_id` e `leader_id` suportam pré-validação e pagamento transacional. Ambos permanecem vazios na baseline; sem cobrança para ações não precificadas durante compatibilidade alpha. Raridade e `deck_cost_legacy` não geram custo energético.
- **Catálogo:** 137 modelos históricos; 27 permitidos em alpha e 110 bloqueados; 27 combos (9 alcançáveis, 18 inertes), quatro passivas, dez líderes e 12 famílias de efeitos de entrada.
- **Validação:** 145/145 testes; compilação; staging 137/27/110; simulação Bo3 A 2–1 B, 87 eventos, seis aplicações de fatigue; demo combo/passiva/líder A 20–10 B, 44 eventos; SQLite íntegro. O pacote extraído foi validado novamente.
- **Integração:** sem Discord/HTTP/frontend/banco publicado/migração/cutover. Os cinco arquivos centrais do motor legado permanecem byte a byte idênticos ao baseline rev. 23.
- **Limite importante:** energia funciona, mas a economia ainda não está fechada porque os preços individuais do catálogo e dos líderes aguardam uma tabela explícita por ID; habilidades ativas genéricas ainda não têm API universal.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-energy-economy-alpha-v0.1.md`, `docs/card-engine-v2-playable-alpha-validation-v0.5.md` e `sistemas/card_engine_v2/README.md`.

---

# Manifesto atual — revisão rev. 23 (2026-11-28)

- **Baseline:** `soulsbo-main-continuity-2026-11-28-rev22.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev23.zip`.
- **Estado:** Card Engine v2 segue isolado em alpha; CardInstance v0.7/schema 7 permanece draft não congelado.
- **Ruleset:** `alpha-test-only.ruleset.v0.3`; mão inicial padrão de quatro cartas, vida 20, combate por diferença de poder por fileira e deck fatigue no início do turno individual.
- **Deck fatigue:** 1 de dano inicial, +1 por aplicação posterior, sem teto; contadores independentes por jogador e persistentes; primeiro turno de cada jogador isento; letal encerra antes da ação. Valores provisórios de balanceamento alpha.
- **Compra:** até duas cartas por início de nova rodada permanece regra do harness; compra por turno não foi definida. Deck de 30 cartas não se esgota normalmente no Bo3 atual só por essa cadência.
- **Catálogo:** 137 modelos históricos; 27 permitidos em alpha e 110 bloqueados; 27 combos (9 alcançáveis, 18 inertes), quatro passivas e dez líderes.
- **Validação:** 135/135 testes; staging 137/27/110; simulação Bo3 A 2–1 B, 72 eventos, seis fatigue ticks e SQLite íntegro; demo combo/passiva/líder aprovada.
- **Integração:** sem Discord/HTTP/frontend/banco publicado/migração/cutover. `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` permanecem byte a byte idênticos à rev. 22.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-deck-fatigue-alpha-v0.2.md`, `docs/card-engine-v2-playable-alpha-validation-v0.4.md` e `sistemas/card_engine_v2/README.md`.

---

# Manifesto atual — revisão rev. 22 (2026-11-28)

- **Baseline:** `soulsbo-main-continuity-2026-11-28-rev21.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev22.zip`.
- **Estado:** Card Engine v2 permanece isolado em alpha; `CardInstance v0.7`/schema 7 ainda é draft não congelado.
- **Ciclo de vida:** auditoria confirma remoção física exata, causas aprovadas, contadores separados, proteção, Vingança causal e arquivamento sem baixa/Vingança. Não existe HP individual ou evento de morte de unidade.
- **Deck fatigue:** contrato candidato v0.1 criado a partir de `CARD_GAME_REDESIGN.md`; parâmetros de dano e cadência permanecem em aberto. Referência matemática isolada e não conectada ao controlador.
- **Catálogo:** 27 cartas alpha; 110 modelos históricos bloqueados. 27 combos registrados (9 alcançáveis, 18 inertes), quatro passivas e dez líderes alpha.
- **Validação:** 130/130 testes; staging 137/27/110 aprovado; regressão Bo3 A 2–1 B, 60 eventos, SQLite íntegro; demo combo/passiva/líder, 25 eventos, SQLite íntegro.
- **Integração:** nenhuma; sem Discord/HTTP/frontend/banco publicado/migração/cutover. `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` permanecem byte a byte idênticos à rev. 21.
- **Limites:** nenhuma mudança de runtime/ruleset/schema/SQL; sem HP individual; sem deck fatigue ativa; valores de dano, incremento, teto, timing e cadência aguardam decisão.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-deck-fatigue-contract-v0.1.md`, `docs/card-engine-v2-lifecycle-audit-v0.1.md`, `docs/card-engine-v2-sacrifice-match-alpha-v0.1.md` e `sistemas/card_engine_v2/README.md`.

---

# Manifesto atual — revisão rev. 20 (2026-11-28)

- **Baseline:** `soulsbo-main-continuity-2026-11-27-rev19.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev20.zip`.
- **Estado:** Card Engine v2 isolado em alpha; grupos A–F aprovados; contrato CardInstance v0.7/schema 7 ainda é draft.
- **Catálogo alpha:** 27 IDs explícitos hash-pinned; staging 137 modelos, 27 alpha-only e 110 bloqueados.
- **Combos/passivas/líderes:** 27 combos registrados (9 alcançáveis, 18 inertes), quatro passivas e dez handlers de líderes em alpha.
- **Combate:** novo ruleset v0.2; 20 de vida por jogador; dano calculado por diferença de poder efetivo em cada fileira no fechamento da rodada; vida zero encerra e letal simultâneo empata.
- **Validação:** 117/117 testes; staging 137/27/110 aprovado; regressão Bo3 A 2–1 B com 16 operações/60 eventos; demonstração combo/passiva/líder aprovada com 25 eventos.
- **Integração:** nenhuma; os arquivos legados protegidos permanecem byte a byte idênticos; sem acesso ao banco publicado, migração ou cutover.
- **Limites:** não há atributos independentes de ataque/armadura/HP por unidade; combate não destrói unidades automaticamente; sacrifício normal no controlador e deck fatigue continuam pendentes.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-combat-alpha-v0.1.md` e `sistemas/card_engine_v2/README.md`.

---

# Manifesto atual — revisão rev. 19 (2026-11-27)

- **Baseline:** `soulsbo-main-continuity-2026-11-27-rev18.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-27-rev19.zip`.
- **Estado:** Grupos A–F aprovados; Card Engine v2 continua alpha isolada, sem integração de produção.
- **Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.
- **Catálogo alpha:** 27 cartas em allowlist v0.3 hash-pinned; o staging mantém 137 modelos, 27 alpha-only e 110 bloqueados.
- **Combos:** 27 definições carregadas; nove alcançáveis pelas tags da allowlist atual e 18 ainda inertes por falta de fontes de tags.
- **Passivas/líderes:** quatro passivas de facção e dez handlers de líderes implementados em alpha.
- **Efeitos de entrada:** 12 famílias novas da revisão anterior permanecem implementadas.
- **Validação:** 109/109 testes; staging 137/27/110 validado; regressão Bo3 A 2–1 B (16 operações/48 eventos); demo combo/passiva/líder A 20–10 B (21 eventos).
- **Integração:** nenhuma; sem alteração do motor legado, bot, API, frontend ou banco publicado.
- **Guardrails:** 110 modelos permanecem bloqueados; combos sem tags-fonte permanecem inertes; nenhum artefato alpha é release publicada; sem migração/cutover.

Leia primeiro `docs/card-engine-v2-combos-faction-passives-leaders-alpha-v0.1.md`, `sistemas/card_engine_v2/README.md` e `docs/card-game-handoff.md`.

---

---

# Manifesto de continuidade — Grupo C auditado, aguardando aprovação (2026-11-27)

- **Baseline de entrada:** `soulsbo-main-continuity-2026-11-27-rev9.zip` (SHA-256 conferido antes da extração).
- **Pacote desta etapa:** `soulsbo-main-continuity-2026-11-27-rev10.zip`.
- **Estado:** Grupos A e B aprovados; Grupo C auditado, mas não aprovado; Grupos D/F/E permanecem abertos.
- **Contrato:** `CardInstance v0.3` permanece draft não congelado. Não foi criado schema v4 nesta etapa.
- **Artefatos novos:** relatório, matriz de 10 decisões, fixture ilustrativa, harness e resultado de validação do Grupo C em `docs/`.
- **Validação:** Grupo C 43/43; Grupo B 20/20; CardInstance v0.3 + Grupo B 42/42; matriz cruzada 272/272; Grupo A 30/30; estados candidatos 41/41; remoção/ressurreição 49/49.
- **Achados:** limpeza de rodada percorre somente o campo em rodadas não terminais; fechamento terminal retorna antes da limpeza; bônus de unidade já removida pode persistir no descarte; resistência climática é escalar; proteção e retorno têm regras distintas por efeito.
- **Política proposta:** evento `round_close` após snapshot de resultado; grants/aplicações com origem e expiração; resistência intrínseca separada de modificadores temporários; regras de escudo, bônus e ressurreição explícitas por política/efeito.
- **Status das decisões C:** CI-008/009, BUF-008/009/010/011/014 e RSRX-07/08/10 permanecem `PENDING_OWNER_APPROVAL`.
- **Integridade:** cinco arquivos novos e três arquivos de continuidade atualizados, todos em `docs/`; nenhum arquivo removido ou alterado fora de `docs/`. Runtime, catálogo ativo, candidates, DB, API, bot e frontend permanecem intactos.
- **Guardrails:** não congelar schema, não migrar partidas, não alterar DB/API/frontend, não integrar resolvedores e não substituir o motor antigo nesta fase.

---

# Manifesto de continuidade — revisão após aprovação do Grupo B (2026-11-27)

- **Baseline de entrada:** `soulsbo-main-continuity-2026-11-27-rev8.zip`.
- **Estado:** Grupo A e Grupo B aprovados; `CardInstance v0.3` especificado, ainda candidato/não congelado.
- **Aprovação B:** CI-005, CI-011, BUF-001/A, BUF-002, BUF-012, RSRX-03 (causas finais no Grupo F), RSRX-05 (separação causal somente).
- **Raridade:** classificação apenas no novo sistema. Não modifica poder de efeito, thresholds, quantidade/seleção de alvos, duração nem outputs mecânicos. Sem `RARITY_EFFECT_BUDGET` no novo engine.
- **Artefatos:** aprovação B, contrato CardInstance v0.3, schemas v3/manifesto/evento, exemplo causal e validação 42/42.
- **Runtime:** nenhuma alteração fora de `docs/`; não houve integração, migração, DDL, API, frontend nem alteração do catálogo ativo.
- **Pendências:** Grupos C, D, F e E; releases reais de catálogo/balanceamento ainda não publicados; números EFP/custo/orçamento/cortes seguem não aprovados.

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

# Estado mais recente — contrato candidato `CardInstance` v0.1 (2026-11-27)

- Baseline de entrada: `soulsbo-main-continuity-2026-11-27-rev3.zip`; pacote desta etapa: `soulsbo-main-continuity-2026-11-27-rev4.zip`.
- Status: `CANDIDATE_FOR_REVIEW_NOT_APPROVED`; nenhuma decisão CI-001…CI-014 foi aprovada e nenhuma integração foi feita.
- Artefatos adicionados: `docs/card-game-card-instance-contract-v0.1.md`, `docs/card-game-card-instance-match.schema.v1.json`, `docs/examples/card-instance-match.example.v1.json`, `docs/card-game-card-instance-contract-validation-v0.1.json` e `docs/scripts/test-card-instance-contract-v0.1.py`.
- Contrato proposto: `card_id` (modelo), `exemplar_id` (registro de coleção do proprietário) e `instance_id` UUIDv4 (ocorrência única na partida); registry central de instâncias; quatro zonas com referências; unicidade global; seleção por `target_instance_id`; transições atômicas/idempotentes com política `policy.identity_only`; `state_revision` monotônica e `expected_revision` como precondição contra ações obsoletas. CAS/serialização persistente permanece decisão aberta em CI-014.
- Validação: 30/30 casos candidatos passaram; schema meta-validado como Draft 2020-12; exemplo válido. Regressões: identidade/ciclo de vida 17/17; TUI 12/12; remoção/ressurreição 49/49; contrato canônico 35/35. Escopos independentes.
- Somente `docs/` mudou. Nenhum arquivo funcional, resolvedor candidato, banco, API, catálogo ativo ou frontend foi alterado.
- Próxima etapa: revisar decisões CI-001…CI-014 e políticas BUF/RSRX de limpeza/preservação; ainda sem autorização para integração ou substituição do motor antigo.

### Histórico por arquivo — CardInstance v0.1

| Arquivo | Alteração | Impacto | Validação |
|---|---|---|---|
| `docs/card-game-card-instance-contract-v0.1.md` | Novo contrato | Define identidade, snapshot, zonas, transições, migração e decisões abertas | Revisão contra baseline rev. 3 |
| `docs/card-game-card-instance-match.schema.v1.json` | Novo schema candidato | Estrutura do envelope e instância | Draft 2020-12; schema válido |
| `docs/examples/card-instance-match.example.v1.json` | Novo exemplo | Mostra identidade distinta de cópias do mesmo modelo | Validado contra schema |
| `docs/scripts/test-card-instance-contract-v0.1.py` | Novo harness isolado | Valida invariantes, transição atômica/idempotente e controle de revisão em memória | 30/30 |
| `docs/card-game-card-instance-contract-validation-v0.1.json` | Novo resultado | Registra evidências e limites | 30/30, zero falhas |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md` | Atualizados | Coloca CardInstance como etapa atual e orienta a próxima sessão | Conferência de caminhos e status |

---

# Estado mais recente — identidade física e ciclo de vida de unidades v0.1

- Data: 2026-11-27
- Resultado: **17/17 assertions aprovadas**; a aprovação significa reprodução da afirmação/gap, não aprovação do comportamento.
- Status: `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`.
- Escopo: identidade `card_id`/`exemplar_id`/`instance_id`; gravação e carregamento de deck; preparação de snapshots; seleção de alvo; remoção, retorno à mão, ressurreição e fim de rodada.
- Evidência: `docs/card-game-identity-lifecycle-audit-v0.1.md/.json` e `docs/scripts/audit-card-identity-lifecycle-v0.1.py`.
- Achados: o endpoint atual bloqueia modelos repetidos em novos decks, mas o snapshot loader não revalida a unicidade; `preparar_carta()` perde `exemplar_id` do caminho padrão; `novo_estado()` não cria `instance_id`; alvo e frontend usam `id`; remoção estrutural por dicionário pode duplicar uma referência em zonas; retorno/ressurreição têm políticas de limpeza diferentes; candidato não valida colisões globais de `instance_id`.
- Regressões direcionadas: identidade/ciclo de vida 17/17; TUI 12/12; TGT 15/15; BUF base 14/14; sequência 10/10; remoção/ressurreição 49/49; identidade 33/33; ciclo de vida 7/7; estados 41/41; catálogo 23/23. Escopos não somáveis.
- Limites: fixtures sintéticas e análise estática; nenhum DB real ou ambiente de produção consultado. A possibilidade de snapshots antigos/malformados não prova existência de registros reais.
- Alterações: três artefatos novos em `docs/` (relatório, JSON e script); README, handoff e manifesto atualizados. Nenhum arquivo funcional alterado.
- Próxima etapa: especificar `CardInstance`, unicidade global, transições de zona, payload `target_instance_id` e política de limpeza/preservação por efeito. Motor legado permanece intocado.

### Histórico por arquivo — identidade física/ciclo de vida v0.1

| Arquivo | Alteração | Impacto | Validação |
|---|---|---|---|
| `docs/card-game-identity-lifecycle-audit-v0.1.md` | Novo relatório | Registra os caminhos de identidade, estados de zona, achados e requisitos candidatos | Revisão contra handlers e 17/17 |
| `docs/card-game-identity-lifecycle-audit-v0.1.json` | Novo resultado estruturado | Preserva os 17 casos, contagens, fontes e limites | 17/17, zero falhas |
| `docs/scripts/audit-card-identity-lifecycle-v0.1.py` | Novo harness read-only | Reproduz identidade de deck, remoção, retorno e gaps do candidato | 17/17 |
| `docs/README-PACOTE-CONTINUIDADE.md` | Atualiza prioridade de leitura | Nova etapa fica como entrada prioritária | Conferência de caminhos |
| `docs/card-game-handoff.md` | Atualiza handoff | Próxima sessão começa pela identidade física e ciclo de vida | Conferência de achados e restrições |
| `docs/PACOTE-MANIFESTO.md` | Acrescenta esta entrada | Registra alteração documental e testes | Conferência de arquivos |

---

# Estado mais recente — auditoria de paridade UI/alvo v0.1

- Data: 2026-11-27
- Resultado: **12/12 verificações aprovadas**.
- Status: `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`.
- Escopo: serialização de alvos, `target_id`, filtro de fileira na UI, métrica exibida/validada, fallbacks automáticos, alvos secundários de Égide/Passo e opções de relíquias.
- Evidência: `docs/card-game-manual-target-ui-parity-audit-v0.1.md/.json` e `docs/scripts/audit-manual-target-ui-parity-v0.1.py`.
- Achados: fallback automático varia por carta; Execução exibe poder-base + bônus mas valida poder efetivo; Lágrima Sagrada/Réquiem exibem poder + bônus, mas validam poder-base; Égide/Passo afetam secundários sem escolha individual; `target_id` não distingue IDs repetidos; Algemas pode consumir sem efeito em bônus 0.
- Alterações: documentação e script de auditoria apenas. Nenhum arquivo funcional alterado.
- Próxima etapa: auditar ciclo de vida e identidade de instância em recuperação/retorno de unidades.
- Regressões repetidas sem falhas: TUI 12/12; TGT 15/15; BUF base 14/14; cruzada 9/9; sequência 10/10; estados 41/41; remoção/ressurreição 49/49; combos/passivas 87/87; líderes 22/22; efeitos 13/13 e 39/39; contrato 35/35; catálogo 23/23; semântica 11/11. Escopos não somáveis.
- Integridade comparativa: nenhuma diferença fora de `docs/`; os cinco módulos centrais mantêm hashes idênticos ao pacote de entrada da continuidade.

---

# Estado mais recente — seleção de alvos e escopo de fileira v0.1 (2026-11-27)

- Adicionados `docs/card-game-target-selection-row-scope-audit-v0.1.md/.json` e `docs/scripts/audit-target-selection-row-scope-v0.1.py`.
- **15/15 verificações aprovadas** com funções reais do motor legado e fixtures sintéticas: poder efetivo, escopo global/por fileira, filtros por estado/escudo, ranking por bônus bruto, fallback e seletores de líderes.
- Confirmado que alvos em campo são filtrados por `row` corrente; `fileira` conserva referência original. Gravidade do Flagelo move `row` e mantém `fileira`.
- Os critérios de ranking variam por efeito. Cisalhamento Gravitacional usa bônus bruto; os seletores dos líderes testados e várias identidades usam poder efetivo. Empates seguem a ordem atual do array.
- Tiro de Cobertura/Contrafogo permanecem branches de identidade filtrados por V18; `v75_blood_pursuit` e `v75_moon_ward` não têm binding individual ativo. Não foram contados como mecânicas ativas.
- Adendo TGT incluído em `card-game-buffs-decision-register-v0.1.md`: BUF-006, BUF-008 e BUF-013 continuam abertos.
- **Runtime preservado:** nenhum handler, carta, catálogo, banco, API ou frontend alterado. Status `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`.

### Histórico por arquivo — seleção de alvos v0.1

| Arquivo | Alteração | Impacto | Validação |
|---|---|---|---|
| `docs/card-game-target-selection-row-scope-audit-v0.1.md` | Novo relatório | Formaliza métricas, filtros, escopo de fileira, fallback e requisitos candidatos | Revisão contra os handlers ativos |
| `docs/card-game-target-selection-row-scope-audit-v0.1.json` | Novo resultado estruturado | Preserva evidência por caso | 15/15 |
| `docs/scripts/audit-target-selection-row-scope-v0.1.py` | Novo harness read-only | Reproduz 15 casos usando funções reais | 15/15 |
| `docs/card-game-buffs-decision-register-v0.1.md` | Adendo TGT | Acrescenta evidência para BUF-006/008/013 sem aprovar decisão | Conferência documental |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md` | Atualizam a entrada principal | Preservam ponto de continuidade | Conferência dos caminhos |

---

# Estado mais recente — auditoria da família de sequência e estado `last_row` v0.1 (2026-11-27)

- Criados `docs/card-game-sequence-power-state-audit-v0.1.md/.json` e `docs/scripts/audit-sequence-power-state-v0.1.py`.
- **10/10** assertions aprovadas. O teste reproduz as três habilidades genéricas ativas (`encadeamento`, `adaptacao`, `quebra_ritmo`) e o ciclo de vida de `player.last_row`.
- Evidência: `last_row` é por jogador e significa a fileira da última unidade jogada com sucesso. É lido antes da resolução da unidade atual; atualizado após a anexação; não muda por movimento (`gwent_passo`), carta especial ou remoção; é limpo ao iniciar a rodada seguinte.
- BUF-008 recebeu evidência adicional e recomendação candidata para distinguir `current_row`, `base_row`, histórico de movimento e `last_unit_play_row`. Não foi aprovada regra/schema.
- `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` não foram editados. Nenhuma habilidade histórica foi reativada; aliases inativos permanecem arquivados.
- Regressões reexecutadas nesta continuidade: buffs 14/14; matriz cruzada 9/9; sequência 10/10; estados 41/41; remoção/ressurreição 49/49; combos/passivas 87/87; líderes 22/22; comportamento genérico 13/13; contrato 35/35; catálogo 23/23; auditoria semântica 11/11. Cada suite tem escopo próprio.
- Pacote de continuidade esperado após esta etapa: **276 arquivos + 15 entradas de diretório (291 entradas ZIP)**. Foi preservado o estado do pacote anterior e adicionados três artefatos da auditoria de sequência; nenhum arquivo foi excluído. A validação final de CRC do ZIP passou sem erros (`testzip() = None`; `unzip -t` sem erros).
- O único arquivo de ambiente empacotado é `.env.r2.example`; não há `.env` real, banco local, cache Python ou bytecode. Os campos de credencial desse exemplo estão vazios.
- SHA-256 dos cinco arquivos funcionais de referência, verificados idênticos ao pacote de continuidade anterior:
  - `sistemas/gwent.py`: `f69e8865759862ddc5bef9ff26ee2ddb43bcfbe33d3e61c985d4b118c6e42383`
  - `sistemas/cartas.py`: `3bed48cbd496de431d92b76653518bda54a59ae5ee7ec8586b448b9fd19a0192`
  - `bot.py`: `a735b2380176a5871f45770d99489825c587033d4a0d760b48b108a6e2a885ff`
  - `database.py`: `ead936a2813335e5a98b31276a9e08ea6dc3a6121543300dd24decc7d69a3ed2`
  - `site/app.js`: `9aafa6ba1ef2641fce9ab169192b27d28b92d2b92ee15881ca5db9984b39386b`
- Status: `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`. Testes sintéticos; sem avaliação de produção, UI, persistência ou equilíbrio.

### Histórico por arquivo — auditoria de sequência v0.1

| Arquivo | Alteração | Impacto | Validação |
|---|---|---|---|
| `docs/card-game-sequence-power-state-audit-v0.1.md` | Novo relatório com semântica, evidências e decisões abertas | Distingue histórico de jogada da posição atual | 10/10 |
| `docs/card-game-sequence-power-state-audit-v0.1.json` | Novo resultado estruturado | Evidência reproduzível por caso | 10/10, zero falhas |
| `docs/scripts/audit-sequence-power-state-v0.1.py` | Novo harness read-only | Reproduz dez cenários com funções do legado | 10/10 |
| `docs/card-game-buffs-decision-register-v0.1.md` | Atualiza BUF-008 | Registra o histórico como estado distinto por jogador | Revisão técnica, recomendação não aprovada |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md` | Atualiza ponto de continuidade | A próxima sessão abre pela etapa correta | Conferência documental |

---

## Etapa anterior — matriz cruzada de buffs e interações v0.1 (2026-11-27)

- Adicionados `card-game-buffs-cross-interactions-v0.1.md/.json` e `scripts/audit-buffs-cross-interactions-v0.1.py`. A matriz cobre nove cruzamentos entre buffs, fileiras, clima, estados negativos, escudo, sacrifício, raridade, combos e passivas.
- Criado `card-game-buffs-decision-register-v0.1.md`, consolidando BUF-001…BUF-014 com evidência, alternativas, recomendação candidata e dependências. As 14 decisões permanecem abertas; não houve aprovação tácita.
- Resultado direcionado: **9/9**. A bateria anterior de buffs permanece 14/14. Suites de regressão executadas: estados 41/41; remoção/ressurreição 49/49; combos/passiva 87/87; líderes 22/22; comportamento genérico 13/13; contrato 35/35; catálogo 23/23; auditoria semântica 11/11. Cada suite tem escopo distinto. Auditoria semântica reexecutada isoladamente: 11/11; a chamada anterior combinada excedeu o tempo, mas a execução isolada confirmou o resultado.
- Achados centrais: clima/estados alteram seletores por poder efetivo; `row` corrente governa combos e buffs de fileira após movimento; `last_row` não muda com movimento; ordem identidade → combo → raridade → passiva; sacrifício com Preço em Sangue ignora escudo; remoção bloqueada por escudo não dispara Vingança.
- `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` não foram editados. Apenas documentação e scripts/resultados de auditoria foram adicionados ou atualizados. Nenhuma decisão BUF-001…BUF-014 foi aprovada nesta etapa.
- O ZIP desta entrega é uma atualização documental/diagnóstica; não contém implementação de substituição do motor. Contagem final, CRC e hashes dos arquivos funcionais serão registrados após empacotamento.

### Histórico por arquivo — matriz cruzada e registro de decisões v0.1

| Arquivo | Alteração | Motivo/impacto | Validação |
|---|---|---|---|
| `docs/card-game-buffs-cross-interactions-v0.1.md` | Novo documento com nove cruzamentos, ordem de resolução, dependências de contrato e decisões abertas | Tornar explícitas interações entre famílias sem aprovar regra nova | Revisão com funções do runtime e 9/9 asserts |
| `docs/card-game-buffs-decision-register-v0.1.md` | Novo registro das 14 decisões BUF | Tornar opções, impactos e recomendações rastreáveis sem aprovação automática | Conferido contra auditoria base e matriz cruzada |
| `docs/card-game-buffs-cross-interactions-v0.1.json` | Novo resultado estruturado | Preservar evidência reprodutível | 9/9, zero falhas |
| `docs/scripts/audit-buffs-cross-interactions-v0.1.py` | Novo harness sintético read-only | Reproduzir cruzamentos sem alterar runtime | 9/9 |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md` | Estado e leitura atualizados | Próxima sessão começar pela etapa correta | Conferência de links e resultados |

---

# Estado mais recente — interações cruzadas de remoção, sacrifício e ressurreição v0.1 (2026-11-27)

- Auditoria cruzada registrada em `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md`, com 12 interações: escudo, sacrifício, Vingança, Devorar, Rykard, ordem de combo/ressurreição, cópias iguais, Esgar, estados residuais e recuperação para mão.
- O resolvedor candidato `sistemas/card_removal_resurrection_candidate.py` foi ajustado para reconhecer `effect_id` canônico singular `effect.vengeance_on_removal`; aliases `effect_ids` e `habilidade="vinganca"` permanecem somente por compatibilidade.
- Seis testes cruzados foram adicionados à suíte específica: total **49/49**. Confirmam: Vingança em Devorar não buffa a carta que ainda não entrou; Rykard soma +1 Vingança e +2 do líder (+3); unidade ressuscitada só contribui para combos em jogadas futuras; round-trip limpa estados no resolvedor candidato.
- Validações de outras etapas reexecutadas em separado: motor legado 251/251 (oito suites), stateful 12/12, contrato 35/35, estado negativo 41/41, catálogo de efeitos 23/23, auditoria semântica 11/11 e tooling de produção 7/7. Não somar esses números como casos únicos.
- **Runtime:** `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` mantidos byte a byte iguais ao ZIP recebido; o resolvedor continua isolado e não é importado no jogo. Nenhum DB, API, frontend, imagem ou carta foi migrado.
- As decisões sobre limite da Execução, Devorar sem alvo, Vingança no sacrifício, acumulação Vingança+Rykard, limites/bônus/fileiras de retorno e `instance_id` permanecem pendentes.
- Pacote mestre desta revisão: **266 arquivos + 15 diretórios (281 entradas)**; CRC do ZIP validado. Foram excluídos caches Python, bytecode, `.env` real, bancos locais, logs, fontes tipográficas e chaves privadas; `.env.r2.example` permanece apenas com valores secretos vazios.

### Histórico por arquivo/função/campo/motivo/impacto

| Arquivo | Função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `sistemas/card_removal_resurrection_candidate.py` | `_has_vengeance()` | Reconhece `effect_id` singular e aliases legados | Alinhar ao contrato canônico | Apenas resolvedor candidato | 49/49 |
| `data/card_game/removal-resurrection-registry-candidate.v1.json` | `on_remove_effects` | Inclui `canonical_check` e `compatibility_check` | Documentar a transição para `effect_id` | Dados candidatos | Schema + 49/49 |
| `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` | seis novos testes | 43 → 49 | Cobrir sobreposições e ordem de resolução | Suite local de auditoria | 49/49 |
| `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` | documento novo | 12 interações cruzadas | Tornar a semântica reproduzível | Documentação | Revisão cruzada |
| `docs/card-game-removal-resurrection-validation-v0.1.md/.json` | relatório | Atualiza 43 → 49, hashes e resultados | Manter prova reproduzível | Documentação | JSON + 49/49 |
| `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` | seção 4.1 | Adiciona ordem e relações cruzadas | Explicitar decisões pendentes | Documentação | Revisão cruzada |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md` | entrada/estado/histórico | Atualiza ponto de continuidade | Próximo chat começa pelo estado correto | Documentação | Links e pacote conferidos |

---

# Estado mais recente — revisão de remoção, sacrifício e ressurreição v0.1 (2026-11-27)

**Status:** proposta executável isolada, não aprovada e não conectada ao runtime. O pacote contém uma matriz de nove atribuições e um resolvedor de referência que não é importado por `sistemas.gwent`.

- Artefatos: `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md`, `data/card_game/removal-resurrection-registry-candidate.v1.json`, schema Draft 2020-12 correspondente, `sistemas/card_removal_resurrection_candidate.py`, `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` e relatório de validação `.md/.json`.
- Evidência: `_remover_unidade` bloqueia por escudo salvo sacrifício; sucesso limpa escudo/status, descarta, incrementa `baixas` e dispara Vingança; Execution cap é sempre 6; Devorar sem alvo é no-op; Esgar filtra todas as cópias de um mesmo `id`; remoção por igualdade de dicionário pode duplicar uma instância entre tabuleiro e descarte; Ressurgir/Réquiem não limpam status explicitamente; Lágrima Sagrada devolve à mão.
- Validação: **43/43** testes da etapa, incluindo schema, resolver candidato e reproduções controladas do motor legado. Não são testes de produção, nem simulações de equilíbrio.
- Runtime: `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js` e outros handlers permaneceram intocados nesta etapa. Não houve migração de `instance_id`, nem integração do resolvedor candidato.
- Pendências: limite da Execução no novo sistema; política sem alvo de Devorar; Vingança e contador em sacrifício; acumulação de Rykard; limites de retorno; bônus/fileira de retorno; identidade física `instance_id` no schema de exemplares.

### Histórico por arquivo — etapa atual

| Arquivo | Campo/função | Alteração e motivo | Impacto | Validação |
|---|---|---|---|---|
| `data/card_game/removal-resurrection-registry-candidate.v1.json` | políticas e atribuições | Centraliza nove operações e candidatos para corrigir cópias e estados | Somente dados, não runtime | Schema/43 testes |
| `data/card_game/removal-resurrection-registry.schema.v1.json` | schema | Valida o registry e sua seção de normalização candidata | Ferramenta de validação | Draft 2020-12 |
| `sistemas/card_removal_resurrection_candidate.py` | remoção/retorno/recuperação | Novo resolvedor isolado com seleção por instância | Não integrado ao motor | 43/43 |
| `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` | suíte | 43 casos reproduzíveis, incluindo os bugs legados | Auditoria somente | 43/43 |
| `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` | relatório | Fontes, linhas, semântica e decisões | Documentação somente | Revisão técnica |
| `docs/card-game-removal-resurrection-validation-v0.1.md/.json` | resultado | Registra contagem, comandos e limites | Documentação/relatório | JSON validado |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `data/card_game/README.md` | estado/ordem | Atualiza ponto de entrada do próximo chat | Continuidade documental | Caminhos conferidos |

---

# Etapa anterior — auditoria dos quatro estados negativos v0.1 (2026-11-27)

A revisão cobre Geada, Podridão Escarlate, Sangramento e Loucura Frenética. Foram criados quatro perfis de estado, 15 aplicações (sete especiais, cinco identidades, dois líderes e uma relíquia) e cinco caminhos de purificação (dois líderes, uma identidade, um especial e uma relíquia). O registry permanece `CANDIDATE_FOR_REVIEW_NOT_APPROVED`; a proposta não está conectada ao runtime.

- `docs/card-game-status-effects-review-v0.1.md` documenta semântica legado, alvos, aplicadores, purificadores, amplificação por raridade e os cinco defeitos/decisões centrais.
- `data/card_game/status-registry-candidate.v1.json` e `status-registry.schema.v1.json` definem a proposta e seu schema Draft 2020-12.
- `sistemas/card_status_candidate.py` é um resolvedor de referência isolado; não é importado por `sistemas.gwent`.
- `docs/scripts/test-card-status-candidate-v0.1.py` passou 41/41; contrato 35/35; catálogo 23/23; auditoria semântica 11/11; motor legado 251/251 em oito suites; partidas stateful 12/12. Todos são resultados de escopos distintos. O ZIP final desta revisão contém 258 arquivos, 18.328.673 bytes (aprox. 17,48 MiB), CRC validado.
- Os cinco arquivos funcionais principais (`sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`) foram comparados com as entradas equivalentes do ZIP mestre aberto no início desta etapa e permaneceram byte a byte iguais. Nenhum banco, API, frontend, imagem ou handler legado foi alterado.
- Limite: os 41 testes da proposta verificam o resolvedor de marcas/limiares/poder/purificação e os metadados de mapeamento; não implementam ainda seletores completos de alvos nem os efeitos colaterais próprios das identidades. Não provam equilíbrio competitivo.

### História detalhada desta revisão

| Arquivo | Função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `data/card_game/status-registry-candidate.v1.json` | quatro estados, `applications`, `cleansers` | Novo registry candidato com perfis, cap, limiares, 15 origens e cinco purificadores | Centralizar os estados sem duplicar suas regras no futuro catálogo | Dados candidatos, runtime inalterado | Schema e testes 41/41 |
| `data/card_game/status-registry.schema.v1.json` | schema Draft 2020-12 | Novo contrato de status | Validar estados e operações de aplicação/purificação | Apenas validação de dados | `check_schema` e instância aprovados |
| `sistemas/card_status_candidate.py` | funções de carga, validação, aplicação, poder efetivo e limpeza | Novo resolvedor de referência isolado | Ensaiar semântica proposta sem alterar o motor | Não importado por `sistemas.gwent` | 41/41 e `py_compile` |
| `docs/scripts/test-card-status-candidate-v0.1.py` | 41 testes | Nova suite de esquema, transições, cap, purificação e reprodução de bugs legados | Evitar regressões e demonstrar discrepâncias | Ferramenta local | 41/41 |
| `docs/card-game-status-effects-review-v0.1.md` | revisão das quatro condições | Novo relatório de evidência e proposta | Tornar condições, duração e raridade explícitas | Documentação somente | Conferência com fonte/registry |
| `docs/card-game-status-effects-validation-v0.1.md/.json` | validação/hash | Novo relatório estruturado | Registrar resultados e limites da etapa | Documentação somente | JSON e hashes conferidos |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `data/card_game/README.md`, `docs/PACOTE-MANIFESTO.md` | estado, ordem de leitura, próximos passos e histórico | Estado dos status promovido ao topo; catálogo anterior reclassificado como etapa anterior | Permitir que outro chat retome do estado atual sem seguir a ordem obsoleta | Documentação somente | Revisão cruzada e testes reproduzidos |

---


# Estado anterior — consolidação + auditoria semântica de efeitos v0.1 (2026-11-27)

- Candidato: 54 famílias (36 unit, 12 special, 6 relic), 59 aliases genéricos/especiais/relíquias, 22 identidades ativas, 27 combos, 10 líderes e quatro passivas. Não aprovado e não conectado ao runtime.
- Auditoria AST: 59 habilidades genéricas = 56 branches diretos, dois hooks de ciclo de vida e um sem handler (`sobrevivente`); `gloria` é um hook separado. 22/22 identidades com branch localizado; quatro campos (`devoto`, `legado`, `escolha_ritmo`, `sinergia_faccao`) têm branch sem binding ativo.
- Triagem semântica: 18 famílias HIGH, seis MEDIUM e 30 LOW (classificação heurística de prioridade, não pontuação de poder nem equivalência). `sequence_power` exige `requires_previous_play=true`; `gloria` e `sobrevivente` não são tratados como equivalentes.
- Validação: candidato 23/23; mapa semântico 11/11; contrato 35/35; motor legado 251/251; stateful 12/12; política de combos 32/32. Suites distintas e com escopo próprio. JSON Schemas Draft 2020-12 e validador do registry aprovados.
- Nesta etapa, apenas scripts/relatórios/documentação foram atualizados; nenhum handler/runtime do jogo foi alterado ou removido. Comparação com o ZIP anterior: 15 arquivos de candidato/auditoria foram acrescentados e cinco documentos foram atualizados; os módulos funcionais `bot.py`, `database.py`, `sistemas/cartas.py`, `sistemas/gwent.py`, `sistemas/card_contract.py` e `site/app.js` permanecem byte a byte idênticos.
- O ZIP mestre de entrada para a etapa de estados continha 251 arquivos; os sete artefatos novos listados no histórico foram acrescentados nesta revisão, totalizando 258 arquivos no pacote final.
- Artefatos atuais: `card-game-effect-catalog-decision-v0.1.md`, `card-game-effect-semantic-audit-v0.1.md`, `card-game-effect-catalog-validation-v0.1.md` e seus JSONs. O README de continuidade orienta a nova IA a começar por estes arquivos.

### Histórico detalhado desta revisão

| Arquivo | Função/campo | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `docs/scripts/audit-effect-semantic-groups-v0.1.py` | AST e tabela `HIGH_RISK`/`MEDIUM_RISK` | Mapa apenas estrutural de famílias, sem prioridade coerente com achados manuais | Inclui `round_victory_survivor` como MEDIUM e alinha SEM-004/005/007 com a prioridade da família | Eliminar níveis contraditórios no relatório | Auditoria read-only; runtime intacto | 18 HIGH, 6 MEDIUM, 30 LOW; prioridade de cada achado testada |
| `docs/card-game-effect-semantic-audit-v0.1.md/.json` | 54 famílias, branches, hooks e achados SEM-001…SEM-007 | Havia lacunas e uma divergência de prioridade | Atualiza evidências, diferenças semânticas, classificação e comandos de reprodução em ordem válida | Tornar a revisão reproduzível e autossuficiente | Relatório documental somente | Auditoria gerada; 11/11 regressões |
| `docs/scripts/test-effect-semantic-audit-v0.1.py` | `test_manual_finding_priority_matches_family_review_priority` | Não comparava prioridades manuais à matriz de famílias | Novo assert compara a prioridade de cada achado a cada família citada | Impedir novos desacordos internos | Ferramenta de teste apenas | 11/11 aprovados |
| `docs/scripts/build-effect-catalog-candidate-v0.1.py` | regras de sequência e ciclo de vida | Texto do candidato podia sugerir equivalência entre `gloria` e `sobrevivente` | `requires_previous_play=true` explícito; `sobrevivente` marcado como texto não implementado e sem migração automática; `gloria` separado; inclui semantic audit na reprodução | Não migrar semântica não comprovada | Artefatos de candidato, nenhum runtime | 23/23 estruturais e registry válido |
| `docs/scripts/summarize-effect-catalog-candidate-v0.1.py` e `docs/card-game-effect-catalog-validation-v0.1.md/.json` | agregação e hashes | Só executava suite estrutural | Executa 23 testes estruturais, regenera auditoria AST e executa 11 testes semânticos; inclui hashes/contagens de ambas | Publicar um único resultado atual | Documentação/tooling | `all_checks_passed=true` |
| `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/card-game-mapping-audit.md`, `data/card_game/README.md` | estado atual, ordem de leitura e próximos passos | Não incluíam auditoria semântica detalhada ou tinham contagem anterior | Adiciona o relatório por família, limites, risco heurístico, precondição de sequência e distinção de ciclo de vida | Garantir continuidade de chat | Documentação somente | Revisão cruzada e suites completas |

---

# Manifesto do pacote mestre de continuidade

## Revisão anterior — primeira consolidação do catálogo de efeitos candidato v0.1 (2026-11-27)

A revisão cruzou o catálogo real de `sistemas/cartas.py` e os executores de `sistemas/gwent.py` e produziu uma proposta de registry canônico sem alterar o runtime.

- 54 famílias de efeitos candidatas (36 unidade, 12 especiais, seis relíquias) cobrindo 59 IDs `HABILIDADES` (32 unidade, 21 especial, seis relíquias).
- 59 aliases preservam descrição/nome legados, parâmetros default e cartas atualmente atribuídas.
- 22 identidades ativas mapeadas por carta; 16 suprimem um campo genérico na resolução atual.
- 27 combos importados da política aprovada; 10 líderes e quatro passivas de facção em registros separados.
- 11 IDs de habilidade de unidade não estão atribuídos a nenhuma carta; 18 ramos V18, seis ramos V75, quatro valores de campo não registrados e cinco IDs órfãos de tags foram classificados sem exclusão.
- `gloria` está em três cartas e é hook em `_resolve_round()`; `sobrevivente` está declarado mas não tem handler identificado. Ambos são candidatos a uma regra explícita de sobrevivência após vitória.
- Na primeira consolidação, a suite estrutural passou 21/21; ela foi ampliada posteriormente para 23/23. O registry candidato passou JSON Schema Draft 2020-12 e `validate_effect_registry()`. Os resultados anteriores permanecem: contrato 35/35, comportamento legado 251/251, stateful 12/12 e política de combos 32/32, em suites diferentes.

**Não aprovado/não implementado:** os 54 `resolution_handler` são nomes candidatos, não funções. Nenhuma habilidade foi removida do motor, nenhuma carta nova foi atribuída, nenhuma fórmula EFP/custo/raridade foi aprovada e nenhum módulo funcional de runtime foi alterado. Próxima etapa: revisar equivalência semântica em cada família e então classificar `keep/merge/redesign/remove`.

### Arquivos adicionados/gerados

- `data/card_game/effect-registry-candidate.v1.json`
- `data/card_game/legacy-effect-aliases-v0.1.json`
- `data/card_game/leader-registry-candidate.v1.json`
- `data/card_game/faction-passives-candidate.v1.json`
- `docs/card-game-effect-catalog-decision-v0.1.md/.json`
- `docs/card-game-effect-catalog-validation-v0.1.md/.json`
- `docs/scripts/build-effect-catalog-candidate-v0.1.py`
- `docs/scripts/test-effect-catalog-candidate-v0.1.py`
- `docs/scripts/summarize-effect-catalog-candidate-v0.1.py`

| Arquivo | Função/campo | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/build-effect-catalog-candidate-v0.1.py` | `FAMILIES`, `build()` | Gera famílias parametrizadas, aliases, overrides de identidade, combos, líderes e passivas; corrige a origem dos registries para `sistemas.gwent` | Tornar a consolidação completa e reproduzível a partir das fontes reais | Ferramenta de migração apenas; não altera runtime | Registry válido; mapeamentos 59/22/27/10/4 |
| `data/card_game/effect-registry-candidate.v1.json` | `effects`, `combos` | Cria 54 famílias candidatas e 27 combos | Centralizar metadados em contrato tipado | Não consumido pelo runtime; handlers ainda não existem | Schema Draft 2020-12 e validador Python aprovados |
| `data/card_game/legacy-effect-aliases-v0.1.json` | aliases e overrides | Preserva 59 IDs, descrições, atribuições, params, 22 identidades e ramos antigos | Garantir rastreabilidade antes de qualquer remoção | Apenas ponte de migração | Aliases e parâmetros validados |
| `data/card_game/leader-registry-candidate.v1.json`, `faction-passives-candidate.v1.json` | registros separados | Estrutura candidatos de 10 líderes e quatro passivas | Separar slot de líder e regra global da habilidade individual | Não ligado ao runtime | 10/10 líderes, 4/4 facções |
| `docs/card-game-effect-catalog-decision-v0.1.md/.json`, `docs/card-game-effect-catalog-validation-v0.1.md/.json` | relatório e validação | Registra famílias, alias por carta, órfãos, pendências, contagens, hashes e testes | Permitir revisão pelo usuário ou outro chat | Documentação | 23/23 testes estruturais, 11/11 semânticos e schema aprovado no estado atualizado |
| `docs/scripts/test-effect-catalog-candidate-v0.1.py`, `audit-effect-semantic-groups-v0.1.py`, `test-effect-semantic-audit-v0.1.py`, `summarize-effect-catalog-candidate-v0.1.py` | suites e agregador | Testa schema, aliases, parâmetros, atribuições, identidade, combos, líderes e passivas | Evitar mapa inconsistente passar para a fase seguinte | Ferramentas locais apenas | 23/23 estruturais; 11/11 semânticos |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `data/card_game/README.md` | status, ordem de leitura, inventário | Atualiza o estado mais recente e a próxima ação autorizada | Manter handoff sem dependência do chat anterior | Documentação | Referências e contagens conferidas |


- Projeto: `soulsbo-main`
- Revisão: 2026-11-27
- Pacote canônico: `soulsbo-main-handoff.zip` (a cópia mais recente substitui a anterior)
- Revisão anterior: 251 arquivos no ZIP mestre de entrada. Pacote desta revisão: 258 arquivos (sem entradas explícitas de diretórios), após incluir sete arquivos novos de auditoria/resolvedor/validação. Inclui a camada canônica v1.1 e os novos schemas, validador, testes e relatórios descritos abaixo. Sem caches, bytecode, banco local, `.env` preenchido, segredos ou arquivos binários de fontes tipográficas.
- Finalidade: permitir que um novo chat/agente assuma o projeto do zero, sem depender do histórico desta conversa.
- Estado funcional atual: a política oficial de combos v0.1 continua implementada em `sistemas/gwent.py`. Nesta revisão foi adicionado `sistemas/card_contract.py`, isolado e ainda não importado pelo runtime antigo; não foram alterados handlers, schema/DB, endpoints/APIs, frontend, catálogo ativo, pipeline de imagens ou arte.
- Estado de validação do jogo: mapa estático das **12 rotas HTTP Gwent** (sem dispatch real), oito suites comportamentais, **251/251 asserts** (32 regressões específicas da política, incluindo `aplicar_jogada(action="play")`); separadamente, **12/12 cenários stateful** aprovados (quatro partidas controladas de três rodadas, snapshots JSON, 137 payloads de catálogo, combo por turno, líder/especial/clima, relíquia, clima manual, snapshot legado e DDL/`state_json` em SQLite `:memory:`). A auditoria pós-política cobre 4.422 pares e 287.430 trincas, zero ativações solo e 2.582/2.582 eventos posteriores com carta participante. HTTP real ainda não foi executado.
- Estado de validação das ferramentas de produção: **7/7 testes locais** em SQLite temporário (incluindo fixture WAL) e cliente S3 simulado; `py_compile` e `--help` dos cinco scripts passaram. Nenhuma fonte real de produção foi acessada. Os scripts operacionais são somente leitura para origem SQLite e R2 (`ListObjectsV2`), e os relatórios são gravados fora do repositório.
- Estado novo da reconstrução: contrato canônico v1.1 e snapshot reprodutível do baseline implementados; 35/35 testes; dois JSON Schemas Draft 2020-12 e exemplos válidos; CLI passou nos fixtures positivo/negativo. Baseline: 137 modelos (110 unidades, 21 especiais, seis relíquias), 15 puras; quota de 30% implica 42. EFP/custo/raridade/teto 32 continuam propostas não aprovadas. Próximo passo: normalizar o registry legado efeito por efeito e ligar cada regra a testes antes de redesenhar cartas. O runbook SQLite/R2 é opcional; o proprietário informou que não há jogadores reais e os dados são de teste.
- Comparação histórica com o ZIP fonte original: 152 arquivos não tipográficos foram comparados; 151 permanecem byte a byte idênticos e a única alteração funcional aprovada está em `sistemas/gwent.py`.
- Comparação com o pacote imediatamente anterior: os 143 arquivos fora de `docs/` permanecem byte a byte idênticos; esta etapa adicionou cinco scripts de auditoria/teste em `docs/scripts/` e atualizou somente documentação e ferramentas de auditoria sob `docs/`.

## Revisão mais recente — contexto operacional de teste informado pelo proprietário (2026-11-27)

O proprietário informou que o jogo ainda não tem jogadores reais; quaisquer usuários/registros existentes são testes realizados por ele. Esta é uma informação declarada, não verificada contra DB, hospedagem, Discord ou R2. Consequência: não é necessário desenhar migrações para preservar economia/progresso de jogadores; pode-se priorizar schema limpo e reset/reseed dos dados de teste quando o escopo estiver definido. O inventário de produção deixa de ser gate obrigatório e passa a ser opcional para recuperar/reutilizar artes e registros. Não apagar automaticamente artes, anexos Discord, bucket R2 ou credenciais.

Foi criado `docs/PROJECT-OPERATING-CONTEXT.md` e atualizado README, handoff e runbook para refletir essa premissa. Nenhum arquivo funcional foi modificado.

| Arquivo | Função/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/PROJECT-OPERATING-CONTEXT.md` | Novo documento | Registra a declaração do proprietário, impactos para reset/migração e salvaguardas para ativos/segredos | Ajustar a estratégia à fase de teste | Habilita reconstrução mais direta; sem autorização irrestrita de exclusão | Revisão documental; status da informação explicitado |
| `docs/README-PACOTE-CONTINUIDADE.md` | Entrada e ordem de leitura | Inclui o contexto e trata inventário SQLite/R2 como opcional | Orientar o próximo chat | Não bloqueia reconstrução à espera de dados reais | Links conferidos |
| `docs/card-game-handoff.md` | Estado e histórico | Reordena os próximos passos; registra que dados são testes segundo o proprietário | Evitar sobreengenharia de migrações | Documentação apenas | Revisão cruzada |
| `docs/card-game-production-audit-runbook-v0.1.md` | Aviso de escopo | Marca o runbook como opcional, voltado à preservação de ativos | Não confundir ambiente hospedado com comunidade de usuários | Nenhum efeito no runtime | Revisão documental |

## Revisão mais recente — preparação da auditoria de produção somente leitura (2026-11-27)

Foram adicionados o runbook `docs/card-game-production-audit-runbook-v0.1.md` e cinco scripts em `docs/scripts/`: `snapshot-sqlite-readonly-v0.1.py`, `audit-production-card-db-v0.1.py`, `inventory-r2-readonly-v0.1.py`, `reconcile-production-card-assets-v0.1.py` e `test-production-audit-tooling-v0.1.py`.

A preparação documenta as quatro origens de arte do código atual: submissões do Ateliê (R2 `atelier/submissions/` e possível BLOB legado), referências do Ateliê/Coliseu em anexos Discord, BLOBs de artes de líderes no SQLite e PNGs do Laboratório no volume `DATA_DIR`. O prefixo R2 `cards/` é cache/CDN, não origem de arte aprovada.

Os utilitários criam snapshot SQLite por `mode=ro`/`query_only`/Backup API; exportam apenas metadados sanitizados; listam R2 usando `ListObjectsV2`, sem baixar ou alterar objetos; e reconciliam hashes contra o bucket primário, recusando inventário filtrado/truncado. Sete testes locais passaram, incluindo fixture WAL com linha ainda não checkpointada e verificação de que o arquivo WAL não mudou. `py_compile`, `--help`, suíte comportamental 251/251 e stateful 12/12 também passaram.

**Limite obrigatório:** não há DB de produção, arquivo `.env` preenchido, credenciais, bucket R2, volume `DATA_DIR` ou sessão privada do Discord no pacote. Nenhuma fonte de produção foi consultada. Não inventar números reais nem incluir snapshot/segredos/relatórios operacionais no ZIP. A próxima ação é executar o runbook no host e compartilhar somente `card-game-production-assets-reconciliation.json` (sanitizado).

| Arquivo | Função/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `docs/scripts/snapshot-sqlite-readonly-v0.1.py` | `create_snapshot()` | Snapshot consistente da origem SQLite em `mode=ro`, `query_only`, `quick_check` e Backup API; saída nova fora do repo com modo 0600 | Obter cópia de leitura sem executar migrações do wrapper `Database.connect()` | Ferramenta local; não altera a origem | Testes em DB temporário padrão e WAL |
| `docs/scripts/audit-production-card-db-v0.1.py` | `build_report()` | Agrega tabelas do jogo e quatro pipelines de arte sem exportar IDs pessoais, prompts, BLOBs, `state_json` ou caminhos locais | Inventário DB sanitizado | Relatório local apenas | Fixture valida agregações e sanitização |
| `docs/scripts/inventory-r2-readonly-v0.1.py` | `_bucket_configs()`, `_client()`, `write_inventory()` | Lista objetos e metadados via `ListObjectsV2`; hashes de chaves, sem download/escrita/exclusão | Inventário R2 com privilégio mínimo | Lê buckets somente quando executado pelo operador | Cliente S3 fake confirma operação única `list_objects_v2` |
| `docs/scripts/reconcile-production-card-assets-v0.1.py` | `reconcile()` | Cruza hashes do DB e R2 primário; recusa inventário filtrado/truncado; classifica candidatos sem apagar | Identificar referências ausentes sem falso positivo do cache público | Relatório sem mutação | Fixtures de match/missing/orphan/scope inválido |
| `docs/scripts/test-production-audit-tooling-v0.1.py` | Sete testes `unittest` | Adiciona teste WAL e mantém testes sintéticos DB/R2 | Provar leitura de dados ainda no WAL e privacidade básica | Harness local | 7/7 aprovados |
| `docs/card-game-production-audit-runbook-v0.1.md` | Runbook novo; `AUDIT_DIR` com `umask` e `chmod 700` | Comandos no host, permissões mínimas, interpretação e política de compartilhamento | Permitir execução real sem expor segredos no chat | Documentação operacional | Comandos revisados contra config/DB/storage do projeto |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/CLOUDFLARE_R2.md`, `docs/PACOTE-MANIFESTO.md` | Estado, quatro pipelines, ordem de leitura e histórico | Registram ferramentas, escopo, limites de produção e próximo passo | Garantir que novo chat não confunda fixtures com produção | Documentação | Revisão cruzada e validação do pacote |

## Revisão mais recente — mapa estático dos contratos HTTP Gwent v0.1 (2026-11-27)

O script `docs/scripts/audit-gwent-http-contracts-v0.1.py` identificou **12 rotas** e gerou `card-game-http-contract-map-v0.1.md/.json`. O mapa cruza registro de rota/handler em `bot.py`, campos e sinais de consumo em `site/app.js`, chamadas do motor, uso de DB e chaves retornadas por `preparar_carta()`.

Achado de custo: o salvamento do deck não soma custo nem aplica orçamento. As rotas podem preencher `payload['custo']` antes de `preparar_carta()`, mas a função reconstrói o dicionário sem `custo`, descartando o valor antes da resposta final. Não corrigir esse contrato até custo/schema/orçamento serem aprovados.

**Limite:** auditoria estática somente. Sem `discord.py` e `aiosqlite`, e instalação bloqueada por falha DNS, não houve `aiohttp.TestClient`, dispatch real, classe `Database`, gateway Discord, navegador ou integração de produção. O relatório não prova comportamento HTTP, autorização ou transações em runtime.

Histórico de alterações por arquivo/função/campo/motivo/impacto: tabela no fim de `card-game-handoff.md` e histórico desta revisão neste manifesto. Os 251 asserts comportamentais e os 12 cenários stateful continuam sendo validações separadas.

## Revisão imediatamente anterior — integração stateful de partidas v0.1 (2026-11-27)

A suíte `docs/scripts/assert-full-match-stateful-v0.1.py` passou **12/12 cenários**, em separado dos 251/251 asserts comportamentais. Foram percorridas quatro partidas controladas de três rodadas pelo motor em memória, snapshots JSON, 137/137 payloads preparados, combo por jogadas normais, líder + carta climática, reset de clima, relíquia, clima manual, snapshot legado e round-trip SQLite de `state_json` usando o DDL extraído de `database.py`. O relatório é `card-game-match-snapshot-integration-v0.1.md/.json`.

A verificação de `bot.py` ↔ `site/app.js` foi estática. Não houve dispatch HTTP, gateway Discord, execução da classe `Database`/`aiosqlite`, browser, convites, partida solo/IA nem produção. O ambiente não possui `discord.py` nem `aiosqlite`; a tentativa de instalar as versões fixadas no `requirements.txt` foi bloqueada por falha de DNS/rede. Nenhum arquivo funcional adicional foi alterado nesta etapa; a única alteração funcional aprovada permanece a política de combos em `sistemas/gwent.py`.

## Estado atual — política de combos aprovada

A política de `card-game-combo-policy-v0.1.md` foi aprovada pelo usuário e implementada: 27 combos com `minimum: 2` instâncias distintas e `priority` única; a carta atual deve contribuir com tag exigida; prioridade crescente decide qual combo ativa; no máximo um combo ativa por jogada; combos pendentes só disparam por participante posterior; bônus individual vai para a carta participante atual e `team_bonus` permanece. Cada combo continua limitado a uma utilização por jogador/rodada pelo estado `synergy_used`.

A alteração funcional está em `sistemas/gwent.py`, nos dados `SYNERGY_COMBOS`, na função `_aplicar_combo_de_cartas()` e nas descrições mecânicas dos combos. Não há migração DB. Partidas já persistidas conservam bônus aplicados antes do patch. EFP, custos, raridades e orçamento de deck permanecem propostas não aprovadas.



## Histórico desta revisão — implementação aprovada da política de combos

| Arquivo | Função/campo/trecho | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `sistemas/gwent.py` | `SYNERGY_COMBOS` (27 definições) | Três combos sem mínimo explícito; sem prioridade declarada; texto não explicitava todos os participantes | `minimum: 2` e `priority` inteiro único em todos os 27; descrições atualizadas para identificar a carta participante | Aplicar a política aprovada: duas instâncias distintas, precedência determinística e participação real | Modifica somente futuras resoluções de combos no motor; bônus, líderes, passivas, DB e APIs não foram migrados | 27 mínimos e prioridades únicos; 32 regressões dedicadas; enumeração pós-patch |
| `sistemas/gwent.py` | `_aplicar_combo_de_cartas()` | Carta com qualquer tag podia recolher combo já completo; ordem do dicionário escolhia; contagem de participantes podia ser implícita | Exige tag atual requerida, todas as tags presentes no campo, mínimo de instâncias distintas, prioridade crescente, no máximo um combo por jogada | Impedir bônus para não participante, ativação solo e precedência incidental | Bônus individual vai à carta participante atual; `team_bonus`, `synergy_used` e reset por rodada preservados | 251/251 asserts em oito suites; auditoria 4.422 pares/287.430 trincas |
| `docs/card-game-combo-policy-v0.1.md`, `docs/scripts/assert-combo-policy-v0.1.py`, `docs/card-game-combo-policy-assertions-v0.1.json` | Nova especificação e regressões | Inexistentes | Contrato oficial e 32 cenários reprodutíveis, incluindo integração pelo `aplicar_jogada()` | Preservar a decisão aprovada e bloquear regressões | Apenas documentação/harness | 32/32 aprovados |
| `docs/scripts/audit-combo-overlap-v0.2.py`, `docs/card-game-combo-overlap-v0.2.md/.json` | Auditoria pós-patch | Apenas diagnóstico v0.1 do defeito original | Nova enumeração com o resolvedor corrigido | Medir o resultado após correção sem apagar baseline | Somente diagnóstico; nenhum efeito adicional no jogo | Zero solo; 2.582/2.582 eventos posteriores participantes |
| `docs/scripts/build-effect-source-map-v0.2.py`, `docs/card-game-effect-source-map-v0.2.json` | Mapa AST atualizado | Índice gerado contra o baseline | Referências AST regeneradas a partir do runtime pós-política | Manter o mapa de evidências sincronizado com o código atual | Somente documentação | 59 genéricas, 22 identidades, 10 líderes, 27 combos |
| `docs/scripts/summarize-card-game-behavior-v0.3.py`, `docs/card-game-behavior-validation-v0.3.md/.json` | Agregador e relatório atual | Sete suites/219 asserts pré-política | Oito suites/251 asserts, incluindo regressões novas | Consolidar estado pós-patch | Somente diagnóstico/documentação | 251/251 aprovados |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/card-game-balance-validation-v0.1.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura, regras e histórico | Indicavam a política de combos como pendente e exibiam métricas pré-patch como atuais | Política registrada como aprovada/implementada; v0.1 marcado histórico; métricas v0.2/v0.3 como atuais | Evitar handoff contraditório | Só documentação; fornece contexto técnico exato ao próximo chat | Links, números, catálogo de combos e SHA conferidos |
| `docs/scripts/assert-full-match-stateful-v0.1.py`, `docs/card-game-match-snapshot-integration-v0.1.md/.json` | Testes stateful e relatório de integração | Suites anteriores cobriam principalmente cenários isolados e não percorriam partidas/snapshots | Adicionados 12 cenários stateful; quatro partidas controladas de três rodadas, 137 payloads, combo, líder, clima, relíquia, snapshot legado e SQLite DDL/state_json | Encontrar defeitos de transição e serialização sem afirmar integração de produção | Apenas testes/documentação; nenhum código funcional alterado | 12/12 cenários; HTTP estático apenas; discord.py/aiosqlite ausentes |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura e pendências | Indicavam partidas completas/snapshots como trabalho futuro | Registram 12/12 stateful concluídos, limites de fixtures e próximo passo HTTP real | Evitar novo chat considerar a integração mais completa do que foi | Somente documentação | Testes e relatório JSON reproduzidos; runtime unchanged |

## Ordem recomendada de leitura

1. `README-PACOTE-CONTINUIDADE.md` — orientação obrigatória para chat novo.
2. `card-game-handoff.md` — estado, quatro blocos da Regra 8, histórico e próximos passos.
3. `card-game-combo-policy-v0.1.md` — regra aprovada e implementada; não redecidir sem pedido.
4. `card-game-behavior-validation-v0.3.md/.json` + `scripts/summarize-card-game-behavior-v0.3.py` — oito suites/251 asserts comportamentais.
5. `card-game-match-snapshot-integration-v0.1.md/.json` + `scripts/assert-full-match-stateful-v0.1.py` — 12/12 cenários stateful, quatro partidas controladas e snapshots; HTTP real permanece pendente.
7. `card-game-combo-overlap-v0.2.md/.json` + `scripts/audit-combo-overlap-v0.2.py` — enumeração pós-correção.
8. `card-game-mapping-audit.md` — baseline histórico com as seções 21 (política) e 22 (integração stateful) como atualizações vigentes.
9. `card-game-effect-source-map-v0.2.json` + `scripts/build-effect-source-map-v0.2.py` — mapa AST do runtime atual; v0.1 é baseline histórico.
10. `scripts/assert-combo-policy-v0.1.py` + `card-game-combo-policy-assertions-v0.1.json` — 32 regressões da política.
11. Suites individuais e relatórios JSON de identidade, genéricas, ciclo de vida, especiais/relíquias, líderes e combos/passivas.
12. `card-game-stale-identity-disposition-v0.1.md/.json` — classificação dos 28 ramos sem associação ativa; recomendações, não remoções.
13. `card-game-card-traceability.md/.csv/.json` — matriz dos 137 modelos do baseline; nenhum redesign dos dados de carta foi aplicado ainda.
14. `card-game-balance-validation-v0.1.md`, `card-game-efp-methodology-v0.2.md`, `card-game-balance-spec-v0.1.md` e `card-game-effect-score-catalog.json` — evidências/propostas quantitativas não aprovadas.
15. `card-game-deck-cost-sampling-v0.2.json` + script e `card-game-combo-activation-v0.1.json` + script — amostragens exploratórias, não simulações competitivas.
16. `card-game-combo-overlap-v0.1.md/.json` — **histórico congelado do defeito pré-patch**. O script v0.1 recusa execução no runtime atual; para estado vigente use v0.2.
17. `card-game-handler-coverage-v0.1.json`, `card-game-effect-runtime-smoke-v0.1.json` e scripts associados — cobertura estática e smoke tests com limites declarados.
18. Os demais arquivos de `docs/` — documentação preexistente; conferir as advertências do handoff antes de tratá-los como regra atual.


## Documentos principais incluídos

- `README-PACOTE-CONTINUIDADE.md` — aviso para chat novo, mensagem inicial sugerida, ordem de leitura e regra de continuidade.
- `card-game-handoff.md` — estado exato, decisões confirmadas, quatro blocos da Regra 8, pendências, histórico e próximos passos.
- `card-game-mapping-audit.md` — mapa do baseline e atualização pós-política: arquivos, funções, APIs, banco, eventos, catálogo de efeitos, líderes, relíquias, arte, falhas de ligação e catálogo atual de combos.
- `card-game-card-traceability.md`, `.csv`, `.json` — matriz individual dos 137 modelos de carta.
- `card-game-effect-score-catalog.json` — scores EFP preliminares; não aprovados.
- `card-game-effect-source-map-v0.1.json` — mapa AST histórico congelado; o gerador v0.1 tem fail-fast no runtime atual.
- `card-game-effect-source-map-v0.2.json` — mapa AST regenerado após a alteração de combos.
- `card-game-efp-methodology-v0.2.md` — decomposição proposta do EFP por componentes, condições, alvos, duração, bloqueios e valor esperado; não aprovada.
- `card-game-balance-spec-v0.1.md` — proposta de poder, pureza, custo, raridade, orçamento, distribuição e lore; não aprovada.
- `card-game-balance-validation-v0.1.md` — limitações metodológicas, amostragens, frequência de combos, cobertura de handlers e próximos passos.
- `card-game-deck-cost-sampling-v0.1.json` — resultado histórico/superado, preservado para rastreabilidade.
- `card-game-deck-cost-sampling-v0.2.json` — amostragem corrigida de custo com/sem relíquia equipada.
- `card-game-combo-activation-v0.1.json` — frequência observada dos 27 combos sob ordem aleatória.
- `card-game-combo-policy-v0.1.md` — política de combos aprovada e implementada.
- `card-game-combo-policy-assertions-v0.1.json` — 32 regressões específicas da política.
- `card-game-combo-overlap-v0.2.md/.json` — auditoria pós-correção do runtime atual.
- `card-game-combo-overlap-v0.1.md/.json` — diagnóstico histórico pré-patch congelado; o script v0.1 tem fail-fast no runtime atual.
- `card-game-handler-coverage-v0.1.json` — relatório estático de catálogo, handlers, identidades antigas e tags órfãs.
- `card-game-effect-runtime-smoke-v0.1.json` — testes de fumaça do motor em estados sintéticos; não representam cobertura total.
- `card-game-effect-behavior-assertions-v0.1.json` — primeira bateria histórica de 13 asserts, preservada como registro da fase inicial.
- `card-game-behavior-validation-v0.2.md/.json` — agregado histórico pré-política, sete suites/219 asserts.
- `card-game-behavior-validation-v0.3.md/.json` — agregado atual pós-política, oito suites/251 asserts.
- `card-game-http-contract-map-v0.1.md/.json` — mapa estático de 12 rotas Gwent; identifica falta de orçamento e perda de `custo` no payload preparado; não executa HTTP.
- `card-game-match-snapshot-integration-v0.1.md/.json` — 12 cenários stateful: quatro partidas controladas, snapshots, preparação de catálogo e DDL SQLite; sem dispatch HTTP real.
- `scripts/assert-full-match-stateful-v0.1.py` — runner reproduzível dos 12 cenários stateful.
- `card-game-leader-assertions-v0.1.json` — 22 cenários, incluindo todos os dez handlers de líder e casos negativos/limite.
- `card-game-combo-faction-assertions-v0.1.json` — 87 cenários relativos aos 27 combos e às quatro passivas de facção.
- `card-game-stale-identity-disposition-v0.1.md/.json` — classificação dos 28 ramos de identidade sem associação ativa, sem exclusão aplicada.
- Relatórios individuais de identidade, habilidades genéricas, ciclo de vida, especiais e relíquias.
- Documentação preexistente em `docs/` preservada do projeto-base, com ressalvas registradas no handoff.

## Scripts reproduzíveis em `docs/scripts/`

- `build-effect-source-map-v0.1.py` — gerador arquivado; só pode ser usado em checkout pré-política e recusa o runtime atual.
- `build-effect-source-map-v0.2.py` — gera o mapa AST do runtime pós-política.
- `assert-card-effect-behavior-v0.1.py` — valida resultados explícitos de 13 efeitos em fixtures sintéticos; não é cobertura completa.
- `sample-deck-cost-v0.1.py` — histórico/superado; não usar para recomendar orçamento (combo parcial e sem líder/relíquia).
- `sample-deck-cost-v0.2.py` — amostragem corrigida de custo, ainda dependente de EFP estimado e hipóteses de líder/relíquia.
- `simulate-combo-activation-v0.1.py` — chama `_aplicar_combo_de_cartas()` para estimar ativação sob ordem aleatória.
- `audit-effect-handler-coverage-v0.1.py` — cruzamento AST/runtime de catálogo, handlers, identidade e tags.
- `validate-card-effect-smoke-v0.1.py` — testes sintéticos de ação/hook no motor atual; não cobre todos os caminhos condicionais.
- `assert-card-identity-behavior-v0.1.py` — 22 identidades positivas e 11 casos negativos/limite.
- `assert-generic-unit-effects-v0.1.py` — 39 assertions para habilidades genéricas de unidade.
- `assert-card-lifecycle-effects-v0.1.py` — hooks de remoção/fim de rodada, incluindo `gloria` e ausência de `sobrevivente`.
- `assert-special-and-relic-effects-v0.1.py` — especiais e seis relíquias pelo fluxo real de ação.
- `assert-leader-effects-v0.1.py` — todos os dez handlers de líder e 12 rejeições/limites; 22/22.
- `assert-combo-and-faction-passive-v0.1.py` — 27 combos com um par ativador cada, requisitos incompletos, bloqueio de repetição, quatro passivas de facção e exclusão do efeito de especiais; 87/87.
- `audit-combo-overlap-v0.1.py` — script arquivado; só roda em checkout pré-política e recusa o runtime atual.
- `audit-combo-overlap-v0.2.py` — enumera o resolvedor corrigido em 4.422 pares e 287.430 trincas de IDs distintos.
- `audit-stale-identity-branches-v0.1.py` — classifica os 28 ramos de identidade sem associação ativa.
- `assert-combo-policy-v0.1.py` — 32 regressões da política aprovada.
- `summarize-card-game-behavior-v0.2.py` — agrega sete suites históricas/219 asserts.
- `summarize-card-game-behavior-v0.3.py` — agrega oito suites/251 asserts e métricas pós-política.
- `audit-gwent-http-contracts-v0.1.py` — inventaria 12 rotas/handlers, campos de request, sinais frontend, DB/motor e contrato de custo por AST/inspeção estática; não executa handlers.
- `assert-full-match-stateful-v0.1.py` — testa quatro partidas controladas de três rodadas, snapshots JSON, payloads, combos, líder, clima, relíquia, snapshot legado e round-trip SQLite; 12/12.

## Resultados e validações atuais pós-política

- Política dos combos: aprovada e implementada em `sistemas/gwent.py`.
- Catálogo: 27 combos; todos possuem `minimum: 2` e `priority` única; carta atual participa por tag; um combo por jogada; uso por ID uma vez por jogador/rodada.
- Testes comportamentais: oito suites, 251/251 assertions aprovadas; 32 assertions são regressões específicas da política. Ver `card-game-behavior-validation-v0.3.md/.json`.
- Mapa HTTP: 12 rotas mapeadas estaticamente; 0 dispatches reais, pendente por dependências indisponíveis.
- Testes stateful: 12/12 cenários aprovados, incluindo quatro partidas controladas de três rodadas e round-trip JSON/SQLite. Ver `card-game-match-snapshot-integration-v0.1.md/.json`.
- Enumeração pós-correção: 4.422 pares e 287.430 trincas; zero ativações solo; 152 pares com sobreposição elegível sob prioridade declarada; 2.582 trincas com múltiplos combos em jogadas sucessivas; todas as 2.582 cartas posteriores participantes por tag. Ver `card-game-combo-overlap-v0.2.md/.json`.
- Único arquivo funcional alterado nesta etapa: `sistemas/gwent.py`. Nenhuma alteração em DB/schema, `bot.py`, frontend, APIs, imagens ou assets do jogo. Partidas já persistidas mantêm bônus antigos; o ZIP não contém DB de produção.
- Os resultados do v0.1 abaixo descrevem o baseline anterior e são preservados apenas para comparação. EFP, custos, raridades, orçamento e redesign de cartas continuam propostas não aprovadas.

## Resultados e limites principais do baseline (histórico pré-política)

- Catálogo: 59 habilidades genéricas; 56 possuem handler direto de jogada, 2 são hooks de ciclo de vida (`vinganca`, `espolios`) e 1 (`sobrevivente`) não tem handler correspondente identificado. `gloria` é um hook oculto em `_resolve_round()` e está fora de `HABILIDADES`.
- Identidades: 22 associações ativas, todas com referência no resolvedor; 28 ramos de identidade continuam sem mapeamento ativo e exigem decisão antes de limpeza.
- Líderes: 10 definições com referências de execução.
- Combos: 27 definições; 72 IDs na tabela de tags, 67 IDs de cartas atuais e cinco IDs órfãos. Todos os combos têm provedores para cada tag requerida, mas isso não prova alcançabilidade em todos os decks/estados.
- Sobreposição: 154/4.422 pares ordenados (3,4826%) têm mais de um combo elegível; 11.780/287.430 trincas ativam ao menos dois combos em sequência. Em 8.096/11.784 eventos posteriores (68,7033%), a carta que recebe o combo não contribui com tag requerida. `eco_convergente` ativa solo por `gwent_unidade_eco`; três combos não declaram `minimum`. Ver relatório completo e exemplos em `card-game-combo-overlap-v0.1.md`.

- Smoke test: 56 ações diretas concluídas sem exceção; 22/22 identidades geraram evento; hooks foram tratados separadamente. Isto não equivale a testes de branch completa nem a partidas competitivas.
- Testes comportamentais v0.2: sete suites, 219/219 assertions aprovadas (13 iniciais + 33 identidades + 39 unidades genéricas + 7 lifecycle + 18 especiais/relíquias + 22 líderes + 87 combos/passivas). Os 87 novos cenários incluem um par ativador por combo, ausência de parceiro, bloqueio de repetição do mesmo combo, passivas nas quatro facções e exclusão de especiais. São fixtures sintéticos selecionados, não 219 habilidades únicas, nem cobertura de todos os estados/raridades ou integração de produção.
- Combos: 100.000 decks aleatórios, seed 42; 57,19% tiveram pelo menos um combo ativado e a média foi 0,956 ativação na mão de dez cartas assumida jogada na mesma rodada. Não mede taxa de vitória nem EV.
- Custo: amostragem v0.2 com 100.000 decks por cenário, seed 42; teto 32 aceita 68,8% sem relíquia e 45,4% com relíquia sob premissas do script. Isso não valida o teto.
- EFP: scores v0.1 são hipóteses fixas não calibradas. A metodologia v0.2 propõe vetores mecânicos e simulação de partidas; não há scores aprovados.

## Modificações desta revisão (mapa de fonte e EFP v0.2)

| Arquivo(s) | Alteração | Motivo/impacto |
|---|---|---|
| `docs/scripts/build-effect-source-map-v0.1.py`, `docs/card-game-effect-source-map-v0.1.json` | Gerador e índice AST histórico pré-política | Mapa de evidências do baseline, antes do patch | Script guardado com fail-fast no runtime atual; JSON congelado; v0.2 é o mapa atual | Evitar sobrescrever o registro histórico | Apenas documentação/harness | 59 genéricas, 22 identidades, 10 líderes, 27 combos no baseline |
| `docs/card-game-efp-methodology-v0.2.md` | Nova metodologia de decomposição por precondições, alvos/caps, consequências imediatas/atrasadas, bloqueios, duração, testes e EV. | Evita transformar pesos subjetivos em EFP definitivo; permanece proposta não aprovada. |
| `docs/scripts/assert-card-effect-behavior-v0.1.py`, `docs/card-game-effect-behavior-assertions-v0.1.json` | Primeira bateria de 13 asserts explícitos para resultados mecânicos selecionados. | Diferencia ação sem exceção de efeito com resultado esperado; preservada como fase inicial, superada em escopo pelas suites agregadas v0.2. |
| `docs/card-game-balance-validation-v0.1.md` | Acrescentada a seção 11 sobre o mapa de fonte e o método EFP v0.2. | Registra evidência e sequência de validação. |
| `docs/card-game-balance-spec-v0.1.md` | Referência explícita ao mapa de source e à metodologia EFP v0.2. | Mantém os scores v0.1 marcados como não calibrados. |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md` | Atualizados estado, ordem de leitura, próxima etapa e histórico. | Novo chat encontra as evidências e sabe que asserts e simulação continuam pendentes. |
| `docs/PACOTE-MANIFESTO.md` | Atualizado manifesto do pacote. | Inventaria documentos/scripts e os limites da revisão. |

| `docs/scripts/assert-card-identity-behavior-v0.1.py`, `docs/card-game-identity-behavior-assertions-v0.1.json` | Nova suite para identidades | 33 assertions: 22 identidades ativas em cenário positivo e 11 casos negativos/limite. | Confirmar efeitos de identidade por resultado de estado. | Diagnóstico apenas; nenhum impacto no runtime. | 33/33 passaram. |
| `docs/scripts/assert-generic-unit-effects-v0.1.py`, `docs/card-game-generic-unit-assertions-v0.1.json` | Nova suite de habilidades de unidade | 39 cenários positivos/negativos para habilidades genéricas de unidade. | Expandir além do smoke de ausência de exceção. | Diagnóstico apenas. | 39/39 passaram. |
| `docs/scripts/assert-card-lifecycle-effects-v0.1.py`, `docs/card-game-lifecycle-assertions-v0.1.json` | Nova suite de ciclo de vida | Testes de remoção, fim de rodada, vitória/derrota e status de `sobrevivente`. | Verificar hooks fora da ação comum de jogar carta. | Diagnóstico apenas; evidencia `gloria` e `sobrevivente`. | 7/7 passaram. |
| `docs/scripts/assert-special-and-relic-effects-v0.1.py`, `docs/card-game-special-relic-assertions-v0.1.json` | Nova suite de especiais e relíquias | 11 handlers especiais adicionais, seis relíquias e um caso de bloqueio. | Verificar o caminho de resolução de especiais/relíquias. | Diagnóstico apenas. | 18/18 passaram. |
| `docs/scripts/assert-leader-effects-v0.1.py`, `docs/card-game-leader-assertions-v0.1.json` | Nova suite para líderes | Dez handlers positivos e 12 casos negativos/limite. | Fechar a ausência de testes da ação de líder. | Diagnóstico apenas; usa `aplicar_jogada(action="leader")`. | 22/22 passaram. |
| `docs/scripts/audit-stale-identity-branches-v0.1.py`, `docs/card-game-stale-identity-disposition-v0.1.md/.json` | Classificação de ramos antigos | Separados 18 V18, quatro campos legados e seis ramos V75, total 28. | Evitar exclusão prematura sem conferir cartas/tags. | Nenhuma remoção funcional. | AST/runtime confirmou decomposição 18+4+6. |
| `docs/scripts/assert-combo-and-faction-passive-v0.1.py`, `docs/card-game-combo-faction-assertions-v0.1.json` | Nova suite de combos/passivas | 87 cenários sobre os 27 combos e quatro passivas; um par concreto por combo. | Verificar o resolvedor de combos e regra global de facção no estado sintético. | Somente harness/JSON; nenhum efeito no runtime. | 87/87 passaram; pares alternativos/precedência sobreposta não exauridos. |
| `docs/scripts/audit-combo-overlap-v0.1.py`, `docs/card-game-combo-overlap-v0.1.json/.md` | Auditoria histórica de pares/trincas | Congelou o comportamento pré-política: 67 unidades, 4.422 pares, 287.430 trincas, bônus posterior a não participante e ativação solo. | Adicionado fail-fast no script atual; JSON/Markdown preservados como registro histórico. | Evitar executar sobre o runtime pós-política e confundir a saída com baseline. | Só reproduz em checkout pré-política; relatório pós-patch v0.2 é a autoridade atual. |
| `docs/scripts/summarize-card-game-behavior-v0.2.py`, `docs/card-game-behavior-validation-v0.2.md/.json` | Agregador e relatório consolidado | Soma/valida sete suites e agrega auditoria estática. | Manter um resultado único reproduzível para o handoff. | Ferramenta e docs apenas. | 219 asserts, 219 aprovados, 0 falhas. |

## Validações da etapa documental pré-política (histórico)

- `build-effect-source-map-v0.1.py` foi executado no baseline pré-política e seu JSON foi congelado. No runtime atual, o gerador recusa execução; consulte o mapa atual v0.2 (59 genéricos, 56 handlers diretos, 2 hooks, 1 sem handler, 22 identidades, 10 líderes e 27 combos).
- As sete suites comportamentais foram executadas: 219 asserts passaram, nenhum falhou. Os casos são sintéticos e selecionados; não representam 219 habilidades únicas nem cobertura completa. Os 27 combos foram testados com um par ativador concreto cada; todas as quatro passivas de facção foram testadas com unidade estrangeira, primeira/segunda unidade e reset de rodada.
- `audit-combo-overlap-v0.1.py` foi executado no baseline pré-política e seu JSON/Markdown foram congelados. Após o patch, o script recebeu fail-fast no checkout atual; os achados antigos não representam a regra vigente. A política agora está aprovada/implementada e a auditoria atual é v0.2.

- O script de mapa de fonte passou por `py_compile`.
- Resultados anteriores de custo, combo, cobertura e smoke permanecem incluídos; seus métodos e limites estão descritos em `card-game-balance-validation-v0.1.md`.
- Hashes dos principais módulos funcionais continuam iguais ao baseline; nenhuma alteração de runtime, API, DB, frontend ou imagem foi feita nesta etapa.
- Histórico: o ZIP mestre da revisão stateful anterior continha **198 arquivos/entradas** e passou em `unzip -t`, sem erros. A revisão atual passou a **226 entradas (212 arquivos + 14 diretórios)** e foi verificada com `unzip -t` sem erros. A comparação com `soulsbo-main(1).zip` confirmou 143 arquivos não documentais do projeto byte a byte idênticos; apenas três fontes tipográficas (`DejaVuSans*.ttf`) foram intencionalmente excluídas. Caches Python, bytecode, bancos locais, `.env` preenchido e binários locais de fontes são excluídos. O único arquivo de exemplo de ambiente é `.env.r2.example`, com valores de credenciais vazios.

## Limitações do baseline e decisões ainda não aprovadas

- EFP, custo individual, raridade, orçamento 32, `leader_load`, inclusão de relíquia e definição de especiais continuam propostas.
- Nenhuma amostragem de custo ou frequência de combos substitui partidas completas nem comprova equilíbrio.
- Nove modelos estão excluídos da amostragem de custo por IDs sem score/canonicalização.
- O contrato HTTP de custo ainda está incompleto: sem orçamento em `POST /deck` e sem `custo` no dicionário final de `preparar_carta()`. Corrigir somente após aprovar a regra/schema.
- A semântica dos combos foi decidida e implementada após esse baseline; consulte `card-game-combo-policy-v0.1.md`. Já foram testadas quatro partidas controladas de três rodadas pelo motor em memória, mas continuam pendentes partidas com decks legais do builder, integração HTTP/API/DB assíncrono, convites, IA, recompensas, browser, arte/R2 e simulação competitiva por facção. Os 251 asserts e 12 cenários stateful são testes automatizados de escopo controlado, não prova de equilíbrio ou integração em produção.
- DB de produção, credenciais/configuração, ambiente publicado, estado R2 e artes aprovadas não vieram no ZIP-fonte.
- Histórico Git do código original não foi fornecido; não inventar a procedência de código legado.
- Nenhum artefato diagnóstico substitui testes de integração no ambiente publicado.

## Histórico desta revisão — mapa estático HTTP Gwent

| Arquivo | Função/campo/trecho | Antes | Depois | Motivo | Impacto | Validação |
|---|---|---|---|---|---|---|
| `docs/scripts/audit-gwent-http-contracts-v0.1.py` | AST de rotas/handlers e `preparar_carta()` | Sem índice reproduzível de endpoints Gwent e conexões frontend/DB/motor | Script identifica 12 rotas e gera JSON/Markdown; foi corrigido para detectar chamadas diretas ao motor por nomes AST | Completar a rastreabilidade bot/site/motor sem declarar integração não executada | Apenas docs/harness; sem impacto no runtime | 12 rotas; `deck_cost_budget_enforced=false`; `prepared_payload_includes_cost=false` |
| `docs/card-game-http-contract-map-v0.1.md/.json` | Novos relatórios | Inexistentes | Contratos, campos, handlers, custos e fluxos de partida inventariados | Tornar pendências visíveis ao próximo chat | Apenas handoff | Gerados e revisados contra fonte |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-mapping-audit.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem, pendências e histórico | Foco parava na análise stateful | Novo estado HTTP estático no topo; etapa stateful preservada como anterior; custo payload ausente explicitado | Atualizar continuidade e evitar que o próximo chat repita análise | Documentação somente | 12 rotas e limitações cruzadas; testes separados preservados |

## SHA-256 dos arquivos funcionais — referência atual

- `sistemas/cartas.py`: `3bed48cbd496de431d92b76653518bda54a59ae5ee7ec8586b448b9fd19a0192`
- `sistemas/gwent.py`: `f69e8865759862ddc5bef9ff26ee2ddb43bcfbe33d3e61c985d4b118c6e42383`
- `bot.py`: `a735b2380176a5871f45770d99489825c587033d4a0d760b48b108a6e2a885ff`
- `database.py`: `ead936a2813335e5a98b31276a9e08ea6dc3a6121543300dd24decc7d69a3ed2`
- `site/app.js`: `9aafa6ba1ef2641fce9ab169192b27d28b92d2b92ee15881ca5db9984b39386b`


## Revisão mais recente — contrato e registry canônico v1.1 (2026-11-27)

A fundação estrutural foi reforçada. `sistemas/card_contract.py` agora valida o registry de efeitos/combos e os parâmetros declarados por efeito; foi criado `data/card_game/effect-registry.schema.v1.json`; o exemplo de registry declara `required_parameters` e `allow_additional_parameters`. O CLI valida registry antes do catálogo, verifica os valores de cada `effect_params` e rejeita parâmetros desconhecidos ou fora de faixa. Para combos, exige `minimum_participants >= 2` e prioridades inteiras positivas e únicas, alinhadas com a política de combos aprovada.

**Validação:** 35/35 testes; dois JSON Schemas Draft 2020-12 válidos e exemplos aceitos; CLI sintético válido (4 modelos, 3 puros) aceito e fixture com parâmetro fora do limite rejeitada; baseline gerado duas vezes com SHA-256 idêntico `df383e6aa10634cf4a0c5d00594e2cbc9f1edb071c95da2ce3119096375297c2`. Os hashes de `sistemas/cartas.py`, `sistemas/gwent.py`, `bot.py`, `database.py` e `site/app.js` permanecem iguais aos registrados na referência anterior. A suíte de runtime 251/251 e os 12 cenários stateful não foram reexecutados porque nenhum arquivo funcional foi alterado nesta etapa.

| Arquivo | Função/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `sistemas/card_contract.py` | `validate_effect_registry`, `_validate_effect_params`, `validate_card_definition`, `validate_catalog` | Acrescenta validação de registry e parâmetros obrigatórios/tipados/limitados; combos com dois participantes e prioridade única | Impedir referências válidas com payload incompatível e combos inválidos | Módulo isolado, sem importação no runtime legado | 35/35 testes |
| `data/card_game/effect-registry.schema.v1.json` | Novo schema | Define formato dos efeitos, parâmetros e combos | Formalizar o registry novo | Nenhum impacto funcional | Draft 2020-12 e exemplo aprovados |
| `data/card_game/effect-registry.example.v1.json` | Campos required/extra parameters | Demonstra parâmetros obrigatórios e bloqueio de campos extras | Tornar o exemplo compatível com validação estrita | Exemplo apenas | CLI e schema aprovados |
| `docs/scripts/validate-card-catalog-v1.py` | `main` | Valida registry antes do catálogo e parâmetros após resolver effect_id | Evitar catálogo com payload quebrado | Ferramenta local | Fixture positivo/negativo |
| `docs/scripts/test-card-contract-v1.py` | Suite | Expande de 25 para 35 casos | Cobrir registry e execução do CLI | Ferramenta local | 35/35 |
| `docs/scripts/validate-card-json-schemas-v1.1.py` | Novo script | Valida ambos os schemas e exemplos; `jsonschema` opcional | Reproduzir validação JSON Schema | Ferramenta de desenvolvimento, não requisito do bot | 2/2 schemas e 2/2 exemplos |
| `docs/card-game-contract-validation-v1.1.md/.json` | Novo relatório | Registra resultados, hashes, comandos e limites | Handoff verificável | Documentação | Conteúdo cruzado com comandos reais |
| README, handoff, manifesto, modelo canônico e contexto operacional | Estado/ordem/histórico | Atualizados para v1.1 e 35/35 | Impedir orientações defasadas | Somente documentação | Revisão cruzada |

## Revisão mais recente — fundação do modelo canônico de cartas v1 (2026-11-27)

Foi criada a primeira camada da reconstrução, sem substituir ainda o runtime antigo. `sistemas/card_contract.py` valida definições novas; `data/card_game/card-definition.schema.v1.json` é o JSON Schema; o exemplo de carta e de registry são ilustrativos. O novo catálogo autoral ainda não existe e nenhum dos 137 cards legados foi renomeado ou redesenhado nesta etapa.

O snapshot `data/card_game/catalog-legacy-baseline-v0.1.json` contém 137 modelos: 110 unidades, 21 especiais táticas, seis relíquias; 59 definições genéricas, 22 identidades ativas, 27 combos e dez líderes. O baseline tem 15 cartas puras, 19 custos divergentes, seis facções a revisar e 43 modelos atingidos pela transformação V18. O snapshot não é fonte de runtime e preserva dados antigos, inclusive anomalias, para migração.

**Decisões estruturais:** unidades usam poder-base inteiro 1–15; especiais/relíquias sem corpo de combate usam `null`; `kind` e slot são separados; no máximo um efeito individual por carta via `effect_id`; tags de combo são explícitas; lore não é descrição mecânica; custo e raridade serão derivados por regras versionadas. A meta de 30% significa pelo menos 42 modelos puros no baseline atual. A meta opcional 35% e as fórmulas EFP/custo/raridade continuam não aprovadas.

**Validação:** 25/25 `unittest`; JSON Schema Draft 2020-12 passou `check_schema`; exemplo passou sem erros; snapshot gerado duas vezes com SHA-256 idêntico `df383e6aa10634cf4a0c5d00594e2cbc9f1edb071c95da2ce3119096375297c2`. `py_compile` passou; Ruff não está instalado no ambiente. Os módulos legados `cartas.py`, `gwent.py`, bot, DB e frontend não foram alterados nesta etapa.

| Arquivo | Função/campo/trecho | Alteração | Motivo | Impacto | Validação |
|---|---|---|---|---|---|
| `sistemas/card_contract.py` | `validate_card_definition`, `validate_catalog`, `is_pure_unit`, `minimum_pure_cards` | Novo validador estrutural sem dependência externa | Congelar invariantes do catálogo novo antes de refatorar o motor | Ainda isolado; sem impacto no runtime ativo | 25/25 testes |
| `data/card_game/card-definition.schema.v1.json` | JSON Schema Draft 2020-12 | Campos, enumerações e condicionais por tipo | Contrato compartilhável entre agentes e ferramentas | Dados, não runtime | Schema e exemplo aprovados |
| `data/card_game/catalog-legacy-baseline-v0.1.json` | Snapshot 137 cartas e registries | Fotografia determinística do catálogo e ligações atuais | Preservar estado pré-reconstrução | Referência de auditoria; não importar no runtime | Duas gerações com SHA idêntico |
| `docs/scripts/build-card-catalog-baseline-v0.1.py` | Gerador do snapshot | Exporta modelos, efeitos, identidades, combos, líderes e alertas | Reproduzir baseline | Ferramenta local | Duas execuções idênticas |
| `docs/scripts/test-card-contract-v1.py` | 25 testes `unittest` | Testa campos, tipos, poderes 1/15, pureza, quota e referências | Evitar regressões na nova estrutura | Harness local | 25/25 |
| `docs/scripts/validate-card-catalog-v1.py` | CLI de validação | Lê catálogo e registry JSON e produz resultado valid/invalid | Preparar validação do manifesto futuro | Ferramenta local | `py_compile`; fixture sintética |
| `docs/card-game-canonical-model-v1.md`, `docs/card-game-legacy-baseline-v0.1.md`, `data/card_game/README.md` | Novos documentos | Especificam contrato, tipos, pureza e estado do baseline | Continuidade autossuficiente | Documentação | Revisão cruzada |
| `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PROJECT-OPERATING-CONTEXT.md`, `docs/card-game-balance-spec-v0.1.md`, `docs/PACOTE-MANIFESTO.md` | Estado, ordem de leitura e propostas | Registra o novo estágio, limites e próximos passos | Evitar handoff desatualizado | Documentação | Contagens e referências conferidas |

## Validações atuais após a fundação do contrato

- Novo contrato: 25/25 testes aprovados.
- JSON Schema: schema Draft 2020-12 válido; exemplo de unidade válido.
- Snapshot legado: 137 modelos; exportação determinística.
- Testes de runtime anteriormente aprovados permanecem 251/251 asserts e 12/12 stateful, mas não foram reexecutados neste novo estágio porque o runtime não foi alterado.


## Grupo A — revisão de identidade física v0.1 (2026-11-27)

- Baseline: pacote de continuidade rev. 5; status `TECHNICAL_PROPOSAL_FOR_OWNER_REVIEW_NOT_APPROVED`.
- Artefatos novos: `docs/card-game-identity-group-A-decision-review-v0.1.md`, `docs/card-game-identity-group-A-decisions-v0.1.json`, `docs/card-game-identity-group-A-validation-v0.1.json` e `docs/scripts/validate-card-game-identity-group-A-v0.1.py`.
- Errata: `cartas_exemplares.id` é PK global no DDL atual; o parecer corrige a recomendação anterior que permitia reutilização por proprietário. O exemplo CardInstance foi ajustado e o contrato v0.1 recebeu nota de errata.
- Grupo A trata CI-001/002/003/004/006/010, BUF-013 e RSRX-09. Todas continuam abertas; nenhuma decisão de design foi aprovada.
- Validação: 30/30 casos sintéticos/estáticos. Não é teste de produção, persistência concorrente ou integração do runtime.
- Alterações limitadas a `docs/`; runtime, API, DB, catálogo ativo e frontend preservados.
