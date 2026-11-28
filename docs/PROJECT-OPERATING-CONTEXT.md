# Estado vigente V77 — 2026-11-28

O runtime principal de cartas está na V77: 179 modelos no índice, 164 cartas no pacote jogável, 30 unidades + 11 especiais e três líderes por facção. Os Esquecidos receberam dez cartas especiais nesta etapa; Abadessa das Ruínas e Mártir da Vigília continuam compondo o trio de líderes com Papa Esquecido. Os títulos são únicos e limitados a 27 caracteres, com IDs preservados. A auditoria catálogo → combate → site está em `docs/AUDITORIA-FIDELIDADE-CARTAS.md/.json`; o manifesto detalhado está em `docs/v77-normalizacao-faccoes-e-nomes.md`. A V77 está no código-fonte e ainda precisa ser implantada no host.

---

# Estado corrente do runtime principal — revisão V76 (2026-11-28)

O runtime principal do Coliseu usa o catálogo `sistemas/cartas.py`, o resolvedor `sistemas/gwent.py`, a API em `bot.py` e a interface `site/app.js`. A revisão V76 expandiu Os Esquecidos, corrigiu atribuições de facção, adicionou dois líderes, padronizou títulos e alinhou os decks-base.

- **Catálogo:** 162 registros no índice (`CARTAS_POR_ID`), incluindo cartas de coleção, primordiais e recompensas de patente; 147 cartas no pacote jogável estático.
- **Unidades por facção:** 30 para Ordem Áurea, 30 para Véu Carmesim, 30 para Lua Negra e 30 para Os Esquecidos.
- **Líderes:** 12, três por facção. O registro de combos permanece em 27; as unidades V76 usam os combos de fé existentes. Os Esquecidos agora oferece Papa Esquecido, Abadessa das Ruínas e Mártir da Vigília.
- **Nomes:** limite validado de 28 caracteres, sem duplicatas no índice atual; recompensas dinâmicas e patentes também usam títulos compactos e distribuem entre as quatro facções; IDs existentes foram preservados.
- **Decks-base:** nove unidades + uma especial por facção, todos com IDs válidos e cartas alinhadas à facção. O deck competitivo continua com 12 cartas.
- **Snapshots antigos:** o servidor resolve facção, nome e lore pelo ID canônico, evitando que decks antigos mantenham dados desatualizados.
- **Validação:** 315 testes e 106 subtestes aprovados; auditoria automática 162/162, 12 líderes e zero divergências estruturais.

A revisão está no código do pacote; não houve deploy, reinício do serviço hospedado nem alteração do banco externo. Os registros abaixo deste cabeçalho sobre Card Engine v2 são históricos e pertencem ao motor alpha isolado, cujo staging antigo de 137 modelos não é o catálogo público do runtime principal. Ver `docs/v76-expansao-os-esquecidos.md` e `docs/AUDITORIA-FIDELIDADE-CARTAS.md`.

---

# Contexto operacional do projeto — ambiente de teste (2026-11-28)

## Atualização técnica corrente — Card Engine v2 alpha rev. 22

A rev. 22 revisa o ciclo de vida das remoções e cria um contrato candidato testável para deck fatigue. As decisões aprovadas dos Grupos C/F já representadas no runtime alpha foram conferidas: remoção por instância física, causas fechadas, contadores distintos, bypass de proteção no sacrifício, Vingança reativa e arquivamento de rodada separado. O combate continua causando dano à vida dos jogadores; não existe contrato de HP individual nem morte automática de unidades.

O redesign diz que deck vazio causa dano crescente por turno, mas não define dano inicial, incremento, teto nem a cadência exata. A alpha atual distribui seis cartas e compra até duas apenas na transição de rodada; quando a pilha esvazia, interrompe a compra sem dano. A rev. 22 cria `deck_fatigue_candidate.py` e policy candidata para testar a fórmula sem ativá-la; o módulo não é importado pelo `AlphaMatchController` e mantém todos os parâmetros de balanceamento em aberto.

**Validação corrente:** 130/130 testes; dez testes do modelo candidato de fatigue; staging 137/27/110; regressão Bo3 A 2–1 B (16 operações/60 eventos); demonstração combo/passiva/líder com 25 eventos. Scripts oficiais executados; SQLite temporário passou quick/integrity/foreign-key checks.

