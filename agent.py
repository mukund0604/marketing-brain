"""Agentic chat over the Brand Brain, with a full retrieval trace.

The agent (Gemini, function calling) decides which tools to use. Every HydraDB call is
recorded: query, collection, mode, latency, every ranked result with its score, graph
paths HydraDB walked, and what HydraDB inferred from raw feedback. Results get ids
(B1, C1, V1, M1, F1..) so we can show which ones the agent actually used vs ignored.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from google.genai import types

import brain as brain_mod

def session_memory_ids():
    """Memories stored via chat (persisted in the feedback log); tagged NEW in the trace when retrieved."""
    return {f["id"] for f in brain_mod.read_log() if f.get("status") == "chat"}

# Marketing Brain layers: tool -> (layer, id prefix, HydraDB type, mode)
SEARCH_TOOLS = {
    "search_brand_book": ("brand", "B", "knowledge", "thinking"),
    "search_campaigns": ("campaigns", "C", "knowledge", "thinking"),
    "search_consumer_voice": ("voice", "V", "knowledge", "thinking"),
    "search_market": ("market", "M", "knowledge", "thinking"),
    "search_client_feedback": ("feedback", "F", "memory", "fast"),
}
ID_RE = r"[BCVMF]\d+"

SYSTEM = """You are the Marketing Brain, Zocket's agent for the brand Tidelight (a fictional San Francisco
clean-skincare brand: fragrance-free, cold-water ocean botanicals, sold DTC, Amazon and Target).
You work for Zocket's account managers, strategists and creative teams. Everything you know lives in HydraDB,
in five layers, each with its own search tool:

- search_brand_book   [B]: brand guidelines at brand-book depth (color system with hex/Pantone/contrast and banned
  combos, type scale per placement, logo rules, layout grid + safe zones, photography/talent rules, tone and vocabulary,
  legal/compliance rule pack incl. FDA SPF + FTC rules), products and product-level overrides, agent skills, org memory.
- search_campaigns    [C]: 18 months of historic campaigns (objective, budget, flight, audience, KPI, actual results,
  learnings) and every creative with ClickHouse performance (ROAS, CTR, CPA, frequency, fatigue) and creative score.
- search_consumer_voice [V]: what consumers say on Amazon, Target, tidelight.com, Trustpilot, Reddit, TikTok and Instagram,
  plus review-theme aggregates.
- search_market       [M]: competitors (petal & pine, dermafact, noma skin), share of voice, category trends, regulation.
- search_client_feedback [F]: the client team's own approvals, send-backs, rejections and reactions to our creatives
  (Sam Rivera brand, Jordan Lee legal, Priya Shah performance).

Other tools: generate_creative, remember_feedback, suggest_skills, promote_skill.

Rules:
- Route by layer and usually combine 2-4 layers: "how are campaigns doing" -> campaigns (+ voice/feedback for why);
  "what are people saying" -> consumer_voice (+ market); strategy questions -> campaigns + voice + market.
- Before generate_creative ALWAYS search: brand_book (guidelines + compliance for that product), campaigns (past winners and
  losers for that product/archetype), client_feedback; add consumer_voice when objections matter. Budget: at most 5
  searches before generating, issued together in one step, then call generate_creative.
- When asked to regenerate or make another version, ask for a genuinely different direction in the brief.
- The brief you pass to generate_creative states the goal, product, audience and constraints only. Never put a headline,
  tagline or a past creative's concept into the brief; the creative step writes new copy.
- Write descriptive queries (6-12 words naming product, metric, platform). Separate searches for separate needs.
- For "all the rules" / brand-compliance questions and before generating, run separate brand_book searches for the
  sections that matter (e.g. "logo usage placement minimum size clear space", "color palette banned combinations",
  "typography type scale", "layout grid safe zones", "compliance rule pack claims" + the product).
- Ground every claim in tool results. Cite result ids inline like [C3] or [V12], ONLY ids returned in this turn.
  If you did not search this turn, cite nothing. Never invent numbers.
- Be concise. Short bullets. Lead with the answer.
- After generate_creative the UI shows the image(s) and every decision with sources. Reply in 1-2 sentences: the core idea,
  and (if a control was generated) the biggest thing memory changed versus the control.
