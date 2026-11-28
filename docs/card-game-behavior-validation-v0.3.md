# Validação comportamental — runtime V76

**Data:** 2026-11-28  
**Estado:** 255/255 assertivas comportamentais aprovadas em 8 suítes; zero falhas no agregado.  
**Fonte de resultados:** `docs/card-game-behavior-validation-v0.3.json`.

## 1. Suítes executadas

| Suíte | Assertivas | Aprovadas | Falhas |
|---|---:|---:|---:|
| Compra inicial e mulligan | 13 | 13 | 0 |
| Identidades ativas | 33 | 33 | 0 |
| Habilidades genéricas de unidade | 39 | 39 | 0 |
| Efeitos de ciclo de rodada | 7 | 7 | 0 |
| Cartas especiais | 18 | 18 | 0 |
| Os doze líderes | 26 | 26 | 0 |
| Combos e passivas de facção | 87 | 87 | 0 |
| Política de combos | 32 | 32 | 0 |
| **Total** | **255** | **255** | **0** |

O conjunto de fim de rodada confirma que `gloria` e `sobrevivente` compartilham o mesmo comportamento: a unidade elegível permanece no campo após vencer a rodada. A carta V76 `Cantor do Último Hino` usa o segundo alias e possui teste direto.

## 2. Liderança de Os Esquecidos

| Líder | Comportamento exercitado | Negativo/limite |
|---|---|---|
| Papa Esquecido | +1 em aliados da facção na fileira escolhida | exige aliado dos Esquecidos |
| Abadessa das Ruínas | purifica até 2 aliados afetados de maior poder efetivo na fileira e concede +1 | exige aliado afetado elegível |
| Mártir da Vigília | revive a unidade mais forte dos Esquecidos com poder-base até 5, concede +1 e limpa estados | exige unidade elegível no descarte |

Os doze líderes são verificados pelo registro `LEADERS`, pelos handlers de `aplicar_jogada()` e pelo fallback do site. Ações e efeitos continuam dentro do fluxo normal de partida.

## 3. Auditoria de sobreposição de combos V76

A enumeração atual percorre 92 unidades catalogadas com tags de sinergia e 27 combos registrados:

| Medida | Resultado |
|---|---:|
| Pares ordenados | 8.372 |
| Pares com mais de um combo elegível | 720 (8,6001%) |
| Trincas ordenadas | 753.480 |
| Trincas com dois ou mais combos em jogadas sucessivas | 24.886 (3,3028%) |
| Gatilhos posteriores que contribuíram com tag exigida | 24.886/24.886 |
| Ativações solo | 0 |

A carta que completa um combo precisa contribuir com ao menos uma tag exigida; os participantes são instâncias distintas e respeitam o mínimo de cada combo. A enumeração não equivale a taxa real de ativação nem a win rate.

## 4. Alterações V76 exercitadas

- 30 unidades de combate por facção; 16 unidades novas para Os Esquecidos e reposições nas demais facções.
- 12 líderes, três por facção; dois líderes novos com efeitos testados.
- Decks-base de 9 unidades e 1 especial, todos alinhados à facção.
- Reclassificação canônica de snapshots Luteranos antigos; nomes e lore são reidratados pelo ID do catálogo.
- Geração de recompensas de jogos e patentes agora inclui Os Esquecidos.
- Todos os títulos do índice têm até 28 caracteres e não há duplicatas.
- As 25 novas cartas têm habilidades registradas e executadas por handlers já existentes; `sobrevivente` foi verificado no ciclo de rodada.

## 5. Limitações

A enumeração de combos utiliza estados sintéticos em memória e IDs de unidade distintos; não constrói todas as combinações legais de decks de 12 cartas e não mede win rate. Os testes de unidade exercitam efeitos específicos, mas não equivalem a uma simulação exaustiva de todas as ordens de jogada, clima, relíquias, líderes, IA, Discord, API hospedada ou banco de produção. O pacote está validado localmente, mas não foi implantado no host.
