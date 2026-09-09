#!/usr/bin/env python3
"""
build_x2m.py
============
Empacota uma pasta de quest X2QS num arquivo ``.x2m`` instalavel pelo
**XV2 Mods Installer** (o mesmo formato do mod de exemplo que mora na raiz
deste repositorio).

Um ``.x2m`` e apenas um ZIP com:

    x2m.xml              <- manifesto (nome, autor, versao, GUID)
    QUEST/quest.x2qs
    QUEST/chars.x2qs
    QUEST/dialogue.x2qs
    QUEST/positions.x2qs
    QUEST/script.x2qs
    QUEST/script1.x2qs   (opcional)
    AUDIO/*.hca          (opcional, se houver dublagem propria)

Uso
---
    python3 tools/build_x2m.py quests/TMQ_URA_01 \
        --name "Nao Coma o Uranio!" --author "Voce" --version 1.0 \
        -o "dist/Nao Coma o Uranio.x2m"

Por padrao ele roda o ``x2qs_lint.py`` antes e se recusa a empacotar se houver
erro (``--force`` ignora).

Observacao: o caminho "oficial" e abrir a pasta no **XV2 Quest Creator** e
salvar por la. Este script gera o mesmo layout de arquivo, o que e pratico para
versionar a quest em texto; se o seu instalador reclamar do manifesto, re-salve
pelo Quest Creator.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
QUEST_FILES = [
    "quest.x2qs",
    "chars.x2qs",
    "dialogue.x2qs",
    "positions.x2qs",
    "script.x2qs",
    "script1.x2qs",
    "script2.x2qs",
    "script3.x2qs",
]

MANIFEST = """<?xml version="1.0" encoding="utf-8" ?>
<X2M type="NEW_QUEST">
    <X2M_FORMAT_VERSION value="26.0" />
    <MOD_NAME value="{name}" />
    <MOD_AUTHOR value="{author}" />
    <MOD_VERSION value="{version}" />
    <MOD_GUID value="{guid}" />
    <UDATA value="" />
</X2M>
"""
# O XV2 Mods Installer escreve/mods oficiais trazem um <UDATA> (blob base64 com
# metadados do instalador). Ele vai vazio aqui: o preenchimento e feito pelo
# proprio installer. O que nao pode e o elemento faltar - foi o que quebrou a
# primeira versao do .x2m da TMQ_URA_01.


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build(qdir: str, name: str, author: str, version: str, out: str, guid: str | None = None) -> list[str]:
    written: list[str] = []
    manifest = MANIFEST.format(
        name=xml_escape(name),
        author=xml_escape(author),
        version=xml_escape(version),
        guid=guid or str(uuid.uuid4()),
    )
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("x2m.xml", manifest)
        written.append("x2m.xml")
        for fname in QUEST_FILES:
            path = os.path.join(qdir, fname)
            if os.path.isfile(path):
                zf.write(path, f"QUEST/{fname}")
                written.append(f"QUEST/{fname}")
        audio = os.path.join(qdir, "AUDIO")
        if os.path.isdir(audio):
            for fname in sorted(os.listdir(audio)):
                if fname.lower().endswith(".hca"):
                    zf.write(os.path.join(audio, fname), f"AUDIO/{fname}")
                    written.append(f"AUDIO/{fname}")
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("quest", help="pasta com os .x2qs")
    ap.add_argument("--name", required=True, help="nome do mod mostrado no instalador")
    ap.add_argument("--author", default="", help="autor do mod")
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--guid", default=None, help="GUID fixo (default: gera um novo)")
    ap.add_argument("-o", "--output", required=True, help="arquivo .x2m de saida")
    ap.add_argument("--force", action="store_true", help="empacota mesmo com erro no lint")
    args = ap.parse_args(argv)

    if not args.force:
        rc = subprocess.call([sys.executable, os.path.join(HERE, "x2qs_lint.py"), args.quest])
        if rc != 0:
            print("\n[build] lint reprovou a quest - corrija os erros ou use --force")
            return rc

    written = build(args.quest, args.name, args.author, args.version, args.output, args.guid)
    size = os.path.getsize(args.output)
    print(f"\n[build] {args.output} ({size} bytes)")
    for w in written:
        print(f"          + {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
