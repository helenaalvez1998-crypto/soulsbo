# NARA AI 2.0 — Implementação

## O que mudou

1. **Memória privada e opt-in**
   - Cada membro decide se ativa a memória em cada servidor.
   - O botão **Memória da Nara** no `/nara` abre os controles de Ativar, Desativar, Ver status e Apagar histórico.
   - Até 12 mensagens recentes por membro/servidor; retenção máxima de 30 dias.
   - A memória é persistida no SQLite em `nara_memoria` e `nara_memoria_privacidade`.
   - Memória começa desativada. Não guarda imagens/anexos.

2. **Visão multimodal**
   - A Nara pode analisar imagens PNG, JPEG, WEBP e GIF quando é mencionada ou quando a mensagem está no canal de conversa livre configurado.
   - Limites: até 2 imagens por mensagem, 5 MiB por arquivo e 8 MiB no total.
   - Os bytes são enviados ao provedor Gemini configurado usando `types.Part.from_bytes` e não são persistidos pelo NARA. Esse formato é documentado pelo SDK Google Gen AI.
   - SVG, HEIC, PDF e outros formatos não são enviados ao modelo.
   - Imagens usadas como comprovantes de platina/run são bloqueadas na conversa e devem seguir pelos formulários oficiais de **Coliseu** dentro do `/nara`.

3. **Canal de conversa configurável por servidor**
   - A configuração automática cria `#nara-conversa`.
   - `/adm` → Canais → Canal de conversa livre da Nara permite trocar o destino.
   - A configuração é persistida no KV por servidor. `NARA_CHANNEL_ID` é apenas fallback opcional.

4. **Failover mantido**
   - A conversa usa os projetos Gemini principal, reserva e terceiro já suportados.
   - Imagens usam o mesmo modelo/provedor Gemini configurado; não exigem uma chave adicional.
   - Tavily continua sendo a integração opcional de pesquisa web. Não habilite pesquisa sem `TAVILY_API_KEY`.
   - DeepSeek não é declarado como provedor ativo porque o roteador principal ainda não o utiliza.

## Configuração no Discord

1. Publique a versão atualizada e reinicie o bot.
2. Execute `/adm` e escolha **Configuração Automática** para criar/vincular `#nara-conversa`.
3. Se preferir outro canal, use `/adm` → **Canais** → **Canal de conversa livre da Nara**.
4. Cada membro que desejar memória abre `/nara`, escolhe **Memória da Nara** e clica em **Ativar memória**.
5. Para apagar dados, o próprio membro abre `/nara`, escolhe **Memória da Nara** e clica em **Apagar histórico**.

## Configuração na FadeHost

- Manter `DATA_DIR=/data` e o banco SQLite no volume persistente.
- Manter as chaves `GEMINI_API_KEY`, `GEMINI_BACKUP_API_KEY` e `GEMINI_THIRD_API_KEY` apenas no gerenciador de variáveis da FadeHost.
- `NARA_CHANNEL_ID` pode permanecer `0` quando o canal for escolhido no `/adm`.
- Não é necessária uma nova variável de ambiente para memória ou visão.

## Limites e segurança

- A memória não é ativada automaticamente para membros; requer consentimento explícito.
- A memória é isolada por `guild_id` e `user_id`.
- A Nara não pode usar memória de outra pessoa.
- O conteúdo recuperado é marcado como contexto não confiável, não como instrução.
- A visão é descritiva; não aprova platinas, runs, cargos ou solicitações.
- A execução de ações continua sujeita às guardas do núcleo `ia_nucleo.py`, permissões e confirmações existentes.

## Validação realizada

- `compileall`: passou.
- `pytest`: 98 testes aprovados.
- `unittest discover`: 56 testes aprovados.
- Não foi possível executar smoke test com sessão Discord real nem validar chamadas reais ao Gemini neste ambiente; isso exige credenciais e ambiente de produção.

Documentação oficial do SDK: https://googleapis.github.io/python-genai/ (entrada multimodal com `Part.from_bytes`).
