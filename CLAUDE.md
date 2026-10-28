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
- `docs/`: `plan.md` (plano e decisões), `deploy.md` (passo a passo de produção).
- `render.yaml` + `bin/build.sh` / `bin/start.sh`: deploy no Render (Blueprint). Admin criado
  por `manage.py ensure_admin` a partir de `DJANGO_ADMIN_USERNAME/PASSWORD/EMAIL`.

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
  Mobile-first (~375px). Base visual: `templates/taymodas_entregas.html` (template da dona do
  projeto, vinculante) + logo oficial. Contexto de produto em `PRODUCT.md`.

## Design (redesign rosa)

- Tokens (`assets/css/source.css`): `creme #fbf7f3` (fundo), `petala #f6e8ec` (campos e fundo
  de foto), `linha #eedfe4`, `tinta #2f242b`, `malva #75666f` (secundário), `rosa #a34f73`
  (acento), `rosa-escuro #813557`, `ameixa #3b2833` (botões, rodapé, faixas de ação),
  `ouro #d5ba7e` (cor do logo; como texto, só sobre `ameixa`).
- Logo: `static/img/logo.svg` (vetor da dona; `logo.png` é a versão raster). Partial
  `partials/wordmark.html` (`size="small|large"`). Favicon `static/img/favicon.svg`.
- Tipos: Bodoni Moda (títulos, nomes de peça; ecoa o "TAY" do logo) + Jost (texto).
- Formas: painéis `rounded-3xl` (`.panel`), pílulas (`.pill`, `.choice`, `.button`), fotos
  `rounded-2xl`. Ícones SVG próprios em `partials/icon.html` (traço 1.5), nunca emoji.
- Movimento: só `.rise`/`.rise-late` no título de cada página e zoom leve na foto ao passar o
  mouse; respeita `prefers-reduced-motion`.
- Evitar: eyebrows/rótulos em caixa alta, palavra única destacada no título, emoji, setas em
  texto, sombras. Contornos de 1px (`border-linha`) só em pílulas e controles.
- Menu: `nav_current` no contexto (`catalogo`, `entregas`, `como-comprar`) marca a aba.
- Listagem = lookbook (direção escolhida no sorteio do Impeccable): no celular uma peça por
  tela, foto de ponta a ponta com etiqueta (nome, preço, tamanhos, "Pedir"); no desktop o
  mosaico `.lookbook` (CSS fora de `@layer`, em `source.css`) põe uma foto 2x2 e duas pequenas
  por bloco, alternando o lado. Hero da home (`partials/list_header.html`, id `titulo-inicio`)
  é uma faixa curta.
- View usa `selectors.catalog_products()` + `presenters.ProductCard` (sem lógica no
  template). Número de queries da listagem não cresce com os produtos (teste cobre).

## Peças reais (import_store_photos)

- `manage.py import_store_photos <pasta> [--sizes P,M,G] [--stock 1]`: cadastra as 9 peças das
  fotos da dona (lista explícita no comando: nome, categoria, cor, preço vindos do nome do
  arquivo; cor descrita da foto quando o arquivo não diz). Idempotente (pula pelo nome).
  Com storage local referencia o arquivo dentro de `MEDIA_ROOT`; com Cloudinary, faz upload.
- Fotos em `media/products/2026/10/` (fora do git). Para produção: rodar localmente com
  `DATABASE_URL`/`CLOUDINARY_URL` de produção, ou cadastrar pelo painel.

## Entregas e Como comprar

- `apps/core/views.py`: `DeliveryView` (`/entregas/`) e `HowToBuyView` (`/como-comprar/`),
  templates em `apps/core/templates/core/`. Estão no sitemap.
- Dados do admin (`StoreSettings`): `store_address` (mapa + rodapé), `mototaxi_cities` (uma
  por linha), `delivery_info` (prazos e detalhes), `about_text` (trecho "Sobre", some se vazio).
- Mapa: iframe do Google Maps sem chave (`map_embed_url`, `loading="lazy"`) + botão
  `map_link_url` (URL oficial `maps/search/?api=1`). Sem endereço, a seção some.
- `StoreSettings.whatsapp_url(text)` monta o `wa.me` (usado também pelo pedido da peça).

## Página do produto (Etapa 5)

- URL `/p/<slug>/` (`catalog:product_detail`). Escolha na querystring `?cor=<pk>&tamanho=<pk>`:
  form GET que funciona sem JS; com HTMX (`hx-trigger="change"`) a view devolve só
  `partials/order_form.html` e a URL é atualizada (`hx-replace-url`). Restore de histórico do
  HTMX recebe a página inteira. Resposta tem `Vary: HX-Request`.
