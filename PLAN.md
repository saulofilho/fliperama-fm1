# FLIPERAMA — plano do firmware

O M-VAVE FM-1 vira um **salão de fliperama de bairro**. Cada máquina do salão é um **chip de som** com o seu
próprio **jogo inventado** na tela. A diferença: você não joga o jogo, **a música joga**. Cada nota que o
sequenciador toca é um pulo, um chute, um fogo de artifício. Você compõe a batida e o jogo acontece sozinho, como o
modo de demonstração das máquinas antigas, que roda até alguém pôr uma ficha.

Seis máquinas para a 1.0:

| Máquina | Chip (inspirado em) | Jogo na tela | O som mexe em |
| --- | --- | --- | --- |
| PULSO | 2 pulsos + triângulo + ruído, estilo console 8 bits | CORREDOR: corre pelos telhados ao entardecer | nota = pulo, altura = afinação, moeda a cada nota |
| ONDA | canal de onda de 4 bits (32 amostras), estilo portátil | SURFE: a onda do mar **é** a forma de onda | o desenho da onda vem da tabela; o volume levanta o mar |
| RUÍDO | ruído LFSR (longo e curto) + pulso 12,5 % | PÊNALTI: bumbo chuta, caixa faz o goleiro pular | bumbo, caixa e chimbal são o lance; placar de gols |
| FM | FM de 2 a 4 operadores, estilo 16 bits | PIPA: pipa sobre as lajes do morro | nota = altura da pipa, grave = rajada de vento |
| PWM | pulso com largura variável + filtro ressonante, estilo computador 8 bits | PISTA: dançarino num salão de baile | a largura do pulso é a largura do canhão de luz |
| ARPEJO | arpejos rápidos de acorde (pulso 25 %) | RÉVEILLON: fogos sobre o mar | acorde = rojão, cada nota do arpejo = faísca da cor da nota |

Firmware livre, GPL-3.0-only. Sem rede.

**Mood board:** [`docs/moodboard/index.html`](docs/moodboard/index.html). Abra no navegador e ponha uma ficha: o
som e as seis cenas funcionam. Linguagem visual: **salão de fliperama de bairro dos anos 90**, com placa pintada à
mão, ficha de metal, gabinete de compensado e tela de tubo.

Criado em 2026-11-26. Pasta: `projetos-git/fliperama-fm1`.

## A decidir antes da Fase 0

| Código | O quê | Proposta |
| --- | --- | --- |
| D1 | Base | **JAZZY** (GPL-3.0, `github.com/JazzyRhythmer/Jazzy`): já tem 31 cenas em pixel art reagindo ao som, o caminho do evento de nota até a tela e o site com galeria. Alternativa: o **Felucca** (a plataforma de baixo do JAZZY), mais limpo, mas sem o motor de cenas. Ver o aviso de licença abaixo |
| D2 | Nome | **FLIPERAMA** (livre no Hub em 2026-11-26). Alternativas: FICHA, SALÃO, CRÉDITO |
| D3 | Identidade | **`FM-1_939`** (livre no catálogo em 2026-11-26; 937, 938, 940, 943, 946 e 947 já são de outros) |
| D4 | Tela | 240×240 do FM-1, com a arte desenhada a **120×120 e dobrada** (pixel 2×2), como pixel art de verdade |
| D5 | Idioma da tela | EN nos nomes curtos (cabe melhor) ou PT? Proposta: **PT** (PLACAR, FICHA, GOL), que é a identidade do projeto |
| D6 | Jogos | Todos **inventados**: personagem, fase e regra. Nenhum personagem, fase, som ou visual de jogo real |

### A base, depois da Fase 0 (2026-11-26)

- **Compila.** `upstream/JAZZY-0.1.0-beta.1-source.tar.gz` foi extraído em `upstream/Jazzy-0.1.0-beta.1/` e
  `./build.sh` roda no Mac com o toolchain da JieLi (`~/.jieli/toolchain`, num container amd64) e o SDK AC79 do
  `fm1-rede/sdk` (tag `AC79NN_SDK_V1.2.1_2023-12-13`). Venv com Pillow e fontTools em `upstream/.venv`. Log em
  `upstream/build.log`.
- **Reprodutível.** O pacote tem o mesmo tamanho do release oficial (909.949 B, `FM-1_900`). Só 16 bytes diferem,
  todos em campos de checksum e cabeçalho: `cmp` aponta 5 regiões de 2 a 4 bytes.
