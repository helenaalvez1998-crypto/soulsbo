# Auditoria técnica — NARA (versão com dois projetos Gemini e pesquisa gratuita)

## Escopo

Revisão estática e testes automatizados de inicialização, configuração, SQLite, economia, progressão, platinas, runs Soulslike, agente, permissões, pesquisa de jogos, importação/publicação de catálogos, ofertas e cogs Discord.

## Arquitetura atual de IA (dois projetos Gemini + busca gratuita)

- O bot usa dois projetos Gemini: `GEMINI_API_KEY` é o principal e `GEMINI_BACKUP_API_KEY` é a reserva. Cada projeto tem modelo, circuit breaker e arquivo de estado próprios.
- As quotas Google são aplicadas por projeto, não por chave. Duas chaves do mesmo projeto compartilham a mesma quota; projetos diferentes permitem isolamento de estado/quota, mas não garantem franquias iguais nem autorizam contornar regras do fornecedor.
- O mecanismo de pesquisa web do Caçador é Tavily Free/Search Basic. O código limita a quantidade de consultas por tarefa, valida URLs HTTPS e armazena somente os resultados necessários.
- Os dois Gemini recebem texto e evidências recuperadas pela Tavily. O código não ativa Google Search grounding para o modelo `gemini-3.5-flash-lite`.
- O bot não habilita billing, não compra créditos e não ativa Pay-as-you-go/upgrade. A administração deve manter os projetos Google sem faturamento vinculado e a Tavily no plano gratuito. Quando a franquia gratuita de pesquisa terminar, o circuito Tavily pausa até a renovação; nenhuma cobrança ou upgrade é acionado.
- A busca e os modelos têm quotas distintas. Se Tavily acabar, dois projetos Gemini não conseguem substituir a busca web; a pesquisa é interrompida com segurança. Se Tavily estiver disponível e o Gemini principal falhar, o Gemini reserva analisa as mesmas fontes sem repetir as consultas.
- Dados recuperados de páginas são tratados como entrada não confiável. O modelo é instruído a ignorar comandos presentes nas páginas, não inventar dados/URLs e usar exclusivamente URLs recebidas.
- A publicação do catálogo exige revisão/auditoria humana; resultados começam não verificados e URLs não retornadas pelo mecanismo de busca são rejeitadas.
- `NARA_CHAT_IA_ENABLED=false` mantém conversas básicas locais/SQLite. Imagens e prints não são baixados, lidos, submetidos a OCR ou enviados à IA.

## Integridade de dados e economia

- SQLite com foreign keys, `busy_timeout` e WAL para banco persistente.
- Transações `BEGIN IMMEDIATE` em operações que precisam ser indivisíveis.
- Proteções contra compras, equipagem, recompensas e aprovações duplicadas em cliques/ações concorrentes.
- Aprovação de run e concessão de XP/bônus na mesma transação.
- Importação de catálogo atômica e publicação revalidada dentro da transação.
- Consultas de perfil, saldo, platinas, zerados, runs, inventário e ranking atendidas por SQLite sem consumo de quota Gemini.
- Respostas locais para saudações, ajuda, identidade, regras, comandos, perguntas frequentes e sistemas do bot.

## Failover e tratamento de erros

- Circuit breakers independentes para Gemini principal, Gemini reserva e Tavily Free.
- Gemini principal é chamado primeiro; em quota, rate limit, credencial/permissão inválida ou indisponibilidade, o segundo projeto recebe o mesmo prompt e evidências.
- Se o primeiro Gemini falhar após uma ferramenta já ter sido executada no fluxo conversacional, o histórico neutro preserva a chamada e o resultado para que a reserva continue sem repetir a ação.
- Erros de quota Tavily (HTTP 432/433 ou mensagens de créditos esgotados) pausam a pesquisa até o próximo mês UTC; HTTP 429 usa pausa temporária; erros de autenticação não são repetidos continuamente.
- `/gemini_status` mostra os estados locais dos dois circuit breakers Gemini e da Tavily. Estado liberado não garante que a quota real do fornecedor esteja disponível.
- Se os serviços de pesquisa/modelo estiverem indisponíveis, nenhuma publicação parcial acontece; recursos locais continuam disponíveis.

## Outras correções incluídas

