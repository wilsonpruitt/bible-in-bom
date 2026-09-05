#!/usr/bin/env python3.11
"""
Turn a collation (tools/collate-isaiah.py --json) into an adjudication file:
one Link per verse, plus a variant register keyed by id.

Every verse of a transcribed Isaiah block IS a quotation and the catalogue must
say so verse by verse (PLAN.md §5) — but the ARGUMENT is not in the fact that
the verse is quoted, it is in the departures. So the machine writes the routine
part of each note (overlap, departure count, the departures themselves) and the
adjudicator supplies prose for the verses where the departures mean something.
Hand-written notes live in NOTES below and are appended, never overwritten.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(slug, ch, book, kch, variants_path, notes, out_path, register_rows):
    bom = json.loads((ROOT / "data" / f"{slug}.json").read_text())
    kjv = json.loads((ROOT / "text" / "kjv.json").read_text())
    rows = json.loads(Path(variants_path).read_text())
    per = {p["ref"]: p["text"] for p in bom["pericopes"] if p["ch"] == ch}

    by_verse = {}
    counters = {}
    for r in rows:
        v = r["bomRef"].split(":")[-1]
        counters[v] = counters.get(v, 0) + 1
        r = dict(r)
        r["id"] = f"{slug}-{ch}:{v}-{chr(96 + counters[v])}"
        by_verse.setdefault(v, []).append(r)
        register_rows.append(r)

    links = {}
    for ref in sorted(per, key=lambda r: int(r.split(":")[1])):
        v = ref.split(":")[1]
        kref = f"{book} {kch}:{v}"
        deps = by_verse.get(v, [])
        parts = []
        for d in deps:
            if d["kind"] == "replace":
                parts.append(f"KJV “{d['kjv']}” → “{d['bom']}”")
            elif d["kind"] == "omit":
                parts.append(f"KJV “{d['kjv']}” omitted")
            else:
                parts.append(f"adds “{d['bom']}”")
        if deps:
            machine = (f"{len(deps)} departure(s) from the KJV: " + "; ".join(parts) + ".")
        else:
            machine = "Reproduces the KJV verse word for word."
        note = machine + (" " + notes[v] if v in notes else "")
        links[ref] = [{
            "source": kref,
            "type": "quotation",
            "subtype": "extended",
            "confidence": "certain",
            "text": kjv[kref],
            "evidence": {"vocabulary": 5, "syntax": 5, "sequence": 5,
                         "context": 5, "rarity": 5, "attestation": 5},
            "kjvSpecific": "yes",
            "mediation": "direct-OT",
            "provenance": {
                "route": f"{book} {kch} → KJV → Book of Mormon",
                "significance": (
                    f"Part of a continuous transcription of {book} {kch} as {bom['name']} {ch}. "
                    "The quotation is not the finding; the departures are, and they are listed "
                    "in the note and registered individually in data/isaiah-collation.json."),
            },
            "note": note,
            "variants": [d["id"] for d in deps],
            "bibliography": [],
            "status": "consensus",
            "citationsPending": True,
            "streams": ["manual"],
        }]

    Path(out_path).write_text(json.dumps({
        "chapter": ch,
        "adjudicated": "2026-09-05",
        "adjudicator": "Opus (collated mechanically by tools/collate-isaiah.py; notes authored)",
        "links": links,
    }, indent=2, ensure_ascii=False) + "\n")
    return len(links), len(rows)


NOTES20 = {
 "1": "The 1830 has no baptismal clause here. The 1840 edition inserted “or out of the waters of baptism” after “out of the waters of Judah”, and modern editions keep it; the first edition does not, so the running text of this catalogue reproduces Isaiah 48:1 with only the additions listed above.",
 "2": "The chapter's largest theological addition in its opening: Isaiah's flat “for they call themselves of the holy city” becomes “Nevertheless … but they do not stay themselves upon the God of Israel, which is the Lord of hosts”. Isaiah reports the claim; the Book of Mormon denies it in the same breath.",
 "10": "KJV Isaiah 48:10 reads “I have refined thee, but not with silver”. The Book of Mormon omits “but not with silver”, which is the one place in this chapter where a whole KJV clause disappears rather than being expanded. Note for the italics question below: “but not with silver” is not italicized in the KJV, so this omission is not explained by the usual italics hypothesis.",
 "11": "KJV “how should my name be polluted?” becomes “I will not suffer my name to be polluted” — a rhetorical question turned into a declaration, which is the commonest single kind of departure in this chapter.",
 "14": "The longest addition in the chapter: fourteen words inserted into Isaiah's oracle about the LORD's beloved doing his pleasure on Babylon — “yea, and he will fulfil his word which he hath declared by them”. The insertion makes the prophets, not Cyrus, the agent.",
 "18": "Word for word. This is the verse Lehi spoke over Laman and Lemuel at the river at 1 Nephi 2:9-10, seventeen chapters earlier, in his own words; here the family reads it out as scripture. See the link at 2:9 — the recurrence is the reason that link was recorded.",
 "22": "The chapter's closing addition, and its sharpest: Isaiah ends “There is no peace, saith the LORD, unto the wicked.” The Book of Mormon prefixes “And notwithstanding he hath done all this, and greater also” — which converts a verdict into a complaint about ingratitude.",
}

NOTES21 = {
 "1": "The chapter's one substantial addition and the reason the whole block is here. Forty-seven words are prefixed to Isaiah 49:1, addressing the oracle to “all ye that are broken off … that are scattered abroad, which are of my people, O house of Israel” — which applies the servant song to Lehi's family specifically, and does so in the vocabulary of Romans 11's broken-off branches that this book has used since 10:12. Hardy's apparatus cites Jeremiah 23:1-2 for “the pastors of my people”, which is the KJV's phrase for shepherds who scatter the flock.",
 "7": "The one whole-clause omission in the chapter: KJV Isaiah 49:7's “and the Holy One of Israel, and he shall choose thee” is absent. Everything else here is number and article.",
 "11": "KJV “I will make all my mountains a way” becomes “I will make all my mountains away” — the two words run together. A typesetting or dictation artifact rather than a reading, and worth registering as such: it is the clearest evidence in the block that the text passed through an ear or a compositor rather than a copyist's eye.",
 "13": "Two additions, both eschatological rather than editorial: “for the feet of them which are in the east shall be established” and “for they shall be smitten no more”. Isaiah 49:13 is a summons to the heavens and earth to sing; the Book of Mormon attaches to it the fate of a scattered people.",
 "14": "Isaiah's Zion says “The LORD hath forsaken me, and my Lord hath forgotten me.” The Book of Mormon adds the answer inside the verse — “but he will shew that he hath not” — so that the complaint and its refutation stand in one sentence rather than across two verses.",
 "20": "KJV Isaiah 49:20 reads “The place is too strait for me”; the Book of Mormon reads “too straight”. The same homophone substitution appears at 1 Nephi 8:20, where “strait is the gate, and narrow is the way” (Matthew 7:14) becomes “a straight and narrow path”. Two independent occurrences of one confusion, in two different biblical books, is evidence about how the text was produced: “strait” meaning narrow was being heard rather than read.",
}


def main():
    register = []
    a = build("1-nephi", 20, "Isaiah", 48, "work/1-nephi/variants-ch20.json",
              NOTES20, "work/1-nephi/adjudicated/ch20.json", register)
    b = build("1-nephi", 21, "Isaiah", 49, "work/1-nephi/variants-ch21.json",
              NOTES21, "work/1-nephi/adjudicated/ch21.json", register)
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
    Path(ROOT / "data" / "isaiah-collation.json").write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    print(f"1 Nephi 20: {a[0]} verses, {a[1]} departures")
    print(f"1 Nephi 21: {b[0]} verses, {b[1]} departures")
    print(f"data/isaiah-collation.json: {len(register)} rows")


if __name__ == "__main__":
    main()
