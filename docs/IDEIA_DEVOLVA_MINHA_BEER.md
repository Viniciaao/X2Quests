# "DEVOLVA MINHA BEER!" — Parallel Quest customizada (TMQ_JUS_01)

Missão paralela para **Dragon Ball Xenoverse 2** (formato X2QS / `.x2m`, para o
**XV2 Quest Creator** + **XV2 Mods Installer** do Eternity Tools).

Fontes em [`quests/TMQ_JUS_01/`](../quests/TMQ_JUS_01) · pacote em
[`dist/Devolva Minha Beer.x2m`](../dist/).

> Os 15 personagens são mods `[OC]` — instale todos (e as skills deles) antes
> da missão. O que ainda não foi testado em jogo está listado na seção 7.

---

## 1. A ideia

Roubaram a última **beer** do **Juse**. Ele é um CAC sério, lv 180, e **não diz
uma palavra** — as únicas "falas" dele na missão inteira são `"....."` e
`"......."`. Mesmo assim ele acompanha o time do começo ao fim.

A perseguição atravessa **três stages** ligados por portais. Em cada um, um
ladrão sozinho espera; quando cai, chegam mais dois. No terceiro stage a missão
termina com o Juse olhando e dizendo `"....."`.

O truque está no **bônus**: se você fechar a missão em **menos de 10 minutos**,
a missão **não** acaba. O Juse sai do time sem falar nada, o jogo fica
**5 segundos em silêncio**, aparece o aviso vermelho na tela com um
`"......."` — e o **Juse volta como inimigo**, lv 180, com vida e defesa
absurdas. Durante essa luta:

* se a vida do jogador cair para **20% ou menos**, entram **Vini Pai** e
  **Vini Jr** como aliados;
* se os dois caírem, entram **Luis (Rykan)** e a **Shinya**.

## 2. Ficha da missão

| Campo | Valor |
| --- | --- |
| ID | `TMQ_JUS_01` |
| Tipo | Parallel Quest, 1 a 3 jogadores |
| Palcos | `BFkoh` → `BFsky` → `BFspe` (os 3 ligados por portal) |
| `start_stage` | `BFkoh` |
| Tempo | 1200 s (20 min) |
| Nível / dificuldade | 140 / 5 |
| Unlock | junto com `TMQ_1400` (Being a Time Patroller) |
| Bônus | terminar em **menos de 10 min** |

### Stages

| # | Código | Nome (Quest Creator) | Inimigos |
| --- | --- | --- | --- |
| 1 | `BFkoh` | Capsule Corporation | Junin Emo + Junin → **Yone + Yasha** |
| 2 | `BFsky` | West City (Industrial Sector) | Ezra → **Ray + Junin do Futuro** |
| 3 | `BFspe` | West City (Suburbs) | Dan Majin Mau → **Zé do Morro + Dimitztri** |
| bônus | `BFspe` | — | **Juse (inimigo)** |

Trocar de mapa é seguro **só** entre pares de stages que o jogo já conecta por
portal. Os únicos comprovados neste repositório são `BFkoh ↔ BFsky ↔ BFspe`
(mod *ginyu mujeres edicion*) e `BFgen ↔ BFkoh` (vanilla `TMQ_4601`). Se trocar,
mude `stages:` / `start_stage:` no `quest.x2qs`, o `stage:` das `QmlChar` e as
`CharPosition` — e refaça o `PortalControl` dos dois sentidos de cada par.

### Recompensas

* `Collection60` (1ª vez) / `Collection70` / `Collection80` — materiais;
* `Mr. Antidote S` (item 20) — a piada interna: "antídoto pra quem bebeu demais";
* `Senzu Bean` (item 12), 60%;
* `Maximum Charge` (skill 593) na primeira conclusão.

## 3. Roteiro / fluxo

