# Sincronização exclusiva dos comandos slash

## Resultado pretendido
A árvore publicada pelo bot deve conter somente:
- `/nara`
- `/adm`

## O que o código faz na inicialização
1. Carrega as extensões existentes para preservar os handlers e sistemas usados internamente pelos painéis.
2. Filtra a árvore local, removendo todos os comandos slash de nível superior exceto `nara` e `adm`.
3. Quando `GUILD_ID` está definido, sincroniza exatamente esses dois comandos no servidor configurado, limpa comandos antigos de outros escopos de servidor conhecidos e remove os comandos globais antigos.
4. Quando `GUILD_ID` não está definido, sincroniza globalmente somente `/nara` e `/adm` e limpa registros antigos específicos de servidor.

## Implantação
- Atualize os arquivos do pacote na hospedagem.
- Preserve `.env`, banco de dados e arquivos de dados.
- Reinicie completamente o processo do bot (não basta recarregar um Cog).
- Confira o log: deve indicar a sincronização com `/nara` e `/adm` e nenhum outro comando.
- No Discord, feche e reabra o seletor `/`. Comandos globais podem levar algum tempo para desaparecer devido ao cache/propagação do Discord; comandos de servidor normalmente atualizam mais rapidamente.

## Observação
A sincronização remota só acontece quando a nova versão inicia com o token e as permissões da aplicação. Este pacote prepara a sincronização forçada, mas não executa a API do Discord a partir deste ambiente.
