# Auditoria e integração da Nara — NARA

**Data da implementação:** 10/11/2026  
**Regra de preservação:** os prompts originais e o tutorial original foram mantidos; não foi criada uma nova personalidade nem uma cópia textual do tutorial em código.

## 1. Diagnóstico da versão recebida

A versão recebida tinha 69 arquivos e 40 testes automatizados aprovados antes das alterações desta entrega.

| Área | Estado encontrado | Consequência |
|---|---|---|
| Identidade | `prompts/nara.md` existia, mas não fazia parte do prompt curto de conversa. | A identidade canônica podia não chegar ao modelo na conversa regular. |
| Conversa e pesquisa | `prompts/nara_conversa.md` e `prompts/nara_pesquisa.md` eram carregados em rotas diferentes. | Não havia composição explícita da identidade canônica com os escopos especializados. |
| Conhecimento do bot | Havia FAQ/consultas SQLite e ferramentas em `ia_ferramentas.py`, mas não um inventário dinâmico de comandos e cogs carregados. | A Nara não podia verificar de forma sistemática o que estava registrado no runtime. |
| Ações | O agente e o núcleo de ferramentas já existiam; o chat geral não encaminhava pedidos imperativos para esse agente. | Parte das ações implementadas não estava acessível por conversa natural. |
| Permissões | `ia_nucleo.py` já aplicava validação, risco e confirmação às ferramentas. | A integração deveria reutilizar essas proteções, não criar execução paralela. |

## 2. Arquitetura depois da alteração

O listener mantém a seguinte precedência:

2. **Consultas locais:** FAQ, comandos, módulos carregados, canais visíveis e dados SQLite do próprio membro.
3. **Ferramentas do NARA:** pedidos imperativos roteados para o registro real de ferramentas; risco, validações, permissões e confirmações permanecem no núcleo já existente.
4. **Conversa livre:** continua sendo controlada por `NARA_CONVERSA_ENABLED`, com limites de cooldown e quota próprios.
5. **Pesquisa factual no chat:** controlada separadamente por `NARA_CHAT_IA_ENABLED` e limitada às ferramentas de leitura habilitadas.
6. **Caçador de Troféus:** `/jogo_buscar` continua como fluxo independente.

### Composição dos prompts

- `prompts/nara.md`: preservado como referência canônica de identidade.
- `prompts/nara_conversa.md`: preservado como escopo da conversa textual. `nara_conversa.py` agora combina esse escopo com a seção `## 1. Quem é Nara` extraída dinamicamente de `nara.md`.
- `prompts/nara_pesquisa.md`: preservado como escopo de pesquisa e combinado com a seção canônica de identidade.

A conversa curta não recebe o documento geral inteiro: a composição fica abaixo do limite de prompt que o projeto já testava. A rota de ações recebe a identidade principal existente e o inventário runtime relevante. Não foi criado um segundo prompt de personalidade.


### Caminho de execução


O caminho local não chama `self.ia`, `conversar()`, `criar_gerador()`, Tavily, SDKs de IA, clientes HTTP ou serviços externos de conhecimento. O bot precisa usar a API oficial do Discord para receber e enviar as mensagens; esse transporte é inerente ao bot e não é uma chamada a modelo ou provedor de instruções.

### Fonte do tutorial

- Leitura UTF-8 do arquivo a cada mensagem relevante, sem cache do conteúdo tutorial.
- Extração dinâmica das etapas 1 a 6, soluções, FAQ e links permitidos.
- O conteúdo integral é lido novamente quando solicitado; não é substituído por texto armazenado em estado de sessão.
- Arquivo ausente, vazio, inacessível ou com codificação inválida produz erro local explícito. Não há reconstrução nem fallback para Gemini.

O texto integral do documento nesta versão tem **10.021 caracteres** e foi dividido em **6 mensagens** de até 2.000 caracteres. O teste concatena as mensagens de saída e compara o resultado, caractere por caractere, com o arquivo original. As seis seções extraídas também ficam abaixo do limite operacional de 1.500 caracteres por resposta.

### Classificação e continuidade


Estado:

- chave composta por `guild_id` e `user_id`;
- etapa atual e status ativo/inativo em memória e SQLite;
- registros de idempotência antigos são limpos após sete dias.

Se o SQLite falhar, o estado continua em memória naquela execução, mas deixa de ser persistente entre reinícios. A falha é registrada no log.

