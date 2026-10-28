---
name: Tay Modas
description: Boutique de bairro que atende pelo WhatsApp; creme e pétala, títulos em Bodoni, ação em ameixa.
colors:
  creme: "#fbf7f3"
  petala: "#f6e8ec"
  petala-forte: "#f0dbe2"
  linha: "#eedfe4"
  branco: "#ffffff"
  tinta: "#2f242b"
  malva: "#75666f"
  rosa: "#a34f73"
  rosa-escuro: "#813557"
  ameixa: "#3b2833"
  ouro: "#dab871"
typography:
  display:
    fontFamily: "Bodoni Moda, Didot, Bodoni 72, Georgia, serif"
    fontSize: "clamp(2.4rem, 9vw, 4.4rem)"
    fontWeight: 400
    lineHeight: 1.02
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Bodoni Moda, Didot, Bodoni 72, Georgia, serif"
    fontSize: "2rem"
    fontWeight: 400
    lineHeight: 1.25
  title:
    fontFamily: "Bodoni Moda, Didot, Bodoni 72, Georgia, serif"
    fontSize: "1.6rem"
    fontWeight: 400
    lineHeight: 1.25
  card-title:
    fontFamily: "Bodoni Moda, Didot, Bodoni 72, Georgia, serif"
    fontSize: "1.05rem"
    fontWeight: 400
    lineHeight: 1.375
  body-lead:
    fontFamily: "Jost, Futura, system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 400
    lineHeight: 1.625
  body:
    fontFamily: "Jost, Futura, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.625
  label:
    fontFamily: "Jost, Futura, system-ui, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
  tag:
    fontFamily: "Jost, Futura, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    letterSpacing: "0.025em"
rounded:
  foto: "16px"
  painel: "24px"
  pilula: "9999px"
spacing:
  gutter: "16px"
  painel-sm: "24px"
  painel-lg: "32px"
  secao: "56px"
  container: "72rem"
components:
  button-primary:
    backgroundColor: "{colors.ameixa}"
    textColor: "{colors.branco}"
    rounded: "{rounded.pilula}"
    padding: "0 24px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.rosa-escuro}"
  button-light:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.ameixa}"
    rounded: "{rounded.pilula}"
    padding: "0 24px"
    height: "48px"
  button-light-hover:
    backgroundColor: "{colors.petala}"
  order-button:
    backgroundColor: "{colors.ameixa}"
    textColor: "{colors.branco}"
    rounded: "{rounded.pilula}"
    padding: "0 24px"
    height: "56px"
    width: "100%"
  order-button-hover:
    backgroundColor: "{colors.rosa-escuro}"
  pill:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    typography: "{typography.label}"
    rounded: "{rounded.pilula}"
    padding: "0 16px"
    height: "44px"
  pill-current:
    backgroundColor: "{colors.ameixa}"
    textColor: "{colors.branco}"
  choice:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.pilula}"
    height: "44px"
  choice-selected:
    backgroundColor: "{colors.ameixa}"
    textColor: "{colors.branco}"
  choice-out:
    textColor: "{colors.malva}"
  photo-tag:
    backgroundColor: "{colors.ameixa}"
    textColor: "{colors.branco}"
    typography: "{typography.tag}"
    rounded: "{rounded.pilula}"
    padding: "4px 12px"
  photo-tag-new:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.rosa-escuro}"
  filter-select:
    backgroundColor: "{colors.branco}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.pilula}"
    padding: "0 16px"
    height: "44px"
  panel:
    backgroundColor: "{colors.branco}"
    rounded: "{rounded.painel}"
    padding: "{spacing.painel-sm}"
  panel-petala:
    backgroundColor: "{colors.petala}"
    rounded: "{rounded.painel}"
    padding: "{spacing.painel-sm}"
  band-ameixa:
    backgroundColor: "{colors.ameixa}"
    textColor: "{colors.branco}"
    rounded: "{rounded.painel}"
    padding: "36px 24px"
  product-photo:
    backgroundColor: "{colors.petala}"
    rounded: "{rounded.foto}"
  nav-link:
    textColor: "{colors.malva}"
    typography: "{typography.label}"
    height: "44px"
  nav-link-current:
    textColor: "{colors.tinta}"
---

# Design System: Tay Modas