**Limites:** nenhum código de runtime, ruleset ativo, schema, SQL, catálogo ou integração foi modificado. Sem integração Discord/HTTP/frontend, adapter assíncrono ou migração. O catálogo permanece 27 cartas alpha e 110 bloqueadas; 18 dos 27 combos continuam inertes.

**Fronteira operacional:** nenhum banco publicado foi acessado. `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` permanecem byte a byte idênticos ao baseline rev. 21.

Para continuidade, considerar `docs/card-game-handoff.md`, `docs/card-engine-v2-deck-fatigue-contract-v0.1.md`, `docs/card-engine-v2-lifecycle-audit-v0.1.md`, `docs/card-engine-v2-sacrifice-match-alpha-v0.1.md` e `sistemas/card_engine_v2/README.md` como os registros correntes; blocos abaixo desta atualização são históricos.

---

# Contexto operacional do projeto — ambiente de teste (2026-11-28)

## Atualização técnica corrente — Card Engine v2 alpha rev. 20

O Card Engine v2 continua isolado do runtime legado. A rev. 20 implementa combate por fileira no `AlphaMatchController`: totaliza poder efetivo por `melee`, `ranged` e `siege`, calcula a diferença positiva como dano à vida do oponente e persiste vida inicial de 20 por jogador. Vida zero encerra a partida; eliminação simultânea resulta em empate. O Bo3 permanece como fallback do harness alpha quando ninguém é derrotado no limite configurado.

**Validação da rev. 20:** 117/117 testes; staging 137/27/110; regressão Bo3 A 2–1 B (16 operações/60 eventos); demonstração combo/passiva/líder com 25 eventos. Repositórios SQLite temporários passaram integrity/foreign-key checks.

**Limites da rev. 20:** a resistência atual é climática; o contrato não define ataque, armadura, defesa física ou HP por unidade. O combate não destrói unidades automaticamente. Sacrifício normal ainda não estava integrado ao controlador; deck fatigue, custos completos e integração Discord/HTTP/frontend seguem pendentes.

**Fronteira operacional da rev. 20:** nenhum banco publicado foi acessado; não houve integração, migração ou cutover. `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` permanecem byte a byte idênticos ao baseline rev. 19.

---

# Contexto operacional do projeto — ambiente de teste (2026-11-27)


## Atualização técnica corrente — Card Engine v2 alpha rev. 19 (2026-11-27)

O novo `sistemas/card_engine_v2/` já possui persistência SQLite isolada, resolvedor de gameplay e controlador de partida alpha. Na rev. 19 foram conectados combos, quatro passivas de facção e dez handlers de líderes. O allowlist contém 27 cartas alpha; 110 dos 137 modelos históricos continuam bloqueados. Dos 27 combos registrados, nove têm tags-fonte na allowlist atual e 18 permanecem inertes.

**Validação corrente:** 109/109 testes; staging histórico 137/27/110; partida Bo3 A 2–1 B; demonstração de combo/passiva/líder A 20–10 B. Os testes usam bancos SQLite descartáveis e fixtures; não são validação de produção ou playtest de interface humana.

**Fronteira operacional:** não houve integração Discord/HTTP/frontend, não foi acessado ou alterado o banco publicado e não houve migração/cutover. `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` permanecem preservados byte a byte em relação à rev. 18. O motor v2 continua isolado.

Para continuidade, considerar `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md` e `docs/card-engine-v2-combos-faction-passives-leaders-alpha-v0.1.md` como o estado técnico mais recente; blocos posteriores no documento são histórico de etapas anteriores.

## Informação confirmada pelo proprietário

O proprietário informou que o jogo ainda não foi lançado para jogadores e não possui usuários reais ativos. Se houver contas ou registros no banco, são apenas contas e dados de teste utilizados pelo próprio proprietário.

**Origem desta informação:** declaração do proprietário nesta conversa. Ela não foi verificada contra o banco de dados, Discord, hospedagem ou Cloudflare R2, porque esses ambientes não estão disponíveis no pacote recebido.

## Como essa informação altera as prioridades