- Corrigida duplicidade de `cog_load` no Caçador, evitando sobrescrita do hook de recuperação de pesquisas interrompidas.
- Operações após `defer` tratadas para reduzir interações Discord sem resposta.
- Falhas em notificações/logs secundários não mascaram compras, platinas ou runs já confirmadas.
- Arquivos de comprovante têm limites de tamanho/quantidade, conversão protegida e limpeza compensatória.
- Leitura de páginas exige HTTPS, valida Content-Type e rejeita imagens, PDFs, vídeo e binários.
- Configurações numéricas inválidas usam padrão seguro em vez de derrubar a importação dos cogs.

## Configuração necessária

```dotenv
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_BACKUP_API_KEY=...
GEMINI_BACKUP_MODEL=gemini-3.5-flash-lite
TAVILY_API_KEY=...
TAVILY_MAX_QUERIES_PER_JOB=4
NARA_CHAT_IA_ENABLED=false
OFFERS_SHOW_DESCRIPTION=false
```

Não vincule faturamento às contas Google nem habilite Pay-as-you-go na Tavily se a exigência for custo zero. Verifique os painéis de uso antes de executar pesquisas em volume.

## Limitações de validação

- Última suíte: `pytest -q` **129 aprovados**; `unittest discover` **21 aprovados**; compilação dos **48 arquivos Python** sem erros de sintaxe; 37 decorators de comandos nomeados sem nomes duplicados.

- Os testes deste pacote são automatizados e simulam erros/alternância; não são homologação com tokens/contas reais.
- Este ambiente não dispõe das chaves Google, chave Tavily, token Discord ou dependências de produção para executar uma pesquisa real.
- Cobertura de colecionáveis/troféus varia por jogo, edição, plataforma e DLC. A revisão humana das fontes continua obrigatória.
- A Tavily Free tem limite mensal; depois de consumido, a pesquisa web fica pausada até renovação. Gemini backup não substitui o mecanismo de busca.
- Duas chaves Gemini do mesmo projeto não fornecem uma quota reserva separada.

## Correção adicional — componentes Discord UI (07/11/2026)

- Corrigida colisão com `discord.ui.Item.parent`, propriedade interna gerenciada pelo `discord.py` e sem setter público.
- Os componentes customizados do Caçador de Troféus agora guardam a referência à view em `self.owner_view`, sem sobrescrever `self.parent`.
- A correção abrange seletores e botões de categorias, itens, troféus e confirmação de pesquisa de jogos.
- Adicionado teste AST de regressão para impedir atribuições futuras a `self.parent` em `cogs/trofeus.py`.
- Validação após correção: 132 testes `pytest` aprovados; compilação Python executada separadamente.


## Auditoria completa do Caçador de Troféus (07/11/2026)

### Defeitos encontrados e corrigidos

