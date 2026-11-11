# Absorção do Catálogo de Jogos, Mods e Radar de Games pela NARA

## Arquitetura entregue nesta etapa
- O catálogo de jogos e o catálogo de mods foram portados para `cogs/catalogo_integrado.py`.
- O Radar RSS foi portado para `cogs/game_news.py`.
- Os dois módulos são carregados pela única instância `NaraBot`; não criam outro `commands.Bot`, não executam `bot.run()` e não sincronizam uma árvore de comandos própria.
- Os comandos slash antigos do módulo de notícias continuam disponíveis como handlers internos do Cog, mas a árvore pública da NARA é filtrada para manter somente `/nara` e `/adm`.
- O painel `/nara` ganhou a categoria **Catálogos**, que abre os catálogos de jogos e mods, pesquisa e envio de sugestões.
- O painel `/adm` ganhou as categorias **Catálogos** e **Radar de Games**.
- A administração do catálogo preserva também a função antiga de publicar/atualizar um painel público em um canal escolhido.
- As ações administrativas de jogos/mods continuam protegidas por `manage_guild` ou pelo cargo configurado em `MOD_ROLE_ID`.
- As funções de aprovação do catálogo usam o armazenamento e os status próprios do catálogo; não misturam aprovações de jogos com a fila de Platinas/Desafios/Zerados da NARA.

## Persistência e dados do bot antigo
O módulo procura `jogos.db`, `capas/` e `capas_mods/` dentro de `CATALOGO_DATA_DIR`. Se a variável não estiver definida, usa o diretório persistente configurado pela NARA (`config.DATA_DIR`).

Para reaproveitar os dados do bot antigo:
1. Pare o bot antigo.
2. Faça backup de `jogos.db`, `capas/` e `capas_mods/`.
3. Copie os três itens para o volume persistente da NARA, mantendo os caminhos relativos das imagens; ou defina `CATALOGO_DATA_DIR` apontando para a pasta original.
4. Preserve `jogos.db` sem renomear. O código cria as tabelas que faltarem e converte caminhos relativos das capas para caminhos absolutos sem mover os arquivos.
5. Não remova a cópia de backup até confirmar os catálogos no Discord.

## Radar RSS
- Usa o mesmo `jogos.db` do catálogo, em tabelas próprias (`news_feeds`, `news_seen`, `news_config`).
- O canal, feeds, listagem e teste são configurados pelo painel `/adm` > **Radar de Games**.
- A primeira leitura de cada feed registra os itens existentes sem publicar notícias antigas.
- O monitor consulta feeds a cada cinco minutos.

## Limites desta etapa
- O ZIP original fornecido continha o código do segundo bot, mas não continha `jogos.db`, as capas, as capas de mods nem configurações da instalação em produção. Portanto, o código foi integrado, mas a recuperação dos registros históricos depende de copiar os dados reais.
- A homologação real no Discord ainda é necessária para validar permissões, upload de imagens, publicação RSS, canal de avisos e comportamento dos menus com a versão instalada de `discord.py`.
- O bot antigo ainda não deve ser removido do servidor até concluir essa homologação e conferir que os dados foram preservados.


## Centrais `/nara` e `/adm` — consolidação

- `/nara` organiza acesso de membros a jogos/conquistas, biblioteca (Platinas, Zerados e Runs e desafios), progresso, preferências, ajuda, catálogos e comunidade.
- `/adm` agrega configurações do servidor, moderação, sistemas, economia, diagnóstico, publicação de painéis, catálogos, radar/conteúdo, cargos/acesso, NARA IA e administração do Caçador de Troféus.
- Ações internas que reutilizam callbacks de comandos administrativos repetem a verificação de `Gerenciar Servidor`/`Administrador` antes de executar.
- Os comandos slash públicos permanecem restritos a `/nara` e `/adm`.
