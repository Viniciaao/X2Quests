#!/usr/bin/env python3
"""
gen_reference.py
================
Gera ``tools/x2qs_reference.json``, a base de dados usada pelo ``x2qs_lint.py``.

Tudo o que o linter cobra (nomes de Action/Condition e sua aridade, tipos de
objeto, campos validos por tipo, codigos de personagem, codigos/nomes de
estagio, posicoes que existem em cada estagio, ids de skill, ids de quest
existentes, idiomas de texto...) e extraido de um corpus de quests X2QS que ja
sabemos ser validos:

* os quests vanilla descompilados (pasta ``Quest`` que vem dentro do
  ``Vanilla quests.rar`` deste repositorio);
* opcionalmente, outras pastas de quest X2QS (``--extra``), como um mod .x2m
  ja descompactado.

Uso
---
    # 1) extrair o corpus (o unrar nao costuma vir instalado)
    unrar x "Vanilla quests.rar" /tmp/van/

    # 2) gerar a referencia
    python3 tools/gen_reference.py \
        --corpus "/tmp/van/Vanilla quests/Quest" \
        --dialogue "/tmp/van/Vanilla quests/Dialogue" \
        --extra "/tmp/mod/QUEST"
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
# "Type Name {" / "Type Name : Parent {" / "Type {"  (a chave pode vir na linha seguinte)
TOP_DECL_RE = re.compile(rf"^({IDENT})(?:\s+({IDENT}))?\s*(?::\s*({IDENT}))?\s*\{{", re.M)
SUB_DECL_RE = re.compile(rf"({IDENT})\s*\{{")
FIELD_RE = re.compile(rf"({IDENT})\s*:")
CALL_RE = re.compile(rf"({IDENT})\s*\(", re.S)
LANG_RE = re.compile(r"\n\t(en|es|ca|fr|de|it|pt|pl|ru|tw|zh|kr|ja)\s*:")


# --------------------------------------------------------------------------- #
# texto
# --------------------------------------------------------------------------- #
def strip_comments(text: str) -> str:
    """Remove comentarios ``;`` respeitando strings entre aspas.

    O codigo que vem *antes* do ``;`` na mesma linha e preservado.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    in_str = in_com = esc = False
    for ch in text:
        if in_com:
            if ch == "\n":
                in_com = False
                out.append(ch)
            continue
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
        elif ch == ";":
            in_com = True
        else:
            out.append(ch)
    return "".join(out)


def split_args(argstr: str) -> list[str]:
    """Divide argumentos pela virgula mais externa (respeita parenteses/aspas)."""
    args, depth, in_str, esc, cur = [], 0, False, False, []
    for ch in argstr:
        if in_str:
            cur.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        args.append(tail)
    return args


def match_brace(text: str, open_idx: int) -> int:
    """Dado o indice de '{', devolve o indice do '}' que o fecha."""
    depth, in_str, esc = 0, False, False
    for i in range(open_idx, len(text)):
        ch = text[i]
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
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