| # | Problema | Correção |
|---|----------|----------|
| 1 | **Limite por minuto do Gemini era tratado como quota diária**: a mensagem de 429 do free tier traz "free_tier" e "check your plan and billing" nos dois casos, então qualquer pico de requisições pausava o projeto por 6 h e forçava o failover à toa. | `classify_gemini_error` separa limite diário/billing (pausa longa) de limite por minuto (usa `retryDelay`). O regex de status HTTP deixou de casar números soltos como "500 tokens". |
| 2 | **Botão "Marcar troféu conquistado" não funcionava** para troféus com colecionáveis vinculados já parcialmente marcados (o estado era derivado do progresso dos itens). | `alternar_trofeu` lê o estado salvo; o rótulo do botão alterna entre marcar e desmarcar. |
| 3 | **Só os 25 primeiros troféus eram acessíveis** (limite do Select, sem paginação). Idem jogos e categorias. | Paginação em jogos, categorias, itens e troféus; filtro por jogo base/DLC. |
| 4 | **Pesquisar um jogo já publicado o rebaixava para revisão** (qualquer jogador podia tirar um catálogo do ar e apagar a validação humana). | `importar_catalogo` recusa sobrescrever catálogo publicado; só `/catalogo_importar` (admin) pode, com aviso explícito. Pesquisa sobre jogo publicado abre o catálogo existente sem gastar API. |
| 5 | **Pedidos duplicados e perdidos** (cada falha/clique criava outra linha; falha de provedor não guardava o motivo para o admin; sem retry). | Módulo `cacador_fila.py`: um pedido ativo por jogo (índice único parcial), status `waiting_provider/interrupted/...`, `/catalogo_retentar`, reconciliação de órfãos na partida. |
| 6 | Falha da pesquisa guardava só a mensagem genérica; `TAVILY_API_KEY` ausente não aparecia para o admin e o jogador via `str(exc)` cru. | Motivo técnico completo na fila; jogador vê só mensagem segura. `diagnostico_configuracao()` avisa chave Tavily ausente, Gemini sem reserva e chaves idênticas (mesma quota) em `/gemini_status`, no painel e no log de inicialização. |
| 7 | Tavily descartava as fontes já pagas se uma consulta posterior falhasse. | Devolve o que foi coletado; só propaga a falha se nada foi coletado. |
| 8 | Reconhecimento de jogos: só "God of War 2018" era local; resto dependia 100% de IA e a falha de IA derrubava tudo. | Base local curada (identidade apenas: título, ano, estúdio), ambiguidades ("dark souls" → 2 edições), sufixo de plataforma, e sugestões por semelhança quando a pesquisa online está fora do ar. Títulos locais não consomem API nem a cota do jogador. |
| 9 | Falha de serviço consumia a cota de 3 identificações/10 min do jogador. | Estorno automático quando a falha é do provedor. Teto diário global de pesquisas (`CACADOR_PESQUISAS_DIA`). |
| 10 | Dados do spec ausentes: troféus sem DLC/perdível/oculto/história; sem progresso separado base/DLC; sem rejeitar/despublicar; sem histórico de alterações. | Colunas novas (migração automática), progresso base/DLC no painel, `/catalogo_rejeitar`, `/catalogo_despublicar`, `/catalogo_historico` (tabela `catalog_history`). |
| 11 | Painéis: botões ficavam mortos após timeout, erros viravam "interação falhou", gravação em catálogo despublicado dava `IntegrityError`, embeds podiam passar dos limites do Discord, slug quebrava com acentos. | `ViewDono` (checagem de dono única, timeout limpo, `on_error` amigável), validações no serviço, textos truncados, slug ASCII estável. |
| 12 | `cog_load` só reconciliava pesquisas com mais de 5 min; após reinício elas ficavam "pesquisando" para sempre. | Na partida todas as 'researching' viram 'interrupted'. |

### Validação

- `pytest` (executor compatível, sem acesso à rede): **140 aprovados**; `unittest discover`: **21 aprovados**; compilação de todos os arquivos sem erros; nenhum nome de comando duplicado (41 comandos).
- O cog foi exercitado de ponta a ponta com uma simulação do `discord.py` (painéis, paginação, filtro de DLC, toggle de troféu, busca, falha de provedor, retry sem duplicar, publicado intocado). **Isso não substitui o teste no Discord real**: valide `/cacador`, `/jogo_buscar "Lies of P"` e `/catalogo_retentar` no servidor.
- Não foram feitas chamadas reais ao Gemini, Tavily ou Discord. Confirme no Google AI Studio que o modelo configurado em `GEMINI_MODEL`/`GEMINI_BACKUP_MODEL` está disponível para os dois projetos.

### Atualização
Faça backup de `.env` e `data/`. As migrações do banco são automáticas e idempotentes na primeira inicialização. Adicione `CACADOR_LIMITE_USUARIO`, `CACADOR_JANELA_MINUTOS` e `CACADOR_PESQUISAS_DIA` ao `.env` se quiser outros tetos (padrões: 3, 10, 15).

### Complemento: 503 de alta demanda (visto em produção)

- Com os dois projetos Gemini apontando para o **mesmo modelo**, um pico de demanda (503 `UNAVAILABLE`) derruba principal e reserva juntos: o failover funciona, mas a reserva herda o mesmo problema. Agora, se **todos** os projetos falharem apenas por 503/timeout, o bot espera 6 s e depois 15 s e tenta de novo, reaproveitando as fontes já buscadas na Tavily (sem gastar créditos). Quota, rate limit e credencial inválida **não** disparam essas rodadas.
- Recomendação: use em `GEMINI_BACKUP_MODEL` um modelo diferente do principal (confirme a disponibilidade no Google AI Studio), para que um modelo sobrecarregado não derrube os dois.
- Corrigido o aviso "Não foi possível atualizar os botões": a confirmação agora desabilita os botões com `response.edit_message` (mensagens efêmeras não aceitam `message.edit`).
- Testes: 142 aprovados.


