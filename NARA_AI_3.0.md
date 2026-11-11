# NARA AI 3.0 — Personalidade, vínculos e escopo comunitário

## Objetivo
Evoluir a NARA para uma inteligência de identidade consistente e uso exclusivo da comunidade NARA. A NARA mantém humor debochado e relações sociais diferenciadas sem se tornar uma IA de uso geral.

## Funcionalidades implementadas nesta versão
- Gate determinístico e fail-closed de escopo antes de qualquer chamada conversacional ao Gemini.
- Conversa social permitida (saudações, agradecimentos, brincadeiras e provocações).
- Vocabulário de comunidade para NARA, Discord, jogos, Soulslike, troféus, platinas e sistemas internos.
- Roteamento de contexto para especialistas lógicos: segurança, administração, jogos/conquistas, comunidade e convivência. Todos preservam a identidade central.
- Relatório operacional `/nara_relatorio`, restrito à equipe, com volume de conversas, adesão à memória e estado dos circuitos Gemini.
- Personalidade canônica atualizada: debochada, sarcástica, provocadora, inteligente e carismática.
- Vínculo social individual com indicadores graduais de afinidade, familiaridade e intimidade de humor, persistido somente quando o membro ativou `/nara_memoria`.
- Memória e perfil social isolados por guilda e usuário; apagar histórico também apaga o perfil social.
- A afinidade adapta somente o tom. Não altera permissões, moderação, recompensas ou decisões administrativas.

## Limites
- O filtro de escopo é determinístico, não um classificador semântico universal. Perguntas novas ou ambíguas são bloqueadas por padrão; ajuste o vocabulário em `nara_social.py` se a comunidade adicionar novos jogos ou sistemas.
- Os especialistas são perfis de instrução no mesmo roteador Gemini, não processos ou modelos independentes.
- Não há automoderação punitiva autônoma nem painel web completo. Casos de segurança devem ser encaminhados à equipe e às ferramentas existentes; o relatório `/nara_relatorio` é um resumo operacional dentro do Discord.
- O painel analítico completo e a memória coletiva de acontecimentos ainda exigem fontes de eventos confiáveis e definição de métricas; esta versão não inventa esses dados.
- A personalidade é uma simulação conversacional, não consciência ou sentimento humano real.

## Privacidade
O perfil social só é criado/atualizado quando a memória individual está ativada. O comando `/nara_memoria` controla ativação, desativação e exclusão. O escopo do banco é `(guild_id, user_id)`.


## Revisão da Central de Ajuda
- As 118 respostas estáticas da FAQ foram revisadas para falar diretamente com o membro, com instruções objetivas e a personalidade debochada da NARA em doses moderadas.
- Removidos dos textos destinados a jogadores detalhes de implementação como nomes de variáveis, SQLite, chaves de API, circuitos de IA e funcionamento interno.
- 30 entradas operacionais foram marcadas como `staff_only` e removidas da Central de Ajuda dos membros. O índice `/comandos` continua sendo o local para comandos de MOD/ADMIN.
- As categorias técnicas foram reorganizadas na Central de Ajuda sob **Sobre a NARA** quando o assunto é relevante para o membro.
- A Central de Ajuda deixou de anunciar que as respostas são “locais” ou que não consomem Gemini; isso é detalhe interno, não informação necessária para quem só quer resolver uma dúvida.
- O texto de contingência também foi ajustado para manter o escopo comunitário e a voz da NARA.
