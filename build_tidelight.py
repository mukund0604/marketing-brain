"""Build the Tidelight Marketing Brain dataset and its HydraDB payloads.

Layers -> HydraDB collections (one tool per layer in the agent):
  tidelight_brand      guidelines sections, products (+ tier overrides), agent skills, org memory
  tidelight_campaigns  historic campaigns + every creative joined with ClickHouse-shaped daily performance
  tidelight_voice      consumer reviews / Reddit threads / TikTok + IG comments (app sources) + theme aggregates
  tidelight_market     competitors, share of voice, category trends
  tidelight_feedback   (memory) client approvals, send-backs, rejections, likes/dislikes
Each knowledge item carries a BYOG graph_payload in BrandOS labels/relationship types.
"""
import json
import random
import zlib
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import tidelight_spec as S

ROOT = Path(__file__).parent
OUT = ROOT / "seed" / "tidelight"
NS = "tidelight"
ORG = "org_demo_tidelight"
COLLECTIONS = {"brand": "tidelight_brand", "campaigns": "tidelight_campaigns", "voice": "tidelight_voice",
               "market": "tidelight_market", "feedback": "tidelight_feedback"}
SECTION_REL = {"ColorPalette": "HAS_COLOR_PALETTE", "Typography": "HAS_TYPOGRAPHY", "LogoUsage": "HAS_LOGO_USAGE",
               "LayoutSystem": "HAS_LAYOUT_SYSTEM", "VisualIdentity": "HAS_VISUAL_IDENTITY", "ToneOfVoice": "HAS_TONE_OF_VOICE",
               "ComplianceRules": "HAS_COMPLIANCE_RULES", "CreativeArchetypes": "HAS_CREATIVE_ARCHETYPES",
               "BrandAmbassador": "HAS_BRAND_AMBASSADOR_GUIDELINES"}


def render(v, indent=""):
    if isinstance(v, dict):
        return "\n".join(f"{indent}- {k}: {render(x, indent + '  ') if isinstance(x, (dict, list)) else x}" for k, x in v.items())
    if isinstance(v, list):
        if all(isinstance(x, str) for x in v):
            return "; ".join(v)
        return "\n" + "\n".join(f"{indent}  * " + (", ".join(f"{k}: {y}" for k, y in x.items()) if isinstance(x, dict) else str(x)) for x in v)
    return str(v)


def E(name, typ):
    return {"name": name, "type": typ, "namespace": NS}


def R(a, pred, b, ctx, when=None):
    r = {"source": a, "target": b, "predicate": pred, "context": ctx}
    if when:
        r["temporal_details"] = when
    return r


def item(iid, title, body, kind="custom", provider="brandos", ts="2026-10-01T00:00:00Z", extra=None, fields=None):
    return {"id": iid, "title": title, "kind": kind, "provider": provider, "timestamp": ts,
            "fields": {"kind": kind, "body": body, **(fields or {})}, "metadata": {},
            "additional_metadata": {"brand": NS, **(extra or {})}}


# ------------------------------------------------------------------ ClickHouse-shaped daily performance
def daily_rows():
    random.seed(5)
    camps = {c["id"]: c for c in S.CAMPAIGNS}
    by_c = defaultdict(list)
    for cr in S.CREATIVES:
        by_c[cr[0]].append(cr)
    rows = []
    for cid, crs in by_c.items():
        c = camps[cid]
        d0, d1 = date.fromisoformat(c["flight"][0]), date.fromisoformat(c["flight"][1])
        days = (d1 - d0).days + 1
        live = [x for x in crs if x[8] > 0]
        weights = [x[8] ** 1.5 for x in live]  # delivery skews to winners, like Advantage+ does
        for x, w in zip(live, weights):
            _, crid, platform, fmt, arch, prod, headline, visual, roas, ctr, fatigue, *_ = x
            budget = c["budget_usd"] * w / sum(weights)
            run_days = 4 if crid == "tl_502" else days  # pulled after 4 days
            cpm = {"meta": 11.5, "tiktok": 8.2, "google": 9.0}[platform]
            for d in range(run_days):
                decay = 1 - fatigue * (d / max(run_days - 1, 1)) ** 1.3
                spend = round(budget / run_days * random.uniform(0.8, 1.2), 2)
                imp = int(spend / cpm * 1000 * random.uniform(0.9, 1.1))
                clicks = int(imp * ctr / 100 * decay * random.uniform(0.9, 1.1))
                reach = int(imp / (1.15 + fatigue * 6.5 * d / max(run_days - 1, 1)))
                value = round(spend * roas * decay * random.uniform(0.85, 1.15), 2)
                orders = max(0, int(value / 46))
                rows.append({"table": {"meta": "dist_meta_ad_daily", "tiktok": "tiktok_ad_daily", "google": "dist_google_ad_daily"}[platform],
                             "organization_id": ORG, "platform": platform, "date": str(d0 + timedelta(days=d)), "campaign_id": cid,
                             "campaign_name": c["name"], "ad_id": f"{platform}:{zlib.crc32(crid.encode())}", "creative_id": crid,
                             "spend": spend, "impressions": imp, "clicks": clicks, "reach": reach, "purchases": orders,
                             "purchase_value": value})
    return rows


