# Integração inicial com Cloudflare R2

## Variáveis de ambiente
Configure no painel de hospedagem (ou no `.env` local, que não deve ser commitado):
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME` (ex.: `narabot-cartas`)
- `R2_PUBLIC_BASE_URL` (URL pública do bucket, sem barra final)

O endpoint S3 é montado automaticamente como
`https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com`.

## Dependência
Instale `boto3` com `pip install -r requirements.txt`.

## Comportamento
- Uploads feitos pela rota do Ateliê são enviados para `cartas/<user_id>/<card_id>/<sha256>.png`.
- A chave do objeto é registrada no SQLite; o segredo do R2 nunca chega ao navegador.
- A rota autenticada de leitura redireciona para a URL pública do objeto.
- Caminhos locais antigos continuam sendo servidos para compatibilidade.
- Sem as variáveis do R2, o endpoint de upload retorna HTTP 503; não grava silenciosamente no disco local.

## Importante
A validação atual em `sistemas/arte_upload_criador.py` aceita imagens horizontais próximas de 5:4 (500×400 a 1200×960). Ela ainda não aceita uma carta vertical completa. A validação de carta completa e o override com restauração são etapas seguintes; não substitua essa validação sem ajustar o contrato visual e os testes.
