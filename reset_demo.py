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
import time
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
        for collection, type_, ids in ((cols["feedback"], "memory", extra_mem), (cols["brand"], "knowledge", extra_brand)):
            pending = list(ids)
            for attempt in range(20):  # HydraDB refuses to delete a source that is still indexing; wait and retry
                if not pending:
                    break
                res = c.context.delete(database=DB, collection=collection, type=type_, ids=pending).data
                pending = [r.id for r in (res.results or []) if not r.deleted] if res and res.results else []
                if pending:
                    print(f"  still indexing, retrying in 15s: {pending}")
                    time.sleep(15)
            if pending:
                print(f"  could not delete (try again in a minute): {pending}")
        for d in ("data", "generated"):
            p = ROOT / d
            if p.exists():
                shutil.rmtree(p)
            p.mkdir()
        print("local logs and generated images cleared")
    print("dry run, nothing changed" if DRY else "reset done")


if __name__ == "__main__":
    main()
