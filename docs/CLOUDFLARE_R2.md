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

As rotas de visualização da fila e de arte oficial recuperam imagens do R2 pelo backend. A fila de revisão continua exigindo autenticação e permissão administrativa; submissões pendentes não entram na rota pública de cartas. Depois de aprovadas, as artes passam a ser servidas pela rota pública de imagem da carta.

Na primeira inicialização após atualizar, o banco recebe a coluna `image_key` automaticamente. Não é necessário apagar nem recriar o SQLite.


## CDN pública de todas as imagens de cartas

A rota `/api/gwent/public-cards/<card_id>/image` atende sem login as cartas publicadas do catálogo, as artes oficiais aprovadas e as cartas geradas que já estejam publicadas e validadas. A URL inclui raridade/poder quando esses atributos alteram a imagem; usuários diferentes com a mesma variante usam a mesma chave de cache.

As renderizações ficam persistidas em `DATA_DIR/cartas_cache`. No primeiro acesso, a instância gera a imagem uma vez e envia uma cópia imutável para o bucket R2 público configurado. As próximas respostas redirecionam diretamente ao domínio CDN da imagem, sem renderizar novamente. Artes ainda pendentes de aprovação não são publicadas.

A implementação reutiliza por padrão o bucket e as credenciais que o bot já usa (`R2_BUCKET_NAME`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID` e `R2_SECRET_ACCESS_KEY`). Portanto, não é necessário criar um segundo bucket. As cartas publicadas e artes aprovadas são copiadas para o prefixo `cards/` e ficam acessíveis sem login pela URL pública.

Para habilitar a distribuição pela CDN:
1. No Cloudflare R2, abra o bucket definido em `R2_BUCKET_NAME` e conecte um domínio próprio em Settings → Public access → Custom Domains, por exemplo `img.seudominio.com`.
2. No painel da FadeHost, defina `R2_PUBLIC_CARDS_BASE_URL=https://img.seudominio.com`. A variável substitui o domínio público somente para as imagens de cartas; as credenciais e o bucket continuam sendo os já configurados.
3. O token S3 usado pelo bot precisa ter permissão de leitura/gravação no bucket configurado. Não coloque as credenciais no GitHub nem no frontend.
4. Reinicie o bot. As variantes são enviadas para `cards/<hash-da-carta>/<etag>.<formato>` com `Cache-Control: public, max-age=31536000, immutable`.

Se preferir isolar os arquivos de cartas em outro bucket, defina `R2_PUBLIC_CARDS_BUCKET_NAME` e `R2_PUBLIC_CARDS_BASE_URL` juntos, e conceda acesso a esse bucket ao token. As variáveis `R2_PUBLIC_CARDS_ACCOUNT_ID`, `R2_PUBLIC_CARDS_ACCESS_KEY_ID` e `R2_PUBLIC_CARDS_SECRET_ACCESS_KEY` são opcionais; vazias, reutilizam as credenciais `R2_*` existentes.

Use um domínio customizado do Cloudflare para a CDN. O endereço `r2.dev` serve para testes, mas não oferece os mesmos recursos de cache/CDN do domínio customizado. Se o R2 não estiver configurado, o sistema continua usando o cache persistente em disco compartilhado pela instância. A rota antiga `/api/gwent/cards/.../image` permanece como compatibilidade; os novos payloads do site e do Gwent usam a rota pública.
