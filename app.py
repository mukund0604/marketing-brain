import json
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import entities as ent  # noqa: E402
import tidelight_spec as tl  # noqa: E402
from brain import DATABASE as DATABASE_MB  # noqa: E402
from brain import get_brain, read_log, read_skills  # noqa: E402

TEXT_MODEL = os.environ.get("TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gemini-3-pro-image-preview")
TL = ROOT / "seed" / "tidelight"
GEN_DIR = ROOT / "generated"
ASSETS = ROOT / "static" / "assets"
PACKSHOTS = {  # verified product assets (static/assets/pack_*.png)
    "Fog Shield Mineral SPF 30": "pack_fog-shield-spf30.png",
    "Kelp Ceramide Barrier Cream": "pack_kelp-ceramide-cream.png",
    "Sea Fennel Vitamin C Serum": "pack_sea-fennel-c-serum.png",
}
GEN_DIR.mkdir(exist_ok=True)

brain = get_brain()
_gemini = None


def gemini():
    global _gemini
    if _gemini is None:
        if not os.environ.get("GEMINI_API_KEY"):
            raise HTTPException(500, "GEMINI_API_KEY missing in .env")
        _gemini = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _gemini


app = FastAPI()
app.mount("/generated", StaticFiles(directory=GEN_DIR), name="generated")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


def context_block(chunks):
    return "\n\n".join(f"[{i + 1}] ({c['kind']}, {c['source']}) {c['text']}" for i, c in enumerate(chunks))


def llm_json(prompt):
    r = gemini().models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.6),
    )
    return json.loads(r.text)


def gen_image(prompt, refs=None, aspect="1:1"):
    contents = [types.Part.from_bytes(data=(ASSETS / f).read_bytes(), mime_type="image/png") for f, _ in (refs or [])] + [prompt]
    r = gemini().models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect, image_size="1K"),
        ),
    )
    for part in r.candidates[0].content.parts:
        if part.inline_data:
            name = f"{uuid.uuid4().hex[:10]}.png"
            (GEN_DIR / name).write_bytes(part.inline_data.data)
            return f"/generated/{name}"
    raise HTTPException(500, "image model returned no image")


@app.get("/")
def index():
    # never cache the page itself, so a refresh always shows the latest UI
    return FileResponse(ROOT / "static" / "index.html", headers={"Cache-Control": "no-store, must-revalidate"})


@app.get("/api/status")
def status():
    return {"mode": brain.mode, "brand": "Tidelight", "fictional": True, "text_model": TEXT_MODEL, "image_model": IMAGE_MODEL}


def write_concept(brief, city, memory_block, cite_hint="result id like [B3]"):
    if memory_block:
        memory = f"""BRAND MEMORY (guidelines, past ad performance, client feedback). Client feedback is
non-negotiable. Brand-book specifics (hex colors, type, logo size/placement, layout margins, safe zones,
banned visuals, compliance wording) are hard requirements. Lean into patterns from WINNER creatives, avoid patterns
from UNDERPERFORMER / rejected ones, and address consumer objections where relevant.
{memory_block}"""
    else:
        memory = "No brand memory available. Use generic best practices for a coffee brand ad."
    return llm_json(f"""You are a senior performance-marketing creative director at Zocket.
Client: Tidelight (fictional San Francisco clean-skincare brand, fragrance-free, ocean botanicals). Placement: {city}.
Brief: {brief}

{memory}

Write ONE paid social static ad concept. Return JSON:
{{
  "headline": "on-image headline",
  "primary_text": "1-2 sentence ad caption",
  "visual": "one-sentence description of the image",
  "image_prompt": "a prose concept for the image model, in the order: purpose and ratio (paid Meta feed ad, 1:1), scene, subject, light, colours (described in words, never hex), on-image copy in quotes with typeface style, logo placement as a sentence, compliance text verbatim if any, explicit negatives for every banned visual, and a physical-realism line: every object rests on a surface or is held; any pour shows a cropped hand (wrist down, no face or body) holding the vessel, otherwise the vessel stands beside the finished cup; no floating or levitating objects.",
  "decisions": [{{"decision": "short choice made", "because": "reason", "source": "{cite_hint} or 'generic'"}}]
}}
Give 3-6 decisions.
Realism is non-negotiable: it must look like a real product photograph. A cropped hand holding a vessel is allowed and
does NOT count as "people in the ad"; faces and bodies do.""")