## Atualização — failover Gemini de três configurações (11/11/2026)

- Ampliado o roteador conversacional para principal → reserva → terceira configuração (`GEMINI_THIRD_API_KEY`).
- Cada configuração usa seu próprio adaptador e circuit breaker persistente, com cooldowns separados.
- A conversa livre, o agente com ferramentas, a síntese de pesquisa Tavily e a geração textual percorrem as três configurações na mesma ordem.
- `/gemini_status` passou a exibir os três circuitos e as três configurações habilitadas.
- A terceira configuração é opcional e pode ser desativada deixando `GEMINI_THIRD_API_KEY` vazia.
- Adicionado `NARA_GEMINI_TRES_CHAVES.md` com configuração e limites de quota.

Validação desta alteração: compilação de todos os arquivos Python; testes `pytest` e testes específicos de failover. Testes usam provedores simulados; nenhuma chave Google, token Discord ou chamada real foi usada. A disponibilidade do modelo e as cotas precisam ser confirmadas nos projetos Google do operador.

- Complemento: timeouts observados no adaptador assíncrono também abrem o circuito individual com cooldown de indisponibilidade, evitando martelar a mesma configuração em mensagens sucessivas.

- Validação final após ampliar timeout/circuito e isolar o arquivo do terceiro circuito: `pytest -q` **85 aprovados**; `python -m unittest discover -s tests -q` **50 aprovados**; `compileall` sem erros.

- Backoff exponencial validado em teste isolado: cooldown inicial de 5 s cresce para 10 s após falha consecutiva no mesmo circuito, com teto de 24 h e reset após chamada bem-sucedida. Validação final: `pytest -q` **86 aprovados**; `unittest discover` **51 aprovados**; compilação sem erros.


## Evolução de implantação e operação — 11/11/2026

### Ajustes implementados nesta entrega

- Centralizado o diretório persistente por `DATA_DIR`. Na FadeHost, use `/data`; SQLite, banco de ofertas e estados JSON dos circuit breakers permanecem fora do diretório substituído pelo deploy. `DB_PATH` continua aceitando caminho explícito.
- Removidos IDs de canais de comunidade como defaults embutidos. Os canais devem ser definidos em variáveis de ambiente ou por servidor no `/adm`.
- Removido do código o ID numérico pessoal usado pelo Santuário; agora a regra usa `BOT_OWNER_ID` e fica desativada quando o valor é `0`.
- A sincronização de comandos deixou de limpar comandos globais por padrão. A operação destrutiva exige `CLEAR_GLOBAL_COMMANDS_ON_GUILD_SYNC=true`.
- Criado um `CommandTree` com respostas efêmeras e orientadas à ação para falhas de permissão, checks, cooldowns e erros de execução; detalhes técnicos permanecem nos logs. Handlers locais dos cogs são respeitados para evitar mensagens duplicadas.
- Os avisos do YouTube agora percorrem as guilds conectadas e consultam as configurações de canal/cargo de cada servidor; um ID de canal de outro servidor é recusado. O loop de vídeos só inicia com `YOUTUBE_CHANNEL_ID` válido; o loop de lives também exige `YOUTUBE_API_KEY`.
- Dependências diretas travadas em `requirements.txt`; dependências de teste separadas em `requirements-dev.txt`.
- Adicionado `DEPLOY_FADEHOST.md` com inicialização `python bot.py`, variáveis, volume persistente, permissões e cuidados com SQLite de instância única.

### Validação desta entrega

- `pytest -q`: **91 aprovados**.
- `python -m unittest discover -s tests -q`: **54 aprovados**. As mensagens de erro simuladas e avisos sobre chaves ausentes são esperados nesses testes.
- `python -m compileall -q .`: concluído sem erros de sintaxe.
- Varredura do código Python: nenhum ID Discord de 17–20 dígitos permaneceu embutido nos módulos de produção.
- Não foi possível instalar as dependências de produção neste ambiente porque o acesso ao índice de pacotes falhou por DNS/rede. Portanto, esta entrega não foi autenticada com token Discord, não executou chamada real ao YouTube/Gemini/Tavily e não foi homologada em uma instância FadeHost. Faça esse smoke test no primeiro deploy.
