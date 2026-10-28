# Tay Modas — Catálogo Online

[![CI](https://github.com/ViniciusRamoss/taymodas/actions/workflows/ci.yml/badge.svg)](https://github.com/ViniciusRamoss/taymodas/actions/workflows/ci.yml)

Catálogo web da **Tay Modas** ([@taymodas23](https://instagram.com/taymodas23)), loja de moda
feminina em Serrana-SP. As clientes navegam pelas peças e fazem o pedido pelo WhatsApp, com a
mensagem já preenchida (produto, tamanho e cor). A dona da loja cadastra produtos, fotos e
estoque por um painel administrativo em português.

**No ar:** https://taymodas.onrender.com

## Funcionalidades

- Catálogo mobile-first com categorias, paginação e selos "Novidade" e "Esgotado".
- Filtros por tamanho e cor com HTMX: atualizam a lista sem recarregar a página e geram URLs
  compartilháveis. Sem JavaScript, viram um formulário comum.
- Página da peça com galeria e escolha de tamanho e cor. Combinações sem estoque aparecem
  riscadas; a peça escolhida vai para a sacola.
- Promoções: preço promocional por peça, com data de término opcional; selo, preço riscado e
  atalho "Promoções" na listagem.
- Sacola na sessão (sem login): quantidades limitadas ao estoque, total, e o botão "Enviar
  pedido pelo WhatsApp" abre a conversa com todas as peças (quantidade, cor, tamanho, valor e
  link) e o total já escritos.
- Painel administrativo em PT-BR para quem não é técnico: fotos com prévia, estoque por
  tamanho e cor, filtros de esgotado e atualização de estoque em lote.
  [Guia do painel](docs/guia-admin.md).
- Prévia com foto e preço ao compartilhar um link (Open Graph), sitemap, `robots.txt` e
  páginas de erro próprias.
- Hospedagem a custo zero: Render, Neon (PostgreSQL) e Cloudinary.

## Decisões técnicas

- **Sem SPA.** Templates Django com HTMX: cada interação também funciona como link ou
  formulário comum, e o botão voltar do navegador restaura o estado.
- **Camadas finas.** `selectors.py` faz as consultas, `services.py` guarda as regras de
  negócio em funções puras (escolha de variante, montagem da mensagem do WhatsApp) e
  `presenters.py` entrega aos templates dados prontos para exibir. As views só ligam as partes.
- **Estoque por variante.** Tamanho e cor só contam como disponíveis juntos, na mesma
  variante com estoque, tanto nos filtros quanto na página da peça.
- **Fotos econômicas.** O Cloudinary reduz as fotos no upload e entrega WebP/AVIF no tamanho
  da tela (`srcset`), para caber na cota gratuita.
- **Qualidade.** mypy strict, ruff e testes com pytest em cada commit (pre-commit) e em cada
  push (GitHub Actions).

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
git clone https://github.com/ViniciusRamoss/taymodas.git
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
docs/              plano, deploy e guia do painel
bin/               scripts de build e start do Render
render.yaml        Blueprint do Render
```

## Variáveis de ambiente

Veja [`.env.example`](.env.example). Em produção, as obrigatórias são `DJANGO_SECRET_KEY`,
`DATABASE_URL`, `CLOUDINARY_URL` e um host (`DJANGO_ALLOWED_HOSTS`, ou o
`RENDER_EXTERNAL_HOSTNAME` que o Render define sozinho). O app não sobe sem elas, porque o
disco do servidor gratuito é apagado a cada deploy.

Em desenvolvimento, sem `CLOUDINARY_URL` as fotos ficam na pasta `media/`.

## Deploy

Push na `main` publica sozinho no Render. Passo a passo da primeira vez, limites do plano
gratuito e problemas comuns em [`docs/deploy.md`](docs/deploy.md).

## Licença

Código publicado como portfólio. Nome, marca e conteúdo da Tay Modas pertencem à loja e não
podem ser reutilizados.