```
State 0  init: 6 PortalControl (2 por par), SetThereAreEnemies nos 3 stages,
               SetFlag(FlagFast, true), InitQuest → BattleModeStart → State 1

State 1  BFkoh   onda 1 (nascem com o stage): Junin Emo + Junin
                 os dois caem → CharaSpawn2 Yasha + Yone
                 os dois caem → SetThereAreEnemies(BFkoh, false)  ← portal acende
                 InStage(Player, "BFsky") → State 2

State 2  BFsky   Ezra (nasce com o stage)
                 Ezra cai → CharaSpawn2 JuninFuturo + Ray
                 os dois caem → SetThereAreEnemies(BFsky, false)
                 InStage(Player, "BFspe") → State 3

State 3  BFspe   Dan Majin Mau (nasce com o stage)
                 Dan cai → CharaSpawn2 Dimitztri + Zé do Morro (lv 150)
                 os dois caem → SetThereAreEnemies(BFspe, false)
                                + fala "....."  → State 4

State 4  QuestFinishState(COMPLETE)
                 FlagFast false → QuestClear (fim normal)
                 FlagFast true  → State 5

State 5  CharaLeave(JuseAllyS3) → Wait(5.0) → ShowWarning
         → CharaSpawn(JuseEnemy, fala ".......") → State 6

State 6  PlayerHealth(<=, 20.0) → CharaSpawn2 ViniJr + Vini Pai
         os dois caem          → CharaSpawn2 Shinya + Luis
         JuseEnemy cai         → State 7

State 7  QuestFinishState(ULTIMATE_FINISH) → QuestClear

script1  vigia: TimePassed(>=, 600.0) → SetFlag(FlagFast, false)
```

Detalhes que valem a pena saber:

* **`CharaSpawn2` usa o retrato do 2º char na fala.** Por isso o personagem que
  fala vem sempre em segundo lugar na chamada (comentado no script).
* **`SetThereAreEnemies(stage, false)`** é o que deixa o ícone do portal verde,
  mas não tem efeito enquanto ainda houver inimigo carregado naquele stage — daí
  ela vir sempre depois do último `Ko()`.
* **`ChangeStage` não é usado**: quem atravessa é o jogador, pelo portal. É o
  mesmo esquema do mod *ginyu mujeres edicion*. (Se um dia usar `ChangeStage`
  em Parallel Quest, o fade tem que ser `NONBG`.)
* **Um aliado por stage.** O Juse tem três `QmlChar` (`JuseAllyS1/S2/S3`), uma
  por stage, porque o jogo trata cada stage como cenário próprio — é o mesmo
  truque que o vanilla usa no Goku do `TMQ_3102` (lá com `CopyHealth` pra
  disfarçar; aqui cada instância entra com a vida cheia).

## 4. Elenco

Todos são mods `[OC]`, referenciados por `X2mMod` no `quest.x2qs`. O
identificador do `X2mMod` é o próprio **ENTRY_NAME** do mod, então o mesmo nome
serve de `char:` nos `QxdChar` e de `actor:` nas falas.

| Papel | Nome | Código | Lv | Observação |
| --- | --- | --- | --- | --- |
| Aliado fixo | Juse | `JUS` | 180 | ataque baixo de propósito (atk 0.35, dano 0.25), vida 3000 |
| 1 · onda 1 | Junin Emo | `JUE` | 100 | stats padrão |
| 1 · onda 1 | Junin | `JUN` | 100 | stats padrão |
| 1 · onda 2 | Yone | `S4P` | 120 | costume 0 |
| 1 · onda 2 | Yasha | `YAS` | 120 | **costume 2** (Coat), SkillSet 3 |
| 2 · solo | Ezra Dito | `CU1` | 140 | costume 0 |
| 2 · onda 2 | Ray | `RAY` | 150 | costume 0 |
| 2 · onda 2 | Junin do Futuro | `JUF` | 150 | **costume 1** (Agent Coat) |
| 3 · solo | Dan Majin Mau | `PU2` | 150 | costume 0 (Majin, BODY_SHAPE 2) |
| 3 · onda 2 | Zé do Morro | `ZEM` | 150 | costume 0 |
| 3 · onda 2 | Dimitztri | `BCT` | 150 | costume 0 |
| bônus · chefe | Juse | `JUS` | 180 | `QxdChar JuseBoss`: vida **15000**, dano 1.2, `guard_damage` 1.5 |
| bônus · reforço | Vini Pai | `VIP` | 160 | time A |
| bônus · reforço | Vini Jr | `VJR` | 155 | time A |
| bônus · reforço | Luis (Rykan) | `LUI` | 175 | time A |
| bônus · reforço | Shinya | `NFT` | 170 | time A, esposa do Luis |

