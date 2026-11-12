# Instalação final e checklist de ativação — NARA/Nara

Este pacote contém o código do bot e a base local ampliada da Nara. Ele está preparado para configuração, mas não vem autenticado: token do Discord, chaves de IA, IDs do seu servidor e banco de produção são específicos da sua instalação e não foram incluídos.

## 1. Preparar a pasta

1. Extraia a pasta `NARA` do ZIP para o computador ou hospedagem. Não execute o bot de dentro do arquivo ZIP.
2. Use Python **3.11 ou superior**.
3. Abra o terminal dentro da pasta `NARA`.
4. Instale as dependências:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Criar a configuração privada

Execute:

```bash
python configurar_bot.py
```


Nunca envie `.env`, token Discord, chaves Gemini/Tavily ou `data/colizeu.db` em chats, tickets ou repositórios públicos.

## 3. Configurar o bot no Discord

No Discord Developer Portal, habilite as intents privilegiadas necessárias: **Message Content Intent**, **Server Members Intent** e **Voice States**. Convide o bot com os escopos `bot` e `applications.commands`. Garanta permissões compatíveis com os módulos utilizados: ver canais e histórico, enviar mensagens, embeds/links, anexar arquivos, usar comandos, ler/enviar mensagens em tópicos, criar/gerenciar tópicos privados e **Gerenciar Cargos**.

O cargo mais alto do bot deve ficar acima dos cargos de patente, verificação e cargos autoatribuíveis. Crie previamente os 10 cargos de patente descritos no README; o bot não cria cargos ausentes. Crie também o cargo de verificação esperado (`Servidor Simplificado`, ou uma das variações compatíveis) e os cargos que quiser oferecer no painel.

## 4. Preencher IDs e canais

No `.env`, confira os IDs correspondentes à sua comunidade. Os IDs herdados no exemplo são apenas valores de referência da instalação de origem e **não devem ser presumidos corretos para outro servidor**. Ajuste pelo menos: `GUILD_ID`, canal de moderação, canal de platinas, canal do Coliseu, canal de perfis e IDs de vídeos/lives/jogos/promoções, conforme os recursos que pretende usar. Consulte `.env.example` para a lista completa.

`DB_PATH=data/colizeu.db` é o banco de dados padrão. Use armazenamento persistente na hospedagem e mantenha `data/` entre reinícios e atualizações.

## 5. Iniciar

```bash
python bot.py
```

No Windows, `INICIAR_WINDOWS.bat` também pode iniciar o bot. No Linux, use `./iniciar_linux.sh` depois de conceder permissão de execução (`chmod +x iniciar_linux.sh`).

## 6. Checklist no servidor

Depois que o bot conectar e sincronizar comandos:

- Execute `/nara` e teste os botões da central dos membros, incluindo Central de Ajuda e Memória da Nara.
- Faça uma pergunta FAQ num canal listado em `IA_CANAIS_LIVRES`; fora desses canais, mencione a Nara.
- Como administrador, abra `/adm` e confira canais, cargos e recompensas personalizados.
- Como moderador, publique os painéis necessários: `/painel_principal`, `/painel_platinas`, `/postar_painel_zerados`, `/painel_santuarios`, `/painel_cargos` e `/painel_loja`. Publique apenas os que realmente utilizar.
- Confira a atribuição de um cargo de teste e a hierarquia do bot antes de liberar cargos autoatribuíveis aos membros.
- Teste uma platina, uma run e um jogo zerado em ambiente controlado e confirme que os três cartões chegam ao mesmo canal central; confira aprovar/rejeitar antes de liberar o fluxo. Não use registros falsos em produção.
- Teste uma run com prova de teste e confirme que DMs estão habilitadas para o bot.
- Use `/gemini_status` e os comandos de status de YouTube/ofertas disponíveis para conferir a configuração, lembrando que status local não prova quota restante do fornecedor.

## 7. Limites desta entrega

Os testes automatizados da versão entregue passam, e os arquivos Python compilam. Ainda assim, não foi possível testar login do Discord, sincronização de comandos, permissões reais, callbacks dos botões, DMs, chaves dos provedores ou persistência na sua hospedagem sem as credenciais e o servidor. Faça o checklist acima antes de considerar a implantação concluída.

A conversa da Nara não analisa prints/imagens. Use os formulários específicos de platina, run e zerado para anexos de comprovação.


## Central de Aprovação

