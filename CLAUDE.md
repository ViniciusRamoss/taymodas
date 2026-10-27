# CLAUDE.md — Tay Modas

Catálogo online da Tay Modas (moda feminina, Serrana-SP). Clientes navegam e pedem via
WhatsApp; a dona da loja (não técnica) gerencia produtos pelo Django Admin.

## Stack

- Python 3.12, Django 5.2 LTS, gerenciado com `uv` (`[tool.uv] package = false`)
- Templates Django + Tailwind via `django-tailwind-cli` (sem Node) + HTMX servido localmente
- Imagens: `apps.core.storage.CloudinaryMediaStorage` (storage próprio sobre o SDK oficial
  `cloudinary`; `django-cloudinary-storage` está sem manutenção desde 2020). Ativado por
  `CLOUDINARY_URL` (obrigatória em prod). Dev: `media/` local. Testes: `InMemoryStorage`.
  URLs redimensionadas via `apps.core.images.image_url(file, width)`.
- Config via env (`django-environ`), `.env.example` documenta tudo
- Produção: gunicorn + whitenoise; alvo Render (web) + Neon (Postgres) + Cloudinary, custo zero
- Qualidade: ruff (lint + format), mypy strict + django-stubs, pytest + pytest-django +
  factory-boy, pre-commit, GitHub Actions

## Comandos

```bash
uv sync                                  # instalar deps
uv run python manage.py runserver        # dev (settings: config.settings.dev)
uv run pytest                            # testes + coverage
uv run ruff check . && uv run ruff format --check .
uv run mypy .
uv run pre-commit run --all-files
uv run python manage.py tailwind build     # gera static/css/tailwind.css (fora do git)
uv run python manage.py tailwind runserver # dev com watch do CSS
uv run python manage.py seed_demo          # produtos fictícios "Demo" (só com DEBUG)
```

## Estrutura

- `config/settings/{base,dev,test,prod}.py`: `manage.py` usa dev; `wsgi`/`asgi` usam prod;
  pytest e mypy usam test.
- `apps/<app>/`: código de domínio. Cada app tem `tests/` próprio.
  - `core`: layout, páginas institucionais, `StoreSettings` (singleton), healthcheck.
  - `catalog` (Etapa 2+): Category, Size, Color, Product, ProductImage, ProductVariant.
- `templates/`: `base.html` e `partials/` (wordmark, footer). Templates de app ficam em
  `apps/<app>/templates/<app>/`, parciais em `partials/`.
- `assets/css/source.css`: fonte do Tailwind v4 (tokens em `@theme`). Fica fora de
  `static/` de propósito (W001 do django-tailwind-cli / manifest storage).
- `static/js/htmx.min.js`: HTMX 2.0.4 vendorizado. `static/css/tailwind.css` é gerado.
- `docs/`: `plan.md` (plano e decisões), `deploy.md` (Etapa 8).

## Convenções

- Código e identificadores em inglês; textos visíveis (labels, help_text, templates) em PT-BR.
- Views finas. Leituras em `selectors.py`, regras de negócio em `services.py` (funções puras
  e tipadas sempre que possível).
- Type hints em tudo (mypy strict). Testes com pytest-style, factories via factory-boy.
- Factories tipadas (`DjangoModelFactory[Model]`); nos testes use `XFactory.create()` /
  `.build()` (não `XFactory()`), assim o mypy enxerga o tipo do model.
- Anotações de queryset (ex.: `total_stock`) não são vistas pelo django-stubs; quando
  necessário, use `# type: ignore[attr-defined]` pontual e comentado.
- Slugs gerados por `apps.core.text.unique_slugify` no `save()`; não mudam se o nome mudar.
- `on_delete`: Category/Size/Color usam PROTECT (não apaga o que está em uso); fotos e
  variantes usam CASCADE com o produto.
- Warnings viram erro no pytest (`filterwarnings = ["error"]`).
- Commits: Conventional Commits (`feat(catalog): ...`, `fix:`, `docs:`, `chore:`, `test:`).
- Nunca inventar dados da loja (telefone, preços, políticas, categorias). Use
  `[PLACEHOLDER]` e pergunte.
- Dependências sempre via `uv add` / `uv add --dev`.
- Frontend: usar skills de design (frontend-design / impeccable) nas etapas de UI.
  Mobile-first (~375px), paleta baseada no logo: fundo preto, "TAY modas" em dourado.

