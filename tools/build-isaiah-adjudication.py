#!/usr/bin/env python3.11
"""
Build the adjudication files for the transcribed Isaiah blocks, and the variant
register that goes with them.

Where a chapter is a continuous transcription (1 Nephi 20-21 = Isaiah 48-49;
2 Nephi 7-8 = Isaiah 50-51:1-52:2; 2 Nephi 12-24 = Isaiah 2-14), every verse IS
a quotation and the catalogue must say so verse by verse (PLAN.md §5) — but the
ARGUMENT is not in the fact that the verse is quoted, it is in the departures.
So the machine writes the routine part of each note (the departures, in words)
and an adjudicator supplies prose for the verses where the departures mean
something.

The blocks are declared in data/isaiah-blocks.json, which is the manifest for
both this tool and the register. A block may `spill` into the following KJV
chapter, because the Book of Mormon's chapter divisions do not always stop where
the KJV's do: 2 Nephi 8 runs Isaiah 51:1-23 and then Isaiah 52:1-2.

**This tool does not overwrite an existing chapter file.** Authored prose,
bibliography and exclusion cross-references live in those files, and a rebuild
that silently discarded them would cost a chapter pass. Use --force only to
discard the current file deliberately. The register (data/isaiah-collation.json)
is purely mechanical and is always rebuilt in full, from every block.

Usage:
  python3.11 tools/build-isaiah-adjudication.py                 # all blocks
  python3.11 tools/build-isaiah-adjudication.py --slug 2-nephi  # one book
  python3.11 tools/build-isaiah-adjudication.py --slug 2-nephi --ch 12 --force
"""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("collate", ROOT / "tools" / "collate-isaiah.py")
_collate_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_collate_mod)
collate = _collate_mod.collate

FLOOR = 0.55


def kjv_ref_for(block: dict, verse: int, kjv: dict) -> str:
    """The KJV verse this Book of Mormon verse is aligned to, honouring `spill`."""
    base = f"{block['book']} {block['kjvChapter']}:{verse}"
    if base in kjv or "spill" not in block:
        return base
    # The KJV chapter ran out. Continue into the next one from its verse 1.
    n = 1
    while f"{block['book']} {block['kjvChapter']}:{n}" in kjv:
        n += 1
    s = block["spill"]
    return f"{s['book']} {s['chapter']}:{verse - (n - 1)}"


def build(block: dict, kjv: dict, register: list, force: bool) -> tuple[int, int, list]:
    slug, ch = block["slug"], block["ch"]
    bom = json.loads((ROOT / "data" / f"{slug}.json").read_text())
    per = {p["ref"]: p["text"] for p in bom["pericopes"] if p["ch"] == ch}
    out_path = ROOT / "work" / slug / "adjudicated" / f"ch{ch:02d}.json"
    var_path = ROOT / "work" / slug / f"variants-ch{ch}.json"

    links, rows, flagged = {}, [], []
    counters: dict[str, int] = {}
    for ref in sorted(per, key=lambda r: int(r.split(":")[1])):
        v = ref.split(":")[1]
        kref = kjv_ref_for(block, int(v), kjv)
        ktext = kjv.get(kref)
        if ktext is None:
            flagged.append((ref, kref, 0.0, "no KJV counterpart"))
            continue
        ops, ratio = collate(per[ref], ktext)
        if ratio < FLOOR:
            flagged.append((ref, kref, ratio, "below the overlap floor"))
        parts, deps = [], []
        for op in ops:
            counters[v] = counters.get(v, 0) + 1
            row = {"bomRef": f"{bom['name']} {ref}", "kjvRef": kref, **op,
                   "id": f"{slug}-{ch}:{v}-{chr(96 + counters[v])}"}
            deps.append(row)
            rows.append(row)
            register.append(row)
            if op["kind"] == "replace":
                parts.append(f"KJV “{op['kjv']}” → “{op['bom']}”")
            elif op["kind"] == "omit":
                parts.append(f"KJV “{op['kjv']}” omitted")
            else:
                parts.append(f"adds “{op['bom']}”")
        note = (f"{len(deps)} departure(s) from the KJV: " + "; ".join(parts) + "."
                if deps else "Reproduces the KJV verse word for word.")
        links[ref] = [{
            "source": kref,
            "type": "quotation",
            "subtype": "extended",
            "confidence": "certain",
            "text": ktext,
            "evidence": {"vocabulary": 5, "syntax": 5, "sequence": 5,
                         "context": 5, "rarity": 5, "attestation": 5},
            "kjvSpecific": "yes",
            "mediation": "direct-OT",
            "provenance": {
                "route": f"{block['book']} {block['kjvChapter']} → KJV → Book of Mormon",
                "significance": (
                    f"Part of a continuous transcription of {block['book']} "
                    f"{block['kjvChapter']} as {bom['name']} {ch}. The quotation is not the "
                    "finding; the departures are, and they are listed in the note and "
                    "registered individually in data/isaiah-collation.json."),
            },
            "note": note,
            "variants": [d["id"] for d in deps],
            "bibliography": [],
            "status": "consensus",
            "citationsPending": True,
            "streams": ["manual"],
        }]

    var_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    wrote = False
    if force or not out_path.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({
            "chapter": ch,
            "adjudicated": "2026-09-05",
            "adjudicator": "collated mechanically by tools/build-isaiah-adjudication.py",
            "links": links,
        }, indent=2, ensure_ascii=False) + "\n")
        wrote = True
    return len(links), len(rows), flagged, wrote


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="build only this book's blocks")
    ap.add_argument("--ch", type=int, help="build only this chapter (needs --slug)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing chapter file, discarding authored prose")
    args = ap.parse_args()

    blocks = json.loads((ROOT / "data" / "isaiah-blocks.json").read_text())["blocks"]
    kjv = json.loads((ROOT / "text" / "kjv.json").read_text())

    register: list = []
    for block in blocks:
        selected = ((args.slug is None or block["slug"] == args.slug)
                    and (args.ch is None or block["ch"] == args.ch))
        # A deselected block is still collated, because the register is rebuilt whole.
        verses, deps, flagged, wrote = build(block, kjv, register, args.force and selected)
        if selected:
            state = "written" if wrote else "kept (authored; --force to rebuild)"
            print(f"{block['slug']} {block['ch']} ~ {block['book']} {block['kjvChapter']}: "
                  f"{verses} verses, {deps} departures — {state}")
            for ref, kref, r, why in flagged:
                print(f"  ⚠ {ref} ~ {kref} ({r:.2f}) — {why}: check the versification")

    reg = {
        "note": ("The variant register for the transcribed Isaiah blocks (PLAN.md §3, §5). "
                 "Every word-level departure of the 1830 Book of Mormon text from the KJV, "
                 "produced mechanically by tools/collate-isaiah.py and referenced by id from "
                 "the `variants` field of the Link for each verse. Punctuation and "
                 "capitalization are not collated; the KJV's italics are not marked in the "
                 "public-domain source text used here (text/SOURCES.md), so the standing "
                 "question of whether these departures cluster at italicized words CANNOT be "
                 "answered from this register as it stands, and no claim about it is made."),
        "kinds": {
            "replace": "The Book of Mormon reads differently where the KJV has words.",
            "omit": "The KJV has words the Book of Mormon does not.",
            "add": "The Book of Mormon has words the KJV does not.",
        },
        "rows": register,
    }
    (ROOT / "data" / "isaiah-collation.json").write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    print(f"data/isaiah-collation.json: {len(register)} rows across {len(blocks)} block(s)")


if __name__ == "__main__":
    main()