1. Não é necessário projetar a reconstrução para preservar economias, coleções, rankings, decks, recompensas ou progresso de uma comunidade de jogadores reais.
2. Não é necessário manter compatibilidade prolongada com dados de jogadores antigos por razões de continuidade de serviço. Para a reconstrução, pode ser mais simples criar um schema limpo e semear novamente o catálogo, ou resetar dados de teste selecionados.
3. O desenvolvimento pode priorizar correção estrutural, consistência do modelo de cartas, motor, deck builder, APIs, interface e testes integrados, em vez de planejar migração sem interrupção para uma base de jogadores.
4. O inventário de SQLite/R2 preparado em `card-game-production-audit-runbook-v0.1.md` deixa de ser um bloqueio obrigatório para continuar a reconstrução. Deve ser executado apenas se for necessário preservar/reutilizar cartas de teste, artes aprovadas, anexos do Ateliê ou objetos já existentes.
5. Registros de teste poderão ser descartados como parte de uma etapa de reset/reseed quando isso for tecnicamente necessário e o escopo estiver definido. Antes de uma operação destrutiva no ambiente hospedado, confirmar quais elementos serão apagados; esta declaração não é uma autorização irrestrita para apagar artes, arquivos, configurações ou credenciais.

## O que continua precisando de cuidado

- Não incluir `.env`, tokens Discord, access keys do R2, senhas, URLs privadas ou credenciais no ZIP nem no chat.
- Não apagar automaticamente o bucket R2, anexos do Discord, imagens do Ateliê ou artes aprovadas. Mesmo sendo um jogo de teste, o proprietário pode querer preservar o trabalho artístico.
- Distinguir “ambiente de produção/hospedagem” de “base com jogadores reais”: pode existir uma implantação hospedada sem que exista uma comunidade de jogadores.
- Antes de resetar o SQLite, identificar o `DB_PATH`/`DATA_DIR` efetivamente usado e confirmar que o alvo é o banco de teste correto. Se as artes precisarem ser mantidas, exportar ou inventariar apenas os registros/arquivos de arte necessários.

## Diretriz para o próximo agente

Não bloquear a implementação do novo sistema de cartas esperando o relatório completo de produção. Primeiro avançar com testes integrados e definição do modelo canônico. Tratar DB/R2 reais como fonte opcional de recuperação de ativos, não como dependência para validar regras do motor. Ao planejar uma limpeza, favorecer um reset/reseed simples para dados de teste em vez de construir migrações complexas para proteger progresso de jogadores inexistentes.


## Atualização da reconstrução — contrato canônico v1 (2026-11-27)

Registro histórico da primeira iteração v1: `sistemas/card_contract.py` validava o novo modelo, `data/card_game/card-definition.schema.v1.json` definia o JSON Schema da carta e `data/card_game/catalog-legacy-baseline-v0.1.json` preservava os 137 modelos antigos. A primeira bateria teve 25/25 testes. O estado atual foi ampliado na atualização v1.1 descrita abaixo (35/35 testes e schema próprio do registry). O módulo permanece isolado do runtime legado.

A nova arquitetura separa `unit`, `special` e `relic`; relíquias ocupam slot próprio. Unidades terão poder-base 1–15; special/relic sem corpo de combate usam `power_base=null`. A quota de pureza de pelo menos 30% foi aplicada ao conjunto de modelos jogáveis: baseline de 137 exige pelo menos 42 unidades puras; o baseline atual tem 15. A fórmula de EFP, custo, raridade, teto de deck e custo do líder continuam propostas não aprovadas.

O próximo passo é consolidar o registry de efeitos e mapear cada implementação legada antes de selecionar, fundir, redesenhar ou remover habilidades. O inventário de SQLite/R2 permanece opcional para recuperação de ativos, não bloqueia o trabalho.


## Atualização da fundação estrutural — registry v1.1 (2026-11-27)

O contrato canônico agora valida também o registry de efeitos/combos e os parâmetros fornecidos por cada carta. Foi criado `data/card_game/effect-registry.schema.v1.json`; `sistemas/card_contract.py` verifica parâmetros obrigatórios, tipos, limites, campos extras, IDs únicos, mínimo de dois participantes e prioridades únicas de combos. A suíte passou 35/35 e o CLI foi testado com fixtures válidas e inválidas. Isso ainda não é catálogo novo nem integração do runtime; fórmulas EFP/custo/raridade continuam pendentes de aprovação.
