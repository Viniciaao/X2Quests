# X2Quests

Missões customizadas (Parallel Quests) para **Dragon Ball Xenoverse 2** no
formato **X2QS**, mais as ferramentas para validar e empacotar essas missões.

## Conteúdo do repositório

| Caminho | O que é |
| --- | --- |
| `quests/TMQ_URA_01/` | **"NÃO COMA O URÂNIO!"** — Parallel Quest em 6 arquivos `.x2qs` |
| `quests/TMQ_JUN_01/` | **"1 BILHÃO DE JUNINS"** — horda de 76 Junins + chefe em 2 fases, em 5 arquivos `.x2qs` |
| `dist/` | as duas missões já empacotadas, prontas para o XV2 Mods Installer |
| `docs/IDEIA_MISSAO.md` | ficha de `TMQ_URA_01`: roteiro, elenco, falas, recompensas, instalação |
| `docs/IDEIA_1BILHAO_DE_JUNINS.md` | ficha de `TMQ_JUN_01`: horda, mods referenciados, chefe em 2 fases |
| `tools/gen_junin_quest.py` | gerador da `TMQ_JUN_01` (76 `QmlChar` + eventos — mexa nas constantes e rode de novo) |
| `tools/gen_reference.py` | extrai a base de referência (actions, conditions, personagens, estágios, skills…) dos quests vanilla |
| `tools/x2qs_reference.json` | a base gerada — é o que o linter consulta |
| `tools/x2qs_lint.py` | valida uma pasta de quest X2QS contra essa base |
| `tools/build_x2m.py` | empacota a pasta num `.x2m` instalável |
| `Vanilla quests.rar` | os 1160 quests vanilla descompilados (corpus de referência) |
| `ginyu mujeres edicion.x2m` | mod de exemplo, usado como referência de formato |

## As missões

**`TMQ_URA_01` — "NÃO COMA O URÂNIO!"**
Uma gangue tomou o Pátio do Exército Red Ribbon e só fala de duas coisas: que
você **não deve comer urânio** e do **tamanho do seu "equipamento"**. Três ondas
de inimigos bocudos, um Hercule como "Grande Moderador" e um final alternativo
para quem terminar em menos de 5 minutos. Textos em pt/en/es.
Detalhes em [`docs/IDEIA_MISSAO.md`](docs/IDEIA_MISSAO.md).

**`TMQ_JUN_01` — "1 BILHÃO DE JUNINS"**
Setenta e seis Junins invadem o Espaço-tempo Distorcido sem aviso e sem cutscene:
caiu a dupla, entra outra. Placar de 76 no canto da tela e, no fim, o Junin do
Futuro em duas fases (Shinya → Agent Coat). Usa os mods `[OC] Junin`,
`[OC] Junin EMO` e `[OC] Junin do Futuro` por referência `X2mMod`, com o skillset
original de cada um.
Detalhes em [`docs/IDEIA_1BILHAO_DE_JUNINS.md`](docs/IDEIA_1BILHAO_DE_JUNINS.md).

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

* **Rápido:** instale `dist/Nao Coma o Uranio.x2m` pelo XV2 Mods Installer e
  reinicie o jogo.
* **Oficial:** abra `quests/TMQ_URA_01` no XV2 Quest Creator (aba *Files* →
  *quest directory*) e salve o `.x2m` por lá.

## Criando a sua própria missão

1. Copie `quests/TMQ_URA_01` para `quests/TMQ_SEU_ID` e troque o id do objeto
   `Quest` (precisa começar com `TMQ_` para Parallel Quest, ou `HLQ_` para
   Expert Mission, e não pode colidir com uma quest vanilla — o linter avisa).
2. Edite `quest.x2qs` (metadados/recompensas), `chars.x2qs` (elenco),
   `dialogue.x2qs` (textos), `positions.x2qs` (pontos de partida) e
   `script.x2qs`/`script1.x2qs` (lógica).
3. Rode `python3 tools/x2qs_lint.py quests/TMQ_SEU_ID` até zerar os erros.
4. Empacote com `tools/build_x2m.py`.
