# Card Engine v2 — partida jogável alpha v0.1

**Status:** `ISOLATED_PLAYABLE_ALPHA_NOT_PRODUCTION_READY`  
**Baseline:** pacote de continuidade rev. 16  
**Catalog:** allowlist explícita de 10 cartas; releases `alpha-test-only.*.v0.1`  
**Runtime legado:** preservado; nenhum cutover ou migração de produção.

## Resultado reproduzível

Comando:

```bash
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.1.py
```

O script cria um arquivo SQLite temporário e executa uma partida de dois jogadores em melhor de três. Resultado esperado da fixture:

| Rodada | Player A | Player B | Vencedor |
|---|---:|---:|---|
| 1 | 9 | 4 | A |
| 2 | 0 | 6 | B |
| 3 | 6 | 0 | A |
| **Série** | **2 vitórias** | **1 vitória** | **A** |

A demonstração executa 16 operações de jogador/sistema e produz 48 eventos. Na primeira rodada, o fluxo demonstra entrada de unidades, buff do Veterano a uma unidade aliada já presente, Tempestade, Frost, oferta de alvo revision-bound, Execução, remoção de Godwyn, Vingança reativa e concessão de Égide. O encerramento congela pontuação, arquiva unidades sem acionar Vingança, expira efeitos temporários e inicia a rodada seguinte. A série termina em 2–1.

O relatório JSON da execução é gerado com `--json-out`; o script verifica `quick_check`, `integrity_check`, foreign keys, revisão do snapshot e sequência do journal.

## Componentes implementados

- `sistemas/card_engine_v2/alpha_catalog.py`: adaptação estritamente allowlisted do snapshot histórico e dos três artefatos alpha; snapshots de definição com digest. O baseline histórico não é carregado como catálogo ativo.
- `sistemas/card_engine_v2/power.py`: projeção de poder efetivo com poder-base, grants de bônus, clima, resistência climática e Frost/estados de controle; raridade não participa do cálculo.
- `sistemas/card_engine_v2/match.py`: controlador de partida 2 jogadores, distribuição inicial, turnos, jogada de unidade, especiais alpha, ofertas de alvo, passagem, pontuação, melhor de três e fechamento de rodada.
- `sistemas/card_engine_v2/repository.py`: persistência SQLite isolada; snapshot e runtime da partida usam a mesma revisão e transação CAS.
- `tests/card_engine_v2/test_playable_match.py`: testes de integração do controlador com a persistência local.
- `docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.1.py`: partida reproduzível em banco temporário.

## Allowlist

Os dez modelos disponíveis nesta alpha são:

1. `arma_lanca_fornalha`
2. `arma_cajado_marulho`
3. `arma_martelo_fornalha`
4. `chefe_vigia_cinzento`
5. `gwent_v75_ordem_veterano_juramento`
6. `gwent_unidade_herdeiro_portao`
7. `gwent_especial_egide`
8. `gwent_especial_execucao`
9. `gwent_especial_tempestade`
10. `elden_especial_geada`

A allowlist é fixture de teste, não a declaração de catálogo completo, nem certifica balanceamento para publicação. As definições saem de um snapshot histórico e são vinculadas a `alpha-test-only` releases. Raridade é metadado classificatório e não escala mecânica.

## Testes

Comando completo:

```bash
python -m unittest discover -s tests/card_engine_v2 -v
```

Resultado desta revisão: **78/78 testes aprovados**, incluindo o repositório, resolvedor genérico, schemas e partida melhor de três. Também há testes específicos de rejeição de oferta de alvo sem revisão e de oferta obsoleta.

Partida de demonstração:

```bash
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.1.py --json-out /tmp/soulsbo-match.json
```

## Limites conhecidos

Esta é uma partida jogável de teste, não ainda uma experiência completa do jogo Soulsbo. Não inclui todo o catálogo nem todos os efeitos, deck builder/custos de construção, líderes, combos, sacrifício via controlador da partida, sistema integral de combate/dano, transições de bleed/rot/madness, UX ou integração multiplayer em rede. O resolvedor genérico já testa alguns contratos isoladamente, mas isso não significa que todas as famílias estejam expostas no controlador de partida.

Não há adapter assíncrono para Discord/HTTP; o repositório é síncrono e SQLite local/single-host. Não há conexão com o banco publicado, API, bot ou frontend. Nenhuma migração de partida real foi executada.

## Próximo bloco

Ampliar a allowlist de efeitos e unidades reais de forma incremental, implementar o restante das famílias do catálogo e construir os contratos de combate/turnos/custos. Depois, integrar por adapter isolado e executar testes de comparação antes de qualquer cutover.
