# Guia de comandos — NARA

A navegação dos membros foi centralizada em um único comando: `/nara`. Ele abre um painel privado com botões para os sistemas de uso diário. Os comandos de moderação e administração continuam separados e são acessados conforme as permissões do Discord.

## Central dos membros

Use `/nara` para abrir os botões:

- **Coliseu** — platinas, runs, desafios, rankings, perfil e Santuários.
- **Jogos zerados** — registrar finalizações, consultar lista e ranking.
- **Loja** — comprar cosméticos com Denários.
- **Meu nível** — consultar XP, nível e patente.
- **Ranking XP** — consultar a classificação de experiência.
- **Pesquisar jogo** — identificar um título e iniciar a pesquisa do catálogo.
- **Remover zerado** — abrir o formulário para informar o número do próprio registro.
- **Memória da Nara** — ativar, desativar, consultar ou apagar a memória pessoal.
- **Central de ajuda** — FAQ interativa por assunto.

Os painéis e formulários são privados. A navegação usa as funções existentes dos módulos originais, sem duplicar regras de negócio. O acesso aos próprios registros continua protegido; membros não podem remover registros de terceiros sem permissão de moderação.

## Comandos administrativos por fluxo

### 1. Administração geral e painéis

- `/adm` — painel central; exige **Administrador**.
- `/painel_principal` — publica ou atualiza o painel principal.
- `/postar_painel` — atalho legado para a mesma finalidade; prefira `/painel_principal`.
- `/painel_platinas` — painel público de platinas.
- `/painel_colizeu` — painel do Colizeu.
- `/colizeu` — atualiza a mensagem informativa e os rankings do canal.
- `/postar_painel_zerados` — painel de jogos concluídos.
- `/painel_loja` — vitrine pública da loja.
- `/painel_santuarios` — painel público de Santuários.

### 2. Cargos e verificação

1. `/painel_verificacao` — publicar/atualizar verificação.
2. `/painel_cargos` — publicar/atualizar escolha de cargos.
3. `/editar_painel_cargos` — editar título e texto.
4. `/cargo_painel` — adicionar, editar ou remover opções.


O fluxo é sequencial: consultar fila → preparar catálogo → auditar → validar manualmente → publicar ou rejeitar.

- `/catalogo_admin` — entrada do painel administrativo.
- `/catalogo_fila` e `/catalogo_retentar` — solicitações pendentes e retomada de um pedido elegível.
- `/catalogo_importar` — importa um rascunho de catálogo para revisão. Para identificar um título, use **Pesquisar jogo** no `/nara`.
- `/catalogo_auditar` — verificar cobertura, fontes e consistência.
- `/catalogo_validar` — registrar que a revisão humana foi concluída.
- `/catalogo_publicar` ou `/catalogo_rejeitar` — decisão final.
- `/catalogo_despublicar` — retirar um catálogo publicado para nova revisão.
- `/catalogo_historico` — consultar o histórico de alterações.

A publicação não é automática. A validação exige conferência humana dos registros e fontes.

### 4. Runs e desafios Soulslike

Jogadores registram as tentativas em **Coliseu → Runs**, dentro de `/nara`. A moderação usa:

- `/sl_admin publicar_central` — publicar a central permanente.
- `/sl_admin jogo_adicionar` — adicionar jogo.
- `/sl_admin desafio_adicionar` — cadastrar desafio e regras.
- `/sl_admin invalidar` — retirar uma run aprovada do ranking e justificar no log.

### 5. Integrações e diagnósticos

- `/status_youtube`, `/teste_video` e `/teste_live` — conferir e testar avisos do YouTube.
- `/status_ofertas` e `/previa_oferta` — conferir monitoramento e prévia de cartões de ofertas.
- `/gemini_status` — conferir o estado dos provedores e circuitos de IA.
- `/nara_relatorio` — relatório operacional da Nara, disponível somente para a equipe autorizada.

Os comandos administrativos dependem das permissões do Discord e das verificações internas da NARA. Em geral, comandos de painéis exigem Gerenciar servidor ou o papel de moderação configurado; `/adm` exige Administrador.

## Atenção: comandos com grafia parecida

- `/nara` — central interativa de todos os recursos dos membros.
- `/adm` — central interativa exclusiva da administração.
- `/colizeu` (com Z) — comando de moderação para atualizar a mensagem informativa e os rankings do canal.

Os comandos individuais dos membros foram retirados da lista de slash commands e suas funções passaram a ser acessadas pelo painel `/nara`. Os fluxos internos e as permissões originais foram preservados.

### Painel fixo da Central de Ajuda

- `/painel_ajuda_nara` — publica no canal atual um painel permanente. Qualquer membro pode clicar em **Abrir Central de Ajuda**; a navegação abre em resposta privada para não poluir o canal. Exige **Gerenciar servidor**.