- **Não sobra espaço.** O app ocupa **584.324 de 584.336 B (12 B livres)**, RAM `.data+.bss` 96.936 de 98.304 B.
  O FLIPERAMA só cabe **tirando** coisas: os presets LXR, o HYDRA, o S1 e a maior parte das 31 engines.
- **De onde vem o código.** Felucca (Leo Kuroshita) → JIANT FM (Juan Jiant) → Rhythmer → JAZZY. O `LICENSING.md`
  da raiz é o do X0X, outro fork do Felucca, copiado junto. Tudo é GPL-3.0-only, com partes MPL-2.0 (Saadet/HYDRA,
  leitor de tela) e Apache-2.0 (msfa no FM6), todas compatíveis. Um fork fica GPL-3.0-only e mantém os avisos.
- **Não levar** os 595 presets LXR: o próprio JAZZY diz que não tem direito de redistribuir.
- **Como as cenas funcionam.** Não são sprites: são desenhos vetoriais (`rhythmer/firmware/src/jazzy_world.c`,
  577 linhas) com linhas, quadriláteros e discos num palco de 240×112, até 480 traços por quadro, na thread da UI.
  Uma struct `jw` recebe o estado do áudio a cada quadro: energia do envelope (`en`), batida com o velocity da nota
  (`hit`), afinação (`pitch`), passo do sequenciador (`step`), número de notas, intervalo do acorde e glide. Cada
  engine aponta para uma cena (`jazzy_object`: FMINI → SKATER, LXR → BALL…). É a mesma regra de ouro do FLIPERAMA,
  já resolvida.
- **Proposta para D1:** fork do JAZZY e corte: ficam a plataforma (HAL, loader, USB, flash, LCD, `gfx`), o
  sequenciador e o `jazzy_world` como base do motor de cena; saem as engines, os presets e as cenas dele. Os chips
  do FLIPERAMA e os seis jogos entram no espaço liberado.
- **Falta (no aparelho, com você):** instalar o `build/felucca.fwsc` no FM-1, voltar ao V15, e medir a CPU com 4
  tracks + cena.
- Sem promoção da base no site e nos READMEs; créditos em `LICENSING.md` e no código (mesma regra do BAILE e do
  RIDDIM).

## Vizinhos

Busca no catálogo do Hub em 2026-11-26 por chiptune, 8-bit, arcade, SID, YM2612, Game Boy:

| Vizinho | O que faz | Onde o FLIPERAMA é diferente |
| --- | --- | --- |
| Chipbox | Editor chiptune com mais de 35 chips | Não competir em quantidade: 6 chips, cada um com o seu jogo |
| KAWA, LSDJ Burrito, FMDj, FM1-TRAX | Trackers (pulso, onda, ruído; Game Boy; Mega Drive) | O FLIPERAMA não é tracker: é groovebox de passos com GEN |
| SID-1, SIDOU, FM-1 SID, SiDJ, OPN-1 | Emulação fiel de um chip, tocar .sid/VGM | Sem fidelidade de emulação nem arquivos de jogos; o chip é só o timbre |
| **INSERT COIN** | Tocador de acordes chiptune com um jogo de nave: cada tecla atira | Lá **você** joga com as teclas. No FLIPERAMA a **música** joga, e são seis jogos, um por chip |
| **Mighty Arcade** | 18 jogos que fazem música enquanto você joga | O sentido é o inverso: lá o jogo gera a música, aqui a música gera o jogo |
| h1 | 16 instrumentos, cada um um quadro animado que você toca | O mais próximo na ideia de "o som e a imagem andam juntos"; o FLIPERAMA tem regra de jogo, placar e o salão |

Frase do Hub: "a neighbourhood arcade where every cabinet is a sound chip and the music plays the game: compose the
beat, watch it jump, score and explode".

## Decisões (propostas)

