# "NÃO COMA O URÂNIO!" — Parallel Quest customizada (TMQ_URA_01)

Missão paralela para **Dragon Ball Xenoverse 2** (formato X2QS / `.x2m`,
feita para o **XV2 Quest Creator** + **XV2 Mods Installer** do Eternity Tools).

Arquivos prontos em [`quests/TMQ_URA_01/`](../quests/TMQ_URA_01) e pacote
instalável em [`dist/Nao Coma o Uranio.x2m`](../dist/).

---

## 1. A ideia

Um bando de desocupados tomou o **Pátio do Exército Red Ribbon** e não deixa
ninguém em paz. Eles só sabem falar de **duas** coisas:

1. **que você NÃO deve comer urânio** (gritando, de preferência); e
2. **o tamanho do seu... "equipamento"** — com direito a medição, laudo e
   comparação com o poder de luta.

A Patrulha do Tempo desistiu de argumentar e te mandou lá. A missão é uma
briga em três ondas que termina no **Grande Moderador** — um Hercule
(Mr. Satan) que se acha o dono do assunto —, com um final alternativo se você
resolver tudo em menos de 5 minutos.

O tom é de zoeira: os inimigos são fracos de dano e fortes de boca. A graça
está nas legendas, não na dificuldade.

## 2. Ficha da missão

| Campo | Valor |
| --- | --- |
| ID | `TMQ_URA_01` |
| Tipo | Parallel Quest (TMQ), 1 a 3 jogadores |
| Palco | `BFrrg` — Red Ribbon Army (Yard) |
| Nível sugerido | 20 |
| Tempo limite | 15 min (`time_limit: 900`) |
| Dificuldade | 2 |
| Desbloqueio | após `TMQ_1400` (Being a Time Patroller) |
| Final alternativo | terminar em menos de **5 minutos** |

### Recompensas

* 3 tabelas de materiais (`Collection60/70/80`) — as mesmas de uma PQ vanilla
  de nível parecido;
* **Sr. Antidoto S** (`item: 20 type: BATTLE`) — a piada interna da missão:
  antidoto pra quem comeu urânio;
* **Taunt** (`skill: 330`) — a skill de zoar, dada de primeira vez;
* **Present For You** (`skill: 522`) — 40% de chance no final alternativo;
* **Hercule** (`CharReward char: "STN" costume: 0`) — o próprio Grande
  Moderador vira personagem jogável;
* 5 TP medals na primeira vez, 3 nas repetições.

## 3. Roteiro / fluxo

```
State 0  init (InitQuest, BattleModeStart)
State 1  ONDA 1 — 3 Fiscais de Urânio (Saibamen "radioativos")   TRESPASS_1
State 2  ONDA 2 — 3 Moderadores (Guprei, Orlen, Raspberry)       TRESPASS_2
State 3  CHEFE  — Grande Moderador (Hercule, com Villainous)     TRESPASS_3
State 4  fim normal  /  abre a fase extra se Flag63 ainda estiver ligado
State 5  FASE EXTRA — Grande Moderador Enfurecido + 2 fiscais
State 6  ULTIMATE FINISH
```

* O script principal (`script.x2qs`) só **reage** a flags.
* O `script1.x2qs` é o **vigia**: usa `Ko()`, `Health()` e `TimePassed()` para
  levantar `Flag0..Flag4` e `Flag63`.

| Flag | Significado |
| --- | --- |
| `Flag0` | onda 1 eliminada |
| `Flag1` | onda 2 eliminada |
| `Flag3` | Grande Moderador com ≤ 50% de vida (ele surta) |
| `Flag2` | Grande Moderador derrotado |
| `Flag4` | fase extra concluída |
| `Flag63` | `true` no início, vira `false` depois de 300 s → sem final alternativo |

O chefe usa `DontRemoveOnKo` + `CharaLeave(..., Dialogue10, 26, true, -1)`:
ele cai, solta a fala de derrota e vai embora (padrão usado em
`TMQ_0203`).

## 4. Elenco

| Papel | Personagem | Código | battle_index |
| --- | --- | --- | --- |
| Onda 1 | Fiscal Verde (Saibaman) | `SBM` c3 | 3 |
| Onda 1 | Fiscal Pálido (Kaiwareman) | `SBM` c0 | 4 |
| Onda 1 | Fiscal Listrado (Kyukonman) | `SBM` c1 | 5 |
| Onda 2 | Moderador Guprei | `RSB` c3 | 3 |
| Onda 2 | Moderador Orlen | `APL` c4 | 4 |
| Onda 2 | Moderador Frambo (Raspberry) | `RSB` c0 | 5 |
| Chefe | Grande Moderador (Hercule) | `STN` c1 | 6 |
| Extra | Grande Moderador Enfurecido | `STD` c0 | 6 |
| Extra | Fiscal Radioativo / Fiscal Tóxico | `SBM` c2 / c5 | 3 / 4 |

