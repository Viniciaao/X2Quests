# "DEVOLVA MINHA BEER!" — Parallel Quest customizada (TMQ_JUS_01)

Missão paralela para **Dragon Ball Xenoverse 2** (formato X2QS / `.x2m`, para o
**XV2 Quest Creator** + **XV2 Mods Installer** do Eternity Tools).

Fontes em [`quests/TMQ_JUS_01/`](../quests/TMQ_JUS_01) · pacote em
[`dist/Devolva Minha Beer.x2m`](../dist/).

> Os 15 personagens são mods `[OC]` — instale todos (e as skills deles) antes
> da missão. O que ainda não foi testado em jogo está listado na seção 7.

---

## 1. A ideia

Roubaram a **beer** do **Juse** e ele saiu caçando quem foi. Ele é um CAC
sério, lv 180, e **não diz uma palavra** — as únicas "falas" dele na missão
inteira são `"....."` e `"......."`. Ele só aponta e vai atrás, e o time vai
junto.

A perseguição atravessa **três stages** ligados por portais. Em cada um, um
ladrão sozinho espera; quando cai, chegam mais dois — e cada um jura que não
foi ele. No terceiro stage a missão termina com o Juse olhando e dizendo
`"....."`.

**Regra dura: se o Juse aliado cair em qualquer momento, a missão falha.** Ele
é o dono da beer; sem ele não tem missão.

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
| Derrota | o time todo cai, o tempo acaba, **ou o Juse aliado cai** |
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
                 Dan cai → CharaSpawn2 Zé do Morro + Dimitztri (lv 150)
                           Dimitztri: "Juse, se acalme! Ninguém sabe onde está isso aí"
                           Juse:      "....."
                           Zé do Morro: "Esquece, ele não dá ouvidos"
                 os dois caem → SetThereAreEnemies(BFspe, false)
                                + fala "....."  → State 4

State 4  QuestFinishState(COMPLETE)
                 FlagFast false → QuestClear (fim normal)
                 FlagFast true  → SetFlag(FlagJuseSaiu) → State 5

State 5  CharaLeave(JuseAllyS3) → Wait(5.0) → ShowWarning
         → CharaSpawn(JuseEnemy, fala ".......") → State 6

State 6  PlayerHealth(<=, 20.0) → CharaSpawn2 ViniJr + Vini Pai
                                + SetAttackTarget(JuseEnemy, ViniJrAlly, true)
           falas: Vini → Vini Jr → Juse "...." → Vini Jr ("olhos profundos")
         os dois caem          → CharaSpawn2 Shinya + Luis
           falas: Rykan → Shinya → Juse "....."
         JuseEnemy cai         → State 7

State 7  QuestFinishState(ULTIMATE_FINISH) → QuestClear

State 8  FALHA - o Juse aliado caiu ( States 1..4 mandam pra cá )
         FlagJuseTaunts true  → as 3 falas do Dimitztri, uma por DialogueFinish,
                                e só no fim QuestFinishState(FAIL) + QuestClear
         FlagJuseTaunts false → QuestFinishState(FAIL) + QuestClear na hora

