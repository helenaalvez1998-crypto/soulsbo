# Painel `/jogo`

A implementação ativa fica em `cogs/painel_jogo.py`.

O painel do Discord é uma entrada compacta: mostra coleção, recursos e desempenho do jogador e mantém apenas três destinos de navegação para o site, um recurso exclusivo do Discord e os controles contextuais.

## Layout atual

| Ação | Destino | Papel |
|---|---|---|
| Arena Gwent | `/#arena` | Abrir o modo Arena do portal |
| Deck e coleção | `/#deck` | Consultar coleção e montar o deck Gwent |
| Mercado e drops | `/#market` | Comprar pacotes e consultar histórico pessoal de drops |
| Ofícios | `/#oficios` | Acessar Forja, Transmutação, Linhagens e Rituais Ancestrais no site |
| Card Engine v2 · Alpha | `/card-engine-v2` | Abrir a experiência nova do motor v2 no site |
| Ritual de Convergência | Operação Discord | Sacrificar três exemplares do mesmo modelo/raridade para gerar um exemplar na raridade seguinte |
| Atualizar resumo | Embed atual | Reconsultar coleção, recursos, partidas e MMR |
| Voltar à NARA | Central `/nara` | Só aparece quando o painel foi aberto a partir da central |

## Destino dos botões antigos

| Botão antigo | Decisão | Justificativa |
|---|---|---|
| Minha coleção | Removido; usar Deck e coleção | A coleção completa já está no site |
| Histórico de drops | Agrupado em Mercado e drops | O histórico fica no portal, junto do mercado e dos pacotes |
| Estatísticas | Removido como botão | Os indicadores essenciais já aparecem no embed |
| Atualizar painel | Renomeado para Atualizar resumo | Mantém apenas a função de atualizar os indicadores |
| Abrir Coliseu no site | Substituído pelos destinos diretos | Evita um clique genérico antes de chegar à Arena ou ao Deck |
| Forja / Forja no site | Agrupados em Ofícios | A Forja do site concentra Lapidação (+1 poder por Almas) e Ascensão (raridade por Fragmentos); o endpoint agora encaminha cada ação para sua operação específica |
| Receitas de Linhagem | Agrupadas em Ofícios | Acesso pelo site e pela navegação contextual de Ofícios |
| Transmutação | Agrupada em Ofícios | Operação completa na página Laboratório |
| Rituais Ancestrais | Agrupados em Ofícios | Operação completa na página de Rituais Ancestrais |
| Biblioteca de Cartas | Removido do painel | Catálogo disponível no site |
| Cartas Geradas | Removido do painel | Arquivo pessoal disponível no site |
| Ateliê de Arte | Removido do painel | Ateliê já existe no portal |
| Partidas v2 · Alpha | Convertido em link do site | `/card-engine-v2` é agora a entrada do motor v2; evita duplicar a interface de deck e partida no Discord |
| Ritual de Convergência | Mantido | Não é o mesmo fluxo das Linhagens, dos Rituais Ancestrais ou da Transmutação; continua exclusivo do Discord |

## Hierarquia visual e segurança

- O embed usa o dourado do Coliseu como única cor de identidade.
- Os cinco destinos web ficam juntos na primeira linha e usam o estilo neutro padrão de links do Discord. Eles representam áreas principais, não cada operação individual.
- A Forja da web é a interface canônica para Lapidação e Ascensão. O endpoint diferencia `lapidar` (`coliseu_aprimorar_exemplar`) de `ascender` (`coliseu_evoluir_exemplar`), evitando que as duas escolhas consumam Fragmentos.
- A antiga Forja local do Discord estava incompleta: a seleção tentava habilitar um botão `Lapidar` que não existia nessa View. A remoção evita expor esse fluxo quebrado e direciona o jogador à Forja web corrigida.
- Convergência usa o estilo primário para destacar a única operação local do painel; a confirmação final do sacrifício usa estilo de perigo (vermelho), pois é irreversível.
- Atualizar e Voltar usam estilo secundário; Voltar só aparece quando aplicável.
- As etapas de seleção e confirmação verificam o dono do painel. O banco revalida posse, elegibilidade e se o exemplar está equipado antes de consumir qualquer carta.
- A lista da Convergência pagina em grupos de mesma carta e raridade para não separar as opções que precisam ser selecionadas juntas.
