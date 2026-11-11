# NARA — Fase 1: Navegação por categorias

## O que mudou

### Central dos membros (`/nara`)
- A tela inicial foi reorganizada em cinco categorias: Jogos e conquistas, Minha biblioteca, Meu progresso, Preferências e Ajuda e suporte.
- Cada categoria abre um submenu com ações relacionadas.
- As dez ações anteriores continuam disponíveis e chamam os módulos originais.
- A pesquisa de jogo e a remoção de registro continuam usando seus formulários.
- Os submenus verificam o usuário que abriu a central e permanecem privados.
- O seletor de guias permanece disponível na tela inicial.

### Central administrativa (`/adm`)
- A tela inicial foi reorganizada em cinco categorias: Servidor, Moderação, Sistemas, Economia e Diagnóstico.
- As doze operações que já estavam no painel continuam acessíveis por submenus.
- Os submenus administrativos verificam o moderador que abriu o painel.
- Os botões da tela inicial possuem `custom_id` estáveis para manter a view raiz persistente.
- As ações continuam encaminhadas aos handlers existentes; não foram recriadas regras de configuração, economia ou moderação.

## O que não mudou
- Nenhuma tabela ou migração do banco de dados foi alterada.
- Nenhuma regra de XP, Denários, platinas, runs ou jogos zerados foi alterada.
- Nenhum canal de aprovação foi removido.
- Nenhum comando slash adicional foi removido nesta fase.
- A Central de Moderação ainda utiliza a navegação existente para abrir o cartão original; aprovação direta pelo painel pertence à fase seguinte.

## Validação executada
- Compilação dos 62 arquivos Python: aprovada.
- Suíte pytest: 104 testes anteriores + 4 testes novos de navegação = 108 testes aprovados.
- Não foi possível validar interações em um servidor Discord real neste ambiente, pois não foram fornecidos credenciais, canais ou servidor de homologação.
- A instalação local não tinha a biblioteca `discord.py` disponível para instanciar as views; por isso, a validação de interface em runtime permanece pendente.

## Instalação
1. Faça backup da pasta atual da NARA e do banco SQLite.
2. Pare o bot.
3. Substitua os arquivos do projeto pelos arquivos deste pacote, preservando o `.env` e o banco de dados de produção.
4. Inicie o bot e verifique os logs de carregamento dos Cogs e sincronização.
5. Teste `/nara` com uma conta comum e `/adm` com um moderador.
6. Confirme que as categorias abrem os submenus e que todas as ações continuam operando.
7. Só depois de homologar, promova a versão para o servidor principal.

> Esta entrega implementa a reorganização de navegação da Fase 1. Não é a conclusão da auditoria completa nem da Central de Moderação com decisões diretas no painel.