def rollup(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["creative_id"]].append(r)
    out = {}
    for crid, rs in by.items():
        rs.sort(key=lambda r: r["date"])
        def agg(xs):
            sp = sum(r["spend"] for r in xs); im = sum(r["impressions"] for r in xs)
            return {"spend": sp, "impressions": im, "ctr": 100 * sum(r["clicks"] for r in xs) / max(im, 1),
                    "roas": sum(r["purchase_value"] for r in xs) / max(sp, 1), "cpa": sp / max(sum(r["purchases"] for r in xs), 1),
                    "frequency": im / max(sum(r["reach"] for r in xs), 1)}
        k = max(1, min(7, len(rs) // 3))
        tot, first, last = agg(rs), agg(rs[:k]), agg(rs[-k:])
        out[crid] = {**tot, "first": first, "last": last, "days": len(rs), "from": rs[0]["date"], "to": rs[-1]["date"],
                     "roas_change": 100 * (last["roas"] / max(first["roas"], 1e-9) - 1),
                     "fatigued": (last["roas"] < first["roas"] * 0.8) or last["frequency"] > 3.5}
    return out


# ------------------------------------------------------------------ build
def build():
    voice = json.loads((OUT / "voice.json").read_text())
    rows = daily_rows()
    perf = rollup(rows)
    payload = {k: {"items": [], "graph": {}} for k in COLLECTIONS}
    graph_nodes, graph_edges = {}, []  # for the Brain view

    def add(layer, it, ents, rels):
        payload[layer]["items"].append(it)
        payload[layer]["graph"][it["id"]] = {"entities": ents, "relations": rels}
        for k, e in ents.items():
            graph_nodes[(e["type"], e["name"])] = {"id": f"{e['type']}:{e['name']}", "label": e["name"], "type": e["type"], "layer": layer}
        for r in rels:
            a, b = ents[r["source"]], ents[r["target"]]
            graph_edges.append({"from": f"{a['type']}:{a['name']}", "to": f"{b['type']}:{b['name']}", "type": r["predicate"]})

    brand = E("tidelight", "BRAND")
    hub = E("tidelight guidelines", "GUIDELINES")

    # ---------------- brand book
    g = S.GUIDELINES
    add("brand", item("tl_guidelines", "Tidelight · Guidelines hub: positioning, USPs, personas",
                      f"{S.BRAND['summary']}\n" + render({k: v for k, v in g.items()})),
        {"b": brand, "g": hub}, [R("b", "HAS_GUIDELINES", "g", "Tidelight brand guidelines (v2026.09)")])
    for sec, props in S.SECTIONS.items():
        add("brand", item(f"tl_sec_{sec.lower()}", f"Tidelight · {sec}", render(props)),
            {"g": hub, "s": E(f"tidelight {sec}", sec.upper())}, [R("g", SECTION_REL[sec], "s", f"{sec} section of the Tidelight brand book")])
    for p in S.PRODUCTS:
        ents = {"b": brand, "p": E(p["name"], "PRODUCT")}
        rels = [R("b", "HAS_PRODUCT", "p", f"Tidelight sells {p['name']} (${p['price']}, {p['category']})")]
        if p.get("compliance_override") or p.get("color_override"):
            ents["pg"] = E(f"{p['name']} guidelines", "PRODUCTGUIDELINES")
            rels.append(R("p", "PRODUCT_HAS_GUIDELINES", "pg", p.get("compliance_override") or p.get("color_override")))
        add("brand", item(f"tl_prod_{p['slug']}", f"Tidelight · Product: {p['name']}", render(p)), ents, rels)
    for sk in S.AGENT_SKILLS:
        add("brand", item(f"tl_skill_{sk['name']}", f"Tidelight · AgentSkill: {sk['title']}", f"{sk['description']}\n{sk['skill']}"),
            {"b": brand, "s": E(sk["name"], "AGENTSKILL")}, [R("b", "HAS_AGENT_SKILL", "s", sk["description"])])
    for m in S.ORG_MEMORY:
        add("brand", item(f"tl_orgmem_{m['key']}", f"Tidelight · Org memory: {m['key']}", m["content"]),
            {"b": brand, "m": E(m["key"], "ORGMEMORY")}, [R("b", "HAS_ORG_MEMORY", "m", m["content"])])

    # ---------------- campaigns + creatives (Neo4j Ad/Creative/Score + ClickHouse perf)
    by_c = defaultdict(list)
    for cr in S.CREATIVES:
        by_c[cr[0]].append(cr)
    camp_results = {}
    for c in S.CAMPAIGNS:
        crs = by_c[c["id"]]
        live = [perf[x[1]] for x in crs if x[1] in perf]
        sp = sum(p["spend"] for p in live)
        roas = sum(p["roas"] * p["spend"] for p in live) / max(sp, 1)
        best = max((x for x in crs if x[1] in perf), key=lambda x: perf[x[1]]["roas"])
        camp_results[c["id"]] = {"spend": sp, "roas": roas}
        body = (f"Campaign {c['id']} '{c['name']}' | objective {c['objective']} | platforms {', '.join(c['platforms'])} | "
                f"flight {c['flight'][0]} to {c['flight'][1]} | budget ${c['budget_usd']:,} | product {c['product']}\n"
                f"Audience: {c['audience']}\nTarget KPI: {c['kpi']}\n"
                f"Actual (ClickHouse): spend ${sp:,.0f}, blended ROAS {roas:.2f}x, {len(crs)} creatives, best {best[1]} \"{best[6]}\" ({perf[best[1]]['roas']:.2f}x)\n"
                f"Post-campaign learning: {c['learning']}")
        add("campaigns", item(f"tl_{c['id']}", f"Tidelight · Campaign: {c['name']} · {c['product']} ({c['flight'][0][:7]})", body, ts=f"{c['flight'][1]}T00:00:00Z",
                              extra={"roas": round(roas, 2)}),
            {"b": brand, "c": E(c["name"], "CAMPAIGN"), "p": E(c["product"], "PRODUCT")},
            [R("b", "RAN_CAMPAIGN", "c", f"Tidelight ran {c['name']}: ROAS {roas:.2f}x on ${sp:,.0f}", f"{c['flight'][0]} to {c['flight'][1]}"),
             R("c", "PROMOTES_PRODUCT", "p", f"{c['name']} promoted {c['product']}")])
    for (cid, crid, platform, fmt, arch, prod, headline, visual, roas, ctr, fatigue, score, pos, neg) in S.CREATIVES:
        camp = next(c for c in S.CAMPAIGNS if c["id"] == cid)
        p = perf.get(crid)
        if p:
            verdict = "WINNER" if p["roas"] >= 2.5 else "UNDERPERFORMER" if p["roas"] < 1.8 else "AVERAGE"
            perf_txt = (f"Performance {p['from']} to {p['to']} ({p['days']} days, {verdict}): spend ${p['spend']:,.0f}, ROAS {p['roas']:.2f}x, "
                        f"CTR {p['ctr']:.2f}%, CPA ${p['cpa']:.0f}, frequency {p['frequency']:.2f}\n"
                        f"Trend: ROAS {p['first']['roas']:.2f}x first week -> {p['last']['roas']:.2f}x last week ({p['roas_change']:+.0f}%), "
                        f"frequency {p['last']['frequency']:.1f}{' | FATIGUE: refresh this concept' if p['fatigued'] else ''}")
        else:
            verdict, perf_txt = "NEVER RAN", "Never ran (killed in review before launch)."
        body = (f"Creative {crid} | {platform} {fmt} | campaign {camp['name']} ({cid}) | archetype {arch} | product {prod}\n"
                f"Headline: \"{headline}\"\nVisual: {visual}\n{perf_txt}\n"
                f"Creative score {score}/10. Positives: {', '.join(pos) or '-'}. Negatives: {', '.join(neg) or '-'}")
        add("campaigns", item(f"tl_cr_{crid}", f"Tidelight · Creative {crid} · {prod} · {camp['name']}: {headline}", body, ts=f"{camp['flight'][1]}T00:00:00Z",
                              extra={"verdict": verdict, "roas": round(p["roas"], 2) if p else None}),
            {"c": E(camp["name"], "CAMPAIGN"), "ad": E(f"ad {crid}", "AD"), "cr": E(f"creative {crid}", "CREATIVE"),
             "a": E(arch, "CREATIVEARCHETYPE"), "p": E(prod, "PRODUCT")},
            [R("c", "HAS_AD", "ad", f"{camp['name']} ran {crid} on {platform}"),
             R("ad", "HAS_CREATIVE", "cr", f"{crid}: {visual}"),
             R("ad", "CREATIVE_HAS_ARCHETYPE", "a", f"{crid} is a {arch} creative; {verdict} at {p['roas']:.2f}x ROAS" if p else f"{crid} is {arch}; never ran"),
             R("ad", "PROMOTES_PRODUCT", "p", f"{crid} promotes {prod}")])

    # ---------------- consumer voice (app sources: review / comment / thread)
    for v in voice:
        kind = {"review": "comment", "thread": "message", "comment": "comment"}[v["kind"]]  # HydraDB app-source classes
        stars = f"{v['rating']}★ " if v.get("rating") else ""
        body = (f"{v['platform']} {v['kind']} by @{v['author']} on {v['date']} about {v['product']}"
                f"{' (' + v['skin'] + ')' if v.get('skin') else ''} | {stars}sentiment {v['sentiment']} | {v.get('likes', 0)} likes\n"
                f"{('Title: ' + v['title'] + chr(10)) if v.get('title') else ''}{v['body']}")
        add("voice", item(f"tl_{v['id']}", f"Tidelight · {v['platform']} {v['kind']}: {v.get('title') or v['body'][:60]}", body, kind=kind,
                          provider=v["platform"], ts=f"{v['date']}T12:00:00Z",
                          extra={"platform": v["platform"], "rating": v.get("rating"), "sentiment": v["sentiment"], "theme": v["theme"]},
                          fields={"author": v["author"], "created_at": f"{v['date']}T12:00:00Z"}),
            {"u": E(f"@{v['author']}", "CONSUMER"), "p": E(v["product"], "PRODUCT"), "t": E(v["theme"], "REVIEWTHEME"), "pl": E(v["platform"], "PLATFORM")},
            [R("u", "TALKED_ABOUT", "p", f"@{v['author']} ({v['sentiment']}) on {v['platform']}: {v['body'][:120]}", v["date"]),
             R("u", "RAISED_THEME", "t", f"{v['theme']} ({v['sentiment']})", v["date"]),
             R("u", "POSTED_ON", "pl", f"posted on {v['platform']}", v["date"])])
    themes = defaultdict(list)
    for v in voice:
        themes[v["theme"]].append(v)
    for t, vs in themes.items():
        plats = Counter(v["platform"] for v in vs)
        prods = Counter(v["product"] for v in vs)
        rated = [v["rating"] for v in vs if v.get("rating")]
        sent = Counter(v["sentiment"] for v in vs)
        dates = sorted(v["date"] for v in vs)
        body = (f"Review theme '{t}': {len(vs)} mentions ({sent.most_common()}) from {dates[0]} to {dates[-1]}.\n"
                f"Platforms: {dict(plats)}. Products: {dict(prods)}. Avg rating where rated: {sum(rated) / len(rated):.1f}★\n" if rated else
                f"Review theme '{t}': {len(vs)} mentions ({sent.most_common()}) from {dates[0]} to {dates[-1]}.\nPlatforms: {dict(plats)}. Products: {dict(prods)}.\n")
        body += "Example quotes: " + " | ".join(f"\"{v['body'][:140]}\" ({v['platform']})" for v in vs[:3])
        add("voice", item(f"tl_theme_{zlib.crc32(t.encode())}", f"Tidelight · ReviewTheme: {t}", body),
            {"b": brand, "t": E(t, "REVIEWTHEME")}, [R("b", "HAS_REVIEW_THEME", "t", f"{t}: {len(vs)} mentions, mostly {sent.most_common(1)[0][0]}")])

    # ---------------- market
    for c in S.COMPETITORS:
        add("market", item(f"tl_{c['id']}", f"Tidelight · Competitor: {c['competitor_name']}", render(c)),
            {"b": brand, "c": E(c["competitor_name"], "COMPETITOR")},
            [R("b", "HAS_COMPETITOR", "c", f"competes on {c['competing_front']}; share of voice {c['share_of_voice']:.0%}")])
    sov = {c["competitor_name"]: c["share_of_voice"] for c in S.COMPETITORS} | {"tidelight": S.TIDELIGHT_SOV}
    add("market", item("tl_sov", "Tidelight · ShareOfVoice (last 90 days)",
                       "Share of category voice across social, reviews and search, last 90 days: " +
                       ", ".join(f"{k} {v:.0%}" for k, v in sorted(sov.items(), key=lambda x: -x[1])) +
                       "\nTidelight rank #3 of 4; gained +5 pts since the tinted SPF relaunch (Jun 2026)."),
        {"b": brand, "s": E("share of voice", "SHAREOFVOICE")}, [R("b", "HAS_SHARE_OF_VOICE", "s", f"Tidelight SOV {S.TIDELIGHT_SOV:.0%}")])
    trends = [
        ("Barrier-repair overtakes 'glow' in search", "Google Trends US: 'skin barrier' searches +46% YoY; 'glass skin' -18%. Ceramide + 'fragrance-free' co-mentions rising on TikTok."),
        ("Mineral SPF inclusivity scrutiny", "TikTok #whitecast videos 210M views; creators audit mineral SPFs on deep skin. Brands showing tinted shades on Fitzpatrick IV-VI earn positive comment sentiment."),
        ("Refill skepticism", "Reddit threads question whether refills are cheaper; brands that show $ savings per refill see higher refill attach."),
        ("FTC focus on greenwashing + creator disclosure", "2026 FTC warning letters to 14 beauty brands over 'reef-safe'/'non-toxic' claims and missing #ad."),
    ]
    for i, (t, body) in enumerate(trends):
        add("market", item(f"tl_trend_{i}", f"Tidelight · CategoryTrend: {t}", body),
            {"b": brand, "t": E(t, "CATEGORYTREND")}, [R("b", "OPERATES_IN_TREND", "t", body[:140])])

    # ---------------- feedback (memory)
    cr_by = {c[1]: c for c in S.CREATIVES}
    memories = []
    for aid, crid, status, who, text in S.APPROVALS:
        c = cr_by[crid]
        memories.append({"id": aid, "status": status, "from": who, "media_id": crid,
                         "text": f"Client feedback [{status}] from {who} (re: {crid} \"{c[6]}\", {c[3]} {c[4]} for {c[5]}): {text}"})
    for fid, crid, status, who, text in S.CREATIVE_FEEDBACK:
        c = cr_by[crid]
        memories.append({"id": fid, "status": status, "from": who, "media_id": crid,
                         "text": f"Client feedback [{status}] from {who} (re: {crid} \"{c[6]}\", {c[3]} {c[4]}): {text}"})

    stats = {
        "layers": {k: len(v["items"]) for k, v in payload.items()} | {"feedback": len(memories)},
        "ad_daily_rows": len(rows), "ad_spend": round(sum(r["spend"] for r in rows)), "campaigns": len(S.CAMPAIGNS), "creatives": len(S.CREATIVES),
        "voice_by_platform": dict(Counter(v["platform"] for v in voice)), "voice_by_sentiment": dict(Counter(v["sentiment"] for v in voice)),
        "voice_range": [voice[0]["date"], voice[-1]["date"]], "graph_nodes": len(graph_nodes), "graph_edges": len(graph_edges),
        "graph_relations": sum(len(g["relations"]) for v in payload.values() for g in v["graph"].values()),
    }
    return payload, memories, rows, perf, camp_results, stats, {"nodes": list(graph_nodes.values()), "edges": graph_edges}


if __name__ == "__main__":
    payload, memories, rows, perf, camps, stats, graph = build()
    (OUT / "ad_daily.json").write_text(json.dumps(rows))
    (OUT / "hydra_payload.json").write_text(json.dumps({"collections": COLLECTIONS, "payload": payload, "memories": memories}, indent=1))
    (OUT / "brain_graph.json").write_text(json.dumps(graph))
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    for cid, r in camps.items():
        print(cid, f"ROAS {r['roas']:.2f} spend {r['spend']:,.0f}")
    for crid in ["tl_101", "tl_701", "tl_802", "tl_202"]:
        p = perf[crid]; print(crid, f"roas {p['roas']:.2f} ctr {p['ctr']:.2f} first {p['first']['roas']:.2f} last {p['last']['roas']:.2f} freq {p['last']['frequency']:.1f} fatigued {p['fatigued']}")
