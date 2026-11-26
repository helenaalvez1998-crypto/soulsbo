# 🎴 PROJETO COMPLETO — NARABOT CARD GAME: "FORJA DAS ALMAS"
## Elden Ring / Dark Souls Card Game — Redesign Completo v1.0

---

## 📋 ÍNDICE
1. [Análise do Sistema Atual](#1-análise)
2. [Filosofia de Design](#2-filosofia)
3. [Sistema de Cartas Detalhado](#3-cartas)
4. [Facções e Identidade Visual](#4-facções)
5. [Raridades e Poder](#5-raridades)
6. [Evolução com Risco — A Forja](#6-evolução)
7. [Gameplay Simplificado](#7-gameplay)
8. [Sistema de Conquistas](#8-conquistas)
9. [Melhorias Visuais](#9-visual)
10. [Regras Oficiais](#10-regras)
11. [Roadmap de Implementação](#11-roadmap)

---

## 1. ANÁLISE DO SISTEMA ATUAL

### ✅ Pontos Fortes (Manter e Expandir)
- Gwent Engine (3 fileiras) funcional
- Facções Temáticas estruturadas
- Raridades (7 níveis) já existem
- Transmutação básica com probabilidades
- Arte procedural com templates
- Sistema de afinidades (12 tipos)

### ❌ Problemas Críticos
1. Complexidade excessiva (18+ habilidades únicas)
2. Evolução sem risco real (falha não destrói carta)
3. Progressão fraca (loop viciante ausente)
4. Feedback visual limitado (raridade só muda moldura)
5. Falta de tutorial integrado

---

## 2. FILOSOFIA DE DESIGN

### 💡 Conceito: "A Forja das Almas"
> *"Toda carta tem uma alma. Evoluí-la é forjar essa alma no fogo do risco. Você pode ganhar poder inimaginável... ou perder tudo em cinzas."*

### 🏛️ 3 Pilares
1. **Simplicidade Enganosa**: "Jogue cartas. Some poder. Vença."
2. **Risco Constante**: Evolução pode destruir carta (10-90% risco)
3. **Recompensa Variável**: Vitórias raras = mais satisfatórias

---

## 3. SISTEMA DE CARTAS

### Estrutura
- **3 Posições táticas de unidade**: Corpo a corpo, Longa distância e Cerco
- **Facção** é um campo independente da posição tática: Ordem Áurea, Véu Carmesim, Lua Negra ou Os Esquecidos
- **Cartas especiais** não ocupam uma fileira de unidade
- **7 Raridades**: Comum → Singular
- **5 Níveis de Evolução**: Cada um com risco crescente

### Facções
- 🔵 **Ordem Áurea**: defesa, escudos, disciplina e proteção
- 🔴 **Véu Carmesim**: agressão, sangramento, sacrifício e pressão
- 🟣 **Lua Negra**: temas lunares/arcaicos, gravidade, congelamento e controle
- ⚪ **Os Esquecidos**: resistência, legado e cooperação

Força, Destreza e Magia são classificações de um sistema antigo e não devem ser usadas como tipo, fileira ou classe de combate. Magia pode continuar como tema narrativo ou habilidade explicitamente definida.

---

## 4. RARIDADES

| Raridade | Cor | Poder | Custo | Drop % | Efeito |
|----------|-----|-------|-------|--------|--------|
| Comum | Cinza | 3-5 | 1 | 69.47% | Base |
| Rara | Azul | 4-6 | 2 | 22.02% | +1 poder |
| Épica | Roxo | 5-7 | 3 | 7.01% | +2 poder, board |
| Lendária | Dourado | 6-8 | 4 | 1.00% | +3 poder, game-changer |
| Mítica | Vermelho | 8-9 | 5 | 0.50% | +4 poder, define deck |
| Primordial | Preto | 8-9 | 6 | Eventos | Poder máx |
| Singular | Arco-íris | 8-10 | 0 | Criação | Quebra regras |

---

## 5. EVOLUÇÃO COM RISCO — A FORJA

### 🔥 Mecânica
Cada carta evolui até nível 5. Cada evolução aumenta poder mas tem risco de destruir a carta.

| Nível | Chance Sucesso | Risco Perda |
|-------|----------------|-------------|
| 0→1 | 80-100% | 0-20% |
| 1→2 | 60-80% | 20-40% |
| 2→3 | 40-60% | 40-60% |
| 3→4 | 25-45% | 55-75% |
| 4→5 | 10-30% | 70-90% |

### 💀 Falha = Carta Destruída
- Carta permanentemente perdida
- Almas e XP perdidos
- Aviso prévio com % exata

### 🛡️ Proteção
- Amuleto de Proteção (consumível raro)
- Anula destruição mas falha = sem evolução

---

## 6. GAMEPLAY SIMPLIFICADO

### 🎯 Loop Central (5 min para aprender)
1. **Comprar 10 cartas** (3 de cada facção)
2. **Jogar 1 carta por turno** em 1 das 3 fileiras
3. **Somar poder** da fileira
4. **Maior poder total vence**

### ⚡ Ações por Turno
- Jogar carta (custo em energia)
- Ativar habilidade (se condição atendida)
- Passar turno

### 🏆 Condições de Vitória
- Reduzir vida do oponente a 0 (vida = 20)
- Oponente desiste
- Oponente fica sem cartas

---

## 7. CONQUISTAS

### 🏅 Sistema de Feitos
- **Primeiro Sangue**: Vença 1 partida
- **Colecionador**: Tenha 50 cartas
- **Forjador**: Evolua 10 cartas com sucesso
- **Apostador**: Evolua 5 cartas até nível 5
- **Lenda**: Tenha 1 carta Singular
- **Sobrevivente**: Falhe 3 evoluções e continue jogando
- **Perfeccionista**: Tenha 100% das cartas Comuns
- **Dedicado**: Jogue 100 partidas

### 🎁 Recompensas
- Títulos cosméticos
- Molduras especiais
- Emotes
- Acesso antecipado a eventos

---

## 8. MELHORIAS VISUAIS

### 🎨 Feedback por Raridade
- **Comum**: Sem brilho
- **Rara**: Brilho azul suave pulsante
- **Épica**: Aura roxa + partículas
- **Lendária**: Chamas douradas + brilho
- **Mítica**: Aura vermelha + raios
- **Primordial**: Escuridão + estrelas
- **Singular**: Iridescente + FX únicos

### ✨ Animações
- Carta sendo jogada: desliza da mão para board
- Habilidade ativada: flash + partículas
- Evolução bem-sucedida: explosão de luz
- Evolução falha: carta se despedaça em cinzas

---

## 9. SISTEMA DE APOSTAS — "APOSTA DAS ALMAS"

### 🎲 Apostas com Cartas (Wager)
**Conceito**: Aposte sua carta contra a do oponente. Vencedor leva ambas.

**Modos de Aposta**:
1. **Amigável** — Sem risco real (cartas retornam ao final)
2. **Arriscada** — Perdedor perde a carta apostada permanentemente
3. **Lendária** — Apenas cartas Míticas/Primordiais/Singulares
4. **Blind Wager** — Cartas reveladas apenas após aposta confirmada

**Regras**:
- Ambas as cartas devem ter **raridade equivalente** (±1 nível)
- Aposta bloqueada: cartas não podem ser usadas/evoluídas durante
- Vencedor ganha a carta do oponente + **bônus de Denários**
- Em empate: ambas as cartas retornam (sem perda)

### 💰 Apostas com Denários (Gold Betting)

**Denários** — Moeda principal do jogo (ganha em partidas, missões, drops)

**Tipos de Aposta**:
| Tipo | Mínimo | Máximo | Multiplicador |
|------|--------|--------|---------------|
| Partida Rankeada | 50 | 5.000 | 1.8x |
| Partida Casual | 10 | 500 | 1.5x |
| Torneio Semanal | 500 | 50.000 | 2.5x |
| Duelo de Chefes (PvE) | 100 | 10.000 | 3.0x |

**Sistema de Odds Dinâmicas**:
- Odds baseadas em **MMR diferença** entre jogadores
- Ex: MMR 1500 vs 1300 → odds 1.4x para favorito, 2.2x para underdog
- Atualização em tempo real antes da confirmação

**Comissão da Casa**: 5% do pote vai para o "Tesouro da Fogueira" (eventos comunitários)

### 🏆 Apostas em Torneios (Spectator Betting)
- Espectadores apostam em quem vai vencer
- Mínimo 10 Denários
- Odds fixadas no início do torneio
- Payout ao final: vencedor leva pool proporcional

### ⚠️ Proteções Anti-Abuso
- Limite diário: 10.000 Denários apostados
- Cooldown 5 min entre apostas arriscadas
- Cartas apostadas não podem ser sacrificadas na Forja
- Histórico público de apostas (transparência)

---

## 10. REGRAS OFICIAIS

### 📜 Setup
1. Cada jogador tem 20 de vida
2. Deck de 30 cartas (máx 3 cópias por carta)
3. Mão inicial: 4 cartas
4. Sorteio decide quem começa

### 🎮 Turno
1. Ganhar 1 energia (máx 5)
2. Jogar cartas (custo em energia)
3. Ativar habilidades
4. Passar turno

### ⚔️ Combate
- Poder total por fileira
- Dano = poder inimigo - poder aliado
- Vida reduzida pelo dano total

### 🏁 Fim de Jogo
- Vida 0 = derrota
- Deck vazio = dano crescente por turno
- Empate se ambos 0 vida no mesmo turno

---

## 10. ROADMAP

### Fase 1: Fundação (2 semanas)
- [ ] Implementar sistema de risco na forja
- [ ] Corrigir descrições de habilidades
- [ ] Adicionar tutorial básico
- [ ] Implementar apostas de cartas e Denários
- [ ] Corrigir lógica de risco de evolução

### Fase 2: Conteúdo (3 semanas)
- [ ] 50 cartas novas temáticas Souls
- [ ] Sistema de conquistas completo
- [ ] Melhorias visuais por raridade

### Fase 3: Polish (2 semanas)
- [ ] Animações de evolução
- [ ] Balanceamento
- [ ] Testes com comunidade

### Fase 4: Lançamento (1 semana)
- [ ] Evento de lançamento
- [ ] Recompensas exclusivas
- [ ] Feedback gathering

---

*Documento vivo — atualizar conforme implementação progride.*