# Auditoria de fileiras e nomenclatura — V80

## Objetivo
Padronizar as informações exibidas nas cartas: unidades devem ser identificadas por facção e fileira de combate; cartas especiais devem ser identificadas como especiais. Os rótulos legados Força, Destreza e Magia não devem aparecer como atributos de combate na interface.

## Alterações
- A interface do catálogo e da inspeção deixou de usar `tipo` como alternativa visual para facção.
- A contagem de facções no construtor de deck usa a facção resolvida da carta, sem fallback visual para os tipos antigos.
- Cartas sem habilidade individual agora exibem `Sem habilidade especial`, em vez de `Força pura`.
- Os textos das habilidades de sinergia foram atualizados para mencionar Ordem Áurea, Véu Carmesim e Lua Negra.
- As sinergias correspondentes consultam a facção da unidade, preservando compatibilidade com cartas antigas salvas que ainda só tenham `tipo`.
- Descrições de recompensas geradas dinamicamente foram atualizadas para usar a facção, sem tratar Força/Destreza/Magia como arquétipos apresentados ao jogador.

## Fileiras
- Todas as 122 cartas estáticas do catálogo foram verificadas.
- As 122 possuem uma fileira mecânica válida (`melee`, `ranged` ou `siege`) no payload canônico.
- Na interface, as unidades exibem Corpo a Corpo, Longa Distância ou Cerco.
- Cartas especiais continuam identificadas como Especial; não recebem uma fileira de unidade como classificação visual.

## Compatibilidade preservada
Os campos e mapas legados `tipo`, `TYPE_ROW` e `FACTIONS` permanecem no modelo interno para leitura de registros antigos, geração determinística e compatibilidade com decks persistidos. Eles não são a classificação apresentada ao jogador. A remoção física desses campos exige migração de dados e revisão mais ampla das sinergias, portanto não foi feita nesta versão.

## Validação
- `node --check site/app.js`: aprovado.
- Auditoria local do catálogo estático: 122/122 cartas com fileira válida.
- Testes direcionados: 63 aprovados; 16 falhas em `test_card_catalog_quality.py` relativas a expectativas de exibição de habilidades de identidade já divergentes do comportamento atual. Essas falhas não foram introduzidas pelas mudanças de fileira e exigem revisão separada.
