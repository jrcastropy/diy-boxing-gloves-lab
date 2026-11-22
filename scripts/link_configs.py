"""Write the DXF link into viewer configs, so every item knows which DXF piece it is (see dxf_link.py).

Built-in items (Chone, Mould 1, Mould 2) take their link from viewer/glove-data.js. Every other item's outline is
matched against the DXFs, trying the ones named in HINTS for that config first, then every DXF in dxf/. Old
version-1 configs are turned into the current form first. Each config is backed up before it's changed.

Usage: uv run --with ezdxf --with shapely --with scipy --with matplotlib python scripts/link_configs.py viewer/config/*.json
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from dxf_link import REPO, find_source

HINTS = [  # config name contains -> DXF(s) its items were imported from
    ("minified-chone-thumb+0.25in", "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.25in.dxf"),
    ("minified-chone-thumb+0.5in", "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in.dxf"),
    ("minified-chone-thumb+0.75in", "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.75in.dxf"),
    ("minified-chone", "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf"),
    ("mould1-thumb-chone-angle", "dxf/Laces Boxing 14OZ - mould1 thumb chone angle.dxf"),
    ("mould-from-chone", "dxf/Mould from Chone - 1in foam.dxf"),
]
GLOVE = json.loads((REPO / "viewer/glove-data.js").read_text().split("=", 1)[1].strip().rstrip(";"))


def migrate(s):  # version-1 configs: the three built-in pieces with their settings spread over the top level
    if isinstance(s.get("items"), list):
        return s
    show, poses, thick = s.get("show", {}), s.get("poses", {}), s.get("thick", {})
    pose = lambda k: {"x": 0, "y": 0, "rot": 0, **poses.get(k, {})}
    items = [
        {"key": "mould2", "builtin": "mould2", "thick": thick.get("mould2"), "opacity": s.get("opacityM2"), "show": show.get("mould2"), "pose": pose("mould2")},
        {"key": "mould1", "builtin": "mould1", "thick": thick.get("mould1"), "opacity": s.get("opacityM1"), "show": show.get("mould1"), "pose": pose("mould1")},
        {"key": "chone", "builtin": "chone", "opacity": s.get("opacity"), "show": show.get("chone"), "pose": {**pose("chone"), "scale": s.get("scale", 100)},
         "drape": s.get("drape"), "edgeR": s.get("edgeR"), "target": s.get("target")},
    ]
    items = [{k: v for k, v in it.items() if v is not None} for it in items]
    keep = {k: s[k] for k in ("app", "savedAt", "noOverlap", "newFor", "hinges") if k in s}
    return {**keep, "version": 2, "item": "chone", "items": items}


def main(paths):
    dxfs = sorted(str(p.relative_to(REPO)) for p in (REPO / "dxf").glob("*.dxf"))
    backup = REPO / "viewer/config" / f"backup-{date.today().isoformat()}"
    for path in map(Path, paths):
        cfg = json.loads(path.read_text())
        backup.mkdir(exist_ok=True)
        if not (backup / path.name).exists():
            shutil.copy2(path, backup / path.name)
        cfg = migrate(cfg)
        first = [f for key, f in HINTS if key in path.name][:1]
        order = first + [f for f in dxfs if f not in first]
        for it in cfg["items"]:
            if it.get("builtin"):
                b = GLOVE[it["builtin"]]
                it["source"], it["path"] = b["source"], b["path"]
                print(f"{path.name}: {it['key']} (built-in) -> {b['source']['file']} piece {b['source']['handle']}")
                continue
            got = find_source(it["outline"], order) or find_source(it["outline"], order, allow_turn=True)
            if not got:
                sys.exit(f"{path.name}: couldn't find which DXF piece {it['key']} ({it.get('label')}) is; nothing written")
            it["source"], it["path"] = got
            print(f"{path.name}: {it['key']} ({it.get('label')}) -> {got[0]['file']} piece {got[0]['handle']}"
                  f"{' mirrored' if got[0]['mirror'] else ''}")
        path.write_text(json.dumps(cfg, indent=1))
    print(f"backups in {backup.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1:])
