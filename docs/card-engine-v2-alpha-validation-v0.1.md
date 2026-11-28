# Card Engine v2 alpha — validação local v0.1

**Status:** `PASS`  
**Resultado:** 62/62 testes aprovados em execução local de 2026-11-27.  
**Comando:** `python docs/scripts/test-card-engine-v2-alpha-v0.1.py`.

## Cobertura de persistência e identidade

- UUIDv4 e partição exclusiva de zonas.
- Cópias do mesmo `card_id` com instâncias físicas distintas.
- Validação estrutural de CardInstance v7 e request interno.
- Transição exata entre zonas e movimentação entre fileiras.
- Preservação de grants e proveniência em transição genérica.
- Rejeição de transição inválida sem mutação parcial.
- `state_revision`, `expected_revision` e compare-and-swap.
- Duas conexões SQLite concorrentes usando a mesma revisão: um commit e um conflito; sem lost update.
- Replay idempotente e conflito de fingerprint.
- Persistência de rejeição sem alteração de estado e sem avançar revisão.
- Rollback integral de handler que lança exceção.
- Atomicidade conjunta de snapshot, operação, eventos, recompensas e outbox.
- Eventos append-only e watermark coerente.
- Cadeia causal explícita entre remoção direta e Vingança reativa.
- Evento reativo com pai causal ausente rejeitado com rollback integral.
- Outbox com lease, retry, dead-letter e confirmação.
- Migration ledger com checksum.
- Backup pela SQLite Backup API e verificação de integridade/hash.
- Recusa de SQLite não vazio sem marcador dedicado.
- Arquivamento de snapshot legado com hash e mapping de ocorrência persistido.

## Cobertura do resolvedor de gameplay

- Oferta de alvos server-side, vinculada à revisão e ordenada deterministicamente.
- Política de alvo diferente por causa (ex.: remoção comum vs. execução).
- Rejeição de fonte inexistente, de outro proprietário, efeito incompatível ou zona não permitida.
- Rejeição de seleção de identidade não incluída na oferta.
- Preview determinístico e confirmação de alvos secundários automáticos.
- Remoção comum, execução e sacrifício em caminhos distintos.
- Escudo bloqueia remoção/execução e consome uma carga; sacrifício ignora escudo.
- Prioridade de proteção por sequência de evento e desempate por `grant_id`.
- Vingança após remoção/execução/sacrifício bem-sucedidos; nunca após bloqueio.
- Resolução de todas as remoções diretas antes de distribuir Vingança em ações multi-alvo.
- Movimento apenas para fileiras autorizadas.
- Bônus e grants de proteção definidos pelo registry do servidor; parâmetros mecânicos enviados pelo cliente são rejeitados.
- Resultado de ação e target offer validados contra os schemas do Grupo D.

## Interpretação correta

Os 62 testes são testes automatizados locais em fixtures e arquivos SQLite temporários. Demonstram o comportamento da implementação alpha isolada, não integração no jogo atual nem correção de todo o catálogo de efeitos. `jsonschema` é dependência opcional para parte das validações de schema.

## Não coberto

- Banco de produção, clone real ou linhas reais de partidas.
- `aiosqlite`, Discord, HTTP, frontend ou event loop real.
- Rede, multi-host, filesystem compartilhado ou failover distribuído.
- Migração completa de snapshots reais e cutover.
- Catálogo ativo de cartas/efeitos e registries gerados de releases reais.
- Cálculo integrado de poder efetivo com clima/estados; é necessário injetar um `metric_resolver` confiável.
- Execução do algoritmo de clamp, embora `clamp_policy_id` seja preservado como metadado.
- Turnos, ativações e custos genéricos; somente consumo configurado de carta-fonte e cargas de proteção são aplicados.
- Combate completo, dano, combos, líderes, clima, fase de rodada e `round_close` global.
- Entrega externa efetiva da outbox; somente o ciclo persistente foi testado.

O resultado é uma fatia de gameplay funcional sobre a fundação transacional isolada, ainda não um motor de jogo completo ou pronto para produção.