<!-- Registrado a partir do código entregue (assets/css/source.css, templates/, apps/*/templates/) em 2026-10-27. Base vinculante: templates/taymodas_entregas.html, enviado pela dona. -->

## Overview

**Creative North Star: "A Boutique de Bairro"**

O site é uma loja pequena de moda feminina que atende pessoalmente, pelo WhatsApp. O mundo visual vem do template da dona: fundo creme quente, campos pétala, títulos em serifa de alto contraste e painéis bem arredondados. A cor que age é a ameixa, quase preta e levemente rosada. Ela marca a ação, o item escolhido e as faixas escuras que fecham as páginas. O rosa é acento: traço no menu, ícones, números de passo, preço. O dourado só aparece no logo e, como texto, apenas sobre ameixa.

A densidade é baixa e o celular vem primeiro. A página é uma coluna de largura contida (72rem). Dentro dela, blocos tonais arredondados se empilham: pétala, branco e ameixa sobre o creme. Não há sombras; a profundidade vem da troca de tom. As peças são as protagonistas: a foto em 3:4 com cantos de 16px é o maior elemento de cada card, e a interface em volta é texto pequeno e calmo.

O movimento é quase nenhum: o título de cada página sobe ao carregar, os botões mudam de cor e as fotos aproximam levemente no hover. Com movimento reduzido, nada se anima.

**Key Characteristics:**
- Fundo creme, campos pétala e painéis brancos; ameixa para ação e fechamento.
- Bodoni Moda nos títulos, Jost no texto; peso 400 na serifa, 500 só para ênfase em Jost.
- Três raios: 16px (fotos), 24px (painéis e faixas), pílula (botões, filtros, opções, selos).
- Plano: nenhuma sombra; profundidade por camadas tonais.
- Ícones SVG de traço 1.5 em `currentColor`, quase sempre em rosa.
- Alvos de toque de 44px no mínimo; o botão de pedido tem 56px.

## Colors

Paleta quente de baixa saturação: creme e rosados claros no fundo, uma ameixa escura para agir, um rosa médio como acento e o dourado reservado ao logo.

### Primary
- **Ameixa** (`ameixa`): cor de ação. Fundo de todo botão principal, do botão "Pedir pelo WhatsApp", da pílula atual, da opção escolhida, do selo "Esgotado", do rodapé e das faixas escuras de fechamento ("Como combinar sua entrega", "Ficou com alguma dúvida?").
- **Rosa-escuro** (`rosa-escuro`): hover dos botões em ameixa, preço da peça, links de texto sublinhados, texto do selo "Novidade" e da faixa do Instagram.

### Secondary
- **Rosa** (`rosa`): acento. Traço de 2px sob o item atual do menu, borda de hover em pílulas, opções e no cartão de entrega, ícones, números dos passos em "Como comprar", contorno de foco e seleção de texto. Também marca o aviso "escolha uma" no formulário de pedido.

### Tertiary
- **Ouro** (`ouro`): cor do logo. Como texto, aparece só sobre ameixa (links do rodapé) e como contorno de foco dentro de `.on-dark`.

### Neutral
- **Creme** (`creme`): fundo da página, do cabeçalho e da barra de categorias fixa (a 95%). Também é o `theme-color`.
- **Pétala** (`petala`): campo do hero do catálogo, painel de mototáxi, lista de passos, fundo das fotos enquanto carregam e do mapa.
- **Pétala forte** (`petala-forte`): faixa do Instagram no topo, divisores dentro de campos pétala, barra de rolagem.
- **Linha** (`linha`): bordas de 1px de pílulas, opções, selects e do cartão de entrega; divisor dentro de painéis brancos.
- **Branco** (`branco`): painéis, pílulas, opções, selects, selo "Novidade", botão claro sobre ameixa.
- **Tinta** (`tinta`): todo o texto principal. Parágrafos de apoio usam tinta a 80%.
- **Malva** (`malva`): texto secundário. Menu em repouso, tamanhos no card, migalhas, paginação, dicas sob o botão de pedido, preço e opções esgotadas.

### Named Rules
**The Gold-on-Plum Rule.** O dourado vira texto só sobre ameixa. Sobre creme, pétala ou branco, ele aparece apenas no logo.

**The Plum Acts Rule.** Ameixa marca o que age ou o que foi escolhido: botão, pílula atual, opção marcada, faixa de fechamento. Rosa nunca preenche um botão.

## Typography

**Display Font:** Bodoni Moda (com Didot, Bodoni 72, Georgia, serif)
**Body Font:** Jost (com Futura, system-ui, sans-serif)

**Character:** A Bodoni ecoa o "TAY" do logo: alto contraste, sempre em peso 400 e com tracking levemente negativo nos tamanhos grandes. A Jost geométrica fica quieta ao lado e só sobe para 500 em ênfase.

### Hierarchy
- **Display** (`display`): título de abertura de cada página ("Peças novas toda semana", "Seu look favorito, até você"). Hero do catálogo vai até 4.4rem; entregas e como comprar usam `clamp(2.4rem, 8vw, 4.2rem)` com line-height 1.04 e largura de 14 a 16ch. Sempre com a entrada `rise`.
- **Headline** (`headline`): títulos de seção ("Onde fica a loja", "Sobre a Tay Modas") e o `h1` da listagem filtrada. Nas faixas ameixa, sobe para `clamp(1.9rem, 5vw, 2.6rem)`. O nome da peça usa 2rem no celular e 2.6rem a partir de `md`.
- **Title** (`title`): títulos dentro de painéis e passos. Na prática varia entre 1.5rem e 1.85rem conforme o bloco.
- **Card title** (`card-title`): nome da peça no card, até duas linhas.
- **Body lead** (`body-lead`): parágrafo de abertura sob o display, em tinta a 80%, até 44 a 52ch.
- **Body** (`body`): texto corrido, line-height relaxed, até 56ch ou `max-w-prose`.
- **Label** (`label`): menu, pílulas, legendas de campo, linhas de detalhe em painéis. Texto auxiliar menor usa 0.875rem.
- **Tag** (`tag`): selos sobre a foto.

### Named Rules
**The Serif Speaks, Sans Serves Rule.** Todo título e o nome de cada peça vão em Bodoni Moda; preço, botões, menu e formulários vão em Jost.

**The Regular Bodoni Rule.** A Bodoni fica em peso 400. Ênfase vem do tamanho, nunca do negrito.

## Layout

Uma coluna central com largura máxima de 72rem (`max-w-6xl`) e respiro lateral de 16px. Pontos de quebra do Tailwind: `sm` 640px, `md` 768px, `lg` 1024px.

- **Cabeçalho:** no celular, logo centrado com o menu embaixo; a partir de `sm`, logo à esquerda e menu à direita numa faixa de 112px. Acima dele fica a faixa do Instagram em pétala forte.
- **Catálogo:** grade de 2 colunas no celular, 3 em `sm` e 4 em `lg`. Espaço horizontal de 12px a 20px e vertical de 40px entre cards. As pílulas de categoria rolam na horizontal, sem barra visível, e ficam fixas no topo sobre creme a 95%.
- **Hero do catálogo:** campo pétala arredondado; em `lg`, divide em 1.3fr e 1fr, com a peça mais nova à direita em 4:5.
- **Peça:** em `md`, 12 colunas: 7 para as fotos (grade de 2) e 5 para as informações, que ficam fixas ao rolar. No celular, as fotos viram um carrossel com scroll-snap, cada uma com 88% da largura para mostrar a próxima na borda.
- **Páginas de conteúdo:** abertura com display e botão, depois blocos de painel com 16px entre si, seções separadas por 56px, e a página fecha com uma faixa ameixa. O rodapé ameixa fica 80px abaixo do conteúdo.
- **Ritmo:** escala de 4px do Tailwind. Painéis usam 24px de padding, ou 32px a partir de `sm`.

## Elevation & Depth

O sistema é plano. Nenhum elemento entregue usa `box-shadow`. A profundidade vem de camadas tonais: creme ao fundo, pétala para campos, branco para painéis e controles, ameixa para o que fecha a página. A única sobreposição é o rótulo branco a 95% sobre a foto do hero e o selo sobre as fotos.

### Named Rules
**The Tonal Layer Rule.** Para separar um bloco, troque o tom do fundo (creme, pétala, branco, ameixa) ou use uma borda `linha` de 1px. A superfície fica plana em repouso; o template tinha uma sombra quase invisível nos cards (alfa 0.045) que o site não adotou.

## Shapes

Três raios e nenhum canto vivo em superfícies:

- **Pílula** (`pilula`): botões, pílulas de categoria e cidade, opções de tamanho e cor, selects de filtro, selos.
- **Painel** (`painel`, 24px): painéis de conteúdo, campo do hero, lista de passos, mapa, faixas ameixa, estado vazio.
- **Foto** (`foto`, 16px): fotos de peça, o rótulo sobre a foto do hero e o cartão de entrega na página da peça.

Bordas são de 1px em `linha`; dentro de campos pétala, o divisor é `petala-forte`. Amostras de cor são círculos de 14px a 16px com anel preto a 20%. As fotos usam proporção 3:4 (4:5 no hero).

## Components

### Buttons
Cheios, arredondados e calmos. Todo botão leva ao próximo passo, quase sempre o WhatsApp.
- **Shape:** pílula (`pilula`).
- **Primary (`button-primary`):** ameixa com texto branco em Jost 500, 48px de altura mínima, 24px de padding lateral, 10px entre ícone e texto.
- **Hover / Focus:** fundo passa para rosa-escuro em 200ms; ao pressionar, desce 1px. O foco é um contorno rosa de 2px com 2px de afastamento.
- **Light (`button-light`):** branco com texto ameixa, usado só sobre as faixas ameixa; o hover vai para pétala e o foco vira dourado.
- **Order button (`order-button`):** variante de largura total, 56px de altura e texto de 1.05rem, com o ícone de conversa. É a ação final da página da peça.

### Chips
- **Pílula (`pill`):** fundo branco, borda `linha`, texto tinta em 0.95rem, 44px de altura mínima. Navega por categoria ou lista cidades atendidas. Como link, a borda vira rosa no hover; a atual fica ameixa com texto branco.
- **Opção (`choice`):** rádio escondido (`peer sr-only`) seguido de uma pílula de 44px. Marcada fica ameixa com texto branco. Esgotada fica sem fundo, em malva e riscada, e fica desabilitada. O foco do rádio aparece como contorno rosa na pílula. Opções de cor levam uma amostra circular.
- **Selo (`photo-tag`):** pílula pequena no canto superior esquerdo da foto. "Esgotado" vai em ameixa; "Novidade" vai em branco com texto rosa-escuro.

### Cards / Containers
- **Card de peça:** sem caixa. Foto 3:4 em `foto` sobre pétala, depois nome em Bodoni, preço em Jost 500, tamanhos em malva e amostras de cor. O link cobre o card inteiro. No hover, a foto aproxima 3% em 500ms e o nome ganha sublinhado rosa. Esgotado: foto em cinza a 55% de opacidade e preço em malva.
- **Painel (`panel`):** branco ou pétala, raio `painel`, padding de 24px (32px a partir de `sm`), ícone de 36px em rosa no topo e linha de detalhe separada por borda no pé.
- **Faixa ameixa (`band-ameixa`):** bloco de fechamento das páginas de conteúdo. Título em Bodoni branco, texto em branco a 80% e botão claro.
- **Shadow Strategy:** nenhuma; ver Elevation & Depth.

### Inputs / Fields
- **Select de filtro (`filter-select`):** pílula branca de 44px com borda `linha`, texto de 1rem e legenda em 0.875rem acima. Muda a lista por HTMX ao trocar o valor; sem JS, aparece um botão "Filtrar".
- **Focus:** contorno global rosa de 2px com afastamento de 2px.

### Navigation
- **Menu principal (`nav-link`):** três links em Jost 0.95rem, malva em repouso e tinta no hover. O item atual fica em tinta com sublinhado rosa de 2px, afastado 0.6em do texto. Cada link tem 44px de altura.
- **Migalhas:** 0.875rem em malva com barra "/" como separador.
- **Paginação:** "Peças anteriores" como link de texto, contador em malva e "Ver mais peças" como botão principal.

### Ícones
Conjunto próprio em SVG de 24px, traço de 1.5, pontas arredondadas, cor `currentColor`: `box`, `moto`, `pin`, `chat`, `hanger`, `ruler`, `arrow-out`. São usados em rosa nos painéis e em branco dentro dos botões.

### Logo
Logo dourado oficial em PNG (`static/img/logo.png`), com 64px a 80px de altura no cabeçalho e 96px a 112px no rodapé. **Pendência da dona:** o arquivo atual foi recortado de um JPEG de 500px; falta o original em alta resolução ou vetor.

## Do's and Don'ts

### Do:
- **Do** terminar cada página com uma ação que leva ao WhatsApp, num botão ameixa em pílula.
- **Do** usar Bodoni Moda em peso 400 para títulos e nomes de peça, e Jost para todo o resto.
- **Do** separar blocos por troca de tom (creme, pétala, branco, ameixa) e raio de 24px.
- **Do** manter fotos em 3:4 com raio de 16px e fundo pétala enquanto carregam.
- **Do** garantir 44px de alvo de toque em links, pílulas, opções e selects.
- **Do** usar ícones do conjunto `partials/icon.html` (traço 1.5) e acrescentar novos no mesmo traço.
- **Do** limitar a animação de entrada ao título e ao parágrafo de abertura (`rise`, `rise-late`), sempre dentro de `prefers-reduced-motion: no-preference`.

### Don't:
- **Don't** usar o dourado como texto ou detalhe sobre fundo claro; ele só aparece como texto sobre ameixa.
- **Don't** preencher botões de rosa; a ação é ameixa e o hover é rosa-escuro.
- **Don't** usar sombras duras, deslocadas ou escuras; a separação é tonal.
- **Don't** pôr sobretítulos em caixa alta acima dos títulos nem usar símbolos de texto ou emoji como ícone.
- **Don't** usar fotos de banco ou inventadas como se fossem da loja.
