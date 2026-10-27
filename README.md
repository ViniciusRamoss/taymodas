# Tay Modas — Catálogo Online

[![CI](https://github.com/OWNER/taymodas/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/taymodas/actions/workflows/ci.yml)

Catálogo web da **Tay Modas** ([@taymodas23](https://instagram.com/taymodas23)), loja de moda
feminina em Serrana-SP. As clientes navegam pelas peças e fazem o pedido pelo WhatsApp, com a
mensagem já preenchida (produto, tamanho e cor). A dona da loja cadastra produtos, fotos e
estoque por um painel administrativo em português.

> 🚧 Em desenvolvimento. Veja o [plano do projeto](docs/plan.md).

## Funcionalidades

- [x] Estrutura do projeto, CI e qualidade de código
- [x] Produtos com várias fotos, categorias e variantes (tamanho + cor) com estoque
- [x] Painel administrativo em PT-BR pensado para quem não é técnico
- [x] Catálogo público mobile-first (listagem por categoria, paginação)
- [ ] Filtros por tamanho e cor (HTMX)
- [ ] Botão "Pedir no WhatsApp" com mensagem preenchida
- [ ] Deploy gratuito (Render + Neon + Cloudinary)

## Stack

| Camada     | Tecnologia                                               |
|------------|----------------------------------------------------------|
| Backend    | Python 3.12, Django 5.2 LTS                              |
| Frontend   | Templates Django, Tailwind CSS (sem Node), HTMX          |
| Banco      | SQLite (dev), PostgreSQL (prod)                          |
| Mídia      | Cloudinary                                               |
| Qualidade  | ruff, mypy (strict), pytest, pre-commit, GitHub Actions  |

## Rodando localmente

Pré-requisito: [uv](https://docs.astral.sh/uv/). Ele instala o Python 3.12 se for preciso.

```bash
git clone https://github.com/OWNER/taymodas.git
cd taymodas
uv sync
cp .env.example .env          # edite DJANGO_SECRET_KEY
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py tailwind build      # gera o CSS (baixa o binário do Tailwind na 1ª vez)
uv run python manage.py seed_demo           # opcional: produtos fictícios para testar
uv run python manage.py tailwind runserver  # servidor + recompila o CSS ao salvar
```

- Site: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin/
- Healthcheck: http://127.0.0.1:8000/health/

Para testar pelo celular na mesma rede Wi-Fi:

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

Adicione o IP do computador em `DJANGO_ALLOWED_HOSTS` (ex.: `localhost,127.0.0.1,192.168.0.10`)
e acesse `http://192.168.0.10:8000` no celular.

## Qualidade

```bash
uv run pre-commit install     # roda os hooks em cada commit
uv run ruff check .           # lint
uv run ruff format .          # formatação
uv run mypy .                 # tipos
uv run pytest                 # testes + coverage
```

A CI roda lint, format, mypy, checagem de migrations pendentes, `check --deploy` com os settings
de produção e os testes em cada push e pull request.

## Estrutura

```
config/settings/   base, dev, test, prod
apps/core/         configurações da loja, storage Cloudinary, healthcheck
apps/catalog/      produtos, variantes, fotos e admin
templates/         templates globais
static/            CSS, JS e imagens
docs/              plano, decisões e deploy
```

## Variáveis de ambiente

Veja [`.env.example`](.env.example). Em produção, as obrigatórias são `DJANGO_SECRET_KEY`,
`DJANGO_ALLOWED_HOSTS`, `DATABASE_URL` e `CLOUDINARY_URL` (o app não sobe sem elas, porque o
disco do servidor gratuito é apagado a cada deploy).

Em desenvolvimento, sem `CLOUDINARY_URL` as fotos ficam na pasta `media/`.

## Deploy

Documentação em `docs/deploy.md` (Etapa 8).

## Licença

[PLACEHOLDER — definir licença]