## Design (Etapa 4)

- Tokens: `preto #000`, `ouro #c8a24a` (só sobre preto), `ouro-escuro #7a5b12` (dourado
  sobre branco), `tinta #2b2b2b`, `cinza #6b6b6b`, `nevoa #f2f2f0` (fundo de foto).
  O dourado é provisório até chegar o arquivo do logo.
- Tipos: Bodoni Moda (wordmark, nomes de peça, títulos) + Jost (texto). Google Fonts.
- Única ousadia: hero preto com wordmark "TAY *modas*" em `clamp(3.25rem,17vw,9rem)`
  (17vw é o máximo sem scroll horizontal em 375/393px). Resto quieto: grade 2→3→4
  colunas, foto 3:4 sem raio, sem cards com sombra. Selos "Novidade"/"Esgotado" = faixa
  preta + texto dourado (`.photo-tag`), derivados de dados reais.
- Evitar: eyebrows em caixa alta, middle dots, setas em botões, palavra única destacada.
- View usa `selectors.catalog_products()` + `presenters.ProductCard` (sem lógica no
  template). Número de queries da listagem não cresce com os produtos (teste cobre).

## Página do produto (Etapa 5)

- URL `/p/<slug>/` (`catalog:product_detail`). Escolha na querystring `?cor=<pk>&tamanho=<pk>`:
  form GET que funciona sem JS; com HTMX (`hx-trigger="change"`) a view devolve só
  `partials/order_form.html` e a URL é atualizada (`hx-replace-url`). Restore de histórico do
  HTMX recebe a página inteira. Resposta tem `Vary: HX-Request`.
- `services.select_variant()` resolve a escolha (opções esgotadas riscadas; opção única já vem
  escolhida). `services.build_whatsapp_order_url()` monta o `wa.me`; mensagem com chaves
  inválidas cai na padrão; sem número cadastrado devolve `None` e o botão some.
- Estilos `.choice`, `.choice-out`, `.swatch` em `source.css` (layer components; utilitários no
  template sobrescrevem, então cor do anel fica no CSS).

## Decisões

- `django_stubs_ext.monkeypatch()` em `base.py` permite `admin.ModelAdmin[Model]` em runtime.
- Prod falha na inicialização sem `DATABASE_URL` ou `CLOUDINARY_URL` (disco efêmero).
- `total_stock` via `Subquery` (não `Sum` com join), para não inflar com filtros de variante.
  Para filtrar por estoque use `Product.objects.in_stock()` / `.sold_out()` (`Exists`).
- Fotos: arquivo é apagado do storage ao apagar/trocar a foto (signals, `on_commit`).
  Upload limitado a 10 MB e reduzido para no máximo 2000px no Cloudinary.
- Admin: grupos escondidos; `StoreSettings` abre direto no formulário (sem add/delete);
  ações em massa mostrar/esconder; estoque editável na lista "Variações".

- `ProductVariant` (tamanho + cor + estoque) é a unidade vendável; carrinho e pedidos
  futuros referenciam ela.
- Estoque baixado **manualmente** no admin (o pedido fecha no WhatsApp; um clique não é venda).
- Itens esgotados: **exibidos com selo "Esgotado"** (padrão recomendado, aguardando confirmação).
- Número do WhatsApp, mensagem padrão e texto de entrega ficam em `StoreSettings`
  (editável no admin), não em env.
- Render Postgres free expira em 30 dias, por isso o banco de produção é o Neon.
- HSTS preload desligado (subdomínio compartilhado); `security.W021` silenciado em prod.
- Futuro: apps `cart` → `orders` → `payments`, sem reescrever `catalog`.

## Pendências com o dono do projeto

- Número do WhatsApp da loja e texto da mensagem padrão (no banco de dev há um número
  provisório, pessoal do dono do projeto; trocar no admin antes do deploy)
- Lista final de categorias e tamanhos
- Confirmação: esgotado exibido vs. escondido
- Textos de entrega (cidades do mototáxi, envio nacional, prazos, retirada)

## Etapas

0. Plano ✅ · 1. Scaffold ✅ · 2. Models ✅ · 3. Admin PT-BR ✅ · 4. Layout + listagem ✅ ·
5. Detalhe + WhatsApp ✅ · 6. Filtros HTMX · 7. Acabamento · 8. Deploy · 9. Portfólio