"""

_q = types.Schema(type="OBJECT", properties={"query": types.Schema(type="STRING")}, required=["query"])
TOOLS = [types.Tool(function_declarations=[
    types.FunctionDeclaration(name="search_brand_book", description="Search brand guidelines, products, compliance rules, skills. Returns ids B1, B2...", parameters=_q),
    types.FunctionDeclaration(name="search_campaigns", description="Search historic campaigns and creatives with performance. Returns ids C1, C2...", parameters=_q),
    types.FunctionDeclaration(name="search_consumer_voice", description="Search consumer reviews, Reddit threads, TikTok/IG comments, review themes. Returns ids V1, V2...", parameters=_q),
    types.FunctionDeclaration(name="search_market", description="Search competitors, share of voice, category trends, regulation. Returns ids M1, M2...", parameters=_q),
    types.FunctionDeclaration(name="search_client_feedback", description="Search the client team's feedback memory on our creatives. Returns ids F1, F2...", parameters=_q),
    types.FunctionDeclaration(
        name="generate_creative",
        description="Generate a paid social static ad (concept + image) using everything retrieved so far in this turn.",
        parameters=types.Schema(type="OBJECT", properties={
            "brief": types.Schema(type="STRING"),
            "placement": types.Schema(type="STRING", description="e.g. Meta feed 4:5, Instagram 1:1"),
            "compare_without_brain": types.Schema(type="BOOLEAN", description="Also generate a no-memory version side by side"),
        }, required=["brief"])),
    types.FunctionDeclaration(
        name="remember_feedback",
        description="Store new client feedback in HydraDB memory.",
        parameters=types.Schema(type="OBJECT", properties={
            "text": types.Schema(type="STRING"), "sender": types.Schema(type="STRING"),
            "on": types.Schema(type="STRING", description="creative id or headline it refers to, or 'general'"),
        }, required=["text"])),
    types.FunctionDeclaration(name="suggest_skills", description="Read feedback memory and propose new Brand Brain Skills from repeated corrections.",
                              parameters=types.Schema(type="OBJECT", properties={})),
    types.FunctionDeclaration(
        name="promote_skill", description="Promote a proposed skill to an active AgentSkill.",
        parameters=types.Schema(type="OBJECT", properties={
            "name": types.Schema(type="STRING"), "title": types.Schema(type="STRING"),
            "description": types.Schema(type="STRING"), "skill": types.Schema(type="STRING")},
            required=["name", "title", "description", "skill"])),
])]


def _kind_of(title, layer):
    if layer == "feedback":
        return "client feedback"
    m = re.match(r"Tidelight · ([^:]+?)(?::|$)", title)
    k = (m.group(1) if m else layer).split(" · ")[0].strip()
    if k.startswith(("Creative ", "Campaign")):
        return k.split()[0].lower()  # "creative" / "campaign"; the id and product live in the title
    if layer == "voice" and not k.startswith("ReviewTheme"):
        return k.split()[0]  # platform: amazon / reddit / tiktok ...
    return {"Guidelines hub": "guidelines", "AgentSkill": "skill", "Org memory": "org memory", "ReviewTheme": "theme",
            "CategoryTrend": "trend", "ShareOfVoice (last 90 days)": "share of voice"}.get(k, k.lower())


class Turn:
    """One user turn: runs the agent loop and yields trace events."""

    def __init__(self, app, history):
        self.app, self.history = app, history
        self.results = {}  # id -> result
        self.counters = {p: 0 for _, p, _, _ in SEARCH_TOOLS.values()}

    # ------------------------------------------------------------ HydraDB search with trace
    def _search(self, query, tool):
        b = self.app.brain
        layer, prefix, type_, mode = SEARCH_TOOLS[tool]
        knowledge = type_ == "knowledge"
        collection = brain_mod.LAYERS[layer]
        t = time.time()
        trace = {"query": query, "layer": layer, "tool": tool, "collection": collection, "type": type_,
                 "mode": mode, "query_by": "hybrid", "max_results": 10}
        res = b.client.query(database=brain_mod.DATABASE, collection=collection, query=query,
                             type=trace["type"], query_by="hybrid", mode=mode, max_results=10, graph_context=knowledge)
        chunks = [{"title": c.source_title or c.id, "id": c.id, "text": c.chunk_content, "score": c.relevancy_score,
                   "chunk_uuid": c.chunk_uuid} for c in (res.data.chunks or [])]
        trace["server_ms"] = round(res.meta.latency_ms) if res.meta and res.meta.latency_ms else None
        trace["paths"] = self._paths(res.data.graph_context, chunks)
        trace["wall_ms"] = int((time.time() - t) * 1000)
        fresh_ids = session_memory_ids()
        out = []
        for rank, c in enumerate(chunks, 1):
            self.counters[prefix] += 1
            rid = f"{prefix}{self.counters[prefix]}"
            text = c["text"]
            body, _, inferred = text.partition("\n\nExtra context:")
            body = re.sub(r"^## Title\n\n.*?\n\n## Content\n\n", "", body, flags=re.S)
            title = c["title"] or ""
            m = re.match(r"Client feedback(?: \[(\w+)\])? from (.+?)(?: on [\d-]+)? \(re: (\S+)", body)
            if not knowledge and m:
                title = f"{m.group(2)} · {m.group(1) or 'feedback'} on {m.group(3)}"
            kind = _kind_of(title, layer)
            if layer == "voice" and not title.startswith("Tidelight"):
                pm = re.match(r"(\S+) (review|thread|comment) by (@\S+)", body.strip())
                if pm:
                    kind, title = pm.group(1), f"{pm.group(1)} {pm.group(2)} by {pm.group(3)}: " + body.strip().split("\n", 1)[-1][:70]
            r = {"rid": rid, "rank": rank, "title": title, "fresh": c["id"] in fresh_ids, "source_id": c["id"], "score": c["score"],
                 "kind": kind, "text": body.strip(), "inferred": inferred.strip() or None}
            self.results[rid] = r
            out.append(r)
        trace["results"] = out
        return trace

    @staticmethod
    def _paths(gc, chunks):
        def g(o, k):
            return o.get(k) if isinstance(o, dict) else getattr(o, k, None)

        if not gc:
            return []
        title_by_chunk = {c.get("chunk_uuid"): c["title"] for c in chunks}
        paths = []
        for rel in (g(gc, "chunk_relations") or []) + (g(gc, "query_paths") or []):
            for t in g(rel, "triplets") or []:
                src, tgt, r = g(t, "source"), g(t, "target"), g(t, "relation")
                paths.append({
                    "source": g(src, "name"), "source_type": g(src, "type"),
                    "predicate": g(r, "canonical_predicate"), "target": g(tgt, "name"), "target_type": g(tgt, "type"),
                    "context": g(r, "context"), "score": g(rel, "relevancy_score"),
                    "via": title_by_chunk.get(g(r, "chunk_id"), g(r, "chunk_id")),
                })
        seen, uniq = set(), []
        for p in paths:
            key = (p["source"], p["predicate"], p["target"])
            if key not in seen:
                seen.add(key)
                uniq.append(p)
        return uniq[:12]

    def _for_model(self, trace):
        lines = [f"[{r['rid']}] (score {r['score']:.3f}, {r['kind']}) {r['title']}\n{r['text'][:900]}" for r in trace["results"]]
        if trace.get("paths"):
            lines.append("Graph paths: " + "; ".join(f"{p['source']} -{p['predicate']}-> {p['target']}" for p in trace["paths"]))
        return "\n\n".join(lines) or "no results"

    # ------------------------------------------------------------ tools
    def tool(self, name, args):
        app = self.app
        if name in SEARCH_TOOLS:
            trace = self._search(args["query"], name)
            return trace, {"results": self._for_model(trace)}

        if name == "generate_creative":
            ctx = list(self.results.values())
            city = args.get("placement") or "Meta feed 4:5"
            # The control must not see memory at all, including memory the agent baked into its brief:
            # it gets the user's original words only.
            user_brief = next((m["text"] for m in reversed(self.history) if m["role"] == "user"), args["brief"])
            jobs = {"brain": (args["brief"], ctx)}
            if args.get("compare_without_brain"):
                jobs["plain"] = (user_brief, None)
            with ThreadPoolExecutor(2) as ex:
                futs = {k: ex.submit(app.make_creative, b, city, v) for k, (b, v) in jobs.items()}
                outs = {k: f.result() for k, f in futs.items()}
            trace = {"brief": args["brief"], "control_brief": jobs.get("plain", (None,))[0], "placement": city, "context_ids": [r["rid"] for r in ctx], **outs}
            b = outs["brain"]
            summary = {"headline": b["headline"], "visual": b["visual"], "image_url": b["image_url"],
                       "decisions": b["decisions"], "plain_headline": outs.get("plain", {}).get("headline")}
            return trace, summary

        if name == "remember_feedback":
            fb = {"id": f"fb_{int(time.time())}", "date": date.today().isoformat(), "status": "chat",
                  "from": args.get("sender") or "Account manager (relayed)", "on": args.get("on") or "general", "text": args["text"]}
            t = time.time()
            app.brain.remember(fb)
            ack_ms = int((time.time() - t) * 1000)
            searchable_s = app.brain.wait_searchable(fb["id"], args["text"])
            trace = {"stored": fb, "collection": brain_mod.FEEDBACK, "type": "memory", "infer": True,
                     "ingest_ack_ms": ack_ms, "searchable_after_s": searchable_s}
            return trace, {"stored": True, "searchable": searchable_s is not None,
                           "note": "Stored and indexed. It will be retrieved by future feedback searches."}

        if name == "suggest_skills":
            out = app.suggest_skills()
            return out, {"skills": [{k: s[k] for k in ("name", "title", "description", "skill")} for s in out["skills"]]}

        if name == "promote_skill":
            out = app.promote_skill(app.Skill(**{k: args[k] for k in ("name", "title", "description", "skill")}))
            return out, {"promoted": out["skill"]["name"]}

        return {"error": f"unknown tool {name}"}, {"error": "unknown tool"}

    # ------------------------------------------------------------ loop
    def run(self):
        # Result ids are per turn; strip old citation markers so the model can't reuse stale ids.
        strip = lambda t: re.sub(r"\s*\[(?:" + ID_RE + r"(?:,\s*)?)+\]", "", t)
        contents = [types.Content(role="user" if m["role"] == "user" else "model", parts=[types.Part(text=strip(m["text"]))])
                    for m in self.history]
        cfg = types.GenerateContentConfig(
            system_instruction=SYSTEM, tools=TOOLS, temperature=0.4,
            thinking_config=types.ThinkingConfig(include_thoughts=True),
        )
        for step in range(8):
            resp = self.app.gemini().models.generate_content(model=self.app.TEXT_MODEL, contents=contents, config=cfg)
            cand = resp.candidates[0].content
            contents.append(cand)
            calls, text = [], []
            for p in cand.parts or []:
                if getattr(p, "thought", False) and p.text:
                    yield {"type": "thought", "text": p.text}
                elif p.function_call:
                    calls.append(p.function_call)
                elif p.text:
                    text.append(p.text)
            if not calls:
                answer = "".join(text).strip()
                found = set(re.findall(r"\b(" + ID_RE + r")\b", answer))
                bogus = found - set(self.results)
                if bogus:  # cited something not retrieved this turn: drop the marker
                    answer = re.sub(r"\[((?:" + ID_RE + r"(?:,\s*)?)+)\]", lambda m: (lambda keep: f"[{', '.join(keep)}]" if keep else "")(
                        [i for i in re.split(r",\s*", m.group(1)) if i in self.results]), answer)
                cited = sorted(found & set(self.results), key=lambda x: (x[0], int(x[1:])))
                yield {"type": "answer", "text": answer, "cited": cited}
                return
            responses = []
            for fc in calls:
                args = dict(fc.args or {})
                yield {"type": "tool_call", "name": fc.name, "args": args}
                t = time.time()
                try:
                    trace, result = self.tool(fc.name, args)
                except Exception as e:  # surface tool errors to the agent and the trace
                    trace, result = {"error": str(e)[:400]}, {"error": str(e)[:400]}
                yield {"type": "tool_result", "name": fc.name, "ms": int((time.time() - t) * 1000), "trace": trace}
                responses.append(types.Part.from_function_response(name=fc.name, response=result))
            contents.append(types.Content(role="user", parts=responses))
        yield {"type": "answer", "text": "I hit my step limit for this turn.", "cited": []}
