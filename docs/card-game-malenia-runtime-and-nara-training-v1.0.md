# Malenia, Lâmina de Miquella — revisão de runtime e treino NARA (2026-11-28)

**Estado:** implementação integrada ao runtime legado do Gwent; não é uma migração do Card Engine v2 alpha.

## Carta canônica atual

| Campo | Valor atual |
|---|---|
| ID | `chefe_malenia_lamina_miquella` |
| Nome | Malenia, Lâmina de Miquella |
| Tipo / facção / fileira | Unidade / Véu Carmesim / Corpo a Corpo (`melee`) |
| Poder-base | 9 |
| Raridade | Primordial |
| Custo | 6 (tabela Primordial) |
| Habilidade | Flor Escarlate (`scarlet_bloom`) |

**Regra executada:** ao entrar, aplica uma marca de Podridão Escarlate a cada inimigo na mesma fileira, respeitando o limite de duas marcas. A consequência de limiar acontece somente na transição de uma para duas marcas. Se o alvo tinha bônus positivo, a regra-base remove um ponto até o piso 0. Como Malenia é Primordial, até três alvos que realmente sofreram essa corrosão perdem mais um ponto, até o piso -2. Um alvo que já está com duas marcas não recebe redução repetida. Bônus não positivos não acionam a corrosão-base.

**Decisão de balanceamento:** poder 9 foi mantido por ser o topo da faixa Primordial (8–9); o custo foi corrigido de 4 para 6, conforme `CUSTO_RARIDADE`. A carta é muito forte por unir poder máximo da raridade e pressão de fileira, mas sua regra tem cap de alvos e não repete o efeito no limite.

**Lore e representação:** a descrição foi atualizada com sua origem como Empírea/semideusa, irmã gêmea de Miquella, Podridão Escarlate, treino com o espadachim cego, Elphael, a Mão de Malenia e a batalha de Caelid. A arte da carta é da fase 1 — Lâmina de Miquella — e não da transformação Deusa da Podridão. A ficha distingue explicitamente a forma pré-transformação.

## Locais sincronizados

- `sistemas/cartas.py`: modelo de catálogo, custo, raridade, poder, lore, habilidade e versão de arte.
- `sistemas/gwent.py`: identidade ativa, texto exibido, resolver de Flor Escarlate, limite das marcas e exclusão do amplificador genérico duplicado. `preparar_carta()` agora entrega o custo e preserva a descrição completa.
- `site/app.js`: explicação curta e exemplo de jogo compatíveis com o resolvedor.
- `sistemas/atelie_coliseu.py` e `sistemas/direcao_arte_prompts.py`: direção visual de Malenia na fase 1, incluindo elmo, cabelo, armadura, próteses e katana; sem asas de borboleta da fase 2.
- `data/card_game/malenia-runtime-current.v1.json`: registro consolidado da carta atual.
- `docs/card-game-card-traceability.md/.json`: mantidos como baseline histórico; adicionada uma advertência e um ponteiro para o override atual.

## Treino NARA — três dificuldades e decks

Cada perfil constrói um deck distinto, validado com 12 cartas (9 unidades e 3 especiais), IDs sem duplicatas e uma única facção para as unidades. Cada um também recebe líder e Relíquia próprios, fornecidos pelo perfil de treino; a Relíquia virtual é marcada como disponível para a NARA e continua sujeita às validações normais de ativação. Os decks e Relíquias são obtidos do catálogo existente, não são listas inventadas fora do runtime.

| Dificuldade | Perfil / deck | Facção | Líder | Relíquia | Plano de jogo |
|---|---|---|---|---|
| Fácil | Aprendiz — Formação da Árvore Áurea | Ordem Áurea | Morgott (`bastiao_ancestral`) | Grande Runa de Godrick | Formação defensiva, unidades acessíveis e efeitos diretos |
| Normal | Estrategista — Observatório Cariano | Lua Negra | Astel (`mestre_eclipse`) | Grande Runa dos Não Nascidos | Controle de fileira, geada e respostas mágicas |
| Difícil | Lendária — Flor Escarlate: Malenia | Véu Carmesim | Esgar (`voz_caidos`) | Runa da Morte | Pressão progressiva com Podridão Escarlate, marcas e recuperação tática |

Os perfis estão definidos em `sistemas/gwent_treino.py`. A IA usa pesos e limiares de decisão distintos por dificuldade; no modo fácil escolhe entre opções próximas em vez de sempre selecionar a linha perfeita.

## Fluxo de partida e atraso de decisão

- A partida solo é criada por `novo_estado()` e usa a mesma estrutura de estado da partida normal.
- O deck e configuração do jogador são preservados; a NARA recebe um deck e líder próprios do perfil escolhido.
- Cada decisão da NARA chama `executar_uma_jogada_ia()`, que simula candidatos e confirma a jogada por `aplicar_jogada()`, o resolvedor comum do combate. Isso preserva regras de unidades, especiais, fileiras, clima, líder, relíquia se equipada, pontuação, passes e fechamento de rodada.
- O worker assíncrono aguarda um valor aleatório entre **3 e 5 segundos antes de cada decisão**, fora da transação do banco, e revalida o estado antes de agir. Se a NARA continuar com o turno, aguarda novamente antes da próxima decisão.
- Partidas de treino não alteram MMR nem concedem recompensas competitivas (`rewards: false`).
- Se o processo reiniciar durante um turno da NARA, o GET do detalhe tenta recuperar o worker pendente.

## Verificação

- `tests/test_gwent_malenia_training.py`: cobre catálogo, custo, lore, payload preparado, texto sem truncamento, limiar e limite das marcas, escala Primordial até três alvos, resolução via `aplicar_jogada()`, três decks com líderes/Relíquias e ação unitária da IA.
- `docs/scripts/test-card-status-candidate-v0.1.py`: teste legado atualizado para garantir que Malenia não corroa novamente no limite.
- `docs/scripts/assert-card-identity-behavior-v0.1.py`: smoke do efeito agora usa raridade Primordial e espera a corrosão adicional correta.
- `docs/scripts/audit-gwent-http-contracts-v0.1.py`: relatório corrigido para registrar custo no payload, decks separados de treino e atraso assíncrono.

**Validação final local:** 282 testes e 106 subtests parametrizados; suite específica Malenia/NARA 10/10; regressão de status 41/41; assertions de identidade 33/33; `node --check site/app.js` e `py_compile` aprovados. O preview 840×1240 foi regenerado e a regra completa cabe no painel em quatro linhas.

**Limite de validação:** os testes unitários e estáticos exercitam o motor e os contratos no código local. A integração HTTP ponta a ponta continua dependente do ambiente com `discord.py` e `aiosqlite`; sem essas dependências não se afirma que todos os handlers foram testados contra servidor/banco reais. Não houve deploy.