### Skills

Cada OC usa o SkillSet do próprio XML que corresponde ao costume pedido, com os
ids traduzidos: `49152 + n` no SkillSet é o `X2mDepends` **`0xC000 + n`** do
mesmo XML. Por exemplo, o `[OC] Juse` tem `49160` no super1 → `0xC008` →
`[JUS Skill]Heading to another planet?`.

Todo mundo usa o **SkillSet 1**, menos os dois que têm costume específico:

* **Junin do Futuro** (costume 1 = Agent Coat) → **SkillSet 2**;
* **Yasha** (costume 2 = Coat) → **SkillSet 3**.

Os `SkillSet` vêm com `CHAR_ID`/`COSTUME_ID` fixos (`0xbacabaca`, `0xbacaca`…),
então a associação é **posicional**: o N-ésimo `SkillSet` do XML é o N-ésimo
`SlotEntry`/costume declarado. Na Yasha os costumes são `0, 1, 2, 4, 5`, logo o
3º SkillSet é o do costume 2. É a mesma regra que faz o costume 1 do Junin do
Futuro bater com a fase Agent Coat do `TMQ_JUN_01`.

São **84 mods de skill** declarados como dependência; o instalador precisa
encontrar todos, então instale os OCs antes da missão.

### Sobre "vida e defesa fortes"

O `QxdChar` do X2QS **não tem multiplicador de dano recebido** — os campos
`atk_damage` / `ki_damage` / `super_*_damage` são o dano que o personagem
**causa**. "Defesa" aqui é feita do jeito que o vanilla faz: **vida enorme**
(o Freeza Dourado do `TMQ_4601` usa `health: 8000.0`; o Juse chefe usa
`15000.0`) mais `guard_damage`. Se quiser um chefe ainda mais esponja, suba o
`health` do `QxdChar JuseBoss`.

## 5. As falas

20 falas em `pt` / `en` / `es`, todas com `voice: ""` (legenda sem dublagem).
Os textos ficam em `dialogue.x2qs` — é só editar lá.

**Regra dura: o Juse nunca fala.** As três falas dele são `"....."`,
`"....."` e `"......."` (a do bônus). Todos os outros personagens falam:
Junin Emo, Junin, o jogador, Yone, Yasha, Ezra, Ray, Junin do Futuro, Dan,
Zé do Morro, Dimitztri, Vini Pai, Vini Jr, Luis e Shinya.

O `actor:` de cada fala usa o ENTRY_NAME do mod (ex.: `actor: "JUS"`). O
retrato só aparece se o mod daquele personagem estiver instalado — que é
exatamente o que a dependência `X2mMod` garante.

## 6. Como instalar

### Caminho A — pacote pronto

`dist/Devolva Minha Beer.x2m` no **XV2 Mods Installer**. Para reempacotar:

```bash
python3 tools/build_x2m.py quests/TMQ_JUS_01 \
    --name "Devolva Minha Beer! (TMQ_JUS_01)" --author "Voce" --version 1.0 \
    -o "dist/Devolva Minha Beer.x2m"
```

### Caminho B — pelo Quest Creator

