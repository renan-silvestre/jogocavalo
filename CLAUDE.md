# Jogo de corrida de cavalos (threads e semáforos)

Trabalho de faculdade (Projeto N2, disciplina de Sistemas Operacionais): um jogo simples em Python que use threads e semáforos. Apresentação em sala em 03/12/2026.

## Requisitos da professora
- Obrigatório usar threads e semáforos. Ela também pediu que o jogo mostre **concorrência e sincronização**.
- O foco é Sistemas Operacionais: interface gráfica e imagens **não** são o principal.
- O jogo precisa estar funcionando na apresentação (computador próprio ou nuvem).
- Apresentação:
  - "Venda" do jogo (pitch) com slides, com entusiasmo.
  - Tema, objetivo e funcionamento do jogo.
  - Explicação detalhada do código: bibliotecas usadas, implementação das threads e uso dos semáforos.

## Stack
- Python + pygame (pymunk só se der tempo, ver "Física").
- Sprites feitos no LibreSprite.

## Visual
- Inspirado no Horsey Game (Steam): 2D chapado, cores fortes, pixel art simples, fonte pixelada (Press Start 2P ou Silkscreen), cavalos com nomes.
- Resolução interna 480x270, ampliada sem suavização (SCALE = 3, janela 1440x810).
- Mockup feito no LibreSprite em 480x270: céu, arquibancada com plateia colorida, 5 faixas, linha de chegada, cerca embaixo.
- O cavalo é feito de peças separadas, cada uma girada pelo código:
  - Sprites PNG (têm detalhe): corpo com pano/número, cabeça.
  - Formas simples (pescoço, pernas, rabo) podem ser polígonos desenhados direto no código.
  - Peças são desenhadas retas no editor; o ângulo é sempre do código.
- O Horsey Game amplia as peças antes de girar, por isso as bordas giradas são lisas. A renderização ainda vai precisar ser ajustada pra isso quando as peças começarem a girar.

## Threads e semáforos
- Cada cavalo é uma thread (daemon=True).
- Largada: semáforo começando em 0 segura todos os cavalos até o "VAI!" liberar todos.
- Pódio: semáforo com valor 1 protege a lista de colocações.
- Gargalo: trecho estreito da pista com semáforo de valor 2 (só 2 cavalos passam por vez). Mostrar na tela, tipo "GARGALO 2/2", com os cavalos esperando na fila.
- Só a thread principal desenha. As threads dos cavalos só atualizam o estado compartilhado.

## Física
- Plano B primeiro (base do jogo): pernas girando com seno, tropeços aleatórios (girar o sprite e pausar a thread um tempo).
- Plano A opcional, só se sobrar tempo: física estilo QWOP com pymunk (PivotJoint + SimpleMotor). A física roda no loop principal e as threads só decidem os comandos.

## Ideias pra depois (só se sobrar tempo, depois dos semáforos)
Cavalos gerados aleatoriamente, diferentes a cada corrida (tudo sorteado no `__init__`, nunca a cada frame):
- Nome: juntar palavras sorteadas de duas listas.
- Cor: desenhar as peças em tons de cinza e pintar uma cópia com `fill(cor, special_flags=pygame.BLEND_RGB_MULT)`.
- Formato: várias versões de cada peça (ex.: 3 cabeças, 3 corpos) sorteadas com `random.choice`, cada uma com o próprio ponto de encaixe.
- Proporção: esticar sprites com `pygame.transform.scale` (pescoço comprido, corpo gordo), sem exagerar.
- Manchas: sprites de mancha sorteados por cima do corpo.

## Escopo
Uma tela de corrida, uma aposta simples antes da largada e o pódio. Sem coleção, cruzamento ou loja.

## Estado atual
- `main.py`: o jogo principal, em desenvolvimento.
  - Pronto: 5 cavalos, cada um numa thread; largada (semáforo 0, ESPAÇO libera); pódio (semáforo 1, falta mostrar na tela); câmera seguindo o cavalo 1; linha de chegada xadrez.
  - Falta: gargalo (semáforo 2), pódio na tela, aposta antes da largada.
- `full_game.py`: versão completa de referência, feita com o Claude. Serve de "gabarito" pro visual.