Os `battle_index` se repetem entre ondas de propósito: quem cai é removido e
libera o slot (o jogo carrega no máximo 7 personagens, índices 0–6). É o mesmo
esquema de `TMQ_0203` e `TMQ_4000`.

O chefe tem `transformation: 300`, `i12: 4` e `ultimate2: 5530` (Villainous
Mode), então ele mesmo entra em Modo Vilão durante a luta — igual a
`TMQ_0505_Z`/`TMQ_2103`.

## 5. As falas

Doze falas em `dialogue.x2qs`, escritas em **pt / en / es** com
`TextAudioEntry` (`voice: ""` = legenda sem dublagem). Amostra:

| Quem | Fala (pt) |
| --- | --- |
| Fiscal Verde | "EI, VOCÊ AÍ! É, você mesmo! NÃO! COMA! O! URÂNIO!" |
| Fiscal Pálido | "Eu comi um pedaço em 762. Olha pra mim: verde, brilhante e cheio de razão!" |
| Fiscal Listrado | "E antes que você pergunte... sim, a gente também reparou no tamanho do seu canhão de ki." |
| Jogador | "Eu só queria atravessar a rua em paz..." |
| Moderador Guprei | "A gente mediu o seu poder de luta. E mais umas coisinhas. As duas medidas deram pena." |
| Moderador Orlen | "Dizem que tamanho não é documento. No seu caso, é laudo médico." |
| Moderador Frambo | "Urânio não é lanche, é herança! E olha que você não tem muito o que herdar..." |
| Grande Moderador | "EU sou o GRANDE MODERADOR! E vim te dar um único aviso: NÃO COMA O URÂNIO!" |
| Grande Moderador | "E sobre o seu 'equipamento'... eu precisei de uma lupa para achar. Uma. Lupa." |
| Grande Moderador (50%) | "COMO É QUE É?! Isso é reação de quem comeu urânio?! MODO VILÃO, AGORA!" |
| Grande Moderador (derrota) | "Tá bom, tá bom! A gente para de falar do urânio... mas do outro assunto a gente continua." |
| Moderador Enfurecido | "FUI CANCELADO?! AGORA É PESSOAL! VEM CÁ, QUE A GENTE TE EXPLICA DE PERTO!" |

As piadas de "tamanho" ficaram como provocação/insinuação (nada explícito).
Está tudo num lugar só: edite `dialogue.x2qs` para mudar o nível da zoeira —
só texto, nenhuma lógica mexe com isso.

## 6. Como instalar

**Precisa:** [Eternity Tools / XV2 Mods Installer](https://videogamemods.com/xenoverse/mods/eternity-tools-1031725)
e o jogo já moddado (xv2patcher).

### Caminho A — pacote pronto

1. Coloque `dist/Nao Coma o Uranio.x2m` em qualquer pasta.
2. Abra o **XV2 Mods Installer** → instale o `.x2m`.
3. Reinicie o jogo. A missão aparece na lista de Parallel Quests
   (desbloqueia depois de *Being a Time Patroller*).

### Caminho B — pelo Quest Creator (recomendado se o instalador reclamar)

1. Abra o **XV2 Quest Creator**.
2. Aba *Info*: preencha nome/autor/versão.
3. Aba *Files*: aponte *quest directory* para `quests/TMQ_URA_01`.
4. Salve como `.x2m` e instale.

> Mudanças em `Quest`, `ItemCollection` ou `QxdChar` exigem **reiniciar o
> jogo**. Mudanças em `QmlChar`, `Dialogue`, `CharPosition` e `Script` só
> pedem um restart da missão pelo menu de pausa.

## 7. O que foi verificado aqui (e o que não foi)

O repositório tem um linter próprio:

```bash
python3 tools/gen_reference.py --corpus "/caminho/Vanilla quests/Quest" \
    --dialogue "/caminho/Vanilla quests/Dialogue" --extra "/caminho/mod/QUEST"
python3 tools/x2qs_lint.py quests/TMQ_URA_01
```

* **1160/1160** quests vanilla descompiladas passam pelo linter sem erro
  (isso é o que dá confiança de que as regras dele batem com o jogo).
* `quests/TMQ_URA_01` passa: 6 arquivos, 69 identificadores e 91
  `Action`/`Condition` validados (nome + aridade + tipos de argumento), todos os
  códigos de personagem/skill/estágio conferidos, e as posições
  (`RBQ_4000_POS_00..02`, `TRESPASS_1/2/3`) confirmadas como existentes no mapa
  do `BFrrg`.
* **Não testado:** rodar a missão dentro do jogo. Não há como executar
  Xenoverse 2 neste ambiente, então balanceamento, cenas e o instalador em si
  precisam de um teste seu.
