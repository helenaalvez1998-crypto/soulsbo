# Card Engine v2 — combos, passivas de facção e líderes alpha v0.1

**Status:** `PASS_ALPHA_ONLY_NOT_RELEASE_APPROVED`  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev18.zip`  
**Pacote resultante:** rev. 19  
**Allowlist executável:** 27 cartas (`alpha-test-only.catalog.v0.3`)  
**Validação:** 109/109 testes; staging histórico PASS (137 modelos, 27 alpha-only, 110 bloqueados).

## Entrega

A alpha do Card Engine v2 agora conecta três famílias de regra ao `AlphaMatchController`:

- **Combos:** carrega 27 definições de `card-engine-v2-alpha-combos.v0.1.json`; exige que a carta recém-jogada contribua com uma tag requerida, valida participantes físicos distintos, escolhe no máximo um combo por jogada pela menor prioridade numérica e permite cada combo uma vez por jogador/rodada. O bônus individual vai para a unidade ativadora; o bônus coletivo vai para aliados que já estavam no tabuleiro na mesma fileira. Eventos de combo são causais à jogada que os ativou.
- **Passivas de facção:** quatro passivas, uma para cada facção (`dark_moon`, `golden_order`, `the_forgotten`, `crimson_veil`). A primeira unidade da facção escolhida pelo jogador jogada em cada rodada recebe +1. Jogar uma unidade de outra facção não consome a ativação; a flag é reiniciada em `round_close`. A facção pode ser declarada no setup ou inferida do líder escolhido.
- **Líderes:** dez handlers alpha, selecionados no setup e utilizáveis uma vez por partida: Godfrey, Morgott, Radagon, Mohg, Rykard, Esgar, Papa Esquecido, Rennala, Astel e Loretta. A validação de setup exige compatibilidade entre facção e líder. Falhas de elegibilidade não consomem a ativação. As resoluções são registradas com eventos e transacionadas pelo repositório.

## Conteúdo habilitado e limites

| Item | Quantidade | Situação |
|---|---:|---|
| Modelos históricos no staging | 137 | Rastreados, não equivalem a catálogo novo |
| Cartas na allowlist alpha v0.3 | 27 | Permitidas somente em teste isolado |
| Modelos ainda bloqueados | 110 | Não executáveis na alpha |
| Combos registrados | 27 | Carregados e validados |
| Combos alcançáveis com tags da allowlist atual | 9 | Executáveis conforme combinação das tags disponíveis |
| Combos sem fontes de tags na allowlist | 18 | Registrados, mas inertes até ampliar a allowlist |
| Passivas de facção | 4 | Handlers alpha implementados |
| Líderes | 10 | Handlers alpha implementados |
| Famílias de efeitos de entrada | 12 | Mantidas da versão anterior |

O catálogo v0.3 permite três cartas adicionais especificamente para cobrir fontes de tags usadas em combos/passivas/líderes. O staging v0.2 atualiza a partição histórica para 27 alpha-only e 110 bloqueadas. O staging v0.1 e a allowlist v0.2 permanecem como artefatos históricos da revisão anterior.

A allowlist, os registries de combos, passivas e líderes são artefatos versionados e validados por `AlphaCatalog`; seus SHA-256 integram o `DefinitionManifest`. Registros com estado `alpha_test_only_not_a_published_registry` não são releases publicadas nem aprovação de custo, facção, texto, arte ou balanceamento de produção.

## Demonstrações reproduzíveis

1. `docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py` executa uma sequência controlada com uma passiva de facção, o combo `muralha_inabalavel` e o líder Godfrey. O resultado registrado é A 20–10 B; são 21 eventos, incluindo um `card_combo_activated`, um `faction_passive_applied`, um `leader_activated` e um `leader_bonus_applied`. SQLite local: `quick_check=ok`, `integrity_check=ok`, sem violações de FK, revisão ou sequência.
2. `docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py` executa a regressão Bo3 já existente, terminando Player A 2–1 Player B, com 16 operações e 48 eventos.
3. `docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py` executa a suíte completa: 109/109, sem falhas ou testes ignorados.
4. `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py` verifica a partição de 137 modelos, proveniência/hashes, 27 alpha-only e 110 bloqueados.

## Limitações explícitas

- Nove dos 27 combos têm fontes de tags completas na allowlist atual; os outros 18 continuam inertes. Não declarar os 27 combos todos alcançáveis.
- Os quatro handlers de passivas e dez handlers de líderes são implementações alpha. Os testes cobrem suas resoluções isoladas; nem todas as ações foram exercitadas por uma UI humana nem por uma partida completa de ponta a ponta.
- A allowlist de 27 cartas é um conjunto controlado de fixtures; os custos/facções/descrições históricos não foram aprovados para publicação. Os 110 restantes permanecem bloqueados.
- O controlador ainda é uma partida alpha, não o jogo integral: combate/dano completo, catálogo completo, todas as famílias especiais, custos/recursos gerais, fluxo normal de sacrifício, adaptação assíncrona e interface ainda faltam.
- Sem integração Discord, HTTP, frontend ou banco publicado. Nenhuma migração, cutover ou alteração em partidas reais foi realizada.

## Comandos

Na raiz do repositório:

```bash
python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

## Integridade

As alterações da rev. 19 ficam limitadas a `data/card_game/`, `docs/`, `sistemas/card_engine_v2/` e `tests/card_engine_v2/`. Os arquivos centrais `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` permanecem byte a byte idênticos ao baseline rev. 18. Nenhuma integração ou migração de produção foi executada.
