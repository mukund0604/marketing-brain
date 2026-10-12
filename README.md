# Marketing Brain

A 360° marketing memory on **HydraDB**, with an agent that reads from it, shows exactly what it used, and learns from every client rejection. Built at the Company Brain Hackathon (Oct 2026) by the Zocket team.

> Demo brand **Tidelight** is fictional (a San Francisco clean-skincare brand), and so are its competitors. All data is synthetic.

## What it does

- **Five memory layers**, one HydraDB collection each:

  | Layer | Collection | Contents |
  |---|---|---|
  | Brand book | `tidelight_brand` | color system (hex/Pantone/contrast, banned combos), type scale per placement, logo, layout grid + safe zones, photography/talent, voice, FDA/FTC rule pack, products, skills |
  | Campaigns | `tidelight_campaigns` | 8 campaigns over 18 months; 23 creatives joined with daily ad performance (ROAS, CTR, CPA, frequency, fatigue) |
  | Consumer voice | `tidelight_voice` | 160 reviews / Reddit threads / TikTok + IG comments across 7 platforms, plus review themes |
  | Market | `tidelight_market` | competitors, share of voice, category trends |
  | Client feedback | `tidelight_feedback` (memory, `infer=true`) | approvals, send-backs, rejections |

- **Agentic chat:** a Gemini agent with one search tool per layer, plus `generate_creative`, `remember_feedback`, `suggest_skills` and `promote_skill`.
- **Brain trace:** every HydraDB query with its collection, mode and latency, results ranked by relevancy, used vs ignored, graph paths, and what HydraDB inferred.
- **With-brain vs control** creative generation. Verified brand assets (logo, packshots) are attached as image references.
- **Learning loop:** relayed feedback becomes a HydraDB memory, is retrieved (tagged NEW) on the next generation, and can be promoted to a Skill.
- **Brain view:** layers, counts, sources, campaign ROAS against target, share of voice, a graph explorer and a records browser.

## Architecture

```
tidelight_spec.py  ─┐  hand-written brand book, products, campaigns, creatives, approvals
gen_voice.py       ─┤  Gemini writes consumer voice from a controlled theme spec
build_tidelight.py ─┤  daily ad performance (BrandOS/ClickHouse shape) + HydraDB payloads with BYOG graphs
ingest_tidelight.py ┘  -> HydraDB: app_knowledge (+ graph_payload) per layer, memories (infer=true)

app.py   FastAPI: /api/chat (SSE agent stream), /api/brain, /api/skills/*
agent.py agent loop (Gemini function calling) + retrieval trace
brain.py HydraDB memory layer (remember, wait_searchable, promote skills)
static/  single-page UI (chat + trace, Brain view, Skills)
```

The graph uses BrandOS labels and relationships via HydraDB **Bring Your Own Graph**: `Brand -HAS_GUIDELINES-> Guidelines -HAS_COLOR_PALETTE-> ColorPalette`, `Campaign -HAS_AD-> Ad -HAS_CREATIVE-> Creative -CREATIVE_HAS_ARCHETYPE-> CreativeArchetype`, `Consumer -TALKED_ABOUT-> Product`, and more.

## Run it

```bash
cp .env.example .env            # add GEMINI_API_KEY and HYDRA_DB_API_KEY
pip install -r requirements.txt
python gen_voice.py             # optional: regenerate consumer voice (seed/tidelight/voice.json is included)
python build_tidelight.py       # build performance rows + HydraDB payloads
python ingest_tidelight.py      # load into HydraDB (indexing is async; graph context appears once indexing completes)
python make_assets.py           # logo lockups (add --packshots to regenerate product packshots)
uvicorn app:app --port 8010
```

Open http://localhost:8010.

## Models

- Agent and copy: `gemini-2.5-flash`
- Images: `gemini-3-pro-image-preview`, with logo and packshot references
