# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Clientes:** mulheres de 18 a 45 anos que chegam pelo Instagram (@taymodas23), quase sempre
  no celular. Veem uma novidade no story ou no feed, abrem o site para conferir tamanhos, cores e
  preço, e fazem o pedido pelo WhatsApp.
- **Dona da loja:** cadastra peças, fotos e estoque pelo painel (Django Admin), sem
  conhecimento técnico. Recebe e conclui cada pedido no WhatsApp.

## Product Purpose

Catálogo online da Tay Modas, loja de moda feminina em Serrana-SP. O site mostra o que está
disponível agora, por tamanho e cor, e leva a cliente ao WhatsApp com a mensagem do pedido já
preenchida. Sucesso: a cliente encontra a peça, escolhe a variação com estoque e abre a conversa
sem precisar perguntar "tem no meu tamanho?".

## Positioning

- Peças novas toda semana, em poucas unidades.
- Atendimento pessoal: a própria dona atende cada cliente no WhatsApp.
- Preço acessível.

## Operating Context

- Pedido e pagamento acontecem no WhatsApp; o site não tem carrinho nem checkout (pode ganhar
  no futuro).
- Entrega para todo o Brasil (frete pelo CEP) e por mototáxi em Ribeirão Preto e região
  (Ribeirão Preto, Serrana, Serra Azul, Cravinhos, Cajuru, Jardinópolis). Valor e prazo do
  mototáxi são combinados no WhatsApp.
- Loja física em Serrana-SP; o endereço é cadastrado no painel.

## Capabilities and Constraints

- Django 5.2 + templates + HTMX + Tailwind v4; tudo funciona sem JavaScript.
- Hospedagem gratuita (Render, Neon, Cloudinary): páginas leves, fotos servidas no tamanho
  da tela, sem dependências pesadas.
- Textos da loja (WhatsApp, mensagem do pedido, entrega, endereço) vêm do painel; nunca
  ficam fixos no código.
- Estoque por variação (tamanho + cor); esgotados aparecem com selo.

## Brand Commitments

- Nome: Tay Modas. Instagram @taymodas23.
- Logo oficial: "TAY" em serifa de alto contraste com "modas" em letra cursiva, em dourado
  sobre fundo claro (`media/Logo.jpeg`, 500×500, raster de baixa resolução; pedir o arquivo
  original em alta ou vetor).
- Template de referência enviado pela dona do projeto: `templates/taymodas_entregas.html`
  (paleta rosa e creme, títulos em serifa, conteúdo da página de entregas). Vinculante como
  base visual e de conteúdo.
- Voz: próxima e calorosa, em português do Brasil, falando direto com a cliente ("você").

## Evidence on Hand

- Logo (raster) e o conteúdo de entregas do template.
- Ainda não há fotos reais de peças, da loja ou de clientes. Não inventar depoimentos,
  números de vendas, avaliações nem fotos apresentadas como da loja.

## Product Principles

1. O caminho até o WhatsApp é curto: escolher tamanho e cor nunca exige mais de um toque cada.
2. O celular vem primeiro: tudo é desenhado para o polegar e para conexão lenta.
3. A dona controla o conteúdo pelo painel; o site nunca exige programador para mudar texto.
4. As peças são as protagonistas; a interface fica em volta delas.

## Accessibility & Inclusion

WCAG 2.2 AA: contraste, foco visível, alvos de toque de 44px, funcionamento sem JavaScript e
com movimento reduzido.
