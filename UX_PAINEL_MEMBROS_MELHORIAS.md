# Melhorias de experiência do painel /nara

## Objetivo
Preservar a identidade visual e as cinco categorias existentes, melhorando a descoberta de funcionalidades reais.

## Alterações
- Mantidas as cinco categorias: Jogos e conquistas, Minha biblioteca, Meu progresso, Preferências e Ajuda e suporte.
- Mantidos os fluxos existentes de Coliseu, Caçador, pesquisa de jogos, Zerados, nível/XP, ranking, Loja, memória e ajuda.
- Adicionados dois acessos diretos na tela principal:
  - Meu perfil: reutiliza `Perfil.embed_perfil`, exibindo patente, nível, Denários, XP, platinas, zerados e posições nos rankings.
  - Meu Santuário: reutiliza `Santuario.abrir_meu`, sem duplicar regras de criação ou personalização.
- Atualizadas as descrições da central e do guia para explicitar Platinas, Zerados, Runs e desafios e Caçador dentro do Coliseu.
- Incluídas opções de orientação para Perfil e Santuário no seletor de guias.
- Mantido o controle de propriedade do painel: somente o membro que abriu `/nara` pode interagir com ele.

## Validação
- `pytest`: 118 aprovados.
- Compilação: 68 arquivos Python, sem erros.
- Nenhuma alteração no schema do banco.
- Não houve teste em servidor Discord real; validar os botões com `discord.py` e permissões de Santuário na homologação.