def verified_assets(brief, results):
    """Pick the verified logo + product packshot to attach as image references (like deepagent's verify_assets)."""
    text = brief + " " + " ".join(r["title"] + " " + r["text"][:300] for r in results)
    counts = {name: text.lower().count(name.lower().split(" ")[0] + " " + name.lower().split(" ")[1]) + (5 if name.lower() in brief.lower() else 0)
              for name in PACKSHOTS}
    refs = [("logo_primary.png", "the official Tidelight logo lockup (lowercase 'tidelight' wordmark + three-wave tide-line mark)")]
    best = max(counts, key=counts.get)
    if counts[best] > 0:
        refs.append((PACKSHOTS[best], f"the exact {best} packaging"))
    return refs


def make_creative(brief, placement, results):
    """Used by the agent. With memory: brand-book/campaign/feedback context with ids, plus verified asset references.
    Without memory (control): just the brief, no assets."""
    block = "\n\n".join(f"[{r['rid']}] ({r['kind']}) {r['title']}\n{r['text'][:900]}" for r in results) if results else None
    concept = write_concept(brief, placement, block, cite_hint="result id like [B3], [C2], [V7] or [F1]")
    aspect = "4:5" if "4:5" in placement else "9:16" if "9:16" in placement else "1:1"
    refs = verified_assets(brief, results) if results else []
    prompt = concept["image_prompt"]
    if refs:
        prompt = ("Reference images: " + "; ".join(f"image {i + 1} is {desc}" for i, (_, desc) in enumerate(refs)) +
                  ". Reproduce the logo and packaging from the references exactly; never redraw, simplify or invent them. "
                  "Use the full logo lockup (wordmark + mark), never the mark alone.\n\n" + prompt)
    return {**concept, "image_url": gen_image(prompt, refs, aspect), "use_brain": bool(results), "aspect": aspect,
            "assets": [f"/static/assets/{f}" for f, _ in refs]}


@app.get("/api/memory")
def memory():
    data = json.loads((TL / "hydra_payload.json").read_text())
    return {"feedback": data["memories"] + read_log(), "mode": brain.mode}


@app.get("/api/brain")
def brain_view():
    """Everything the Marketing Brain holds, for the Brain view."""
    data = json.loads((TL / "hydra_payload.json").read_text())
    stats = json.loads((TL / "stats.json").read_text())
    graph = json.loads((TL / "brain_graph.json").read_text())
    layers = {}
    for layer, col in data["collections"].items():
        items = data["payload"][layer]["items"] if layer != "feedback" else []
        layers[layer] = {
            "collection": col,
            "count": len(items) if layer != "feedback" else len(data["memories"]) + len(read_log()),
            "relations": sum(len(g["relations"]) for g in data["payload"][layer]["graph"].values()) if layer != "feedback" else 0,
            "samples": [{"title": it["title"].replace("Tidelight · ", ""), "body": it["fields"]["body"][:600],
                         "provider": it["provider"], "ts": it["timestamp"][:10]} for it in items]
            if layer != "feedback" else [{"title": f"{m['from']} · {m['status']} on {m['media_id']}", "body": m["text"], "provider": "approvals"}
                                         for m in data["memories"] + read_log()],
        }
    rows = json.loads((TL / "ad_daily.json").read_text())
    import build_tidelight as bt
    perf = bt.rollup(rows)
    camps = []
    for c in tl.CAMPAIGNS:
        live = [(x, perf[x[1]]) for x in tl.CREATIVES if x[0] == c["id"] and x[1] in perf]
        sp = sum(p["spend"] for _, p in live)
        camps.append({"id": c["id"], "name": c["name"], "flight": c["flight"], "platforms": c["platforms"], "product": c["product"],
                      "spend": round(sp), "roas": round(sum(p["roas"] * p["spend"] for _, p in live) / max(sp, 1), 2), "kpi": c["kpi"],
                      "creatives": len([x for x in tl.CREATIVES if x[0] == c["id"]]), "fatigued": sum(1 for _, p in live if p["fatigued"])})
    return {"brand": tl.BRAND, "stats": stats, "layers": layers, "campaigns": camps, "graph": graph,
            "competitors": tl.COMPETITORS, "sov": tl.TIDELIGHT_SOV, "database": DATABASE_MB}


