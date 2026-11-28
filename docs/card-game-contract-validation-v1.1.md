# Validação do contrato canônico de cartas e registry v1.1

**Data:** 2026-11-27  
**Estado:** aprovada dentro do escopo estrutural; não representa integração do runtime nem aprovação de balanceamento.

Relatório estruturado: `docs/card-game-contract-validation-v1.1.json`.

## O que foi validado

1. **35/35 testes unitários** com `python docs/scripts/test-card-contract-v1.py`.
2. Os dois schemas Draft 2020-12 — definição de carta e registry de efeitos/combos — passaram `Draft202012Validator.check_schema()`; os dois exemplos foram aceitos.
3. O CLI `docs/scripts/validate-card-catalog-v1.py` aceitou um catálogo sintético válido com quatro modelos e três unidades puras (75%) e rejeitou um catálogo cujo `ally_bonus` excedia o máximo declarado pelo efeito.
4. O snapshot legado com 137 modelos foi gerado duas vezes e produziu o mesmo SHA-256: `df383e6aa10634cf4a0c5d00594e2cbc9f1edb071c95da2ce3119096375297c2`.
5. Os hashes dos cinco arquivos centrais de runtime permaneceram iguais ao baseline: `sistemas/cartas.py`, `sistemas/gwent.py`, `bot.py`, `database.py` e `site/app.js`.

## Novas garantias do contrato

- Efeitos têm `effect_id` único, `resolution_handler` e `timing` declarados.
- Os parâmetros de um efeito podem declarar tipo, mínimo, máximo, enum, obrigatoriedade e política de parâmetros adicionais.
- O validador rejeita parâmetro ausente, desconhecido, com tipo errado ou fora dos limites.
- Combos exigem `minimum_participants >= 2` e prioridade inteira positiva e única.
- O CLI valida o registry antes do catálogo, e depois verifica cada `effect_params` contra a definição do efeito referenciado.

## Comandos reproduzíveis

```bash
python docs/scripts/test-card-contract-v1.py
python docs/scripts/validate-card-json-schemas-v1.1.py
python docs/scripts/build-card-catalog-baseline-v0.1.py
python docs/scripts/validate-card-catalog-v1.py --catalog CAMINHO/catalog-v1.json --registry CAMINHO/effect-registry-v1.json
```

`validate-card-json-schemas-v1.1.py` requer a dependência opcional `jsonschema`; ela não é dependência do bot. O validador Python e os 35 testes do contrato não exigem biblioteca externa.

## Limites explícitos

- Não existe ainda `catalog-v1.json` com o redesenho dos 137 modelos.
- `effect-registry.example.v1.json` é apenas exemplo; não representa o registry completo aprovado.
- O módulo `sistemas/card_contract.py` ainda não é importado pelo runtime antigo.
- A suíte de 251 assertions e os 12 cenários stateful referem-se à última validação anterior do runtime. Não foram repetidos nesta etapa porque nenhum arquivo funcional do motor foi modificado.
- Fórmulas EFP/custo/raridade, orçamento do deck, distribuição final, nomes, lore, facções e seleção de efeitos continuam pendentes.

## Próximo passo

Construir o registry consolidado a partir do inventário de 59 habilidades genéricas, 22 identidades, 27 combos, 10 líderes e seis efeitos de relíquia. Cada entrada precisa de handler real, timing, gatilho, alvos, duração, stacking, parâmetros tipados, texto, testes e decisão `keep/merge/redesign/remove`. Só depois aprovar o balanceamento e produzir o catálogo autoral.