Abra a pasta `quests/TMQ_JUS_01` no **XV2 Quest Creator** e salve por lá. É o
caminho oficial e o único que recompila de verdade os `.x2qs`.

Ordem de instalação: **primeiro os 15 mods de personagem e as skills deles**,
depois a missão.

### Validação

```bash
python3 tools/x2qs_lint.py quests/TMQ_JUS_01
# [lint] TMQ_JUS_01: OK - 6 arquivos, 204 identificadores,
#         114 Action/Condition validados, 9 aviso(s)
```

Os 9 avisos são esperados:

* 4× `spawn_at_start: true` num stage que não é o `start_stage` — é de
  propósito, são os personagens que já estão lá quando o jogador chega pelo
  portal (o linter só avisa, não é erro);
* 4× `battle_index` compartilhado — índices se repetem entre stages e entre
  ondas que nunca estão em campo ao mesmo tempo (o mod *ginyu* faz igual);
* 1× skill `1553` (super2 do Ezra, vem do XML dele) não aparece no corpus
  vanilla escaneado — fica entre `1552` e `1554`, que existem.

## 7. O que não foi verificado em jogo

Aqui só roda o linter — nada foi testado dentro do DBXV2.

1. **`PlayerHealth(<=, 20.0)`** — assume "vida do jogador em % ". Está no
   `x2qs_reference.json` com aridade 2, mas nenhuma quest do corpus usa, então
   a semântica não foi confirmada. Se no jogo não disparar, o substituto é
   `Condition Health(<=, Player, 20.0)` (mesmo formato usado nos inimigos).
2. **`actor: "JUS"` com mod** — retrato de personagem de mod na legenda. A ação
   `PlayDialogue` é das mais usadas do corpus (66 ocorrências), mas nenhuma
   quest vanilla referencia um char de mod no `actor`. Se o retrato não
   aparecer, há dois fallbacks: `PlayDialogue2(dlg, 1000, stage, -1, QmlChar)`
   (força o retrato por `QmlChar`; documentada, mas não aparece no corpus) ou
   passar a fala pelo parâmetro `dialogue` do `CharaSpawn`/`CharaSpawn2`, que é
   o que a missão já faz nas entradas de onda.
3. **`CharaLeave` num aliado** seguido de `Wait(5.0)` no mesmo Event — o
   tutorial avisa que o jogo pode ignorar um segundo `Wait` por Event; aqui é
   só um, mas a cena do `CharaLeave` + `Wait` na sequência não foi testada.
   Se cortar o silêncio, separe em dois Events.
4. **`Ko(char, false, -1)`** — é o idioma vanilla pra "caiu, avança a missão"
   (`Ko(GokuSSGSSEnemy, false, -1)` → `QuestFinishState(COMPLETE)` no
   `TMQ_4303`, e as duas outras missões deste repositório usam igual). O corpus
   também tem `Ko(char, true, -1)` pro **mesmo** personagem no mesmo script, e
   o segundo parâmetro não é documentado em lugar nenhum — se uma onda não
   avançar, é o primeiro lugar pra olhar.
5. **SkillSet ↔ costume** — a associação posicional da seção 4 é inferência.
   Se no jogo a Yasha de Coat vier com as skills erradas, troque o bloco de
   skills do `QxdChar Yasha` pelo SkillSet 1 (`49156, 49153, 49154, 49159,
   49155, 49160, 10130, 21081, 65535`).
6. **Recompensas** — valores chutados pro nível 140; nada de `CharReward` do
   Juse porque recompensar personagem de mod não foi testado.

**Decisões já confirmadas pelo autor**

Os três maps (`BFkoh` → `BFsky` → `BFspe`), o gatilho dos reforços
(`PlayerHealth(<=, 20.0)` = vida do jogador em 20% ou menos) e as recompensas
da ficha foram confirmados como estão. Nível 140, `health: 15000.0` do chefe e
o texto das falas continuam livres pra ajustar.
