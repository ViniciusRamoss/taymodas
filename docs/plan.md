# Plano do projeto

## Objetivo

Catálogo online da Tay Modas: as clientes navegam e pedem pelo WhatsApp; a dona gerencia
produtos pelo Django Admin. Custo zero. A arquitetura deve evoluir para um e-commerce
(carrinho, pagamento) sem reescrita.

## Arquitetura

| Camada      | Escolha                                                              |
|-------------|----------------------------------------------------------------------|
| Runtime     | Python 3.12, Django 5.2 LTS, uv                                      |
| Frontend    | Templates Django, Tailwind (`django-tailwind-cli`, sem Node), HTMX   |
| Imagens     | Cloudinary (prod), storage local (dev)                               |
| Config      | `django-environ`, `.env.example`                                     |
| Produção    | gunicorn, whitenoise, Render (web) + Neon (Postgres)                 |
| Qualidade   | ruff, mypy strict, pytest, factory-boy, pre-commit, GitHub Actions   |

### Apps

- `core`: layout, páginas institucionais, `StoreSettings` (singleton editável), healthcheck.
- `catalog`: catálogo e admin.
- Futuro: `cart`, `orders`, `payments`.

### Models (`catalog`)

```
Category       name, slug, position, is_active
Size           name, position                          (reutilizável)
Color          name, hex_code                          (reutilizável)
Product        name, slug, description, price, category, is_active, timestamps
ProductImage   product, image, alt_text, position      (primeira = capa)
ProductVariant product, size, color, stock             único por (product, size, color)
```

### Camadas

`selectors.py` (leituras otimizadas) → `services.py` (regras, ex.: URL do WhatsApp) → views finas.

## Etapas

| #  | Etapa                | Entrega                                                       |
|----|----------------------|---------------------------------------------------------------|
| 0  | Plano                | Este documento                                                |
| 1  | Scaffold             | Projeto, settings, qualidade, CI, healthcheck                 |
| 2  | Models do catálogo   | Models, migrations, factories, testes                         |
| 3  | Admin PT-BR          | Inlines de foto/variante, thumbnails, filtros, StoreSettings  |
| 4  | Layout + listagem    | Tailwind, paleta preto/dourado, lista mobile-first            |
| 5  | Detalhe + WhatsApp   | Galeria, seleção de variante via HTMX, botão de pedido        |
| 6  | Filtros HTMX         | Categoria/tamanho/cor sem reload, URL compartilhável          |
| 7  | Acabamento           | Open Graph, 404/500, acessibilidade, imagens otimizadas       |
| 8  | Deploy               | Produção + `docs/deploy.md`                                   |
| 9  | Portfólio            | README final, screenshots, guia do admin                      |

## Decisões

| Tema               | Decisão                                       | Status                |
|--------------------|-----------------------------------------------|-----------------------|
| WhatsApp           | Número e mensagem em `StoreSettings`          | Aguardando número     |
| Categorias         | Model no admin + seed via data migration      | Aguardando lista      |
| Esgotado           | Exibir com selo "Esgotado"                    | Padrão recomendado    |
| Baixa de estoque   | Manual no admin                               | Padrão recomendado    |
| Hospedagem         | Render free + Neon free + Cloudinary free     | Padrão recomendado    |
| Domínio            | Subdomínio grátis do Render                   | Padrão recomendado    |
| Entrega            | Página "Entrega" + rodapé, texto editável     | Aguardando textos     |

### Limites de free tier (verificados em 2026-10)

- Render web free: hiberna após 15 min sem tráfego, ~1 min para acordar; 750 h/mês por
  workspace; disco efêmero.
- Render Postgres free: expira 30 dias após a criação (14 dias de carência) e 1 GB. Por isso
  usamos o Neon.
- PythonAnywhere free: internet de saída só por allowlist (descartado).
- A verificar na Etapa 8: cotas do Neon e do Cloudinary, shell/one-off jobs no Render free.

## Evolução

1. Hoje: `build_whatsapp_order_url(variant)`.
2. `cart`: carrinho em sessão, itens apontando para `ProductVariant`.
3. `orders`: `Order`/`OrderItem` com preço congelado; baixa de estoque com `select_for_update`.
4. `payments`: interface `PaymentGateway` (Pix/Mercado Pago ou similar).