@app.get("/api/entities")
def entities_api():
    return {"entities": ent.entities()}


# ---------------------------------------------------------------- Promote to Skill
def seed_skills():
    return [{**sk, "is_active": True, "promoted": False} for sk in tl.AGENT_SKILLS]


@app.get("/api/skills")
def skills():
    return {"skills": seed_skills() + [{**s, "promoted": True} for s in read_skills()]}


@app.post("/api/skills/suggest")
def suggest_skills():
    t = time.time()
    mems = brain.feedback_memories(20)
    recall_ms = int((time.time() - t) * 1000)
    existing = [f"{s['name']}: {s['description']}" for s in skills()["skills"]]
    out = llm_json(f"""You turn repeated client corrections into durable Brand Brain Skills for Zocket's Creative AI.
A Skill = per-brand instruction: when to reach for it (trigger) and exactly what to do.

CLIENT FEEDBACK MEMORY (from HydraDB):
{context_block(mems)}

EXISTING SKILLS (do not duplicate):
{chr(10).join(existing) or "none"}

Group the feedback into 2-4 NEW skills. Prefer themes that multiple corrections point at. Return JSON:
{{"skills": [{{
  "name": "kebab-case-name",
  "title": "short title",
  "description": "one sentence: when this skill fires",
  "skill": "markdown body: '# Title', 'Trigger:' line, then 3-5 '- ' bullet rules (do / don't), concrete and checkable",
  "evidence": [memory indices like 1, 3],
  "why": "one sentence on the pattern across the feedback"
}}]}}""")
    for sk in out["skills"]:
        sk["evidence"] = [mems[i - 1] for i in sk.get("evidence", []) if 0 < i <= len(mems)]
    return {"skills": out["skills"], "recall_ms": recall_ms}


class Skill(BaseModel):
    name: str
    title: str
    description: str
    skill: str


@app.post("/api/skills/promote")
def promote_skill(body: Skill):
    sk = {**body.model_dump(), "tags": ["creative_ai", "learned"], "is_active": True,
          "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    brain.add_skill(sk)
    cypher = (
        "MATCH (b:Brand {name: $brand, country_code: 'us'})\n"
        "MERGE (b)-[:HAS_AGENT_SKILLS]->(hub:AgentSkills)\n"
        "MERGE (hub)-[:HAS_AGENT_SKILL]->(s:AgentSkill {name: $name})\n"
        "SET s.title = $title, s.description = $description, s.skill = $skill,\n"
        "    s.tags = $tags, s.is_active = true, s.updated_at = $updated_at"
    )
    return {"ok": True, "skill": sk, "brandos_cypher": cypher}


# ---------------------------------------------------------------- agentic chat
class Chat(BaseModel):
    messages: list[dict]


@app.post("/api/chat")
def chat(body: Chat):
    import sys

    import agent

    def stream():
        try:
            for ev in agent.Turn(sys.modules[__name__], body.messages).run():
                yield f"data: {json.dumps(ev, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)[:500]})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
