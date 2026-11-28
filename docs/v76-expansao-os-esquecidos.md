> **Nota de continuidade:** este documento registra a V76 como histórico. A V77 supersede as contagens de especiais e nomes: quatro facções com 30 unidades + 11 especiais e três líderes cada; catálogo com 179 modelos (164 no pacote); títulos únicos limitados a 27 caracteres. Consulte `docs/v77-normalizacao-faccoes-e-nomes.md` e `docs/AUDITORIA-FIDELIDADE-CARTAS.md/.json` para o estado vigente.

# Revisão V76 — expansão de Os Esquecidos e padronização do catálogo

**Estado:** implementado no código-fonte do pacote; não implantado no servidor hospedado.

## Equilíbrio de facções

A contagem foi fechada por unidades de combate, que são a base de composição/validação dos decks. Cada facção tem exatamente 30 unidades. As cartas especiais continuam separadas da contagem de unidades, conforme `contar_faccoes_deck()`.

| Facção | Unidades | Especiais | Líderes |
|---|---:|---:|---:|
| Ordem Áurea | 30 | 8 | 3 |
| Véu Carmesim | 30 | 7 | 3 |
| Lua Negra | 30 | 11 | 3 |
| Os Esquecidos | 30 | 1 | 3 |

## Líderes de Os Esquecidos

| ID | Líder | Efeito canônico
|---|---|---|
| `lider_papa_esquecido` | Papa Esquecido | Concede +1 de bônus às unidades dos Esquecidos na fileira escolhida. |
| `lider_abadessa_ruinas` | Abadessa das Ruínas | Purifica até 2 aliados dos Esquecidos afetados e de maior poder efetivo na fileira escolhida, removendo Sangramento, Geada, Podridão e Loucura. Cada um recebe +1 de bônus. |
| `lider_martir_vigilia` | Mártir da Vigília | Ressuscita do descarte a unidade mais forte dos Esquecidos com poder-base até 5 na fileira escolhida, com +1 de bônus. |

As novas unidades usam os seis combos de fé existentes (`Glória Divina`, `Devoção`, `Evangelho`, `Irmandade Esquecida`, `Soberania Divina` e `Sacerdócio`); o registro total permanece em 27 combos, sem introduzir uma política paralela.

Os três líderes da facção usam o fluxo de seleção e ativação existente: Papa Esquecido, Abadessa das Ruínas e Mártir da Vigília. Os efeitos são resolvidos em `sistemas/gwent.py` e suas descrições vêm do registro `LEADERS`, consumido pelo site/API.

## Novas cartas da revisão V76

| Nome | Facção | Raridade | Poder | Custo | Fileira | Habilidade |
|---|---|---:|---:|---:|---|---|
| Cavaleiro Penitente | Os Esquecidos | Comum | 4 | 1 | melee | `escudo_ferro` |
| Peregrino das Cinzas | Os Esquecidos | Comum | 3 | 1 | ranged | `legado` |
| Guardião dos Vitrais | Os Esquecidos | Comum | 4 | 1 | siege | `estandarte` |
| Irmã das Ruínas | Os Esquecidos | Comum | 3 | 1 | ranged | `—` |
| Confessor Velado | Os Esquecidos | Rara | 5 | 2 | ranged | `devoto` |
| Guardiã do Santuário | Os Esquecidos | Rara | 5 | 2 | melee | `guardiao_fileira` |
| Cantor do Último Hino | Os Esquecidos | Rara | 4 | 2 | ranged | `sobrevivente` |
| Diaconisa do Altar | Os Esquecidos | Rara | 5 | 2 | siege | `escolha_ritmo` |
| Oráculo Silencioso | Os Esquecidos | Épica | 6 | 3 | siege | `eco_arcano` |
| Serafim Caído | Os Esquecidos | Épica | 6 | 3 | ranged | `gloria` |
| Mártir Cinzento | Os Esquecidos | Épica | 6 | 3 | melee | `vinganca` |
| Prelado das Ruínas | Os Esquecidos | Épica | 6 | 3 | siege | `sinergia_faccao` |
| Arauto do Cântico | Os Esquecidos | Lendária | 7 | 4 | ranged | `estandarte` |
| Guardião do Relicário | Os Esquecidos | Lendária | 7 | 4 | melee | `ressurgir` |
| Santo Sem Nome | Os Esquecidos | Mítica | 8 | 5 | siege | `sinergia_faccao` |
| Anjo do Último Selo | Os Esquecidos | Mítica | 8 | 5 | ranged | `gloria` |
| Guardião do Graal | Ordem Áurea | Rara | 4 | 2 | melee | `guardiao_fileira` |
| Sentinela da Graça | Ordem Áurea | Rara | 5 | 2 | ranged | `estandarte` |
| Tecelã da Névoa | Lua Negra | Rara | 4 | 2 | siege | `eco_arcano` |
| Cavaleiro Astral | Lua Negra | Rara | 5 | 2 | melee | `resistencia_climatica` |
| Flagelante de Mohgwyn | Véu Carmesim | Rara | 4 | 2 | melee | `legado` |
| Lâmina Hemática | Véu Carmesim | Rara | 5 | 2 | ranged | `contragolpe` |
| Carrasco do Altar | Véu Carmesim | Épica | 6 | 3 | melee | `devorar` |
| Arauto do Sangue | Véu Carmesim | Épica | 6 | 3 | ranged | `estandarte` |
| Cão Rubro | Véu Carmesim | Comum | 4 | 1 | melee | `instinto` |

