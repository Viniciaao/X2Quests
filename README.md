# X2Quests

Missões customizadas (Parallel Quests) para **Dragon Ball Xenoverse 2** no
formato **X2QS**, mais as ferramentas para validar e empacotar essas missões.

## Ferramentas

As ferramentas precisam só de Python 3.8+ (sem dependências externas).

### 1. Gerar a base de referência

Só é preciso fazer isso de novo se você atualizar o corpus. O `.rar` precisa de
um `unrar` (ou `unar`) para extrair.

```bash
unrar x "Vanilla quests.rar" /tmp/van/

python3 tools/gen_reference.py \
    --corpus  "/tmp/van/Vanilla quests/Quest" \
    --dialogue "/tmp/van/Vanilla quests/Dialogue" \
    -o tools/x2qs_reference.json
```

### 2. Validar uma quest

```bash
python3 tools/x2qs_lint.py quests/TMQ_URA_01
```

O linter confere sintaxe, tipos de objeto e campos, **nome e aridade** de cada
`Action`/`Condition`, se toda referência (QmlChar, Dialogue, Flag, TextEntry)
foi declarada, códigos de personagem/skill/estágio, se as posições existem no
mapa do estágio escolhido, `battle_index` e o `start_stage` dos jogadores.

Ele é calibrado contra o próprio jogo: as **1160 quests vanilla passam sem
nenhum erro**, então um erro apontado na sua missão é erro de verdade.

### 3. Empacotar

```bash
python3 tools/build_x2m.py quests/TMQ_URA_01 \
    --name "Nao Coma o Uranio! (TMQ_URA_01)" --author "Voce" --version 1.0 \
    -o "dist/Nao Coma o Uranio.x2m"
```

O build roda o linter antes e se recusa a empacotar com erro (`--force` ignora).

## Instalação no jogo

Requer [Eternity Tools / XV2 Mods Installer](https://videogamemods.com/xenoverse/mods/eternity-tools-1031725)
e o jogo já preparado com o xv2patcher.

## Missões prontas

| ID | Nome | Palco(s) | Ideia |
| --- | --- | --- | --- |
| `TMQ_URA_01` | Não coma o urânio! | `BFrrg` | [docs/IDEIA_MISSAO.md](docs/IDEIA_MISSAO.md) |
| `TMQ_JUN_01` | 1 bilhão de Junins | `BFtol` | [docs/IDEIA_1BILHAO_DE_JUNINS.md](docs/IDEIA_1BILHAO_DE_JUNINS.md) |
| `TMQ_JUS_01` | Devolva minha beer! | `BFkoh` → `BFsky` → `BFspe` | [docs/IDEIA_DEVOLVA_MINHA_BEER.md](docs/IDEIA_DEVOLVA_MINHA_BEER.md) |

## Criando a sua própria missão

1. Copie `quests/TMQ_URA_01` para `quests/TMQ_SEU_ID` e troque o id do objeto
   `Quest` (precisa começar com `TMQ_` para Parallel Quest, ou `HLQ_` para
   Expert Mission, e não pode colidir com uma quest vanilla — o linter avisa).
2. Edite `quest.x2qs` (metadados/recompensas), `chars.x2qs` (elenco),
   `dialogue.x2qs` (textos), `positions.x2qs` (pontos de partida) e
   `script.x2qs`/`script1.x2qs` (lógica).
3. Rode `python3 tools/x2qs_lint.py quests/TMQ_SEU_ID` até zerar os erros.
4. Empacote com `tools/build_x2m.py`.