### Segurança e limitações do tutorial

A proteção identifica marcadores textuais `PrivateKey`/`Private Key`, não repete o segredo na resposta e orienta a pessoa a apagar a mensagem e revogar a configuração no Proton, conforme o documento original. O listener não abre imagens nem faz OCR; portanto, não consegue detectar automaticamente uma chave que apareça apenas em um print. Nesses casos, ele informa que não analisou o anexo e pede uma descrição textual sem dados privados.

## 4. Conhecimento runtime do NARA e do Discord

O novo `nara_conhecimento.py` usa objetos ativos, não nomes inferidos de arquivos:

- comandos efetivamente registrados em `bot.tree`, incluindo subcomandos;
- cogs atualmente carregados em `bot.cogs`;
- canais que o membro consegue visualizar, usando `permissions_for(member)`;
- cargos do próprio membro, sem enumerar cargos privados de terceiros.

Comandos com `default_permissions` incompatíveis são omitidos. Comandos que apresentam checks customizados que o inventário não consegue avaliar sem executar lógica de autorização também são omitidos por precaução.

Isso não representa um inventário completo de todas as configurações administrativas, overrides por canal, dados de todos os membros, esquemas internos do banco ou comportamento de cada função. A Nara usa as consultas e ferramentas concretas que já existem; não deve declarar uma função disponível apenas porque um cog tem nome sugestivo.

## 5. Ações e limites de autorização

Pedidos imperativos para capacidades reconhecidas são roteados ao agente com `criar_registro(..., pesquisa=False)`. A execução reaproveita `Ctx`, `Risco`, `rodar_agente`, a confirmação de `ia_confirmacao.py` e as implementações registradas em `ia_ferramentas.py`.

- Consultas usam as ferramentas de leitura e handlers SQLite existentes.
- Ações de risco `CONFIRMAR` aguardam confirmação do membro pelo mecanismo já existente.
- Ações `PROPRIA` continuam limitadas ao próprio membro pelas validações do núcleo.
- Ações de moderação não são incluídas por padrão: `IA_ACOES_MODERACAO=false`. Para habilitá-las é necessário alterar essa configuração; as validações de moderador no código continuam obrigatórias.
- Se o provedor não estiver disponível ou não houver ferramenta compatível, a Nara informa que nada foi alterado.

## 6. Arquivos alterados nesta entrega

| Arquivo | Alteração |
|---|---|
| `nara_conhecimento.py` | Novo inventário runtime de comandos/cogs e consultas de canais/cargos visíveis. |
| `nara_conversa.py` | Composição da seção canônica de identidade com o prompt de conversa existente. |
| `nara_local.py` | Rota de pedidos imperativos e intenções runtime; documentação do roteador ajustada. |
| `README.md` | Documentação de rotas, variáveis e inicialização conversável. |
| `env.example` / `.env.example` | Exemplo de ambiente com conversa livre ativa e pesquisa com ferramentas desligada por padrão. |
| `env (1).example` | Mantida a mesma variável também no arquivo de exemplo duplicado distribuído. |
| `tests/test_conversa.py` | Regressões da composição de prompts e roteamento de ações. |
| `tests/test_nara_conhecimento.py` | Testes de inventário runtime e restrições de visibilidade. |
| `NARA_INTEGRACAO_AUDITORIA.md` | Este relatório e complemento operacional do bot conversável. |
| `configurar_bot.py` | Assistente de configuração que grava `.env` sem ecoar segredos. |
| `.gitignore` | Protege `.env`, bancos e dados locais contra inclusão acidental no Git. |
| `INICIAR_WINDOWS.bat` / `iniciar_linux.sh` | Instalação das dependências e inicialização local assistida. |
| `tests/test_configurar_bot.py` | Testes do atualizador e leitor de variáveis `.env`. |

## 7. Evidências de teste

Execução no ambiente desta entrega:

| Verificação | Resultado |
|---|---:|
| `pytest -q` | **74 aprovados** |
| `python -m unittest discover -s tests -q` | **47 aprovados** |
| `python -m compileall -q .` | **Sem erros de sintaxe** |
| Arquivos Python no pacote após as adições | **53** |
| Decorators de comandos slash nomeados | **41** |
| Nomes duplicados de comandos encontrados | **0** |