script1  vigia: TimePassed(>=, 600.0)                  → SetFlag(FlagFast, false)
                Ko(JuseAllyS3) + IsAlive(Dimitztri)    → FlagJuseTaunts + FlagJuseMorreu
                Ko(JuseAllyS1/S2/S3)                   → FlagJuseMorreu
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
* **A falha é scriptada.** O jogo só falha sozinho quando o time inteiro cai ou
  o tempo acaba; o tutorial diz explicitamente que condição especial ("*such as
  a quest ally killed*") é responsabilidade da quest, com `QuestFinishState(FAIL)`.
  Como são três instâncias do Juse, o `script1.x2qs` vigia as três e levanta
  `FlagJuseMorreu`; os States 1 a 4 checam a flag no **primeiro** Event (a ordem
  de declaração é a ordem de avaliação, então a derrota do Juse ganha de
  qualquer outra coisa que esteja acontecendo no mesmo frame).
* **`FlagJuseSaiu`** é levantada no State 4 antes de entrar no bônus: dali em
  diante o Juse não é mais aliado, então a regra de falha deixa de valer — sem
  isso o `CharaLeave`/chefe poderia ser lido como morte do aliado.

## 4. Elenco

Todos são mods `[OC]`, referenciados por `X2mMod` no `quest.x2qs`. O
identificador do `X2mMod` é o próprio **ENTRY_NAME** do mod, então o mesmo nome
serve de `char:` nos `QxdChar` e de `actor:` nas falas.

| Papel | Nome | Código | Lv | Vida | AI | Observação |
| --- | --- | --- | --- | --- | --- | --- |
| Aliado fixo | Juse | `JUS` | 180 | 3000 | 140 | ataque baixíssimo de propósito: `atk`/`ki_atk`/`super_atk`/`super_ki` = **-5.35** |
| 1 · onda 1 | Junin Emo | `JUE` | 100 | 1500 | 144 | — |
| 1 · onda 1 | Junin | `JUN` | 100 | padrão | 144 | `health: -1.0` = stats padrão do mod |
| 1 · onda 2 | Yone | `S4P` | 120 | padrão | 144 | costume 0 |
| 1 · onda 2 | Yasha | `YAS` | 120 | padrão | 144 | **costume 2** (Coat), SkillSet 3 |
| 2 · solo | Ezra Dito | `CU1` | 140 | 2500 | **142** | costume 0 |
| 2 · onda 2 | Ray | `RAY` | 150 | 2200 | 144 | costume 0 |
| 2 · onda 2 | Junin do Futuro | `JUF` | 150 | 2200 | 144 | **costume 1** (Agent Coat) |
| 3 · solo | Dan Majin Mau | `PU2` | 150 | 3200 | 144 | costume 0 (Majin, BODY_SHAPE 2) |
| 3 · onda 2 | Zé do Morro | `ZEM` | 150 | 2600 | 144 | costume 0 |
| 3 · onda 2 | Dimitztri | `BCT` | 150 | 2600 | **322** | costume 0 |
| bônus · chefe | Juse | `JUS` | 180 | **15000** | **611** | dano 1.2, `guard_damage` 1.5 |
| bônus · reforço | Vini Pai | `VIP` | 160 | padrão | **606** | time A |
| bônus · reforço | Vini Jr | `VJR` | 155 | padrão | **315** | time A; vira o alvo do Juse chefe |
| bônus · reforço | Luis (Rykan) | `LUI` | 175 | padrão | **606** | time A |
| bônus · reforço | Shinya | `NFT` | 170 | 3000 | **611** | time A, esposa do Luis |

`Vida: padrão` = `health: -1.0`, ou seja, vale o `PscSpecEntry` do próprio mod.
A coluna **AI** é o `ait_table_entry` do `QxdChar`. Player = 138, Teacher = 140.

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

27 falas em `pt` / `en` / `es`, todas com `voice: ""` (legenda sem dublagem).
Os textos ficam em `dialogue.x2qs` — é só editar lá.

**Regra dura: o Juse nunca fala.** As 7 falas dele são só reticências —
`"...."`, `"....."` e `"......."` — e nada mais. Todos os outros personagens
falam: Junin Emo, Junin, o jogador, Yone, Yasha, Ezra, Ray, Junin do Futuro,
Dan, Zé do Morro, Dimitztri, Vini Pai, Vini Jr, Luis e Shinya.

Quem mais fala é o **Dimitztri** (4): a chegada dele no stage 3 e as três
provocações da falha.

| Momento | Falas |
| --- | --- |
| Dimitztri entra (stage 3) | `BCT` "Juse, se acalme! Ninguém sabe onde está isso aí." → `JUS` `"....."` → `ZEM` "Esquece, ele não dá ouvidos." |
| Juse cai com o Dimitztri vivo | `BCT` "Eu disse Juse, você deveria ter me escutado.." → "Agora olha pro 'cê... que humilhante." → "Mas você vem trabalhar amanhã, né?" → **só então** a tela de resultados |
| Vini Pai e Vini Jr entram | `VIP` "Parece que você está em problemas..." → `VJR` "Pra trás, meu pai e eu vamos cuidar disso" → `JUS` `"...."` → `VJR` "Pai, ele ta me olhando com aqueles olhos profundos... me da arrepios" |
| Luis e Shinya entram | `LUI` "Vini!, n-não!" → `NFT` "Sem drama idiota!, eles estão vivos. eu acho..." → `JUS` `"....."` |

A última provocação do Dimitztri é de propósito: a Super Soul do Juse é
*"[JUS SS]Tenho que trabaia amanhã!"*. E o "olhos profundos" do Vini Jr não é
só texto — quando os dois entram, `SetAttackTarget(JuseEnemy, ViniJrAlly, true)`
joga o alvo do Juse chefe pra ele.

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
# [lint] TMQ_JUS_01: OK - 6 arquivos, 221 identificadores,
#         161 Action/Condition validados, 9 aviso(s)
```

Além do linter, uma checagem estrutural do fluxo: os 9 `State` declarados
cobrem todos os 8 alvos de `GotoState`, nenhuma `Flag`/`Dialogue` é usada sem
ser declarada, nenhuma fica declarada sem uso, e o `script1.x2qs` não
redeclara flag nenhuma.

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
5. **`QuestFinishState(FAIL)`** — o tutorial prescreve exatamente este caso
   ("*if you need special failure conditions (such as a quest ally killed, etc),
   you will have to code the logic yourself and eventually call
   QuestFinishState(FAIL)*"), mas **nenhuma** das 1160 quests do corpus chama
   isso — só `COMPLETE` e `ULTIMATE_FINISH`. Se a tela sair como "concluída" em
   vez de "falhou", é aqui.
6. **`IsAlive(char)`** — tem 2 usos vanilla (`TMQ_4601`, junto com
   `DialogueFinish`), então a condição existe; o que não foi testado é combinar
   `Ko(aliado)` + `IsAlive(inimigo)` no mesmo Event pra escolher entre "falha com
   provocação" e "falha seca".
7. **Ordem de avaliação dos Events** — toda a prioridade da falha depende de os
   Events serem avaliados **na ordem em que aparecem no arquivo** (é o que
   `TMQ_URA_01` e o mod *ginyu* assumem). Se o jogo avaliar em outra ordem, o
   Event de `CheckFlag(FlagJuseMorreu, true)` pode perder para o de avanço de
   onda no mesmo frame — nesse caso o State 8 precisa virar checagem dentro de
   cada Event, não um Event próprio.
8. **SkillSet ↔ costume** — a associação posicional da seção 4 é inferência.
   Se no jogo a Yasha de Coat vier com as skills erradas, troque o bloco de
   skills do `QxdChar Yasha` pelo SkillSet 1 (`49156, 49153, 49154, 49159,
   49155, 49160, 10130, 21081, 65535`).
9. **Recompensas** — valores chutados pro nível 140; nada de `CharReward` do
   Juse porque recompensar personagem de mod não foi testado.
10. **`SetAttackTarget(JuseEnemy, ViniJrAlly, true)`** — a ação tem 19 usos
    vanilla (todos no `TMQ_4303`), mas **todos com `false`**, ou seja, tirando o
    alvo do jogador; usar com `true` pra *dar* um alvo a um inimigo não tem
    precedente no corpus. Se o Juse não fixar no Vini Jr, mova a chamada do
    Event 0 pro Event 1 do State 6 (quando os dois já estão garantidamente em
    campo).
11. **`CharPortrait` são os inimigos, não o elenco todo.** O `Quest` tem
    exatamente **6 slots** fixos — as 6 quests de referência do repositório
    (`TMQ_0101`, `TMQ_4303`, `TMQ_4601`, `TMQ_4200`, `folder/`, ginyu) têm 6
    linhas cada uma. Somam 25 entradas preenchidas e **todas** são inimigos:
    nenhum `Player`/`HUM` e nenhum aliado (o Jiren é aliado no `TMQ_4303` e não
    aparece; o `TMQ_0101` não lista o player). Escolhidos aqui: `JUE`, `JUN`,
    `S4P`, `YAS` (costume 2), `CU1`, `RAY`, todos com o mesmo costume do
    `QxdChar`. Ficam de fora por falta de slot: `JUF`, `PU2`, `ZEM`, `BCT` e o
    `JUS` chefe. *Onde o jogo desenha esses retratos eu não testei — a regra vem
    do corpus.*

**Decisões já confirmadas pelo autor**

Os três maps (`BFkoh` → `BFsky` → `BFspe`), o gatilho dos reforços
(`PlayerHealth(<=, 20.0)` = vida do jogador em 20% ou menos), as recompensas da
ficha, a falha quando o Juse cai e as falas do Dimitztri foram pedidos
explicitamente. Nível 140 e `health: 15000.0` do chefe continuam livres pra
ajustar.
