# "1 BILHÃO DE JUNINS" — Parallel Quest customizada (TMQ_JUN_01)

Missão paralela para **Dragon Ball Xenoverse 2** (X2QS / `.x2m`), feita para o
**XV2 Quest Creator** + **XV2 Mods Installer**.

Fontes em [`quests/TMQ_JUN_01/`](../quests/TMQ_JUN_01) · pacote em
[`dist/1 Bilhao de Junins.x2m`](../dist/) · gerador em
[`tools/gen_junin_quest.py`](../tools/gen_junin_quest.py).

---

## 1. A ideia

Setenta e seis Junins invadiram o **Espaço-tempo Distorcido** e não param de
aparecer. Sem aviso, sem cutscene, sem conversa: eles só surgem e vêm pra cima.
Quando caem, outros dois entram no lugar. No fim de tudo, aparece o
**Junin do Futuro** — que cai, levanta e volta de Agent Coat muito mais forte.

Uma missão de **moer horda**: o placar de 76 fica no canto da tela e o jogo
incrementa sozinho a cada Junin derrubado.

## 2. Ficha

| Campo | Valor |
| --- | --- |
| ID | `TMQ_JUN_01` |
| Tipo | Parallel Quest, 1 a 3 jogadores |
| Palco | `BFtol` — Twisted Timespace (Espaço-tempo Distorcido), palco único |
| Objetivo | 76 Junins + o Junin do Futuro |
| Nível | 85 |
| Dificuldade | 5 |
| Tempo limite | 30 min (`time_limit: 1800`) |
| Desbloqueio | após `TMQ_1400` (Being a Time Patroller) |
| Diálogo | **nenhum** (`dialogue.x2qs` vazio — legal em vanilla, cf. `CBF_DELI_00`) |

## 3. Os mods referenciados

A missão não embute nada: ela **referencia** os seus `.x2m` pelo par
`name` + `guid`. Se alguém instalar a quest sem ter os mods, o XV2 Mods
Installer avisa e cancela — comportamento correto.

```
X2mMod JuninChar       { name: "[OC] Junin"           guid: "5f6e184a-a144-e8bc-b8e8-27c0be55388d" }
X2mMod JuninEmoChar    { name: "[OC] Junin EMO"       guid: "65cbcff2-b81b-ce77-f4e6-6d1220c2e330" }
X2mMod JuninFuturoChar { name: "[OC] Junin do Futuro" guid: "1e471bf4-cf30-6d50-7d1f-4fcb705e0a27" }
```

Mais **13 `X2mMod` de skill**, para que cada um lute com o **skillset do próprio
mod** (copiado dos blocos `<SkillSet>` dos XML, na ordem do CUS:
`super1-4, ultimate1-2, evasive, blast, awaken`):

| Personagem | super1 | super2 | super3 | super4 | ult1 | ult2 | evasive | blast | awaken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Junin (costume 1) | 801 | 355 | Soltar Ra Preto | Limit Breaker Charge | 5420 | 5060 | 10360 | 21080 | Super Villainous Mode |
| Junin EMO (costume 0) | Power Trip | Piin | Burning Swan | 1 | Jibaku | Jibaku | 10341 | 21081 | — |
| Junin do Futuro (fase 1) | 620 | Muro de Defesa | Explosive Bullet | Dual Gun Shot | The Jackal | 5800 | 10300 | 21081 | Surge Mode |
| Junin do Futuro (fase 2) | 620 | Muro de Defesa | Explosive Bullet | Dual Gun Shot | The Jackal | 5800 | 10310 | Gun Ki Blast | Surge Mode |

## 4. Como a horda funciona

* **76 Junins = 38 duplas.** Cada Junin tem o seu próprio `QmlChar`
  (`Junin01`…`Junin76`), então o script sabe exatamente quem caiu.
  (Vanilla aguenta bem: `CTP_27_50` tem 206 `QmlChar`.)
* **Dupla ímpar** usa `battle_index` **3/4**; **dupla par** usa **5/6**. Assim
  duas duplas ficam em campo ao mesmo tempo — **4 Junins vivos** — sem nunca
  brigar pelo mesmo slot. O jogo só carrega 7 personagens (índices 0–6), e
  0/1/2 são os jogadores.
* **Mistura:** ímpares = Junin normal (tanque, 900 HP, atk 1.25);
  pares = Junin EMO (fraco e rápido, 520 HP, atk 1.05).
* **Caiu a dupla → entra a próxima**, com `CharaSpawn2`, que é a única variante
  de spawn **sem parâmetro de cena** — ou seja, zero cutscene de entrada.
