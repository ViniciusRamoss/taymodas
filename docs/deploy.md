# Deploy

Produção a custo zero: **Render** (site), **Neon** (Postgres) e **Cloudinary** (fotos). O
Render lê o `render.yaml` da raiz do repositório e roda `bin/build.sh` e `bin/start.sh`.

Faça na ordem: cada passo usa um valor do anterior.

## 1. GitHub

1. Em github.com, crie o repositório `taymodas` **vazio** (sem README, sem .gitignore).
   Privado é o mais seguro até a Etapa 9 (portfólio).
2. No terminal, dentro do projeto:

   ```bash
   git remote add origin https://github.com/<seu-usuario>/taymodas.git
   git push -u origin main
   ```

O CI (`.github/workflows/ci.yml`) roda lint, tipos, `check --deploy` e testes a cada push.

## 2. Neon (banco)

1. **New project**: nome `taymodas`, Postgres 17, região **AWS US East 1 (N. Virginia)**, a
   mesma do Render. Banco e site em regiões diferentes deixam cada página lenta.
2. Em **Connect**, desligue **Connection pooling** e copie a connection string. Ela termina
   em `?sslmode=require`. Esse é o `DATABASE_URL`.

Por que sem pooling: o pooler do Neon usa o modo transação do PgBouncer, que quebra os cursores
do lado do servidor que o Django usa em `QuerySet.iterator()` (exigiria
`DISABLE_SERVER_SIDE_CURSORS`). Com 2 workers a conexão direta fica muito abaixo do limite.

## 3. Cloudinary (fotos)

No **Dashboard**, copie **API environment variable**
(`cloudinary://<api_key>:<api_secret>@<cloud_name>`). Esse é o `CLOUDINARY_URL`.

## 4. Render (site)

1. **New > Blueprint**, escolha o repositório `taymodas`. O Render lê o `render.yaml`.
2. Preencha as variáveis pedidas:

   | Variável                | Valor                                                       |
   |-------------------------|-------------------------------------------------------------|
   | `DATABASE_URL`          | Connection string do Neon (passo 2)                         |
   | `CLOUDINARY_URL`        | Variável do Cloudinary (passo 3)                            |
   | `DJANGO_ADMIN_URL`      | Caminho secreto do painel, terminando em `/`. Ex.: `painel-7f3k9q/` |
   | `DJANGO_ADMIN_USERNAME` | Usuário do painel                                           |
   | `DJANGO_ADMIN_PASSWORD` | Senha forte (12+ caracteres)                                |
   | `DJANGO_ADMIN_EMAIL`    | Opcional                                                    |

   `DJANGO_SECRET_KEY` é gerada pelo próprio Render. O host (`*.onrender.com`) entra sozinho
   via `RENDER_EXTERNAL_HOSTNAME`; domínio próprio, depois, vai em `DJANGO_ALLOWED_HOSTS`.
3. **Apply**. O primeiro build leva alguns minutos. Pronto quando `/health/` responder
   `{"status": "ok"}`.

## 5. Primeiro acesso

1. Abra `https://<servico>.onrender.com/<DJANGO_ADMIN_URL>` e entre com o usuário do passo 4.
2. Troque a senha no painel (canto superior direito) e **apague `DJANGO_ADMIN_PASSWORD`** no
   Render (Environment). O usuário já existe; a variável só servia para criá-lo.
3. **Configurações da loja**: número do WhatsApp (55 + DDD + número), mensagem e entrega.
4. Cadastre categorias, tamanhos, cores e os produtos com fotos.

## Como funciona cada deploy

- Push na `main` dispara deploy automático (`autoDeploy: true`).
- `bin/build.sh`: instala dependências com `uv`, gera o CSS do Tailwind e roda `collectstatic`.
- `bin/start.sh`: `migrate`, `ensure_admin` (só cria o admin se não existir) e gunicorn com 2
  workers. Migrations rodam no start porque o plano free não tem pre-deploy.
- O app recusa subir sem `DATABASE_URL`, `CLOUDINARY_URL` ou host: o disco do Render é
  apagado a cada deploy, então SQLite e `media/` local perderiam tudo.

## Limites do plano gratuito

- O site **hiberna após 15 min sem visitas**; a primeira visita depois disso leva ~1 min.
  Um monitor externo (ex.: UptimeRobot a cada 10 min em `/health/`) evita isso, gastando
  horas do limite de 750 h/mês do workspace (um único serviço cabe).
- Neon free (verificado em 2026-10): 0,5 GB de armazenamento e 100 CU-hora/mês por projeto;
  suspende após 5 min parado e volta na primeira consulta. Um catálogo pequeno usa uma fração.
- Cloudinary free (verificado em 2026-10): 25 créditos/mês, somados entre armazenamento
  (1 GB = 1 crédito), banda (1 GB = 1 crédito) e transformações (1.000 = 1 crédito). Fotos são
  reduzidas para até 2000px no upload, e o site pede só 400/600/800/1200px.
- Sem shell no Render free: tarefas de manutenção viram management commands no start ou são
  feitas pelo admin.

## Problemas comuns

| Sintoma                                   | Causa provável                                       |
|-------------------------------------------|------------------------------------------------------|
| Deploy falha com `ImproperlyConfigured`   | Variável obrigatória vazia (a mensagem diz qual)     |
| `DisallowedHost` / 400                    | Domínio próprio fora de `DJANGO_ALLOWED_HOSTS`       |
| Fotos somem após um deploy                | `CLOUDINARY_URL` errada (caiu no disco local)        |
| Páginas lentas (1–2 s) sempre             | Neon e Render em regiões diferentes                  |
| Admin 404                                 | Endereço sem o `DJANGO_ADMIN_URL` exato (com `/`)    |
