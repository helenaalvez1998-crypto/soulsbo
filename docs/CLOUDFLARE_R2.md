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
A validação atual em `sistemas/arte_upload_criador.py` aceita cartas completas verticais próximas de 2:3 (mínimo 512×768, saída limitada a 1536×2304). A normalização preserva o enquadramento integral com `thumbnail`; não usa `ImageOps.fit` nem corta moldura, textos ou ilustração. O contrato do Ateliê é uma carta completa gerada por IA e vinculada ao exemplar específico.


## Ateliê de Cartas — submissões para aprovação

A rota `POST /api/gwent/atelier/submit` agora:
1. autentica o usuário e valida origem, carta, prompt e imagem;
2. normaliza a imagem com o validador já existente;
3. envia a imagem para `atelier/submissions/<user>/<card-hash>/<sha256>-<nonce>.jpg`;
4. registra no SQLite a chave `image_key`, mantendo `image_data` vazio para novos envios;
5. mantém submissões antigas em BLOB compatíveis;
6. continua enviando a imagem em memória ao canal de revisão do Discord.

As rotas de visualização da fila e de arte oficial recuperam imagens do R2 pelo backend. A imagem pendente não é exposta por URL pública; o endpoint de revisão continua exigindo autenticação e permissão administrativa.

Na primeira inicialização após atualizar, o banco recebe a coluna `image_key` automaticamente. Não é necessário apagar nem recriar o SQLite.
