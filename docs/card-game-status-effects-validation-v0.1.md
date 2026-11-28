# Validação da auditoria de estados — v0.1

**Data:** 2026-11-27  
**Status:** proposta candidata, ainda não aprovada e não conectada ao runtime.

## Conteúdo validado

- Quatro estados: Geada, Podridão Escarlate, Sangramento e Loucura Frenética.
- 15 aplicações mapeadas: sete especiais, cinco identidades, dois líderes e uma relíquia.
- Cinco caminhos de purificação: dois líderes, uma identidade, um especial e uma relíquia.
- Schema JSON Schema Draft 2020-12 e instância do registry aprovados.

## Testes executados

| Suite | Resultado |
|---|---:|
| `test-card-status-candidate-v0.1.py` | 41/41 |
| `test-card-contract-v1.py` | 35/35 |
| `test-effect-catalog-candidate-v0.1.py` | 23/23 |
| `test-effect-semantic-audit-v0.1.py` | 11/11 |
| `summarize-card-game-behavior-v0.3.py` | 251/251 em oito suites |
| `assert-full-match-stateful-v0.1.py` | 12/12 |

Os totais pertencem a suites de escopos diferentes; não devem ser somados como se fossem testes independentes de cada carta. As suites legadas validam regressões do motor antigo. Elas não aprovam automaticamente os comportamentos que a proposta candidata pretende corrigir.

## Riscos legados confirmados

1. Malenia pode repetir a corrosão de bônus de Podridão quando o alvo já tem duas marcas.
2. Oráculo da Geada pode receber bônus novamente mesmo quando o alvo já está no limite.
3. `_aplicar_potencia_raridade()` pode adicionar uma segunda alteração a bônus após a consequência de um estado.
4. Algumas aplicações por raridade escolhem os primeiros alvos pela ordem do tabuleiro, não por uma regra explícita de prioridade.
5. `_resolve_round()` retorna no encerramento terminal antes do bloco de limpeza dos estados.

## Integridade do runtime nesta etapa

Os hashes dos cinco arquivos funcionais principais foram comparados com as mesmas entradas do ZIP mestre aberto no início da etapa. Todos permaneceram idênticos:

| Arquivo | SHA-256 | Igual ao ZIP de entrada |
|---|---|---|
| `sistemas/gwent.py` | `f69e8865759862ddc5bef9ff26ee2ddb43bcfbe33d3e61c985d4b118c6e42383` | sim |
| `sistemas/cartas.py` | `3bed48cbd496de431d92b76653518bda54a59ae5ee7ec8586b448b9fd19a0192` | sim |
| `bot.py` | `a735b2380176a5871f45770d99489825c587033d4a0d760b48b108a6e2a885ff` | sim |
| `database.py` | `ead936a2813335e5a98b31276a9e08ea6dc3a6121543300dd24decc7d69a3ed2` | sim |
| `site/app.js` | `9aafa6ba1ef2641fce9ab169192b27d28b92d2b92ee15881ca5db9984b39386b` | sim |

O módulo `sistemas/card_status_candidate.py` é novo e isolado. Não é importado por `sistemas.gwent`. Não foram alterados handlers legados, banco, APIs, frontend, imagens ou configuração de produção.

## Limitações

- A proposta permanece `CANDIDATE_FOR_REVIEW_NOT_APPROVED`.
- 41/41 testes do resolvedor candidato são unitários/sintéticos; ainda faltam integração de partidas completas e calibração competitiva específica destes estados.
- Antes de integrar, é necessário aprovar a transição para o limiar de duas marcas, o comportamento de alvo já no limite, a duração até o fechamento da rodada e a ausência de amplificação oculta por raridade.
- O relatório JSON correspondente contém comandos, contagens, hashes e limites em formato estruturado.
