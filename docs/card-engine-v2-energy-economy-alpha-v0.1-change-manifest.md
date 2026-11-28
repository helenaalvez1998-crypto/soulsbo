# Manifesto de alteração — economia de energia alpha v0.1

**Baseline:** Soulsbo rev. 23  
**Saída planejada:** Soulsbo rev. 24  
**Ruleset:** `alpha-test-only.ruleset.v0.4`  
**Escopo:** Card Engine v2 alpha isolado; sem integração de produção.

| Arquivo | Alteração | Validação |
|---|---|---|
| `data/card_game/card-engine-v2-alpha-ruleset.v0.4.json` | Regras de +1 energia por turno, máximo 5, saldo que persiste entre rodadas, mapas explícitos de custo por ID e política alpha para ações ainda sem preço | Carregado e validado pelo `AlphaCatalog` |
| `sistemas/card_engine_v2/alpha_catalog.py` | Carrega/valida maps de custo por ID; raridade não é fonte; metadados de view mostram custo configurado | Testes de IDs desconhecidos, booleanos, mapa inválido e default |
| `sistemas/card_engine_v2/match.py` | Geração no início de turno, teto, validação de custo antes da ação, dedução transacional para unidade/especial/líder, view e custos nos receipts | Testes de ganho, persistência, cap, insuficiência, pagamento e eventos |
| `sistemas/card_engine_v2/repository.py` | Validação de invariantes do saldo/limite/contadores no runtime persistido; versão interna atualizada | Teste de rollback para saldo acima do limite |
| `tests/card_engine_v2/test_energy_economy.py` | Dez testes de integração e validação da economia alpha | Parte da suíte integral |
| `tests/card_engine_v2/test_deck_fatigue_runtime.py`, `test_playable_match.py` | Expectativas atualizadas para o novo release de ruleset v0.4 | Regressão integral |
| `docs/card-engine-v2-energy-economy-alpha-v0.1.md` | Contrato funcional, limites e decisões abertas | Revisão contra código e ruleset |
| `docs/scripts/test-card-engine-v2-playable-alpha-v0.5.py` | Runner da suíte da nova revisão | Runner executado localmente |
| `docs/card-engine-v2-playable-alpha-validation-v0.5.*` | Resultado verificável da suíte | Gerado pelo runner |
| `docs/card-game-handoff.md`, `docs/PACOTE-MANIFESTO.md`, `sistemas/card_engine_v2/README.md` | Estado/continuidade atualizados | Revisão cruzada |

## Resultado consolidado

- Suíte integral: **145/145**, zero falhas e zero testes ignorados.
- Compilação Python: aprovada.
- Staging histórico: 137 modelos, 27 permitidos em alpha e 110 bloqueados.
- Simulação Bo3: Player A venceu 2–1, 87 eventos, seis aplicações de fatigue e integridade SQLite `ok`.
- Simulação de combos/passivas/líderes: Player A 20–10, 44 eventos e integridade SQLite `ok`.
- Os cinco arquivos centrais do motor legado foram comparados por SHA-256 com a baseline e permanecem idênticos.

## Decisões importantes

- Nenhum custo numérico foi atribuído às 27 cartas ou aos líderes na baseline; os mapas de custos permanecem vazios. Preço ausente permite ação sem cobrança somente nesta alpha de transição.
- `rarity_id` permanece metadado classificatório conforme BUF-001 aprovado.
- `deck_cost_legacy` não é convertido em energia; é um campo de deck building e não um contrato de energia por turno.
- O saldo vive no runtime sidecar; CardInstance v7 e migrações SQL permanecem inalterados.
- Os cinco arquivos centrais do motor legado devem permanecer byte a byte idênticos ao baseline rev. 23.
