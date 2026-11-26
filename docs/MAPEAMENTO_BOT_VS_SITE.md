# 🗺️ MAPEAMENTO: BOT vs SITE

Objetivo: tudo o que o bot faz deve estar no site, com versão visualmente melhor.

---

## 1. EXISTENTES EM AMBOS (já mapeados)

| Funcionalidade | Bot (Discord) | Site (HTML/API) | Status |
|----------------|---------------|------------------|--------|
| Transmutação | ✅ Comando slash | `/transmutacao` + API | ✅ Completo |
| Linhagens | ✅ Comando slash | `/linhagens` + API | ✅ Completo |
| Rituais Ancestrais | ✅ Comando slash | `/rituais-ancestrais` + API | ✅ Completo |
| Forja (Evolução) | ✅ Comando slash | `/forja` + API | ✅ Completo |
| Cartas Geradas | ✅ Comando slash | `/cartas-geradas` + API | ✅ Completo |
| Ateliê de Arte | ✅ Comando slash | `/atelie-arte` + API | ✅ Completo |
| Gwent (Batalha) | ✅ Comando slash | `/gwent` + API | ✅ Completo |

---

## 2. EXISTENTES NO SITE, FALTAM NO BOT

| Funcionalidade | Site | Bot | Ação |
|----------------|------|-----|------|
| Portal Comunidade | ✅ | ❌ | Manter no site (é web-only) |
| Loja Digital | ✅ | ❌ | Manter no site (é web-only) |
| Perfil/Santuário | ✅ | ❌ | Manter no site (é web-only) |
| Chat NARA | ✅ | ❌ | Manter no site (é web-only) |

---

## 3. EXISTENTES NO BOT, FALTAM NO SITE ❌ CRÍTICO

| Funcionalidade | Bot | Site | Ação Necessária |
|----------------|-----|------|-----------------|
| **Evolução com Risco** | ✅ `sistemas/evolucao_risk.py` | ❌ NÃO | Criar página `/evolucao` + API |
| **Sistema de Apostas** | ✅ `sistemas/apostas.py` | ❌ NÃO | Criar página `/apostas` + API |
| **Ranking Geral** | ✅ Comando slash | ❌ NÃO | Criar página `/ranking` + API |
| **Perfil do Jogador** | ✅ Comando slash | ❌ NÃO | Criar página `/perfil` + API |
| **Coleção de Cartas** | ✅ Comando slash | ❌ NÃO | Criar página `/colecao` + API |
| **Deck Builder Gwent** | ✅ Comando slash | ❌ NÃO | Criar página `/deck` + API |
| **Economia (Denários)** | ✅ Comando slash | ❌ NÃO | Criar página `/economia` + API |
| **Conquistas** | ✅ Comando slash | ❌ NÃO | Criar página `/conquistas` + API |
| **Tutorial** | ✅ Comando slash | ❌ NÃO | Criar página `/tutorial` + API |
| **Eventos** | ✅ Comando slash | ❌ NÃO | Criar página `/eventos` + API |

---

## 4. PRIORIDADE DE IMPLEMENTAÇÃO

### Fase 1: Core (Essencial)
1. `/evolucao` — Sistema de evolução com risco (já implementado no módulo)
2. `/apostas` — Sistema de apostas (já implementado no módulo)
3. `/ranking` — Ranking geral de jogadores
4. `/colecao` — Visualização da coleção de cartas

### Fase 2: Gameplay
5. `/deck` — Deck builder para Gwent
6. `/perfil` — Perfil do jogador
7. `/conquistas` — Sistema de conquistas

### Fase 3: Social/Economia
8. `/economia` — Gestão de Denários e recursos
9. `/eventos` — Eventos e desafios
10. `/tutorial` — Tutorial interativo

---

## 5. ARQUITETURA DO SITE

O site deve ser a interface principal (visual bot):
- Toda funcionalidade do bot acessível via web
- Design moderno inspirado em Elden Ring/Dark Souls
- Responsivo e otimizado para mobile
- Animações e feedback visual ricos
- PWA (Progressive Web App) para uso offline básico

---

## 6. PRÓXIMOS PASSOS

1. Criar as páginas HTML faltantes
2. Implementar as APIs correspondentes no site_hub.py
3. Conectar frontend ao backend via fetch
4. Testar fluxo completo
5. Documentar URLs e endpoints
