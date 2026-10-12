"""Marketing Brain memory layer on HydraDB.

One database, one collection per layer (see build_tidelight.py / ingest_tidelight.py):
  tidelight_brand      knowledge: brand book sections, products, agent skills, org memory
  tidelight_campaigns  knowledge: historic campaigns + creatives joined with daily ad performance
  tidelight_voice      knowledge: consumer reviews / threads / comments (app sources) + review themes
  tidelight_market     knowledge: competitors, share of voice, category trends
  tidelight_feedback   memory:    client approvals / send-backs / rejections (infer=true, so HydraDB
                                  extracts the rule behind a raw comment)
Knowledge items carry a BYOG graph_payload in BrandOS labels and relationship types.
"""
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).parent
LOG = ROOT / "data" / "feedback_log.json"
SKILLS_LOG = ROOT / "data" / "promoted_skills.json"

DATABASE = os.environ.get("MB_DATABASE", "zocket_marketing_brain")
BRAND = "tidelight_brand"          # brand book collection (promoted skills land here)
FEEDBACK = "tidelight_feedback"    # client feedback memory
LAYERS = {  # Marketing Brain layer -> HydraDB collection
    "brand": "tidelight_brand", "campaigns": "tidelight_campaigns", "voice": "tidelight_voice",
    "market": "tidelight_market", "feedback": "tidelight_feedback",
}


def feedback_to_text(fb):
    status = f" [{fb['status']}]" if fb.get("status") else ""
    when = f" on {fb['date']}" if fb.get("date") else ""
    return f"Client feedback{status} from {fb['from']}{when} (re: {fb['on']}): {fb['text']}"


# ---------------------------------------------------------------- local logs (UI only; HydraDB is the source of truth)
def read_log():
    return json.loads(LOG.read_text()) if LOG.exists() else []


def append_log(entry):
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text(json.dumps(read_log() + [entry], indent=2))


def read_skills():
    return json.loads(SKILLS_LOG.read_text()) if SKILLS_LOG.exists() else []


def save_skill(skill):
    SKILLS_LOG.parent.mkdir(exist_ok=True)
    skills = [s for s in read_skills() if s["name"] != skill["name"]] + [skill]
    SKILLS_LOG.write_text(json.dumps(skills, indent=2))


def skill_item(sk):
    """A promoted AgentSkill in the same app_knowledge + BYOG shape as the seeded skills."""
    item_id = f"tl_skill_{sk['name']}"
    item = {
        "id": item_id, "title": f"Tidelight · AgentSkill: {sk['title']}", "kind": "custom", "provider": "brandos",
        "timestamp": sk["updated_at"], "fields": {"kind": "custom", "body": f"{sk['description']}\n{sk['skill']}"},
        "metadata": {}, "additional_metadata": {"brand": "tidelight", "promoted_from_feedback": True},
    }
    graph = {item_id: {
        "entities": {"brand": {"name": "tidelight", "type": "BRAND", "namespace": "tidelight"},
                     "sk": {"name": sk["name"], "type": "AGENTSKILL", "namespace": "tidelight"}},
        "relations": [{"source": "brand", "target": "sk", "predicate": "HAS_AGENT_SKILL",
                       "context": f"Tidelight skill (learned from client feedback): {sk['title']}"}],
    }}
    return item, graph


# ---------------------------------------------------------------- HydraDB
class HydraBrain:
    mode = "hydradb"

    def __init__(self):
        from hydra_db import HydraDB

        if not os.environ.get("HYDRA_DB_API_KEY"):
            raise RuntimeError("HYDRA_DB_API_KEY missing in .env")
        self.client = HydraDB(token=os.environ["HYDRA_DB_API_KEY"])

    def remember(self, fb, log=True):
        self.client.context.ingest(
            database=DATABASE, collection=FEEDBACK, type="memory", upsert="true",
            memories=json.dumps([{"id": fb["id"], "text": feedback_to_text(fb), "infer": True, "user_name": fb["from"]}]),
        )
        if log:
            append_log(fb)

    def add_skill(self, sk):
        item, graph = skill_item(sk)
        item["database"], item["collection"] = DATABASE, BRAND
        self.client.context.ingest(database=DATABASE, collection=BRAND, type="knowledge", upsert="true",
                                   app_knowledge=json.dumps([item]), graph_payload=json.dumps(graph))
        save_skill(sk)

    def wait_searchable(self, mid, probe, timeout=45):
        """HydraDB indexes async (~10-20s for a memory). Poll until the memory is retrievable."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            res = self.client.query(database=DATABASE, collection=FEEDBACK, query=probe, type="memory",
                                    query_by="hybrid", mode="fast", max_results=5)
            if any(c.id == mid for c in (res.data.chunks or [])):
                return round(time.time() - t0, 1)
            time.sleep(1.5)
        return None

    def feedback_memories(self, k=20):
        res = self.client.query(
            database=DATABASE, collection=FEEDBACK, type="memory", query_by="hybrid", mode="fast", max_results=k,
            query="client corrections, rejections, change requests and preferences about creatives",
        )
        return [{"text": c.chunk_content, "source": c.source_title or c.id or "", "kind": "feedback", "score": c.relevancy_score}
                for c in (res.data.chunks or [])]


def get_brain():
    return HydraBrain()
