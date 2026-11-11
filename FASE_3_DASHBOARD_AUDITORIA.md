# Fase 3 — Dashboard operacional e auditoria

## Entregas
- Dashboard no menu `/adm` → Diagnóstico.
- Indicadores de solicitações pendentes, decisões de aprovação e rejeição gravadas em logs nos últimos 7 dias, separadas por Platinas, Runs/Desafios e Jogos Zerados.
- Identificação da solicitação pendente mais antiga.
- Contagem de eventos já gravados em logs cujo nome da ação contém `erro` ou `falha` nas últimas 24 horas.
- Atividade recente no dashboard.
- Histórico de auditoria com filtros (todas, moderação, administração, erros/falhas), pesquisa por ID de ator/ação/detalhes e paginação.
- Restrição dos painéis ao moderador que os abriu e nova validação de permissão a cada interação.
- Sem alteração do esquema do banco: utiliza a tabela `logs` existente.

## Limitações de interpretação
- A métrica de erros conta apenas eventos que já tenham sido gravados em `logs` com `erro` ou `falha` no campo `action`; exceções apenas escritas no arquivo de log do processo não aparecem no indicador.
- A pesquisa retorna no máximo os 200 eventos mais recentes que correspondem ao filtro. Não é uma pesquisa em todo o histórico se houver mais de 200 correspondências.
- As métricas são globais ao banco instalado no bot. A tabela `logs` atual não possui `guild_id`, portanto não é possível separar o histórico por servidor sem uma migração futura.
- O sistema não inventa eventos retroativos: o histórico depende dos registros efetivamente existentes.

## Instalação e validação
1. Faça backup da pasta `data` e do `.env`.
2. Substitua os arquivos do projeto pelo conteúdo deste pacote, preservando `.env` e o banco.
3. Reinicie a NARA e abra `/adm` → Diagnóstico.
4. Teste Dashboard operacional e Histórico de auditoria com uma conta moderadora.
5. Compare as contagens com os registros do banco antes de liberar o painel.

Não apague nem recrie o banco de dados.
