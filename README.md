# Tay Modas

Catálogo online de moda com seleção de peças, sacola de compras e pedidos pelo WhatsApp. Desenvolvido em Python com Django, permite administrar produtos, fotos, preços, promoções e estoque por tamanho e cor.

## Funcionalidades

- Catálogo com filtros por categoria, tamanho, cor e promoções.
- Página de produto com fotos e seleção de variações disponíveis.
- Estoque individual por combinação de tamanho e cor.
- Sacola com alteração de quantidades, subtotais e valor total.
- Mensagem de pedido pelo WhatsApp com produtos, quantidades, tamanhos, cores, valores e links.
- Preços promocionais com data de término opcional.
- Identificação de novidades e produtos esgotados.
- Painel administrativo para gerenciar o catálogo e as informações da loja.
- Armazenamento de imagens local ou no Cloudinary.
- Sitemap para auxiliar a indexação do catálogo.

O fechamento da compra acontece pelo WhatsApp. Após uma venda, o estoque deve ser atualizado no painel administrativo.

## Tecnologias

| Área | Tecnologias |
| --- | --- |
| Backend | Python 3.12 e Django 5.2 |
| Interface | Django Templates, Tailwind CSS e HTMX |
| Banco de dados | SQLite no desenvolvimento e PostgreSQL em produção |
| Imagens | Pillow e Cloudinary |
| Publicação | Gunicorn, WhiteNoise e configuração para Render |
| Qualidade | Pytest, pytest-django, coverage, Ruff e Mypy |
| Integração contínua | GitHub Actions |

O Tailwind utiliza um binário standalone, sem necessidade de Node.js.

## Executando localmente

### Pré-requisitos

- Python 3.12.
- Gerenciador de dependências `uv`.
- Git.

### 1. Clone o repositório

```bash
git clone https://github.com/ViniciusRamoss/taymodas.git
cd taymodas
```

### 2. Instale as dependências

```bash
uv sync --locked
```

### 3. Configure o ambiente

Copie `.env.example` para `.env`.

**Windows — PowerShell:**

```powershell
Copy-Item .env.example .env
```

**Linux ou macOS:**

```bash
cp .env.example .env
```

Gere uma chave para o Django:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copie o resultado para `DJANGO_SECRET_KEY` no arquivo `.env`.

| Variável | Finalidade |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave secreta da aplicação |
| `DJANGO_DEBUG` | Ativa o modo de desenvolvimento |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por vírgulas |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origens confiáveis para requisições protegidas por CSRF |
| `DJANGO_ADMIN_URL` | Caminho do painel administrativo, com `/` ao final |
| `DJANGO_LOG_LEVEL` | Nível dos registros da aplicação |
| `DATABASE_URL` | Conexão com o banco; vazio utiliza SQLite local |
| `CLOUDINARY_URL` | Credenciais do Cloudinary; vazio salva as imagens em `media/` no desenvolvimento |

Não publique o arquivo `.env` nem credenciais no repositório.

### 4. Prepare o banco e o painel

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

### 5. Gere o CSS e inicie o servidor

```bash
uv run python manage.py tailwind build
uv run python manage.py runserver
```

Acesse:

- **Catálogo:** http://127.0.0.1:8000/
- **Painel:** http://127.0.0.1:8000/admin/

Se você alterar `DJANGO_ADMIN_URL`, utilize o caminho configurado para acessar o painel.

## Configuração inicial da loja

No painel administrativo:

1. Preencha as **Configurações da loja**, incluindo o WhatsApp com código do país e DDD, a mensagem do pedido e as informações de entrega.
2. Cadastre as categorias.
3. Cadastre os tamanhos e as cores.
4. Adicione os produtos com preço, fotos e variações.
5. Informe o estoque de cada combinação de tamanho e cor.

Enquanto o número do WhatsApp estiver vazio, a sacola e os botões de pedido não aparecem no site.

A mensagem do pedido pode utilizar:

- `{itens}`: relação das peças e suas informações.
- `{total}`: valor total da sacola.

Consulte o [guia do painel](docs/guia-admin.md) para instruções sobre cadastro, promoções e manutenção do estoque.

## Dados de demonstração

Para criar produtos fictícios durante o desenvolvimento:

```bash
uv run python manage.py seed_demo --count 10
```

O comando funciona somente com `DEBUG=True` e cria produtos na categoria **Demo**, com imagens e variações fictícias. Cada execução adiciona novos produtos.

## Estrutura do projeto

```text
taymodas/
├── apps/
│   ├── cart/             # Sacola e mensagem de pedido
│   ├── catalog/          # Produtos, categorias, variações e estoque
│   └── core/             # Configurações da loja e recursos compartilhados
├── assets/css/           # CSS de origem do Tailwind
├── bin/                  # Scripts de build e inicialização
├── config/
│   └── settings/         # Configurações de desenvolvimento, testes e produção
├── docs/                 # Guias de administração e deploy
├── static/               # Arquivos estáticos
├── templates/            # Templates compartilhados
├── .env.example          # Modelo de configuração do ambiente
├── manage.py
├── pyproject.toml
├── render.yaml           # Configuração de publicação no Render
└── uv.lock
```

## Testes e qualidade

Execute os testes com relatório de cobertura:

```bash
uv run pytest
```

Verifique o código e a formatação:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

Confira se existem alterações de modelos sem migrações:

```bash
uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test
```

O GitHub Actions executa verificações de código, formatação, tipagem, migrações pendentes, configuração de produção e testes em pushes para `main` e em pull requests.

## Publicação

O repositório inclui configuração para:

- **Render:** hospedagem da aplicação.
- **PostgreSQL/Neon:** banco de dados.
- **Cloudinary:** armazenamento das fotos.

O processo de publicação utiliza:

- `bin/build.sh`: instalação das dependências, geração do CSS e coleta dos arquivos estáticos.
- `bin/start.sh`: aplicação das migrações, criação inicial do administrador quando configurada e inicialização do Gunicorn.

Em produção, configure `DATABASE_URL`, `CLOUDINARY_URL`, a chave secreta e os hosts permitidos. O ambiente de produção exige banco e armazenamento de imagens externos para preservar os dados entre publicações.

Veja o passo a passo no [guia de deploy](docs/deploy.md).

## Autor

Desenvolvido por [Vinicius Silva Ramos](https://github.com/ViniciusRamoss).
