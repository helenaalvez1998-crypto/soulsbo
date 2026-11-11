# Entrega — Base local de FAQ da Nara

## Implementação

A base `dados/nara_faq.json` foi integrada ao roteamento local. O arquivo contém 40 intenções, 295 exemplos de perguntas/paráfrases, 26 respostas finais prontas para Discord e 14 handlers dinâmicos que reutilizam consultas já existentes no NARA.

`faq_base.py` faz normalização e correspondência determinística por similaridade lexical, com limiar mínimo e margem entre a primeira e a segunda intenção. Não usa IA, embeddings, APIs nem dependências externas. Frases exatas cadastradas têm prioridade; paráfrases são aceitas apenas quando a confiança é suficiente. Perguntas ambíguas ou fora do escopo não são classificadas pelo FAQ.

Respostas fixas são carregadas do JSON e enviadas diretamente ao Discord. Consultas pessoais, saldo, inventário, estatísticas e rankings continuam usando os handlers e o SQLite, evitando valores estáticos para dados que mudam.

## Testes executados

- `pytest -q`: 80 aprovados.
- `python -m unittest discover -s tests -q`: 47 aprovados.
- `python -m compileall -q .`: concluído sem erros.
- 247 frases cadastradas verificadas individualmente contra sua intenção esperada.
- Paráfrases de registro de platina, remoção de zerado, consulta de jogos finalizados, avisos de live, saldo, patentes, canais, perfil, Caçador de Troféus e rankings verificadas.
- Perguntas de OBS/streaming externo não são absorvidas pelo FAQ e continuam fora do escopo local documentado.

## Limitações

O reconhecimento aproximado é lexical, não um modelo semântico. Ele funciona melhor quando a pergunta usa termos ou construções próximos aos exemplos. Para novos padrões, acrescente exemplos ao JSON e teste. Não foi realizada homologação em servidor Discord real nesta execução.

## Arquivos alterados/adicionados nesta etapa

- `dados/nara_faq.json` (novo)
- `faq_base.py` (novo)
- `tests/test_faq_base.py` (novo)
- `nara_local.py` (integração do classificador)
- `cogs/nara_ia.py` (envio de resposta final pronta)
- `README.md` (documentação)
- `BASE_LOCAL_NARA.md` (novo guia de manutenção)


## Revisão técnica adicional

- Foram adicionadas 50 paráfrases testadas para loja, canais, avisos do YouTube, XP, saldo, rankings, ajuda, patentes e regras.
- Testes após a revisão: 82 pytest e 47 unittest aprovados.
- A homologação em servidor Discord real continua pendente.
