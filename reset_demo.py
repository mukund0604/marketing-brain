"""Reset the demo to its seeded state before a recording.

- Deletes HydraDB memories / knowledge items that aren't part of the seed (feedback relayed in chat,
  skills promoted from feedback), comparing against seed/tidelight/hydra_payload.json.
- Clears local UI logs (data/) and generated images (generated/).
Run: python reset_demo.py            (add --dry-run to only report)
"""
import json
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from hydra_db import HydraDB

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
DB = os.environ.get("MB_DATABASE", "zocket_marketing_brain")
c = HydraDB(token=os.environ["HYDRA_DB_API_KEY"])
seed = json.loads((ROOT / "seed" / "tidelight" / "hydra_payload.json").read_text())
cols = seed["collections"]


def listed(collection, type_):
    out, page = [], 1
    while True:
        d = c.context.list(database=DB, collection=collection, type=type_, page=page, page_size=50).data
        rows = (d.user_memories if type_ == "memory" else d.sources) or []
        out += [getattr(r, "memory_id", None) or getattr(r, "id", None) for r in rows]
        if not (d.pagination and d.pagination.has_next):
            return [i for i in out if i]
        page += 1


def main():
    DRY = "--dry-run" in sys.argv
    # feedback memory: keep only seeded memories
    seed_mem = {m["id"] for m in seed["memories"]}
    extra_mem = [i for i in listed(cols["feedback"], "memory") if i not in seed_mem]
    # brand book: keep only seeded knowledge items (promoted skills land here)
    seed_brand = {it["id"] for it in seed["payload"]["brand"]["items"]}
    extra_brand = [i for i in listed(cols["brand"], "knowledge") if i not in seed_brand]

    print(f"feedback memories to remove: {extra_mem or 'none'}")
    print(f"brand-book items to remove:  {extra_brand or 'none'}")
    if not DRY:
        if extra_mem:
            c.context.delete(database=DB, collection=cols["feedback"], type="memory", ids=extra_mem)
        if extra_brand:
            c.context.delete(database=DB, collection=cols["brand"], type="knowledge", ids=extra_brand)
        for d in ("data", "generated"):
            p = ROOT / d
            if p.exists():
                shutil.rmtree(p)
            p.mkdir()
        print("local logs and generated images cleared")
    print("dry run, nothing changed" if DRY else "reset done")


if __name__ == "__main__":
    main()
