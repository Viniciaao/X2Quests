#!/usr/bin/env python3
"""
x2qs_lint.py
============
Valida uma pasta de quest X2QS (quest.x2qs, chars.x2qs, dialogue.x2qs,
positions.x2qs, script.x2qs[, script1..3.x2qs]) contra a base de referencia
gerada por ``gen_reference.py`` a partir dos quests vanilla.

O que ele checa
---------------
* sintaxe: chaves/aspas balanceadas, ``;`` de comentario, identificadores;
* arquivos obrigatorios presentes;
* tipos de objeto e campos conhecidos pelo compilador X2QS;
* nomes e ARIDADE de cada ``Action`` / ``Condition`` usados nos scripts;
* toda referencia resolvida: QmlChar, Dialogue, Flag, TextEntry/TextAudioEntry,
  ItemCollection (nada de apontar pra algo que nao foi declarado);
* codigos de personagem (CMS), ids de skill, codigos de estagio;
* posicoes nomeadas (``RBQ_4000_POS_00``, ``TRESPASS_N``...) que realmente
  existem no mapa do estagio escolhido;
* indice de spawn (``TRESPASS_N``) usado nos CharaSpawn ja atestado no estagio;
* ``battle_index`` 0..6 (o jogo so carrega 7 personagens de uma vez);
* ``stage`` dos QmlChar com ``spawn_at_start: true`` == ``start_stage`` do Quest;
* idiomas de texto validos e id da quest que nao colide com uma quest vanilla.

Uso
---
    python3 tools/x2qs_lint.py quests/TMQ_URA_01
    python3 tools/x2qs_lint.py "/tmp/van/Vanilla quests/Quest/TMQ/TMQ_0203"   # auto-teste

Saida: lista de ERROS/AVISOs. Exit code 1 se houver erro.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_reference import CALL_RE, IDENT, match_brace, split_args, strip_comments  # noqa: E402

REF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x2qs_reference.json")

REQUIRED_FILES = ["quest.x2qs", "chars.x2qs", "dialogue.x2qs", "positions.x2qs", "script.x2qs"]
OPTIONAL_SCRIPTS = ["script1.x2qs", "script2.x2qs", "script3.x2qs"]

TOP_DECL_RE = re.compile(rf"^({IDENT})(?:\s+({IDENT}))?\s*(?::\s*({IDENT}))?\s*\{{", re.M)
FIELD_LINE_RE = re.compile(rf"^\s*({IDENT})\s*:\s*(.*)$")
LITERAL_WORDS = {"true", "false", "DEFAULT"}
OPERATORS = {"<=", ">=", "<", ">", "==", "!="}

# papel dos argumentos por funcao: qual "familia" de nome declarado e esperado
ARG_ROLES = {
    "CharaSpawn": [(0, "QmlChar"), (2, "Dialogue")],
    "CharaSpawn2": [(0, "QmlChar"), (1, "QmlChar"), (3, "Dialogue")],
    "CharaSpawn3": [(0, "QmlChar"), (1, "QmlChar"), (2, "QmlChar"), (4, "Dialogue")],
    "PlayDialogue": [(0, "Dialogue")],
    "DialogueFinish": [(0, "Dialogue")],
    "CheckFlag": [(0, "Flag")],
    "SetFlag": [(0, "Flag")],
    "Ko": [(0, "QmlChar")],
    "Health": [(1, "QmlChar")],
    "InStage": [(0, "QmlChar")],
    "LoadChara": [(0, "QmlChar")],
    "DontRemoveOnKo": [(0, "QmlChar")],
    "DontAutoRemoveOnKo": [(0, "QmlChar")],
    "CharaLeave": [(0, "QmlChar"), (2, "Dialogue")],
    "Revive": [(0, "QmlChar"), (1, "Dialogue")],
    "ReviveEx": [(0, "QmlChar"), (1, "Dialogue")],
    "PlayScene": [(0, "QmlChar")],
    "SetStat": [(0, "QmlChar")],
    "Unk61": [(0, "QmlChar")],
    "Unk63": [(0, "QmlChar")],
    "Unk64": [(0, "QmlChar")],
    "Unk73": [(0, "QmlChar")],
    "HealthCap": [(1, "QmlChar")],
    "EnableMovement": [(1, "QmlChar")],
}
STAGE_ARG = {"CharaSpawn": 4, "CharaSpawn2": 4, "CharaSpawn3": 5, "PortalControl": None}
POS_ARG = {"CharaSpawn": 1, "CharaSpawn2": 2, "CharaSpawn3": 3}


def _shallow(body: str) -> str:
    """Apaga o conteudo dos blocos ``{...}`` aninhados, preservando as quebras de linha.

    Assim da para olhar so os campos do nivel atual (os campos de um
    ``DialoguePart`` pertencem ao ``DialoguePart``, nao ao ``Dialogue`` pai).
    """
    res: list[str] = []
    depth = 0
    in_str = esc = False
    for ch in body:
        keep = depth == 0
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            res.append(ch if keep else (" " if ch != "\n" else "\n"))
            continue
        if ch == '"':
            in_str = True
            res.append(ch if keep else " ")
        elif ch == "{":
            depth += 1
            res.append(" ")
        elif ch == "}":
            depth = max(0, depth - 1)
            res.append(" ")
        else:
            res.append(ch if keep else (" " if ch != "\n" else "\n"))
    return "".join(res)


class Linter:
    def __init__(self, ref: dict, qdir: str, allow_existing_id: bool = False) -> None:
        self.ref = ref
        self.qdir = qdir
        self.allow_existing_id = allow_existing_id
        self.errors: list[str] = []
        self.warns: list[str] = []
        self.declared: dict[str, str] = {}   # nome MINUSCULO -> tipo de objeto
        # O compilador X2QS NAO diferencia maiuscula/minuscula nos identificadores:
        # "QxdChar Ray" colide com "X2mMod RAY" ("Ray" had already been defined).
        # Por isso a tabela e indexada em minusculo e self.names guarda a grafia.
        self.names: dict[str, str] = {}      # nome minusculo -> grafia original
        self.texts: dict[str, set[str]] = {}  # TextEntry/TextAudioEntry -> idiomas
        self.qml: dict[str, dict] = {}
        self.quest: dict[str, str] = {}
        self.quest_name = ""
        self.positions: list[dict] = []
        self.calls: list[tuple[str, str, list[str], str, int]] = []  # kind, name, args, file, lineno

    # ------------------------------------------------------------------ #
    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warns.append(msg)

    # ------------------------------------------------------------------ #
    def load(self) -> bool:
        ok = True
        for f in REQUIRED_FILES:
            if not os.path.isfile(os.path.join(self.qdir, f)):
                self.err(f"arquivo obrigatorio ausente: {f}")
                ok = False
        if not ok:
            return False
        # O compilador le os arquivos numa ordem fixa (quest, chars, dialogue,
        # positions, script, script1..3) e nao aceita referencia a algo que ainda
        # nao foi definido. O lint precisa ler na mesma ordem, senao ele reclama
        # de coisa que o compilador aceitaria (ex.: X2mMod declarado em quest.x2qs
        # e usado em chars.x2qs).
        present = [f for f in os.listdir(self.qdir) if f.endswith(".x2qs")]
        order = [f for f in REQUIRED_FILES if f in present]
        order += sorted(f for f in present if f not in order)
        self.files = {
            f: open(os.path.join(self.qdir, f), encoding="utf-8", errors="replace").read()
            for f in order
        }
        for f, raw in self.files.items():
            self._syntax(raw, f)
        return not self.errors

    # ------------------------------------------------------------------ #
    def _syntax(self, raw: str, fname: str) -> None:
        text = raw.replace("\r\n", "\n").replace("\r", "\n")
        # aspas balanceadas por linha (strings nao atravessam linha neste formato)
        for n, line in enumerate(text.split("\n"), 1):
            body = strip_comments(line)
            if body.count('"') % 2:
                self.err(f"{fname}:{n}: aspas desbalanceadas -> {line.strip()[:80]}")
            if re.search(r'"[^"]*\\[^nrt"\\][^"]*"', body):
                self.warn(f"{fname}:{n}: sequencia de escape incomum dentro de string")
        # chaves balanceadas no arquivo inteiro
        stripped = strip_comments(text)
        depth, line = 0, 1
        for ch in stripped:
            if ch == "\n":
                line += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    self.err(f"{fname}:{line}: '}}' sobrando (chaves desbalanceadas)")
                    depth = 0
        if depth:
            self.err(f"{fname}: faltam {depth} '}}' para fechar os blocos")

    # ------------------------------------------------------------------ #
    def collect(self) -> None:
        for fname, raw in self.files.items():
            text = strip_comments(raw.replace("\r\n", "\n").replace("\r", "\n"))
            self._collect_objects(text, fname)
            self._collect_calls(text, fname)

    def _collect_objects(self, text: str, fname: str) -> None:
        for m in TOP_DECL_RE.finditer(text):
            typ, name, parent = m.group(1), m.group(2), m.group(3)
            start = m.end() - 1
            end = match_brace(text, start)
            body = text[start + 1 : end] if end > 0 else ""
            line = text.count("\n", 0, m.start()) + 1

            if typ in ("Script",):
                continue
            if name is None:
                self.err(f"{fname}:{line}: bloco '{typ}' sem nome")
                continue

            known = self.ref["object_types"]
            if typ not in known and typ not in ("Flag", "StringVar", "X2mMod"):
                self.err(f"{fname}:{line}: tipo de objeto desconhecido '{typ}'")

            if typ == "Flag":
                # "Flag Flag0" nao tem corpo; tratado abaixo
                continue
            if name.lower() in self.declared:
                self.err(
                    f"{fname}:{line}: identificador duplicado '{name}' "
                    f"(o compilador ignora maiuscula/minuscula; ja existe "
                    f"'{self.names[name.lower()]}' como {self.declared[name.lower()]})"
                )
            self.declared[name.lower()] = typ
            self.names[name.lower()] = name

            if typ == "Quest":
                self.quest_name = name
                self._check_quest(body, fname, line)
            elif typ in ("QmlChar",):
                self._check_qml(name, parent, body, fname, line)
            elif typ in ("QxdChar", "QxdSpecialChar"):
                self._check_qxd(name, body, fname, line)
            elif typ in ("TextEntry", "TextAudioEntry"):
                langs = set(re.findall(rf"^\s*({'|'.join(self.ref['langs'])})\s*:", body, re.M))
                for bad in re.findall(r"^\s*([a-z]{2,3})\s*:", body, re.M):
                    if bad not in self.ref["langs"] and bad != "voice":
                        self.err(f"{fname}:{line}: idioma de texto invalido '{bad}' em {name}")
                if not langs:
                    self.err(f"{fname}:{line}: {name} nao tem nenhum texto (esperado 'en:')")
                self.texts[name] = langs
            elif typ == "CharPosition":
                self._check_position(body, fname, line)
            elif typ == "Dialogue":
                self._check_dialogue(body, fname, line)

            # campos conhecidos (so os do proprio nivel: blocos aninhados tem o seu tipo)
            allowed = self.ref["fields_by_type"].get(typ)
            if allowed:
                # TextEntry/TextAudioEntry aceitam uma chave por idioma; os dumps
                # multilíngues ficam fora da pasta de quest, entao a lista de
                # campos extraida do corpus so mostra 'en'.
                if typ in ("TextEntry", "TextAudioEntry"):
                    allowed = set(allowed) | set(self.ref["langs"])
                for fm in re.finditer(rf"^\s*({IDENT})\s*:", _shallow(body), re.M):
                    if fm.group(1) not in allowed:
                        self.err(f"{fname}:{line}: campo '{fm.group(1)}' nao existe em {typ} ({name})")

        # Flags: "Flag FlagN"
        for m in re.finditer(rf"^Flag\s+({IDENT})\s*$", text, re.M):
            if m.group(1).lower() in self.declared:
                self.err(f"{fname}: Flag duplicada '{m.group(1)}'")
            self.declared[m.group(1).lower()] = "Flag"
            self.names.setdefault(m.group(1).lower(), m.group(1))
        for m in re.finditer(rf"^StringVar\s+({IDENT})\s*$", text, re.M):
            self.declared.setdefault(m.group(1).lower(), "StringVar")
            self.names.setdefault(m.group(1).lower(), m.group(1))

    # ------------------------------------------------------------------ #
    def _check_quest(self, body: str, fname: str, line: int) -> None:
        for key in ("title", "success", "failure", "outline", "warning", "ex_success"):
            m = re.search(rf"^\s*{key}\s*:\s*(\S+)", body, re.M)
            if not m:
                # warning/ex_success nao existem em expert missions (HLQ)
                (self.warn if key in ("warning", "ex_success") else self.err)(
                    f"{fname}:{line}: Quest sem campo '{key}'"
                )
                continue
            val = m.group(1)
            if val.startswith('"'):
                self.warn(f"{fname}:{line}: Quest.{key} usa id vanilla {val} em vez de TextEntry propria")
            elif val.lower() not in self.declared:
                self.err(f"{fname}:{line}: Quest.{key} aponta para '{val}', que nao foi declarado")
        m = re.search(r'^\s*start_stage\s*:\s*"([^"]+)"', body, re.M)
        if m:
            self.quest["start_stage"] = m.group(1)
            if m.group(1) not in self.ref["stage_names"]:
                self.err(f"{fname}:{line}: estagio desconhecido '{m.group(1)}'")
        m = re.search(r"^\s*stages\s*:\s*\(([^)]*)\)", body, re.M)
        if m:
            for s in re.findall(r'"([^"]+)"', m.group(1)):
                if s not in self.ref["stage_names"]:
                    self.err(f"{fname}:{line}: estagio desconhecido em stages: '{s}'")
        for m in re.finditer(r"ItemReward\s*\{[^}]*\}", body):
            blk = m.group(0)
            it = re.search(r"item:\s*(\S+)", blk)
            if it and it.group(1).lstrip("-").isdigit():
                pass  # id numerico de item
            elif it and it.group(1).lower() not in self.declared:
                self.err(f"{fname}:{line}: ItemReward referencia ItemCollection '{it.group(1)}' inexistente")
            for t in re.findall(r"type:\s*([A-Z0-9]+)", blk):
                if t not in self.ref["reward_types"] and t not in ("COLLECTION",):
                    self.err(f"{fname}:{line}: tipo de reward desconhecido '{t}'")
        for m in re.finditer(r"SkillReward\s*\{\s*skill:\s*(\d+)", body):
            self._check_skill(m.group(1), fname, line)
        for m in re.finditer(r'CharReward\s*\{\s*char:\s*"([^"]+)"\s+costume:\s*(-?\d+)', body):
            self._check_char(m.group(1), fname, line)
        for m in re.finditer(r'CharPortrait\s*\{\s*char:\s*"?([A-Za-z0-9\-]+)"?\s+costume:\s*(-?\d+)', body):
            if m.group(1) != "-1":
                self._check_char(m.group(1), fname, line)
        for key in ("episode", "num_players", "time_limit", "difficulty", "level"):
            if not re.search(rf"^\s*{key}\s*:", body, re.M):
                self.err(f"{fname}:{line}: Quest sem campo '{key}'")

    # ------------------------------------------------------------------ #
    def _check_qxd(self, name: str, body: str, fname: str, line: int) -> None:
        m = re.search(r'char:\s*"?([A-Za-z0-9_\-]+)"?', body)
        if not m:
            self.err(f"{fname}:{line}: {name} sem campo 'char'")
        else:
            self._check_char(m.group(1), fname, line)
        for f in re.finditer(r"(super[1-4]|ultimate[12]|evasive|blast|awaken)\s*:\s*(\d+)", body):
            self._check_skill(f.group(2), fname, line)
        if re.search(r"^\s*costume:\s*(\d+)", body, re.M):
            pass

    def _check_char(self, code: str, fname: str, line: int) -> None:
        if code.lstrip("-").isdigit():
            return  # vanilla aceita id numerico de personagem em rewards/portraits
        if self.declared.get(code.lower()) == "X2mMod":
            return  # personagem vindo de um mod .x2m (char: NomeDoX2mMod)
        if code not in self.ref["char_codes"]:
            self.err(f"{fname}:{line}: codigo de personagem desconhecido '{code}'")

    def _check_skill(self, sid: str, fname: str, line: int) -> None:
        # a lista de skills vem dos comentarios dos quests vanilla, entao ela e
        # incompleta: id fora da lista e aviso, nao erro.
        if self.declared.get(sid.lower()) == "X2mMod":
            return  # skill customizada de um mod .x2m
        if sid not in self.ref["skill_ids"]:
            self.warn(f"{fname}:{line}: id de skill '{sid}' nao aparece em nenhuma quest vanilla")

    # ------------------------------------------------------------------ #
    def _check_qml(self, name: str, parent: str | None, body: str, fname: str, line: int) -> None:
        info: dict[str, object] = {"line": line, "file": fname}
        if not parent:
            self.err(f"{fname}:{line}: QmlChar {name} sem pai (esperado 'QmlChar X : Y')")
        m = re.search(r"battle_index:\s*(-?\d+)", body)
        info["battle_index"] = int(m.group(1)) if m else None
        if info["battle_index"] is None:
            self.err(f"{fname}:{line}: QmlChar {name} sem battle_index")
        elif not (-1 <= int(info["battle_index"]) <= 7):
            self.err(f"{fname}:{line}: QmlChar {name} com battle_index {info['battle_index']} fora de faixa")
        elif int(info["battle_index"]) > 6:
            self.warn(f"{fname}:{line}: {name} usa battle_index {info['battle_index']}; o jogo so carrega 7 de uma vez (0-6)")
        m = re.search(r'stage:\s*"([^"]+)"', body)
        info["stage"] = m.group(1) if m else None
        info["spawn_at_start"] = bool(re.search(r"spawn_at_start:\s*true", body))
        m = re.search(r"ai:\s*([A-Za-z_]+)", body)
        info["ai"] = m.group(1) if m else None
        for f in re.finditer(r"(super[1-4]|ultimate[12]|evasive|blast|awaken)\s*:\s*(\d+)", body):
            self._check_skill(f.group(2), fname, line)
        self.qml[name] = info

    # ------------------------------------------------------------------ #
    def _check_position(self, body: str, fname: str, line: int) -> None:
        char = re.search(r"char:\s*([A-Za-z0-9_]+)", body)
        stage = re.search(r'stage:\s*"([^"]+)"', body)
        pos = re.search(r'position:\s*"([^"]+)"', body)
        rec = {
            "line": line,
            "char": char.group(1) if char else None,
            "stage": stage.group(1) if stage else None,
            "position": pos.group(1) if pos else None,
        }
        self.positions.append(rec)
        if rec["stage"] and rec["stage"] not in self.ref["stage_names"]:
            self.err(f"{fname}:{line}: estagio desconhecido '{rec['stage']}'")
        if rec["stage"] and rec["position"]:
            known = self.ref["stage_positions"].get(rec["stage"], [])
            if rec["position"] not in known:
                self.err(
                    f"{fname}:{line}: posicao '{rec['position']}' nao existe no estagio "
                    f"'{rec['stage']}' (disponiveis: {', '.join(known[:6])}...)"
                )

    # ------------------------------------------------------------------ #
    def _check_dialogue(self, body: str, fname: str, line: int) -> None:
        parts = re.findall(r"DialoguePart\s*\{(.*?)\n\s*\}", body, re.S)
        if not parts:
            # existe em quests vanilla como marcador vazio, entao e so aviso
            self.warn(f"{fname}:{line}: Dialogue sem nenhum DialoguePart")
        for p in parts:
            ta = re.search(r"text_audio:\s*(\S+)", p)
            if not ta:
                self.err(f"{fname}:{line}: DialoguePart sem text_audio")
                continue
            val = ta.group(1)
            if val.startswith('"'):
                self.warn(f"{fname}:{line}: text_audio usa id vanilla {val} (nao ha .msg customizado)")
            elif val.lower() not in self.declared:
                self.err(f"{fname}:{line}: text_audio '{val}' nao foi declarado")
            actor = re.search(r'actor:\s*"([^"]+)"', p)
            if actor:
                self._check_char(actor.group(1), fname, line)

    # ------------------------------------------------------------------ #
    def _collect_calls(self, text: str, fname: str) -> None:
        for m in re.finditer(r"\b(Action|Condition)\s+([^\n]*)", text):
            kind, rest = m.group(1), m.group(2).strip()
            line = text.count("\n", 0, m.start()) + 1
            call = CALL_RE.match(rest)
            if call:
                name = call.group(1)
                close = self._close_paren(rest, call.end() - 1)
                if close < 0:
                    self.err(f"{fname}:{line}: parenteses nao fechados em {kind} {name}")
                    continue
                args = split_args(rest[call.end() : close]) if rest[call.end() : close].strip() else []
            else:
                name = rest.rstrip(";").strip()
                if not re.fullmatch(IDENT, name):
                    self.err(f"{fname}:{line}: {kind} malformado -> '{rest[:60]}'")
                    continue
                args = []
            self.calls.append((kind, name, args, fname, line))

    @staticmethod
    def _close_paren(text: str, i: int) -> int:
        depth, in_str, esc = 0, False, False
        for j in range(i, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return j
        return -1

    # ------------------------------------------------------------------ #
    def check_calls(self) -> None:
        table = {"Action": self.ref["actions"], "Condition": self.ref["conditions"]}
        for kind, name, args, fname, line in self.calls:
            known = table[kind]
            if name not in known:
                self.err(f"{fname}:{line}: {kind} desconhecido '{name}'")
                continue
            arities = known[name]
            if len(args) not in arities:
                self.err(
                    f"{fname}:{line}: {kind} {name} recebeu {len(args)} argumentos "
                    f"(o jogo aceita {arities})"
                )
            for idx, role in ARG_ROLES.get(name, []):
                if idx < len(args):
                    self._check_role(args[idx], role, fname, line, name)
            if name in STAGE_ARG and STAGE_ARG[name] is not None:
                i = STAGE_ARG[name]
                if i < len(args):
                    st = args[i].strip().strip('"')
                    if st.startswith('"') and st not in self.ref["stage_names"]:
                        self.err(f"{fname}:{line}: estagio desconhecido {st} em {name}")
            if name in POS_ARG:
                i = POS_ARG[name]
                stage_i = STAGE_ARG[name]
                if i < len(args) and stage_i < len(args):
                    pos = args[i].strip()
                    st = args[stage_i].strip().strip('"')
                    if pos.lstrip("-").isdigit():
                        ok = self.ref["spawn_positions"].get(st, [])
                        if ok and int(pos) not in ok:
                            self.err(
                                f"{fname}:{line}: {name} usa TRESPASS_{pos} no estagio '{st}', "
                                f"que so tem {ok} atestados"
                            )
            for a in args:
                self._check_bare_ident(a, fname, line)

    def _check_role(self, arg: str, role: str, fname: str, line: int, fn: str) -> None:
        a = arg.strip()
        if a.startswith('"') or a.lstrip("-").isdigit() or a in ("-1",):
            return
        if not re.fullmatch(IDENT, a):
            return
        got = self.declared.get(a.lower())
        if got is None:
            self.err(f"{fname}:{line}: {fn}() referencia '{a}', que nao foi declarado")
        elif got != role:
            self.err(f"{fname}:{line}: {fn}() espera um {role} no lugar de '{a}' (que e um {got})")

    def _check_bare_ident(self, arg: str, fname: str, line: int) -> None:
        a = arg.strip()
        if not re.fullmatch(IDENT, a):
            return
        if a in LITERAL_WORDS or a in self.ref["constants"] or a in OPERATORS:
            return
        if a.lower() not in self.declared:
            self.err(f"{fname}:{line}: identificador '{a}' nao declarado em lugar nenhum")

    # ------------------------------------------------------------------ #
    def cross_checks(self) -> None:
        if self.quest_name:
            if self.quest_name in self.ref["quest_ids"] and not self.allow_existing_id:
                self.err(f"o id '{self.quest_name}' ja existe em uma quest vanilla (troque o id)")
            if not re.match(r"^(TMQ|HLQ)_", self.quest_name):
                self.warn(f"id '{self.quest_name}' nao comeca com TMQ_/HLQ_ (so esses viram PQ/EM)")
        start = self.quest.get("start_stage")
        for name, info in self.qml.items():
            if info.get("spawn_at_start") and start and info.get("stage") != start:
                msg = (
                    f"{info['file']}:{info['line']}: {name} tem spawn_at_start: true em "
                    f"'{info['stage']}' mas o start_stage da quest e '{start}'"
                )
                # para o jogador isso quebra o CharaSpawn; para NPC e usado em
                # quests de varios estagios (eles entram por portal)
                # vanilla faz isso em quests multi-estagio (entra por portal),
                # entao fica como aviso - mas confira se e o seu caso.
                self.warn(msg)
            if info.get("spawn_at_start"):
                if not any(p["char"] == name for p in self.positions):
                    self.warn(f"{name} tem spawn_at_start: true mas nao tem CharPosition")
        # battle_index: alerta quando o mesmo indice e usado por personagens vivos ao mesmo tempo
        by_idx: dict[int, list[str]] = {}
        for name, info in self.qml.items():
            bi = info.get("battle_index")
            if isinstance(bi, int) and bi >= 0:
                by_idx.setdefault(bi, []).append(name)
        for bi, names in sorted(by_idx.items()):
            if len(names) > 1:
                self.warn(
                    f"battle_index {bi} compartilhado por {', '.join(names)} "
                    f"(ok se eles nunca estao em campo ao mesmo tempo)"
                )
        # dialogue nao usada
        used = {a.strip() for _, _, args, _, _ in self.calls for a in args}
        for p in self.positions:
            pass
        for name, typ in self.declared.items():
            if typ == "Dialogue" and self.names.get(name, name) not in used:
                self.warn(f"Dialogue {self.names.get(name, name)} nunca e tocada pelo script")

    # ------------------------------------------------------------------ #
    def run(self) -> int:
        if not self.load():
            self._report()
            return 1
        self.collect()
        self.check_calls()
        self.cross_checks()
        return self._report()

    def _report(self) -> int:
        name = os.path.basename(os.path.normpath(self.qdir)) or self.qdir
        for w in self.warns:
            print(f"  AVISO  {w}")
        for e in self.errors:
            print(f"  ERRO   {e}")
        if self.errors:
            print(f"\n[lint] {name}: {len(self.errors)} erro(s), {len(self.warns)} aviso(s)")
            return 1
        n_files = len(getattr(self, "files", {}))
        n_calls = len(self.calls)
        print(
            f"[lint] {name}: OK - {n_files} arquivos, {len(self.declared)} identificadores, "
            f"{n_calls} Action/Condition validados, {len(self.warns)} aviso(s)"
        )
        return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("quest", nargs="+", help="pasta(s) de quest X2QS a validar")
    ap.add_argument("--ref", default=REF_PATH, help="arquivo x2qs_reference.json")
    ap.add_argument(
        "--allow-existing-id",
        action="store_true",
        help="nao reclama se o id da quest for o de uma quest vanilla (usado no auto-teste)",
    )
    ap.add_argument("--quiet", action="store_true", help="nao imprime avisos")
    args = ap.parse_args(argv)

    ref = json.load(open(args.ref, encoding="utf-8"))
    rc = 0
    for q in args.quest:
        lint = Linter(ref, q, allow_existing_id=args.allow_existing_id)
        if args.quiet:
            lint.warn = lambda msg: None  # type: ignore[assignment]
        r = lint.run()
        rc |= r
    return rc


if __name__ == "__main__":
    sys.exit(main())
