#!/usr/bin/env python3
"""
gen_junin_quest.py
==================
Gera a Parallel Quest **TMQ_JUN_01 - "1 Bilhao de Junins"** em
``quests/TMQ_JUN_01/``.

Por que um gerador e nao os arquivos na mao: a missao tem 76 Junins, cada um
com o seu proprio ``QmlChar`` (identidade propria => condicao ``Ko()`` propria
=> respawn deterministico). Sao ~80 objetos e ~40 eventos; escrever a mao seria
ilegivel e facil de quebrar. Mude as constantes abaixo e rode de novo.

Mecanica
--------
* Palco unico: ``BFtol`` (Twisted Timespace).
* 76 Junins em 38 duplas. Dupla impar usa ``battle_index`` 3/4, dupla par usa
  5/6 -- assim duas duplas ficam em campo ao mesmo tempo (4 Junins vivos) sem
  nunca brigar pelo mesmo slot.
* Caiu a dupla => entra a proxima, com ``CharaSpawn2`` (a unica variante de
  spawn que nao tem parametro de cena, ou seja: zero cutscene de entrada).
* ``ShowEnemyKoCounter(true, 76)`` mostra o placar no canto da tela; o proprio
  jogo incrementa a cada inimigo derrubado.
* Mortos os 76, entra o Junin do Futuro. Ele cai, levanta e vira a forma
  "Agent Coat" via ``Revive`` + ``ModelChange`` (padrao de ``BAQ_CCR_POW``).

Uso:  python3 tools/gen_junin_quest.py
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "quests", "TMQ_JUN_01")
TEMPLATE_QUEST = os.path.join(ROOT, "quests", "TMQ_URA_01", "quest.x2qs")

N_JUNINS = 76            # objetivo da missao
STAGE = "BFtol"          # Twisted Timespace
STAGE_COMMENT = "Twisted Timespace"
SPAWN_POINTS = [0, 1, 2]  # TRESPASS disponiveis no BFtol
TIME_LIMIT = 1800        # 30 minutos
EX_TIME_LIMIT = 900.0    # 15 minutos: janela do Ultimate Finish (ex_success)
LEVEL = 85
DIFFICULTY = 5
QUEST_ID = "TMQ_JUN_01"

# ---------------------------------------------------------------- mods X2M ---
# name = MOD_NAME do .x2m (tem que bater), guid = MOD_GUID
CHAR_MODS = [
    ("JuninChar", "[OC] Junin", "5f6e184a-a144-e8bc-b8e8-27c0be55388d"),
    ("JuninEmoChar", "[OC] Junin EMO", "65cbcff2-b81b-ce77-f4e6-6d1220c2e330"),
    ("JuninFuturoChar", "[OC] Junin do Futuro", "1e471bf4-cf30-6d50-7d1f-4fcb705e0a27"),
]
SKILL_MODS = [
    ("JunSkillTektek", "[JUN Skill]Tektek Tchuruq", "0a06569e-7cc6-1965-5e50-237f6d2f05f1"),
    ("JunSkillLimitBreaker", "[JUN Skill]Limit Breaker Charge [KICH]", "4cf2608c-1129-b12f-a62e-8d95c3f3c824"),
    ("JunSkillSuperVillainous", "[JUN Skill]Super Villainous Mode", "4d061ab3-42a3-cf82-f2b9-56028c20be1b"),
    ("JunSkillFacaMaluca", "[JUNSkill]Faca Maluca", "e60c9833-3a8a-2f40-a65f-879d79c75073"),
    ("JunSkillRaPreto", "[JUN Skill]Soltar Ra Preto", "2c76c4e9-3f0d-75a3-6111-e2eebaeb3c0e"),
    ("JueSkillJibaku", "[JUE Skill]Jibaku", "2f407646-50c4-eaf8-5a07-580b136adbac"),
    ("JueSkillPiin", "[JUE Skill]Piin", "318e9d53-6d53-f4e6-86c4-2e2881ed0a6d"),
    ("JueSkillBurningSwan", "[JUE Skill]Burning Swan", "c29942cc-3d1f-0cad-1533-e94eff0aa327"),
    ("JueSkillCowardly", "[JUE Skill]Cowardly Deception", "0a826011-525d-1ea2-561f-49842b128538"),
    ("JueSkillPowerTrip", "[JUE Skill]Power Trip", "32e9e79a-d7b8-999d-4d2a-7ebecd65e959"),
    ("MuroDeDefesaSkill", "[JUE Skill] Muro de Defesa", "a46e6d7f-d13a-2ce9-adf7-6a167916ee78"),
    ("JufSkillSurgeMode", "[JUF Skill]Surge Mode", "c8ca0cf7-40d5-0319-c972-5de6e792b3e9"),
    ("JufSkillJackal", "[JUF Skill]The Jackal", "805e330f-0f4b-848d-39b4-da6bcd163a35"),
    ("JufSkillExplosiveBullet", "[JUF Skill]Explosive bullet", "e0f49bb6-9802-38fe-0f9a-56f5d1919e0e"),
    ("JufSkillDualGunShot", "[JUF Skill]Dual gun shot", "c6ad9982-18b1-cc5e-d326-4ace42e6ef49"),
    ("JufSkillGunKiBlast", "[JUF Skill]Gun Ki Blast", "5f9f8dac-4e2d-2ddf-64fe-cdb91614f344"),
]

# Skillsets copiados dos <SkillSet> dos proprios .x2m, na ordem do CUS:
# super1, super2, super3, super4, ultimate1, ultimate2, evasive, blast, awaken
JUNIN_TANK_SKILLS = [801, 355, "JunSkillRaPreto", "JunSkillLimitBreaker",
                     5420, 5060, 10360, 21080, "JunSkillSuperVillainous"]
JUNIN_EMO_SKILLS = ["JueSkillPowerTrip", "JueSkillPiin", "JueSkillBurningSwan", 1,
                    "JueSkillJibaku", "JueSkillJibaku", 10341, 21081, -1]
JUF_F1_SKILLS = [620, "MuroDeDefesaSkill", "JufSkillExplosiveBullet", "JufSkillDualGunShot",
                 "JufSkillJackal", 5800, 10300, 21081, "JufSkillSurgeMode"]
JUF_F2_SKILLS = [620, "MuroDeDefesaSkill", "JufSkillExplosiveBullet", "JufSkillDualGunShot",
                 "JufSkillJackal", 5800, 10310, "JufSkillGunKiBlast", "JufSkillSurgeMode"]

SKILL_FIELDS = ["super1", "super2", "super3", "super4",
                "ultimate1", "ultimate2", "evasive", "blast", "awaken"]

TEXTS = {
    "title": ("ONE BILLION JUNINS", "1 BILHÃO DE JUNINS", "¡MIL MILLONES DE JUNINS!"),
    "success": (r"-Defeat all 76 Junins\n-Defeat the Junin of the Future",
                r"-Derrote os 76 Junins\n-Derrote o Junin do Futuro",
                r"-Derrota a los 76 Junins\n-Derrota al Junin del Futuro"),
    "failure": (r"-All team HP depleted\n-Time expires",
                r"-Vida do time esgotada\n-Tempo esgotado",
                r"-Salud del equipo agotada\n-Se acaba el tiempo"),
    "outline": ("Seventy-six Junins are flooding the Twisted Timespace. "
                "They keep coming. Just keep swinging.",
                "Setenta e seis Junins estão invadindo o Espaço-tempo Distorcido. "
                "Eles não param de aparecer. Continua batendo.",
                "Setenta y seis Junins están invadiendo el Espacio-tiempo Distorsionado. "
                "No paran de aparecer. Sigue golpeando."),
    "warning": ("-Defeat the Junin of the Future",
                "-Derrote o Junin do Futuro",
                "-Derrota al Junin del Futuro"),
    "ex_success": ("-Clear in under 15 minutes",
                   "-Zere em menos de 15 minutos",
                   "-Termínala en menos de 15 minutos"),
}


def pair_of(junin: int) -> int:
    """Numero da dupla (1-based) a que o Junin N pertence."""
    return (junin + 1) // 2


def slots_of(pair: int) -> tuple[int, int]:
    """battle_index da dupla: impares em 3/4, pares em 5/6."""
    return (3, 4) if pair % 2 == 1 else (5, 6)


def name_of(junin: int) -> str:
    return f"Junin{junin:02d}"


def qxd_char(ident: str, char_ref: str, costume: int, skills: list, *,
             level: int, health: float, atk: float, atk_dmg: float,
             comment: str = "", extra: str = "") -> str:
    lines = [f"QxdChar {ident}", "{", f'\tchar: {char_ref}', f"\tcostume: {costume}",
             "\ttransformation: 0", "\tspecial_effect: -1", "",
             f"\ti12: {extra and 4 or 0}", f"\tlevel: {level}", f"\thealth: {health:.1f}",
             "\tf24: -1.0", "\tki: -1.0", "\tstamina: -1.0",
             f"\tatk: {atk:.2f}", "\tki_atk: -1.0", f"\tsuper_atk: {atk:.2f}",
             "\tsuper_ki: -1.0", f"\tatk_damage: {atk_dmg:.2f}", "\tki_damage: -1.0",
             f"\tsuper_atk_damage: {atk_dmg:.2f}", "\tsuper_ki_damage: -1.0",
             "\tguard_atk: -1.0", "\tguard_damage: -1.0",
             "\tmove_speed: -1.0", "\tboost_speed: -1.0", "\tf84: -1.0",
             "\tait_table_entry: 144", ""]
    for field, value in zip(SKILL_FIELDS, skills):
        lines.append(f"\t{field}: {value}")
    lines += ["", "\ti106: 0", "\ti108: 0", "\ti112: 0", "\ti124: -1", "\ti126: 0", "}"]
    body = "\n".join(lines)
    return f"; {comment}\n{body}" if comment else body


def qml_char(ident: str, base: str, index: int, *, ai: str, team: str,
             spawn_at_start: str) -> str:
    # o compilador exige o bloco de skills no QmlChar (super1..awaken);
    # -1 = nao sobrescreve, herda os valores do QxdChar base (vanilla).
    return "\n".join([
        f"QmlChar {ident} : {base}", "{",
        f"\tbattle_index: {index}", "\ti12: 0",
        f'\tstage: "{STAGE}" ; {STAGE_COMMENT}',
        f"\tspawn_at_start: {spawn_at_start}", "",
        f"\tai: {ai}", f"\tteam: {team}", "",
        "\ti36: 9999", "\ti40: 5", "\ti44: 0", "\ti48: -1",
        "\ti50: -1", "\ti52: 0", "\ti56: 0", "",
        "\tsuper1: -1", "\tsuper2: -1", "\tsuper3: -1", "\tsuper4: -1", "",
        "\tultimate1: -1", "\tultimate2: -1", "",
        "\tevasive: -1", "\tblast: -1", "\tawaken: -1", "}",
    ])


def grab_item_collections() -> str:
    """Reaproveita as ItemCollection ja validadas da quest anterior."""
    src = open(TEMPLATE_QUEST, encoding="utf-8").read()
    blocks = re.findall(r"ItemCollection Collection\d+\n\{.*?\n\}\n", src, re.S)
    return "\n".join(blocks)


# ------------------------------------------------------------------ quest ---
def build_quest() -> str:
    mods = ["; Personagens e skills vindos de mods .x2m externos.",
            "; Se o usuario nao tiver esses mods instalados, o XV2 Mods Installer",
            "; avisa e cancela a instalacao (comportamento esperado).", ""]
    for ident, name, guid in CHAR_MODS + SKILL_MODS:
        mods.append(f"X2mMod {ident}\n{{\n\tname: \"{name}\"\n\tguid: \"{guid}\"\n}}\n")

    texts = []
    for i, key in enumerate(("title", "success", "failure", "outline", "warning", "ex_success")):
        en, pt, es = TEXTS[key]
        texts.append(
            f"TextEntry {QUEST_ID}_{i}\n{{\n\ten: \"{en}\"\n\tpt: \"{pt}\"\n\tes: \"{es}\"\n}}\n")

    quest = f"""Quest {QUEST_ID}
{{
\tepisode: 3 ; textos proprios via TextEntry (nao usa .msg vanilla).
\tsub_type: 0
\tnum_players: 3

\ttitle: {QUEST_ID}_0 ; ONE BILLION JUNINS
\tsuccess: {QUEST_ID}_1 ; -Defeat all 76 Junins
\tfailure: {QUEST_ID}_2 ; -All team HP depleted / time expires
\toutline: {QUEST_ID}_3 ; Seventy-six Junins are flooding the Twisted Timespace.
\twarning: {QUEST_ID}_4 ; -Defeat the Junin of the Future
\tex_success: {QUEST_ID}_5 ; -Clear in under 15 minutes

\ti40: 1
\tparent_quest: "TMQ_1400" ; Being a Time Patroller
\ti44: 0
\ti48: 1
\ti52: -1
\ti56: -1
\ti60: -1
\tunlock_requirement: "TMQ_1400" ; Being a Time Patroller
\ti68: -1
\ti72: -1
\ti76: -1
\ti80: 1
\ti84: 1

\tQxdUnk1(3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
\tQxdUnk2(0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
\tQxdUnk2(1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

\ttime_limit: {TIME_LIMIT}
\tdifficulty: {DIFFICULTY}
\tlevel: {LEVEL}
\ti112: 0
\tstart_stage: "{STAGE}" ; {STAGE_COMMENT}
\tstart_demo: 0

\txp_reward: 26000
\tult_xp_reward: 45000
\tfail_xp_reward: 8000
\tzeni_reward: 14000
\tult_zeni_reward: 22000
\tfail_zeni_reward: 7500
\ttp_medals_once: 5
\ttp_medals: 0
\ttp_medals_special: 0
\tresistance_points: 0

\tItemReward {{ item: Collection60 type: COLLECTION condition: 1 chance: 100 flags: 0 i12: 0 i20: 0 }}
\tItemReward {{ item: Collection70 type: COLLECTION condition: 0 chance: 100 flags: 0 i12: 0 i20: 0 }}
\tItemReward {{ item: Collection80 type: COLLECTION condition: 0 chance: 100 flags: 0 i12: 0 i20: 0 }}
\tItemReward {{ item: 12 type: BATTLE condition: 0 chance: 100 flags: 0 i12: 0 i20: 0 }} ; Senzu Bean
\tSkillReward {{ skill: 330 condition: 1 chance: 100 i12: 0 }} ; Taunt

\tstages: ("{STAGE}", -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1) ; {STAGE_COMMENT}
\ti192: 1

\tCharPortrait {{ char: "HUM" costume: 0 trans: -1 }}
\tCharPortrait {{ char: JuninChar costume: 1 trans: -1 }}
\tCharPortrait {{ char: JuninEmoChar costume: 0 trans: -1 }}
\tCharPortrait {{ char: JuninFuturoChar costume: 1 trans: -1 }}
\tCharPortrait {{ char: -1 costume: 0 trans: -1 }}
\tCharPortrait {{ char: -1 costume: 0 trans: -1 }}

\ti232: 0
\ti234: 2
\ti236: 3
\ti238: 4
\ti240: 5
\ti242: 7
\ti244: 0
\ti246: 0
\ti248: 0
\ti250: 0
\tflags: 0x400000

\tupdate_requirement: ANY
\tdlc_requirement: NONE

\ti264: 0
\tno_enemy_bgm: 9
\tenemy_near_bgm: 24
\tbattle_bgm: 16
\tultimate_finish_bgm: 14
\tf276: 1.0
\ti280: 0
}}
"""
    # o compilador le quest.x2qs de cima para baixo: o que o Quest referencia
    # (ItemCollection) precisa vir ANTES dele.
    return ("\n".join(mods) + "\n" + "\n".join(texts) + "\n"
            + grab_item_collections() + "\n" + quest)


# ------------------------------------------------------------------ chars ---
def qxd_special_char(ident: str, char_code: str, ait: int, comment: str = "") -> str:
    """QxdSpecialChar completo (PlayerBase/Teacher), como nos quests vanilla:
    o compilador exige 'costume' e o bloco inteiro, nao so 'char'."""
    lines = [f"QxdSpecialChar {ident}", "{", f"\tchar: {char_code}",
             "\tcostume: 0", "\ttransformation: -1", "\tspecial_effect: -1", "",
             "\ti12: 0", "\tlevel: 1", "\thealth: -1.0", "\tf24: -1.0",
             "\tki: -1.0", "\tstamina: -1.0", "\tatk: -1.0", "\tki_atk: -1.0",
             "\tsuper_atk: -1.0", "\tsuper_ki: -1.0", "\tatk_damage: -1.0",
             "\tki_damage: -1.0", "\tsuper_atk_damage: -1.0",
             "\tsuper_ki_damage: -1.0", "\tguard_atk: -1.0",
             "\tguard_damage: -1.0", "\tmove_speed: -1.0", "\tboost_speed: -1.0",
             "\tf84: -1.0", f"\tait_table_entry: {ait}", "",
             "\tsuper1: -1", "\tsuper2: -1", "\tsuper3: -1", "\tsuper4: -1", "",
             "\tultimate1: -1", "\tultimate2: -1", "",
             "\tevasive: -1", "\tblast: -1", "\tawaken: -1", "",
             "\ti106: 0", "\ti108: 0", "\ti112: 0", "\ti124: -1", "\ti126: 0", "}"]
    body = "\n".join(lines)
    return f"; {comment}\n{body}" if comment else body


def build_chars() -> str:
    out = [
        qxd_special_char("PlayerBase", '"HUM"', 138, "Player"),
        "",
        qxd_special_char("Teacher", '"MST"', 140, "Teacher"),
        "",
        "; O Junin normal: mais tanque (costume 1 do mod [OC] Junin).",
        qxd_char("JuninBruto", "JuninChar", 1, JUNIN_TANK_SKILLS,
                 level=LEVEL, health=900.0, atk=1.25, atk_dmg=1.35), "",
        "; O Junin EMO: mais fraco e mais rapido (costume 0 do mod [OC] Junin EMO).",
        qxd_char("JuninEmoBase", "JuninEmoChar", 0, JUNIN_EMO_SKILLS,
                 level=LEVEL, health=520.0, atk=1.05, atk_dmg=1.05), "",
        "; Chefe fase 1 - camiseta da Shinya (stats mais leves do mod).",
        qxd_char("JuninFuturoFase1", "JuninFuturoChar", 0, JUF_F1_SKILLS,
                 level=LEVEL + 3, health=1300.0, atk=1.45, atk_dmg=1.50), "",
        "; Chefe fase 2 - Agent Coat (stats fortes do mod: HEALTH 2.0, defesas altas).",
        qxd_char("JuninFuturoFase2", "JuninFuturoChar", 1, JUF_F2_SKILLS,
                 level=LEVEL + 7, health=2200.0, atk=1.70, atk_dmg=1.90, extra="x"), "",
    ]
    for i, (ident, idx) in enumerate((("Player", 0), ("Player2", 1), ("Player3", 2))):
        out.append(qml_char(ident, "PlayerBase", idx, ai="HUMAN", team="A",
                            spawn_at_start="true"))
        out.append("")
    # 76 Junins, um QmlChar por Junin
    out.append(f"; {N_JUNINS} Junins. Cada um tem o seu proprio QmlChar para que o")
    out.append("; script consiga identificar qual caiu e chamar o proximo.")
    out.append("; Dupla impar -> battle_index 3/4 | dupla par -> battle_index 5/6.")
    for n in range(1, N_JUNINS + 1):
        pair = pair_of(n)
        idx = slots_of(pair)[0] if n % 2 == 1 else slots_of(pair)[1]
        base = "JuninBruto" if n % 2 == 1 else "JuninEmoBase"
        out.append(qml_char(name_of(n), base, idx, ai="NORMAL", team="B",
                            spawn_at_start="false"))
        out.append("")
    out += [
        qml_char("JuninFuturoEnemy", "JuninFuturoFase1", 6, ai="NORMAL", team="B",
                 spawn_at_start="false"), "",
        "; battle_index diferente do fase 1: ModelChange exige indices distintos.",
        qml_char("JuninFuturoEnemy2", "JuninFuturoFase2", 5, ai="NORMAL", team="B",
                 spawn_at_start="false"), "",
        qml_char("TeacherAlly", "Teacher", -1, ai="NORMAL", team="A",
                 spawn_at_start="false"), "",
    ]
    return "\n".join(out)


# -------------------------------------------------------------- positions ---
def build_positions() -> str:
    rows = [("PlayerPosition", "Player", "TRESPASS_3"),
            ("Player2Position", "Player2", "CTP_27_03_POS_00"),
            ("Player3Position", "Player3", "CTP_27_06_POS_00")]
    out = []
    for ident, char, pos in rows:
        out.append("\n".join([
            f"CharPosition {ident}", "{", f"\tchar: {char}",
            f'\tstage: "{STAGE}" ; {STAGE_COMMENT}', f'\tposition: "{pos}"',
            "\ttype: 3", "\ti40: 0", "\ti50: 0", "}", ""]))
    return "\n".join(out)


# ----------------------------------------------------------------- script ---
def build_script() -> str:
    n_pairs = N_JUNINS // 2
    out = ["Flag FlagFase2", "Flag FlagExOpen ; janela do Ultimate Finish (15 min)", "", "Script", "{"]

    # State 0 - inicializacao
    out += ["\tState 0", "\t{", "\t\tEvent 0", "\t\t{", "\t\t\tCondition Always", ""]
    for a in ("InitQuest", "SetFlag(FlagExOpen, true)", "Unk20", "BattleModeStart",
              f"ShowEnemyKoCounter(true, {N_JUNINS})",
              "DontRemoveOnKo(JuninFuturoEnemy)",
              f'SetThereAreEnemies("{STAGE}", true)',
              f'CharaSpawn2({name_of(1)}, {name_of(2)}, {SPAWN_POINTS[0]}, -1, "{STAGE}", 0, -1, -1)',
              f'CharaSpawn2({name_of(3)}, {name_of(4)}, {SPAWN_POINTS[1]}, -1, "{STAGE}", 0, -1, -1)',
              "GotoState(1)"):
        out.append(f"\t\t\tAction {a}")
    out += ["\t\t}", "\t}", ""]

    # State 1 - a horda: caiu a dupla, entra a proxima
    out += ["\tState 1", "\t{"]
    for p in range(1, n_pairs + 1):
        a, b = 2 * p - 1, 2 * p
        out += ["\t\tEvent %d" % p, "\t\t{",
                f"\t\t\tCondition Ko({name_of(a)}, false, -1)",
                f"\t\t\tCondition Ko({name_of(b)}, false, -1)", ""]
        if p + 2 <= n_pairs:
            nxt = slots_of(p + 2)
            pos = SPAWN_POINTS[(p + 2) % len(SPAWN_POINTS)]
            out.append(f'\t\t\tAction CharaSpawn2({name_of(2 * (p + 2) - 1)}, '
                       f'{name_of(2 * (p + 2))}, {pos}, -1, "{STAGE}", 0, -1, -1)'
                       f" ; dupla {p + 2} -> slots {nxt}")
        else:
            out.append(f"\t\t\tAction Nop ; ultima dupla ({p}) - nao tem mais o que chamar")
        out += ["\t\t}", ""]
    # Fim da horda: os 4 ultimos Junins cairam.
    last = [name_of(n) for n in range(N_JUNINS - 3, N_JUNINS + 1)]
    out += ["\t\tEvent 90", "\t\t{"]
    for c in last:
        out.append(f"\t\t\tCondition Ko({c}, false, -1)")
    out += ["", f"\t\t\tAction ShowEnemyKoCounter(false, {N_JUNINS})",
            "\t\t\tAction GotoState(2)", "\t\t}", "",
            "\t\tEvent 91", "\t\t{",
            f"\t\t\tCondition NumCharsDefeated({N_JUNINS}, ENEMY_TEAM, -1)", "",
            f"\t\t\tAction ShowEnemyKoCounter(false, {N_JUNINS})",
            "\t\t\tAction GotoState(2)", "\t\t}", "\t}", ""]

    # State 2 - entrada do chefe
    out += ["\tState 2", "\t{", "\t\tEvent 0", "\t\t{", "\t\t\tCondition Always", "",
            f'\t\t\tAction CharaSpawn(JuninFuturoEnemy, {SPAWN_POINTS[2]}, -1, 20, "{STAGE}", 0)',
            "\t\t\tAction ShowWarning ; -Defeat the Junin of the Future",
            "\t\t\tAction GotoState(3)", "\t\t}", "\t}", ""]

    # State 3 - chefe em duas fases
    out += ["\tState 3", "\t{", "\t\tEvent 0", "\t\t{",
            "\t\t\tCondition Ko(JuninFuturoEnemy, false, -1)",
            "\t\t\tCondition CheckFlag(FlagFase2, false)", "",
            "\t\t\tAction Revive(JuninFuturoEnemy, -1, 35, 100.0)",
            "\t\t\tAction ModelChange(JuninFuturoEnemy, JuninFuturoEnemy2, 0, -1, 25)",
            "\t\t\tAction SetFlag(FlagFase2, true)", "\t\t}", "",
            "\t\tEvent 1", "\t\t{",
            "\t\t\tCondition Ko(JuninFuturoEnemy2, false, -1)",
            "\t\t\tCondition CheckFlag(FlagFase2, true)", "",
            "\t\t\tAction GotoState(4)", "\t\t}", "\t}", ""]

    # State 4 - conclusao: se ainda dentro da janela (FlagExOpen true),
    # vai pro State 5 (ULTIMATE_FINISH); senao, encerra normal.
    out += ["\tState 4", "\t{", "\t\tEvent 0", "\t\t{", "\t\t\tCondition Always", "",
            "\t\t\tAction QuestFinishState(COMPLETE)", "\t\t}", "",
            "\t\tEvent 1", "\t\t{", "\t\t\tCondition CheckFlag(FlagExOpen, false)", "",
            "\t\t\tAction QuestClear", "\t\t}", "",
            "\t\tEvent 2", "\t\t{", "\t\t\tCondition CheckFlag(FlagExOpen, true)", "",
            "\t\t\tAction GotoState(5)", "\t\t}", "\t}", "",
            "\tState 5", "\t{", "\t\tEvent 0", "\t\t{", "\t\t\tCondition Always", "",
            "\t\t\tAction QuestFinishState(ULTIMATE_FINISH)",
            "\t\t\tAction QuestClear", "\t\t}", "\t}", "}"]
    return "\n".join(out) + "\n"


def build_script1() -> str:
    """script1.x2qs roda em paralelo ao fluxo principal (estado vigia):
    inicia a FlagExOpen em true e, depois de 15 min (900s), fecha a janela
    do Ultimate Finish (SetFlag false) - mesmo padrao do TMQ_URA_01."""
    return "\n".join([
        "; script vigia: controla a janela de 15 min do Ultimate Finish.",
        "Script", "{",
        "\tState 0", "\t{",
        "\t\tEvent -1", "\t\t{", "\t\t\tCondition Never", "\t\t}", "",
        "\t\tEvent 0", "\t\t{", "\t\t\tCondition Always", "",
        "\t\t\tAction GotoState(1)", "\t\t}", "\t}", "",
        "\tState 1", "\t{",
        "\t\tEvent -1", "\t\t{", "\t\t\tCondition Never", "\t\t}", "",
        "\t\tEvent 0", "\t\t{",
        f"\t\t\tCondition TimePassed(>=, {EX_TIME_LIMIT:.1f}) ; {EX_TIME_LIMIT / 60:.0f} min", "",
        "\t\t\tAction SetFlag(FlagExOpen, false)",
        "\t\t}", "\t}", "}", "",
    ])


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    files = {
        "quest.x2qs": build_quest(),
        "chars.x2qs": build_chars(),
        "dialogue.x2qs": "",          # sem dialogo: os Junins so apanham em silencio
        "positions.x2qs": build_positions(),
        "script.x2qs": build_script(),
        "script1.x2qs": build_script1(),  # vigia: janela de 15 min do Ultimate Finish
    }
    for name, body in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"  {name:16s} {len(body.splitlines()):5d} linhas")
    print(f"\n[gen] {N_JUNINS} Junins em {N_JUNINS // 2} duplas -> {OUT}")


if __name__ == "__main__":
    main()
