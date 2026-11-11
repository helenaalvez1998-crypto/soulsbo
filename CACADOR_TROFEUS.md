# Caçador de Troféus — identificação, pesquisa e catálogo

O Caçador mantém um catálogo separado da loja cosmética e salva o progresso de cada jogador. A IA identifica jogos e prepara rascunhos de colecionáveis/troféus, mas **não publica dados automaticamente**.

## Como o jogador pesquisa um jogo

1. Abra `/nara` e escolha **Caçador de Troféus**.
2. Use **Solicitar cadastro** e escreva o nome como lembrar: título original/traduzido, abreviação ou erro de digitação.
3. O sistema procura primeiro um título/alias já catalogado. Se não encontrar, pesquisa fontes com Tavily Free e usa Gemini principal para analisar os resultados; outro projeto Gemini assume se o primeiro falhar.
4. Se o principal atingir quota, rate limit ou ficar indisponível, o mesmo pedido é tentado pelo segundo projeto Gemini configurado.
5. O jogador confere ano, estúdio, escopo e fontes e confirma o jogo correto. Depois da confirmação começa a pesquisa detalhada do catálogo.
6. O resultado fica em revisão administrativa. Falhas de API, JSON, fonte ou banco não publicam catálogo.

O mapa local de aliases de `God of War (2018)` é apenas um atalho de identificação; não é fonte de troféus e não dispensa pesquisa/revisão.

## Como o administrador revisa e publica

- `/catalogo_admin`: abre o painel administrativo.
- `/catalogo_fila`: mostra solicitações e erros técnicos.
- `/catalogo_auditar slug:<slug>`: mostra itens, troféus, fontes e estado de validação.
- `/catalogo_validar slug:<slug>`: registra revisão humana.
- `/catalogo_publicar slug:<slug>`: publica somente se a auditoria transacional encontrar itens/troféus, fontes HTTPS, pelo menos dois domínios distintos e validação humana.
- `/catalogo_importar arquivo:<arquivo.json>`: importa para revisão; os dados começam não verificados.
- `/catalogo_rejeitar slug:<slug> motivo:<texto>`: rejeita um catálogo em revisão; o motivo fica no histórico.
- `/catalogo_despublicar slug:<slug> motivo:<texto>`: tira um catálogo do ar (volta para revisão) sem apagar o progresso dos jogadores.
- `/catalogo_historico [slug]`: mostra quem importou, validou, publicou, rejeitou ou despublicou cada catálogo.
- `/catalogo_retentar pedido:<id>`: retoma um pedido da fila (provedor fora do ar, reinício do bot, limite diário) reaproveitando o mesmo registro.

Todos os comandos que recebem `slug` oferecem autocomplete. O painel administrativo tem o botão **Diagnóstico da pesquisa**, que mostra chaves ausentes e o estado dos circuit breakers.

## Fila de pesquisas

- Existe no máximo **um pedido ativo por jogo**: pedir o mesmo jogo de novo (ou dois membros pedirem juntos) reaproveita o registro.
- Se Tavily/Gemini falham, o pedido fica em `aguardando provedor` com o motivo técnico (por exemplo, `TAVILY_API_KEY` ausente) visível só para administradores; o jogador recebe uma mensagem segura e pode tentar de novo pelo mesmo botão.
- Pesquisas interrompidas por reinício viram `interrompida` e podem ser retomadas.
- Pesquisar um jogo que já está **publicado** abre o catálogo existente; nunca o rebaixa para revisão.
- Tetos: `CACADOR_LIMITE_USUARIO` por janela e `CACADOR_PESQUISAS_DIA` por dia (servidor). Títulos reconhecidos pela base local não gastam API nem a cota do jogador.

O painel de jogadores lista somente jogos em `ready`. A IA não transforma uma solicitação em catálogo público sozinha.

## Configuração Gemini

```dotenv
GEMINI_API_KEY=sua_chave_do_projeto_principal
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_BACKUP_API_KEY=sua_chave_de_outro_projeto_google
GEMINI_BACKUP_MODEL=gemini-3.5-flash-lite
TAVILY_API_KEY=sua_chave_do_plano_free
TAVILY_MAX_QUERIES_PER_JOB=4
```

A Tavily Free faz as consultas web; o Gemini principal analisa os resultados e o outro projeto Gemini assume em caso de quota/rate limit/indisponibilidade. As duas chaves devem pertencer a projetos Google diferentes para que os circuit breakers e as quotas por projeto sejam independentes. Duas chaves do mesmo projeto compartilham quota. Não é necessário ativar billing; sem billing, ao atingir os limites gratuitos o pedido falha de forma controlada.

A busca externa usa somente Tavily Free/Search Basic (1.000 créditos mensais publicados no plano gratuito; até 4 consultas por tarefa neste bot). Os modelos Gemini recebem as fontes como texto e não ativam Google Search grounding. Não vincule faturamento no Google nem habilite Pay-as-you-go/upgrade na Tavily; quando os créditos gratuitos terminarem, a pesquisa pausa sem cobrança.

Referências oficiais:
- https://docs.tavily.com/documentation/api-reference/endpoint/search
- https://tavily.com/pricing
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/pricing

## Limitações importantes

- Não existe API única com cobertura completa de colecionáveis e troféus para todos os jogos.
- Se a busca não retornar fontes HTTPS verificáveis, o sistema falha fechado.
- URL mencionada apenas no texto do modelo não é aceita como evidência; os registros precisam usar URLs retornadas pela Tavily nesta pesquisa.
- Títulos, aliases, DLC, NG+, itens perdíveis, locais e requisitos precisam de revisão humana.
- Duas fontes/domínios são um bloqueio mínimo; não provam completude.
- Reimportações preservam o progresso de jogadores. Registros ausentes no novo rascunho não são apagados automaticamente.

## Atualização

Faça backup de `data/colizeu.db` antes de substituir o código. Não substitua o `.env` nem apague o banco. `/gemini_status` exibe os dois circuit breakers de IA.