# --------------------------------------------------------------------------- #
# referencia
# --------------------------------------------------------------------------- #
class Reference:
    def __init__(self) -> None:
        self.object_types: set[str] = set()
        self.fields_by_type: dict[str, set[str]] = defaultdict(set)
        self.actions: dict[str, set[int]] = defaultdict(set)
        self.conditions: dict[str, set[int]] = defaultdict(set)
        self.char_codes: set[str] = set()
        self.char_names: dict[str, str] = {}
        self.stage_names: dict[str, str] = {}
        self.stage_positions: dict[str, set[str]] = defaultdict(set)
        self.spawn_positions: dict[str, set[int]] = defaultdict(set)
        self.skill_ids: dict[str, str] = {}
        self.quest_ids: set[str] = set()
        self.reward_types: set[str] = set()
        self.langs: set[str] = set()
        self.constants: set[str] = set()

    # ------------------------------------------------------------------ #
    def scan_quest_dir(self, qdir: str) -> None:
        for path in sorted(glob.glob(os.path.join(qdir, "*.x2qs"))):
            raw = open(path, encoding="utf-8", errors="replace").read()
            self._scan_named(raw)
            self._scan_blocks(strip_comments(raw))

    def _scan_named(self, raw: str) -> None:
        """Informacao que so existe nos comentarios (nomes legiveis)."""
        for m in re.finditer(r'\n\s*;\s*([^\n\r;]+?)\s*\n\s*char:\s*"([A-Za-z0-9]{2,4})"', raw):
            self.char_names.setdefault(m.group(2), m.group(1).strip())
        for m in re.finditer(
            r"(?:super[1-4]|ultimate[12]|evasive|blast|awaken|skill):\s*(\d+)\s*;\s*([^\n\r]+)", raw
        ):
            self.skill_ids.setdefault(m.group(1), m.group(2).strip())
        for m in re.finditer(r'stage:\s*"([A-Za-z0-9]+)"\s*;\s*([A-Za-z][^\n\r]*)', raw):
            self.stage_names.setdefault(m.group(1), m.group(2).strip())
        for m in re.finditer(r'"([A-Za-z0-9]{4,10})"\s*;\s*([A-Za-z][^\n\r]*?)\s*->', raw):
            self.stage_names.setdefault(m.group(1), m.group(2).strip())
        for m in re.finditer(r"\n\t(en|es|ca|fr|de|it|pt|pl|ru|tw|zh|kr|ja)\s*:", raw):
            self.langs.add(m.group(1))

    # ------------------------------------------------------------------ #
    def _scan_blocks(self, text: str) -> None:
        for m in TOP_DECL_RE.finditer(text):
            typ, name = m.group(1), m.group(2)
            start = m.end() - 1
            end = match_brace(text, start)
            if end < 0:
                continue
            body = text[start + 1 : end]
            self.object_types.add(typ)
            if typ == "Quest":
                self.quest_ids.add(name)
            self._walk(typ, body)

    def _walk(self, typ: str, body: str) -> None:
        """Registra campos de ``typ`` e desce nos sub-objetos inline."""
        pos = 0
        while pos < len(body):
            sub = SUB_DECL_RE.search(body, pos)
            field = FIELD_RE.search(body, pos)
            if sub is None and field is None:
                break
            # o que vem primeiro?
            if field is not None and (sub is None or field.start() < sub.start()):
                self.fields_by_type[typ].add(field.group(1))
                pos = field.end()
                continue
            styp = sub.group(1)
            sstart = sub.end() - 1
            send = match_brace(body, sstart)
            if send < 0:
                pos = sub.end()
                continue
            self.object_types.add(styp)
            sbody = body[sstart + 1 : send]
            for f in FIELD_RE.finditer(sbody):
                self.fields_by_type[styp].add(f.group(1))
            # campos inline do proprio sub-objeto
            pos = send + 1
        # recompensa / tipo
        for m in re.finditer(r"type:\s*([A-Z][A-Z0-9]*)", body):
            self.reward_types.add(m.group(1))
        # codigos de personagem
        for m in re.finditer(r'char:\s*"([A-Za-z0-9]{2,4})"', body):
            self.char_codes.add(m.group(1))
        # posicoes nomeadas por estagio
        for m in re.finditer(r'stage:\s*"([A-Za-z0-9]+)"(.*?)(?:\n\s*\}|\Z)', body, re.S):
            stage = m.group(1)
            for p in re.finditer(r'position:\s*"([^"]+)"', m.group(2)):
                self.stage_positions[stage].add(p.group(1))
        # codigos de estagio (com ou sem comentario com o nome legivel)
        for m in re.finditer(r'stage:\s*"([A-Za-z0-9]+)"', body):
            self.stage_names.setdefault(m.group(1), "")
        for m in re.finditer(r"stages:\s*\(([^)]*)\)", body):
            for st in re.findall(r'"([^"]+)"', m.group(1)):
                self.stage_names.setdefault(st, "")
        # constantes conhecidas
        for c in re.findall(
            r"\b(HEALTH|KI|STAMINA|ALL|COMPLETE|FAIL|ULTIMATE_FINISH|NORMAL|HUMAN|DEFAULT|"
            r"WHITE|BLACK|NONBG|SUPER[1-4]|ULTIMATE[12]|EVASIVE|BLAST|AWAKEN|MATERIAL|"
            r"COLLECTION|SUPERSOUL|ACCESSORY|ILLUSTRATION|TOP|BOTTOM|SHOES|GLOVES|BATTLE)\b",
            body,
        ):
            self.constants.add(c)
        # actions/conditions
        for m in re.finditer(r"\b(Action|Condition)\s+([^\n]*)", body):
            self._record_call(m.group(1), m.group(2))

    # ------------------------------------------------------------------ #
    def _record_call(self, kind: str, rest: str) -> None:
        rest = rest.strip()
        call = CALL_RE.match(rest)
        if call:
            name = call.group(1)
            close = self._close_paren(rest, call.end() - 1)
            if close < 0:
                return
            inner = rest[call.end() : close]
            args = split_args(inner) if inner.strip() else []
            nargs = len(args)
        else:
            name = rest.rstrip(";").strip()
            if not re.fullmatch(IDENT, name):
                return
            nargs = 0
            args = []
        bucket = self.actions if kind == "Action" else self.conditions
        bucket[name].add(nargs)
        for a in args:
            a = a.strip()
            if re.fullmatch(r"[A-Z][A-Z0-9_]*(?:\|[A-Z][A-Z0-9_]*)*", a):
                for part in a.split("|"):
                    self.constants.add(part)
        self._collect_spawn_positions(name, rest)

    @staticmethod
    def _close_paren(text: str, open_idx: int) -> int:
        depth, in_str, esc = 0, False, False
        for i in range(open_idx, len(text)):
            ch = text[i]
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
                    return i
        return -1

    def _collect_spawn_positions(self, name: str, rest: str) -> None:
        if name not in ("CharaSpawn", "CharaSpawn2", "CharaSpawn3"):
            return
        call = CALL_RE.match(rest)
        if not call:
            return
        close = self._close_paren(rest, call.end() - 1)
        if close < 0:
            return
        args = split_args(rest[call.end() : close])
        pos = stage = None
        # layout confirmado nos quests vanilla:
        #   CharaSpawn (char, pos, dialogue, scene, stage, unk)
        #   CharaSpawn2(c1, c2, pos, dialogue, stage, unk, unk, unk)
        #   CharaSpawn3(c1, c2, c3, pos, dialogue, stage, unk, unk)
        if name == "CharaSpawn" and len(args) >= 5:
            pos, stage = args[1], args[4]
        elif name == "CharaSpawn2" and len(args) >= 5:
            pos, stage = args[2], args[4]
        elif name == "CharaSpawn3" and len(args) >= 6:
            pos, stage = args[3], args[5]
        if pos is None or stage is None:
            return
        st = stage.strip().strip('"')
        if pos.strip().lstrip("-").isdigit():
            self.spawn_positions[st].add(int(pos.strip()))

    # ------------------------------------------------------------------ #
    def scan_dialogue_dir(self, ddir: str) -> None:
        for path in glob.glob(os.path.join(ddir, "*", "*.txt")):
            raw = open(path, encoding="utf-8", errors="replace").read()
            for m in LANG_RE.finditer(raw):
                self.langs.add(m.group(1))

    # ------------------------------------------------------------------ #
    def to_json(self) -> dict:
        return {
            "object_types": sorted(self.object_types),
            "fields_by_type": {k: sorted(v) for k, v in sorted(self.fields_by_type.items())},
            "actions": {k: sorted(v) for k, v in sorted(self.actions.items())},
            "conditions": {k: sorted(v) for k, v in sorted(self.conditions.items())},
            "char_codes": sorted(self.char_codes),
            "char_names": dict(sorted(self.char_names.items())),
            "stage_names": dict(sorted(self.stage_names.items())),
            "stage_positions": {k: sorted(v) for k, v in sorted(self.stage_positions.items())},
            "spawn_positions": {k: sorted(v) for k, v in sorted(self.spawn_positions.items())},
            "skill_ids": dict(sorted(self.skill_ids.items(), key=lambda kv: int(kv[0]))),
            "quest_ids": sorted(self.quest_ids),
            "reward_types": sorted(self.reward_types),
            "langs": sorted(self.langs),
            "constants": sorted(self.constants),
        }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--corpus", required=True, help="pasta 'Quest' com os quests vanilla descompilados")
    ap.add_argument("--dialogue", help="pasta 'Dialogue' dos dumps de texto (para a lista de idiomas)")
    ap.add_argument("--extra", action="append", default=[], help="pasta extra de quest X2QS")
    ap.add_argument("-o", "--output", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "x2qs_reference.json"))
    args = ap.parse_args(argv)

    ref = Reference()
    n = 0
    for fam in sorted(os.listdir(args.corpus)):
        fdir = os.path.join(args.corpus, fam)
        if not os.path.isdir(fdir):
            continue
        for quest in sorted(os.listdir(fdir)):
            qdir = os.path.join(fdir, quest)
            if os.path.isdir(qdir):
                ref.scan_quest_dir(qdir)
                n += 1
    for extra in args.extra:
        ref.scan_quest_dir(extra)
        n += 1
    if args.dialogue:
        ref.scan_dialogue_dir(args.dialogue)

    data = ref.to_json()
    data["_meta"] = {"quests_scanned": n, "corpus": os.path.basename(args.corpus.rstrip("/"))}
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    print(f"[gen_reference] {n} quests lidos -> {args.output}")
    print(
        f"[gen_reference] {len(data['object_types'])} tipos de objeto | "
        f"{len(data['actions'])} actions | {len(data['conditions'])} conditions | "
        f"{len(data['char_codes'])} codigos de personagem | {len(data['stage_names'])} estagios | "
        f"{len(data['skill_ids'])} skills | idiomas: {','.join(data['langs'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
