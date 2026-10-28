---
version: 1
slug: "templates-base-html"
primary_target: "templates/base.html"
related_targets: ["apps/core/templates/core/delivery.html","apps/core/templates/core/how_to_buy.html","apps/catalog/templates/catalog/product_list.html","apps/catalog/templates/catalog/product_detail.html"]
---

# Site público Tay Modas (catálogo, peça, entregas, como comprar)

Scope: páginas públicas `/`, `/p/<slug>/`, `/entregas/`, `/como-comprar/`. Mode: Persuade (catálogo/entregas) com tarefa de Operate na página da peça (escolher variação e pedir).

Audience: mulheres de 18 a 45 anos vindas do Instagram, no celular. Action: abrir o WhatsApp com o pedido pronto. Constraints: template `templates/taymodas_entregas.html` é vinculante (paleta rosa/creme, títulos em serifa, painéis arredondados); logo dourado oficial; sem fotos reais ainda (não inventar).

## Direction contract

THESIS: uma boutique de bairro que atende pelo WhatsApp; toda página termina na conversa. Recusa o marketplace genérico de banners e carrosséis.
OWN-WORLD: fundo creme #fbf7f3 do template, campos pétala #f6e8ec, ação em ameixa #3b2833 com hover rosa-escuro, rosa #a34f73 como acento; logo dourado #dab871; Bodoni Moda (eco do "TAY" do logo) + Jost; painéis 24px, pílulas, fotos 16px; ícones SVG de traço 1.5.
STORY: vê que chega peça nova toda semana, escolhe tamanho e cor com estoque, entende como recebe (mototáxi ou correio), pede no WhatsApp.
FIRST VIEWPORT: faixa do Instagram, logo SVG + menu (Peças, Entregas, Como comprar), faixa pétala curta com "Peças novas toda semana" e a frase de apoio; logo abaixo título, categorias e filtros, e a primeira foto grande do lookbook (a peça mais nova).
FORM: Lookbook do feed (2ª do ranking de 7; sorteio de superfície entregou Provador, Lookbook e Etiqueta; a usuária escolheu o Lookbook), com as cores do template. Celular: uma peça por tela, foto de ponta a ponta com etiqueta de nome, preço e "Pedir". Desktop: mosaico em blocos de 3 (uma foto 2x2 e duas pequenas, alternando lado). seed:96c79ae95dbf87f2
FINISH: unreviewed and undocumented is unfinished; ship only after the finish reviewer returns ship.