* `ShowEnemyKoCounter(true, 76)` mostra o placar; o próprio jogo incrementa
  (opcode 86, usado em 28 quests vanilla — `TMQ_0701` usa `(true, 30)`).

### Por que em duplas e não 1 por 1

`CharaSpawn` (1 personagem) **exige** um parâmetro de cena — é ele que faz a
animação de chegada. `CharaSpawn2`/`CharaSpawn3` não têm esse parâmetro, mas
spawnam 2 ou 3 de uma vez. Como você pediu *sem cena de entrada*, fui de
`CharaSpawn2`. Se preferir 1-por-1 aceitando uma animação de portal, é trocar as
linhas de respawn por `CharaSpawn(JuninNN, pos, -1, 0, "BFtol", 0)`.

### Restrição do BFtol

O `BFtol` só tem **3 pontos de spawn** (`TRESPASS_0/1/2`). O script rotaciona
entre eles — como o Junin sai andando na hora, não fica ninguém empilhado.

## 5. O chefe em duas fases

```
State 2  CharaSpawn(JuninFuturoEnemy, 2, -1, 20, "BFtol", 0)   ; scene 20 = Character Entrance
State 3  Event 0: Ko(fase1) -> Revive + ModelChange -> fase 2 (Agent Coat)
         Event 1: Ko(fase2) -> State 4
State 4  QuestFinishState(COMPLETE) + QuestClear
```

* **Fase 1** — costume 0 (Camiseta da Shinya), nível 88, 1300 HP.
* **Fase 2** — costume 1 (Agent Coat), nível 92, 2200 HP, atk 1.70 / dano 1.90.
  É o costume que já tem `HEALTH 2.0` e defesas altas no próprio mod.
* A transição usa `DontRemoveOnKo` + `Revive(..., 35, 100.0)` +
  `ModelChange(fase1, fase2, 0, -1, 25)` — o padrão exato de `BAQ_CCR_POW`
  (Goku → Goku SSJ3). `ModelChange` exige `battle_index` diferentes, então a
  fase 1 usa 6 e a fase 2 usa 5.
* Só o chefe tem cena de entrada (scene 20) — de propósito, é o gran finale.

## 6. Instalação

**Requer:** [Eternity Tools / XV2 Mods Installer](https://videogamemods.com/xenoverse/mods/eternity-tools-1031725)
e os três mods de personagem (`[OC] Junin`, `[OC] Junin EMO`,
`[OC] Junin do Futuro`) **mais os mods das skills customizadas** deles.

1. Instale `dist/1 Bilhao de Junins.x2m` pelo XV2 Mods Installer.
2. Reinicie o jogo (mudança em `Quest`/`QxdChar` exige reboot, não só restart).
3. A missão aparece depois de *Being a Time Patroller*.

Alternativa: abra `quests/TMQ_JUN_01` no XV2 Quest Creator (aba *Files* → *quest
directory*) e salve o `.x2m` por lá.

## 7. O que foi verificado (e o que não foi)

```bash
python3 tools/gen_junin_quest.py            # regenera os .x2qs
python3 tools/x2qs_lint.py quests/TMQ_JUN_01
```

* **1160/1160** quests vanilla descompiladas passam pelo linter com **0 erros**
  (é isso que dá confiança de que as regras dele batem com o jogo).
* `TMQ_JUN_01` passa: 5 arquivos, 120 identificadores, **147 `Action`/`Condition`
  validados** (nome + aridade + tipos), posições `TRESPASS_0/1/2/3`,
  `CTP_27_03_POS_00` e `CTP_27_06_POS_00` confirmadas no mapa do `BFtol`.
* Durante o desenvolvimento o linter pegou dois erros reais que teriam quebrado
  a missão: `ItemCollection` declarada **depois** do `Quest` que a referencia (o
  compilador lê de cima para baixo) e três campos `i124/i128/i132` inventados.
* **Não testado:** rodar a missão no jogo. Não há como executar Xenoverse 2
  aqui. Em particular, o que eu não consigo garantir sem teste seu:
  * `NumCharsDefeated(76, …)` — vanilla usa no máximo 22; deixei essa condition
    como *backup* (Event 91). O caminho principal (Event 90) são os 4 `Ko()` dos
    últimos Junins, que não depende de limite nenhum.
  * Se `ModelChange` entre dois costumes do mesmo mod X2M se comporta igual ao
    vanilla (Goku → SSJ3). Se falhar, o plano B é spawnar a fase 2 com
    `CharaSpawn` em vez de transformar.
  * Se o instalador resolve as 16 referências `X2mMod` de uma vez.