A expansão contém 16 unidades novas para Os Esquecidos e reposições de equilíbrio: 2 para Ordem Áurea, 2 para Lua Negra e 5 para Véu Carmesim. Com seis cartas Luteranas existentes corrigidas de facção, cada facção termina com 30 unidades.

## Reclassificação preservando IDs

Os IDs abaixo foram mantidos para preservar coleções, decks e instâncias salvas; o catálogo passa a ser a fonte canônica da facção. `faction_for_card()` e `preparar_carta()` agora consultam o ID canônico antes de confiar nos campos de snapshots antigos.

| ID preservado | Nome atual | Facção antiga | Facção atual |
|---|---|---|---|
| `luterano_apostolo` | Apóstolo Esquecido | Ordem Áurea | Os Esquecidos |
| `luterano_profeta` | Profeta Esquecido | Ordem Áurea | Os Esquecidos |
| `luterano_pastor` | Pastor Esquecido | Véu Carmesim | Os Esquecidos |
| `luterano_vigia` | Vigia da Noite | Véu Carmesim | Os Esquecidos |
| `luterano_mistico` | Místico Esquecido | Lua Negra | Os Esquecidos |
| `luterano_anjo2` | Anjo de Segunda Ordem | Lua Negra | Os Esquecidos |
| `gwent_especial_requiem` | Chamado dos Mortos | Lua Negra | Os Esquecidos |

## Simplificação dos nomes

O limite atual é 28 caracteres por título. A revisão preserva os IDs de carta e altera somente o nome apresentado. As recompensas dinâmicas de jogo e de patente também passaram a usar títulos compactos.

| Antes | Depois |
|---|---|
| Godfrey, Primeiro Lorde Prístino | Godfrey, Primeiro Lorde |
| Sentinela do Portão de Leyndell | Sentinela de Leyndell |
| Leitora de Estrelas de Sellia | Leitora de Sellia |
| Cavaleiro da Dinastia Mohgwyn | Cavaleiro de Mohgwyn |
| Cavaleiros de sangue juramentados | Cavaleiros Juramentados |
| Bibliotecária de Raya Lucaria | Bibliotecária de Raya |
| Fia, Companheira do Leito de Morte | Fia, Leito de Morte |
| Recusante da Mansão Vulcânica | Recusante Vulcânico |
| Erudito das Pedras Cintilantes | Erudito das Pedras |
| Apóstolo da Pele Divina Errante | Apóstolo Errante |
| Mestre Ferreiro de Volcano Manor | Ferreiro de Gelmir |
| Cavaleiro Consagrado do Haligtree | Cavaleiro Consagrado |
| Juramento Primordial do Crisol | Juramento Primordial |
| Veterano do Juramento Dourado | Veterano do Juramento |
| Acólito da Dinastia Sanguínea | Acólito Sanguíneo |
| Carrasco da Procissão Carmesim | Carrasco Carmesim |
| Caçador das Catacumbas de Mohgwyn | Caçador de Mohgwyn |
| Cartógrafo das Cidades Eternas | Cartógrafo de Nokron |
| Aprendiz de Feitiçaria Cariana | Aprendiz Cariano |
| Maliketh, Guardião da Morte Destinada | Maliketh, Guardião da Morte |
| Besta Prístina, Arauto da Vontade Maior | Besta Prístina |

Outros nomes dinâmicos: `carta_jogo()` utiliza arquétipos curtos por facção; `carta_patente()` usa diretamente o nome da patente. Verificações atuais: todos os 162 registros têm título não vazio com até 28 caracteres e não há nomes duplicados no catálogo gerado.

## Decks-base

Os quatro decks-base foram corrigidos para não misturar cartas de facções diferentes. Cada um contém 9 unidades da própria facção e 1 especial da mesma facção. A regra normal do construtor de decks (12 cartas) não foi alterada. As rotas de recompensa `carta_jogo()` e `carta_patente()` agora também podem gerar cartas dos Esquecidos; antes, elas só distribuíam recompensas entre as outras três facções.

O especial `Chamado dos Mortos` (`gwent_especial_requiem`) passou a pertencer a Os Esquecidos, coerente com o tema de retorno dos mortos e com o deck-base da facção.

## Arte e interface

- Retratos padrão dedicados adicionados para Abadessa das Ruínas e Mártir da Vigília em `site/assets/leaders/`.
- Os dois líderes foram incluídos no fallback da interface, no mapeamento de arte e nas escolhas de fileira.
- A pintura procedural reconhece Abadessa, Mártir e Serafim para selecionar arquétipos próprios.
- A versão das artes foi incrementada para invalidar caches anteriores.

## Validação

- Catálogo: 162 modelos; 162 publicados no contrato do site.
- Unidades: 120 no total; 30 por facção.
- Líderes: 12; 3 por facção.
- Título máximo: 28 caracteres; nomes duplicados: 0.
- Auditoria de efeitos: OK; 0 divergências estruturais.
- Testes: 315 aprovados + 106 subtestes parametrizados.
- `python -m py_compile` e `node --check site/app.js`: aprovados.

## Fronteira de implantação

As alterações estão aplicadas ao código do pacote. Não foi possível instalar no host, reiniciar o bot ou consultar o banco externo a partir deste ambiente. O Card Engine v2 alpha separado mantém seus snapshots históricos de 137 modelos; essa base de staging não é o catálogo público do runtime legado e não foi misturada com esta expansão.
