# Soulsbo — entrega de prontidão de produto rev. 31

## Decisão de escopo

A rev. 31 transforma parte da alpha existente em um pacote reproduzível de implantação e fecha fluxos que estavam mostrando sucesso sem ter uma operação segura por trás. Ela **não** declara o jogo pronto para produção: o ambiente de criação não dispõe das credenciais, do banco legado real, de Docker Engine nem de staging Discord/OAuth.

## Entregue nesta revisão

### Operação e deploy

- Imagem Docker baseada em Python 3.13, dependências runtime pinadas, usuário não-root e volume persistente `/data`.
- Compose com filesystem root read-only, `tmpfs` para `/tmp`, remoção de capabilities, `no-new-privileges`, healthcheck HTTP + Discord + `PRAGMA quick_check` do SQLite.
- Entrypoint que roda `scripts/runtime_preflight.py` antes de executar `bot.py`.
- Modelo `.env.production.example` sem segredos reais e runbook para configurar Discord/OAuth, restaurar banco, iniciar e fazer backup.
- Workflow CI para testes, compilação Python, sintaxe JS, validação Compose e build de imagem.
- Backup consistente usando SQLite Online Backup API, com integridade verificada.

### Conquistas

- Métricas são calculadas do lado servidor: exemplares, raridade Singular, ascensões de raridade, modelos comuns e resultados/rankings de partida.
- O navegador nunca envia progresso ou identifica o jogador; a sessão Discord autenticada é a fonte do user ID.
- GET é read-only. POST aceita somente JSON vazio para recalcular e persistir progresso do servidor; payload forjado ou JSON malformado é rejeitado.
- Desbloqueios são monotônicos e persistidos. Perder posteriormente um exemplar não remove uma conquista já desbloqueada.
- `Apostador` e `Sobrevivente` ficam `tracking_pending`, não como progresso zero, até haver nível individual e ledger de tentativas/falhas.

### Fechamento seguro de módulos incompletos

- Apostas em Denários, cartas e torneios ficam indisponíveis, sem débito ou reserva, até existir custódia/escrow, aceitação bilateral, timeout/cancelamento, liquidação atômica e auditoria.
- Evolução com risco fica indisponível, sem mutar exemplar ou amuleto, até existir nível persistido por exemplar, ledger de tentativas/falhas, custo transacional e inventário real de amuletos.
- A Forja de ascensão de raridade é diferente da evolução com risco e permanece separada.

## Estado do produto depois da entrega

| Área | Estado | Evidência / limite |
|---|---|---|
| Card Engine v2 | Alpha isolada | Runtime, resolver, persistência e controlador de partida; `CardInstance v0.7/schema 7` ainda draft |
| Combate | Alpha implementada | Poder por fileira e dano à vida; não há HP individual/armadura física por unidade |
| Energia/custos | Alpha provisória | 27 cartas e dez líderes com custo; sem playtest humano ou balanceamento aprovado |
| Deck Builder | Alpha | 30 cartas, até três cópias/modelo, exemplares físicos, allowlist de 27 |
| Discord | Código alpha | Transport/handlers testados localmente; login e dispatch real ainda não validados em Discord staging |
| Site | Código alpha | Sessão OAuth existente, APIs e páginas exercitadas por testes HTTP locais; OAuth público não testado |
| Catálogo | Incompleto | 137 modelos históricos, 27 permitidos, 110 bloqueados; 9/27 combos alcançáveis, 18 inativos |
| Efeitos | Parcial | 12 famílias de efeitos de entrada implementadas no recorte alpha; catálogo canônico histórico enumera mais famílias |
| Líderes/passivas | Alpha | Dez handlers de líderes e quatro passivas de facção |
| Conquistas | Parcial funcional | Seis objetivos rastreáveis, dois pendentes; sem recompensas concedidas |
| Evolução com risco | Bloqueada | Schema atual não suporta nível individual e ledger de tentativas/amuleto com segurança |
| Apostas | Bloqueadas | Sem escrow e liquidação transacional |
| Balanceamento | Pendente | Preços provisórios; não há telemetria nem partidas humanas |
| Deploy | Preparado, não executado | Docker/Compose/CI/runbook presentes; Docker Engine e secrets ausentes no ambiente |

## Não confundir os testes com validação de produção

Nesta revisão:

- `python -m pytest tests/card_engine_v2 -q`: 240 testes aprovados e 61 subtests parametrizados.
- Suite oficial playable alpha v0.5: 240/240 aprovada.
- Staging histórico do catálogo: 137 modelos; 27 permitidos e 110 bloqueados.
- Simulação Bo3: A vence 2–1; 97 eventos; SQLite integrity/quick-check `ok`.
- Simulação combo/passiva/líder: A vence 20–10; 49 eventos; SQLite integrity/quick-check `ok`.
- `py_compile`, `node --check`, `sh -n` e parse YAML foram aprovados.
- Preflight do ambiente atual: 9 pass, 0 warnings, 22 blockers. Os blockers são dependências ausentes/fora da pinagem, secrets e OAuth ausentes, DATA_DIR e banco real ausentes.

O host de criação não tem Docker CLI; portanto o Docker build não foi executado. O acesso à rede/PyPI não estava disponível para instalar as dependências faltantes. Não houve login real, duas contas em Discord staging, OAuth real, deploy ou acesso à base publicada.

## Critérios para considerar pronto para jogadores

1. Configurar secrets no painel seguro do host, nunca no ZIP ou repositório.
2. Restaurar backup real da coleção em volume persistente e validar `integrity_check`.
3. Instalar dependências pinadas e obter preflight operacional sem blockers.
4. Executar Discord token probe e OAuth de navegador com duas contas.
5. Criar deck com exemplares reais, desafiar/aceitar, completar partida, validar estado/histórico e privacidade.
6. Reiniciar o serviço e reabrir a partida; verificar que inventário e progresso não foram duplicados.
7. Testar concorrência, recuperação de backup e logs antes de beta.
8. Completar catálogo, playtests humanos e módulos bloqueados antes de anunciar a experiência como produto completo.

## Próxima ordem de trabalho

- Primeiro: executar o runbook no host real e corrigir diferenças de ambiente.
- Segundo: expandir o catálogo com rastreabilidade `card_id -> effect_id -> handler -> parâmetros -> testes -> texto`, preservando os 110 bloqueados até aprovação individual.
- Terceiro: cobrir as famílias de efeitos que ainda não estão implementadas no runtime alpha e validar interações cruzadas.
- Quarto: construir schema/ledger de evolução com risco e sistema escrow de apostas em transações idempotentes, somente depois de reconciliar as regras oficiais.
- Quinto: balancear por simulações com preços reais e partidas humanas; testar beta fechado.