- as sete frases obrigatórias;
- início/reinício/etapas/continuidade;
- identificação de `PrivateKey` sem ecoar o segredo;
- mensagem ambígua durante sessão ativa;
- troca explícita de assunto;
- tutorial ausente/vazio/UTF-8 inválido;
- conteúdo integral dividido e reconstituído exatamente;
- isolamento entre usuários e servidores;
- deduplicação de eventos repetidos;
- arquivo ausente, falha na recuperação do estado e falha inesperada na interceptação sem fallback para IA;
- auditoria AST dos imports do módulo local;
- listener exercitado com `_SpyIA`, que falha se `conversar()` ou `criar_gerador()` forem chamados.


A execução de `unittest` imprime logs de exceção deliberadamente provocados por um teste de ferramenta e mensagens de failover simuladas. O comando concluiu com `OK`; esses logs pertencem aos cenários negativos testados e não representam falha da suíte nem homologação real do Discord.

## 8. O que não foi possível homologar neste ambiente

- `discord.py` e `aiosqlite` não estão instalados no runtime de validação, embora constem em `requirements.txt`.
- Não havia token de bot nem acesso a um servidor Discord real; portanto, não foi possível testar o login, intents, árvore sincronizada, permissões configuradas no portal, envio REST real, limites de rate, banco SQLite de produção ou persistência após reinício do processo real.
- Não havia chaves Gemini/Tavily de produção. Não foi feita nenhuma chamada real a esses provedores.
- Os testes de listener usam stubs para importar `cogs/nara_ia.py` sem `discord.py`; são evidência do fluxo de chamadas e do bloqueio local, não homologação de gateway/API do Discord.
- A visibilidade das permissões de comandos em runtime é conservadora, mas não consegue reproduzir todos os overrides específicos configurados na interface de Integrações do Discord. O núcleo de execução continua sendo a autoridade para aceitar/rejeitar ações.
- A Nara não analisa prints nem anexos visuais; não foi implementado OCR.

## 9. Configuração nova


## 10. Complemento operacional — bot conversável

Na etapa de preparação para execução, foi encontrada uma lacuna operacional: a conversa livre tinha `NARA_CONVERSA_ENABLED=true` por padrão, mas o pacote não continha `.env` nem credenciais. Sem `GEMINI_API_KEY` ou `GEMINI_BACKUP_API_KEY`, a Nara permanecia online para funcionalidades locais, mas só podia responder com frases de contingência no papo livre. Isso não era uma conversa generativa funcional.

Foram adicionados:

- `configurar_bot.py`: cria/atualiza `.env`, solicita o token Discord e uma chave Gemini com entrada oculta, preserva outras configurações e define conversa livre ativa, pesquisa com ferramentas desligada e moderação desligada.
- `.env.example`: modelo de configuração para cópia manual.
- `.gitignore`: exclui `.env`, bancos e dados locais do controle de versão.
- `INICIAR_WINDOWS.bat` e `iniciar_linux.sh`: instalação de dependências, configuração e inicialização local.
- Log explícito no `cogs/nara_ia.py` quando a conversa está ligada mas nenhuma chave Gemini foi configurada ou o adaptador falhou.
- Testes do configurador em `tests/test_configurar_bot.py`.

O modelo padrão permanece `gemini-3.5-flash-lite`, que foi conferido na listagem atual de modelos da API Gemini no momento desta entrega. O configurador não valida credenciais junto aos serviços: ele não conecta à internet e não inicia o bot. A conexão real continua dependendo do token e da chave inseridos pelo operador. O pacote distribuído não contém `.env`, token Discord, chave Gemini ou banco de dados privado.

## 11. Passos antes de produção

1. Faça backup do `.env` e de `data/` antes de substituir o projeto.
2. Instale as dependências de `requirements.txt` no ambiente do bot.
3. Execute `python configurar_bot.py` ou preencha `.env` manualmente com token Discord e pelo menos uma chave Gemini.
5. Confira `NARA_CONVERSA_ENABLED=true`, `NARA_CHAT_IA_ENABLED=false` e `IA_ACOES_MODERACAO=false` no `.env`.
6. Inicie o bot e teste em um canal de homologação com um membro comum e um moderador.
7. Teste as intents Message Content/Server Members necessárias aos demais cogs e a permissão do bot para responder nos canais.
