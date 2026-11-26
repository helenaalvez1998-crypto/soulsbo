# Revisão de identidade das cartas — V82

## Objetivo
Eliminar da ficha pública das cartas os rótulos legados Força, Destreza e Magia. A classificação exibida passa a usar exclusivamente categoria, facção, fileira e papel de combate.

## Contrato público
- Categoria: Unidade ou Especial.
- Facção: Ordem Áurea, Véu Carmesim ou Lua Negra.
- Fileira: Corpo a Corpo, Longa Distância ou Cerco (cartas especiais são exibidas como Especial).
- Papel: classificação tática derivada da facção e da fileira; cartas especiais usam Tática.
- Campo `identidade`: descrição compacta da classificação completa.
- O campo legado `tipo` não é serializado para a interface nem devolvido por `preparar_carta`.

## Compatibilidade
Os rótulos antigos permanecem apenas como fallback interno para interpretar cartas/decks antigos já persistidos. Eles não são usados como informação pública da carta. A validação de facção agora prioriza `faccao`.

## Auditoria
- 122 cartas estáticas verificadas: todas possuem categoria, facção, fileira e papel válidos.
- 41 cartas dinâmicas amostradas (recompensas de jogos e patentes): todas possuem a classificação completa.
- Nenhuma das 163 cartas auditadas expõe o campo `tipo`.
- A ficha do modal passa a exibir categoria, facção, fileira e papel tático.
- Cache das artes atualizado para V30.

## Testes
- `tests/test_gwent_catalog_audit_v77.py`
- `tests/test_card_catalog_quality.py`
- `tests/test_gwent_reward_identity_v76.py`
- `tests/test_gwent_competitivo_v74.py`
- `tests/test_gwent_expansao_v75.py`
- `tests/test_elden_gwent.py`

A suíte direcionada deve ser executada após a atualização do ambiente de produção.