| Tema | Proposta |
| --- | --- |
| O salão | A tela HOME é o corredor do salão: os seis gabinetes lado a lado. Knob 1 anda pelo corredor, OK entra na máquina. A máquina parada mostra o modo de demonstração, como as máquinas reais |
| Tracks | 4 tracks por projeto: cada uma escolhe uma máquina. A tela mostra o jogo da track selecionada; as outras jogam sozinhas por baixo |
| A regra de ouro | Todo movimento na tela vem de um evento do áudio (nota, accent, envelope, LFO, largura de pulso). Nada anima sozinho fora do modo de demonstração. Teste host que confere isso |
| PLACAR | Cada jogo conta pontos (moedas, gols, fogos). O placar é um medidor de performance: quantas notas, quantos accents, quanto tempo sem parar. "RECORDE" salvo por projeto |
| GEN | Gera linhas no estilo de cada chip: melodia de corredor, linha de baixo de triângulo, virada de bateria de ruído, arpejos de acorde |
| Envelopes | Em degraus de 1/60 s e 16 níveis, como os chips, e não curvas lisas. Faz parte do timbre |
| Teclas | Brancas: tocam o chip da track na escala do projeto. Pretas: FICHA (entra e sai da máquina), PAUSA, TURBO (dobra o tempo da cena e do arpejo), GAME OVER (corta tudo com o som de fim de jogo), CONTINUE |
| Captura para o site | O firmware tem um modo de captura do framebuffer: 40 quadros a 50 ms, em WebP animado de 240×240 (~20 KB), mais um PNG parado. Mesma técnica do site do JAZZY |
| Som | 100 % sintetizado. Nada de sample de jogo, música de jogo ou efeito sonoro de jogo real |
| Gravação | Áudio por USB; REC desliga o alto-falante |
| Repositório | git local; trabalho no `main`; o autor faz push, merge e tags |
| READMEs | PT e EN no mesmo commit de cada melhoria |

## Fases

0. **A base.** Baixar e compilar o JAZZY (ou o Felucca). Instalar no FM-1 e voltar ao V15. Medir a CPU de 4 tracks
   de chip + uma cena 120×120 a 30 fps.
1. **Identidade.** `PRODUCT` `FM-1_939`, `APP_NAME` FLIPERAMA, pacote `fliperama.fwsc`, magics próprios.
   Boot: a porta de ferro do salão sobe, a luz fluorescente pisca e acende, aparece "INSIRA FICHA". `LICENSING.md`,
   READMEs, `fmhub.json`.
2. **O motor de cena.** Camada de tiles e sprites a 120×120 dobrada para 240, paleta por máquina, fonte 3×5 e o
   barramento de eventos do áudio para a cena (nota, accent, passo, envelope, LFO).
3. **Os seis chips.** Pulso (12,5/25/50/75 %), triângulo de 4 bits, onda de 32 amostras, ruído LFSR (longo e curto),
   FM de 2 a 4 operadores e PWM com filtro. Envelope em degraus. Teste host que mede cada timbre.
4. **Os seis jogos.** Uma cena por vez: CORREDOR, SURFE, PÊNALTI, PIPA, PISTA, RÉVEILLON. Cada uma com modo de
   demonstração, placar e o teste da regra de ouro.
5. **O salão e o sequenciador.** HOME do corredor, 4 tracks, sequenciador de passos, GEN por chip, PLACAR e RECORDE,
   teclas pretas.
6. **Web.** Site com o salão (as capturas em WebP, como a galeria do JAZZY), áudio de cada máquina renderizado pelo
   firmware, emulador no navegador, manual e guia em PT e EN.
7. **Release.** `./build.sh --release 1.0`, teste no FM-1 (instalar a partir do V15 e de outro firmware, sair,
   voltar, update interrompido, uma hora tocando), `docs/TEST-RESULTS-1.0.md`, envio ao Hub.

## Riscos

| Risco | O que fazer |
| --- | --- |
| O código do JAZZY não compila ou a origem não fica clara | Partir do Felucca e escrever o motor de cena do zero |
| CPU com 4 chips + cena | Cena a 30 fps (ou 20), só a track da tela desenha; as outras só atualizam o placar |
| Parecer cópia de jogo famoso | Personagens, cenários e regras inventados; conferir cada cena antes da release |
| Parecer "mais um chiptune" no Hub | O argumento é o jogo que a música joga e o salão, não o número de chips |
| Seis jogos é muito para a 1.0 | A 1.0 sai com 4 (CORREDOR, PÊNALTI, PIPA, RÉVEILLON); SURFE e PISTA entram na 1.x |

## Mood

Salão de fliperama de bairro dos anos 90: porta de ferro, luz fluorescente, chão de granilite, gabinetes de
compensado com adesivo na lateral, ficha de metal, placa amarela pintada à mão na fachada e o recorde escrito a
caneta num papel colado na máquina. Na tela: tubo com linhas de varredura, cores fortes e chapadas, pixel grande.
Ver o mood board.

## Andamento

**2026-11-26:** plano e mood board criados.

**2026-11-26, Fase 0 (no Mac):** código do JAZZY 0.1.0-beta.1 baixado e compilado; pacote igual ao release a menos de
16 bytes de checksum. Achados: 12 B livres na flash, a origem de cada parte e o motor de cenas vetorial
(`jazzy_world.c`). Faltam a instalação no FM-1, a volta ao V15 e a medida de CPU no aparelho.