- `services.select_variant()` resolve a escolha (opções esgotadas riscadas; opção única já vem
  escolhida).
- Botão "Adicionar à sacola" (só se a loja tem número): POST na própria URL da peça
  (`formmethod="post"` + `hx-post`; o GET do HTMX tira o token com `hx-params`). Completa: entra
  na sacola; HTMX recebe o form com "Peça na sacola." + `#contador-sacola` fora de banda; sem JS,
  302 para `?cor&tamanho&adicionado=1`. Incompleta: destaca o grupo pendente com `autofocus`.

## Sacola (`apps/cart`)

- `Cart` (`cart.py`): `session["sacola"] = {"<variant_id>": qtd}`, sempre limitada ao estoque.
- `services.py`: `cart_variants()` (só produtos visíveis), `build_lines()`, `cart_total()`,
  `build_whatsapp_cart_url()` com `{itens}`/`{total}` (`StoreSettings.order_message_template`;
  chaves inválidas caem na padrão; sem número ou sem peça disponível devolve `None`).
- `/sacola/` (`cart:detail`, noindex, fora do robots): linhas com −/+/Remover (POST
  `cart:update`, `quantidade=0` remove), Esvaziar (`cart:clear`), PRG + `hx-boost`. Peças que
  saíram do site ou esgotaram aparecem uma vez e são tiradas da sessão.
- Contador no topo: `partials/cart_link.html` + context processor `apps.cart.context_processors.cart`.
- Migration core 0003 troca mensagens antigas (`{produto}`...) pela padrão da sacola.
- Estilos `.choice`, `.choice-out`, `.swatch`, `.order-button` em `source.css` (layer components; utilitários no
  template sobrescrevem, então cor do anel fica no CSS).

## Filtros da listagem (Etapa 6)

- Querystring `?categoria=<slug>&tamanho=<pk>&cor=<pk>`; a mesma URL serve a página inteira e
  o HTMX, então funciona sem JS e é compartilhável. Ids fora das opções são ignorados.
- Tamanho + cor precisam bater na **mesma variante com estoque**; com filtro ativo, esgotados
  somem (`selectors.catalog_products`). Opções vêm de `selectors.filter_options(category)`.
- `presenters.CatalogFilters` guarda opções, escolha, `clear_url` e `query_prefix` (paginação).
- HTMX: `#catalogo` é trocado inteiro (categorias com `hx-boost`, form com `hx-trigger="change"`
  e `hx-push-url`). A resposta (`partials/catalog_htmx.html`) traz `<title>` e o `#topo`
  (hero ou cabeçalho) via `hx-swap-oob`. Hero só na lista sem categoria, sem filtro, página 1;
  fora dela o título da lista vira `<h1>`.
- Comentário multilinha em template Django é `{% comment %}`; `{# #}` só vale numa linha.

## Acabamento (Etapa 7)

- Metadados no `base.html` vêm do contexto: `meta_title`, `meta_description` (cortada em 160),
  `meta_image`, `og_type`, `canonical_url` (padrão do context processor `core.seo`, sem
  querystring). Lista com categoria: canônico `/?categoria=<slug>`. Produto: `og:type=product`,
  foto de capa em 1200px como `og:image` e `product:price:*` no bloco `extra_meta`.
- Não usar `{% block title %}`/`description`: defina as variáveis na view.
- `404.html` usa o layout; `500.html` é autossuficiente (sem request, banco nem `base.html`).
- `/robots.txt` (bloqueia URLs com filtro/página; não cita o admin) e `/sitemap.xml`
  (`apps/catalog/sitemaps.py`: início, categorias com produto, produtos visíveis).
- Favicon provisório em `static/img/favicon.svg` (trocar pelo logo).
- Card usa `heading` (h2/h3) conforme o título da lista, para a ordem de títulos não pular nível.
  Verificado com axe-core (wcag2a/aa + best-practice) em lista, filtro, produto e 404.

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
- Tamanhos e estoque reais das 9 peças importadas (entraram com P, M, G e estoque 1)
- Imagem de compartilhamento da home (hoje sem `og:image`)
- Textos de entrega (cidades do mototáxi, envio nacional, prazos, retirada)
- Screenshots do README: tirar depois do novo layout e com fotos reais de produção
  (as fotos lisas do `seed_demo` não servem para portfólio)

## Etapas

0. Plano ✅ · 1. Scaffold ✅ · 2. Models ✅ · 3. Admin PT-BR ✅ · 4. Layout + listagem ✅ ·
5. Detalhe + WhatsApp ✅ · 6. Filtros HTMX ✅ · 7. Acabamento ✅ · 8. Deploy ✅ (taymodas.onrender.com) · 9. Portfólio ✅
(README + `docs/guia-admin.md`; screenshots pendentes)
