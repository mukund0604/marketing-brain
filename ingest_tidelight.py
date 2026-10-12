"""Load the Tidelight Marketing Brain into a fresh HydraDB database (one collection per layer)."""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from hydra_db import HydraDB

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
DATABASE = os.environ.get("MB_DATABASE", "zocket_marketing_brain")
c = HydraDB(token=os.environ["HYDRA_DB_API_KEY"])
data = json.loads((ROOT / "seed" / "tidelight" / "hydra_payload.json").read_text())
cols, payload = data["collections"], data["payload"]

try:
    c.databases.create(database=DATABASE)
    print("created", DATABASE)
except Exception as e:
    print("create:", e.__class__.__name__)
for _ in range(90):
    if getattr(c.databases.status(database=DATABASE).data.infra, "ready_for_ingestion", False):
        break
    time.sleep(2)

for layer, col in cols.items():
    if layer == "feedback":
        continue
    items, graph = payload[layer]["items"], payload[layer]["graph"]
    for i in range(0, len(items), 40):
        batch = items[i:i + 40]
        for it in batch:
            it["database"], it["collection"] = DATABASE, col
        res = c.context.ingest(database=DATABASE, collection=col, type="knowledge", upsert="true",
                               app_knowledge=json.dumps(batch),
                               graph_payload=json.dumps({it["id"]: graph[it["id"]] for it in batch}))
        print(f"{col}: +{res.data.success_count} (failed {res.data.failed_count})")

mems = [{"id": m["id"], "text": m["text"], "infer": True, "user_name": m["from"]} for m in data["memories"]]
res = c.context.ingest(database=DATABASE, collection=cols["feedback"], type="memory", upsert="true", memories=json.dumps(mems))
print(f"{cols['feedback']}: +{res.data.success_count} memories")
