"""Entity profiles for the Explore page: what the brain knows about one product, campaign,
archetype, review theme, competitor or platform, assembled from the same seed data that is in HydraDB."""
import json
from collections import Counter, defaultdict
from pathlib import Path

import build_tidelight as bt
import tidelight_spec as S

SEED = Path(__file__).parent / "seed" / "tidelight"


def _voice():
    return json.loads((SEED / "voice.json").read_text())


def _sent(vs):
    c = Counter(v["sentiment"] for v in vs)
    n = max(len(vs), 1)
    return {"positive": c.get("positive", 0), "mixed": c.get("mixed", 0) + c.get("neutral", 0), "negative": c.get("negative", 0),
            "pct_positive": round(100 * c.get("positive", 0) / n)}


def _quote(v):
    return {"text": v["body"][:280], "who": f"@{v['author']}", "where": v["platform"], "date": v["date"],
            "rating": v.get("rating"), "sentiment": v["sentiment"], "skin": v.get("skin")}


def build():
    voice = _voice()
    perf = bt.rollup(json.loads((SEED / "ad_daily.json").read_text()))
    camps = {c["id"]: c for c in S.CAMPAIGNS}
    crs = [dict(zip(["cid", "id", "platform", "format", "archetype", "product", "headline", "visual", "roas_t", "ctr_t", "fat_t", "score", "pos", "neg"], x))
           for x in S.CREATIVES]
    for c in crs:
        p = perf.get(c["id"])
        c["roas"] = round(p["roas"], 2) if p else None
        c["fatigued"] = bool(p and p["fatigued"])
        c["verdict"] = "Never ran" if not p else "Winner" if p["roas"] >= 2.5 else "Underperformer" if p["roas"] < 1.8 else "Average"
    fb = [{"id": a, "creative": cr, "status": st, "who": who, "text": t} for a, cr, st, who, t in S.APPROVALS] + \
         [{"id": a, "creative": cr, "status": st, "who": who, "text": t} for a, cr, st, who, t in S.CREATIVE_FEEDBACK]
    camp_roas = {}
    for cid in camps:
        live = [(perf[c["id"]]) for c in crs if c["cid"] == cid and c["id"] in perf]
        sp = sum(p["spend"] for p in live)
        camp_roas[cid] = (round(sum(p["roas"] * p["spend"] for p in live) / max(sp, 1), 2), round(sp))

    def target(c):
        try:
            return float(c["kpi"].split("ROAS ")[1].split()[0])
        except (IndexError, ValueError):
            return None

    def cref(c):
        return {"id": f"creative:{c['id']}", "name": f"{c['id']} · {c['headline']}"}

    def creative_rows(cs):
        return [{"cells": [c["id"], c["headline"], c["archetype"], c["platform"], f"{c['roas']:.2f}x" if c["roas"] is not None else "–"],
                 "tag": ("fatiguing" if c["fatigued"] else c["verdict"]), "link": f"archetype:{c['archetype']}"}
                for c in sorted(cs, key=lambda c: -(c["roas"] or 0))]

    def fb_quotes(cids):
        return [{"text": f["text"], "who": f["who"], "where": f"{f['status']} · {f['creative']}", "sentiment": "negative" if f["status"] in ("rejected", "sent_back", "dislike") else "positive"}
                for f in fb if f["creative"] in cids]

    E = {}

    # products
    for p in S.PRODUCTS:
        name = p["name"]
        pcs = [c for c in crs if c["product"] == name]
        pcamps = [c for c in S.CAMPAIGNS if c["product"] == name]
        pv = [v for v in voice if name in v["product"]]
        themes = Counter(v["theme"] for v in pv)
        live = [c for c in pcs if c["roas"] is not None]
        spend = sum(perf[c["id"]]["spend"] for c in live)
        roas = round(sum(perf[c["id"]]["roas"] * perf[c["id"]]["spend"] for c in live) / spend, 2) if spend else None
        s = _sent(pv)
        E[f"product:{name}"] = {
            "type": "product", "name": name, "subtitle": f"{p['category']} · ${p['price']} · {p['size']}",
            "signal": f"{roas:.2f}x ROAS" if roas else f"{len(pv)} mentions",
            "status": ("ok" if roas >= 2.5 else "bad" if roas < 1.8 else "warn") if roas else None, "weight": len(pv) + 4 * len(pcs),
            "metrics": [["Blended ROAS", f"{roas:.2f}x" if roas else "–"], ["Campaigns", len(pcamps)], ["Creatives", len(pcs)],
                        ["Consumer mentions", len(pv)], ["Positive", f"{s['pct_positive']}%" if pv else "–"]],
            "sections": [
                {"title": "Why it sells", "kind": "text", "text": " · ".join(p["rtb"]) + (f"\n\nNote: {p['notes']}" if p.get("notes") else "")},
                {"title": "Campaigns", "kind": "table", "cols": ["Campaign", "Flight", "ROAS", "Target"],
                 "rows": [{"cells": [c["name"], f"{c['flight'][0]} → {c['flight'][1]}", f"{camp_roas[c['id']][0]:.2f}x", c["kpi"]],
                           "tag": "beat target" if target(c) and camp_roas[c["id"]][0] >= target(c) else ("missed" if target(c) else ""), "link": f"campaign:{c['name']}"} for c in pcamps]},
                {"title": "Creatives, best first", "kind": "table", "cols": ["ID", "Headline", "Archetype", "Platform", "ROAS"], "rows": creative_rows(pcs)},
                {"title": "What consumers talk about", "kind": "bars", "rows": [{"label": t, "n": n, "link": f"theme:{t}",
                  "sentiment": Counter(v["sentiment"] for v in pv if v["theme"] == t).most_common(1)[0][0]} for t, n in themes.most_common(6)]},
                {"title": "In their words", "kind": "quotes", "rows": [_quote(v) for v in sorted(pv, key=lambda v: -v.get("likes", 0))[:4]]},
                {"title": "Client feedback on its ads", "kind": "quotes", "rows": fb_quotes({c["id"] for c in pcs})},
            ]}

    # campaigns
    for c in S.CAMPAIGNS:
        ccs = [x for x in crs if x["cid"] == c["id"]]
        roas, spend = camp_roas[c["id"]]
        t = target(c)
        during = [v for v in voice if c["product"] in v["product"] and c["flight"][0] <= v["date"] <= c["flight"][1]]
        E[f"campaign:{c['name']}"] = {
            "type": "campaign", "name": c["name"], "subtitle": f"{c['objective']} · {', '.join(c['platforms'])} · {c['flight'][0]} → {c['flight'][1]}",
            "signal": f"{roas:.2f}x" + (f" vs {t}" if t else ""), "status": ("ok" if roas >= t else "bad") if t else None,
            "metrics": [["ROAS", f"{roas:.2f}x"], ["Target", c["kpi"]], ["Spend", f"${spend / 1000:.0f}k"], ["Budget", f"${c['budget_usd'] / 1000:.0f}k"], ["Creatives", len(ccs)]],
            "links": [{"id": f"product:{c['product']}", "name": c["product"]}],
            "sections": [
                {"title": "What we learned", "kind": "text", "text": c["learning"]},
                {"title": "Audience", "kind": "text", "text": c["audience"]},
                {"title": "Creatives, best first", "kind": "table", "cols": ["ID", "Headline", "Archetype", "Platform", "ROAS"], "rows": creative_rows(ccs)},
                {"title": "Client feedback during review", "kind": "quotes", "rows": fb_quotes({x["id"] for x in ccs})},
                {"title": "Consumers during the flight", "kind": "quotes", "rows": [_quote(v) for v in during[:4]]},
            ]}

    # archetypes
    by_arch = defaultdict(list)
    for c in crs:
        by_arch[c["archetype"]].append(c)
    for a, cs in by_arch.items():
        live = [c for c in cs if c["roas"] is not None]
        avg = round(sum(c["roas"] for c in live) / len(live), 2) if live else None
        wins = sum(1 for c in live if c["roas"] >= 2.5)
        E[f"archetype:{a}"] = {
            "type": "archetype", "name": a, "subtitle": "creative archetype", "signal": f"{avg:.2f}x avg" if avg else "–",
            "status": ("ok" if avg >= 2.5 else "bad" if avg < 1.8 else "warn") if avg else None,
            "metrics": [["Avg ROAS", f"{avg:.2f}x" if avg else "–"], ["Creatives", len(cs)], ["Win rate", f"{round(100 * wins / max(len(live), 1))}%"],
                        ["Best", max(live, key=lambda c: c["roas"])["id"] if live else "–"]],
            "sections": [
                {"title": "Every creative that used it", "kind": "table", "cols": ["ID", "Headline", "Archetype", "Platform", "ROAS"], "rows": creative_rows(cs)},
                {"title": "Client feedback", "kind": "quotes", "rows": fb_quotes({c["id"] for c in cs})},
            ]}

    # review themes
    by_theme = defaultdict(list)
    for v in voice:
        by_theme[v["theme"]].append(v)
    for t, vs in by_theme.items():
        s = _sent(vs)
        dates = sorted(v["date"] for v in vs)
        months = Counter(v["date"][:7] for v in vs)
        E[f"theme:{t}"] = {
            "type": "theme", "name": t, "subtitle": f"review theme · {dates[0]} → {dates[-1]}", "signal": f"{len(vs)} mentions",
            "status": "ok" if s["positive"] >= s["negative"] else "bad",
            "metrics": [["Mentions", len(vs)], ["Positive", s["positive"]], ["Negative", s["negative"]], ["Platforms", len({v['platform'] for v in vs})]],
            "links": [{"id": f"product:{p}", "name": p} for p in sorted({v["product"] for v in vs}) if f"product:{p}" in E],
            "sections": [
                {"title": "Mentions by month", "kind": "spark", "rows": [{"label": m, "n": n} for m, n in sorted(months.items())]},
                {"title": "Where it's said", "kind": "bars", "rows": [{"label": p, "n": n, "link": f"platform:{p}"} for p, n in Counter(v["platform"] for v in vs).most_common()]},
                {"title": "In their words", "kind": "quotes", "rows": [_quote(v) for v in sorted(vs, key=lambda v: -v.get("likes", 0))[:6]]},
            ]}

    # competitors
    for c in S.COMPETITORS:
        n = c["competitor_name"]
        mv = [v for v in voice if n.split()[0] in v["body"].lower()]
        E[f"competitor:{n}"] = {
            "type": "competitor", "name": n, "subtitle": f"competitor · {c['pricing']}", "signal": f"{round(100 * c['share_of_voice'])}% SOV",
            "metrics": [["Share of voice", f"{round(100 * c['share_of_voice'])}%"], ["Tidelight SOV", f"{round(100 * S.TIDELIGHT_SOV)}%"], ["Pricing", c["pricing"]], ["Consumer mentions", len(mv)]],
            "sections": [
                {"title": "How they compete", "kind": "text", "text": c["competing_front"]},
                {"title": "Their ad activity", "kind": "text", "text": c["ad_activity"]},
                {"title": "Consumers comparing us", "kind": "quotes", "rows": [_quote(v) for v in mv[:5]]},
            ]}

    # platforms
    by_pl = defaultdict(list)
    for v in voice:
        by_pl[v["platform"]].append(v)
    for p, vs in by_pl.items():
        s = _sent(vs)
        rated = [v["rating"] for v in vs if v.get("rating")]
        E[f"platform:{p}"] = {
            "type": "platform", "name": p, "subtitle": "consumer voice source", "signal": f"{len(vs)} posts",
            "metrics": [["Posts", len(vs)], ["Avg rating", f"{sum(rated) / len(rated):.1f}★" if rated else "–"], ["Positive", f"{s['pct_positive']}%"], ["Negative", s["negative"]]],
            "sections": [
                {"title": "Top themes here", "kind": "bars", "rows": [{"label": t, "n": n, "link": f"theme:{t}"} for t, n in Counter(v["theme"] for v in vs).most_common(6)]},
                {"title": "In their words", "kind": "quotes", "rows": [_quote(v) for v in sorted(vs, key=lambda v: -v.get("likes", 0))[:5]]},
            ]}

    # creative profiles (reached via links, not listed in the directory)
    for c in crs:
        camp = camps[c["cid"]]
        p = perf.get(c["id"])
        E[f"creative:{c['id']}"] = {
            "type": "creative", "name": f"{c['id']} · {c['headline']}", "subtitle": f"{c['platform']} {c['format']} · {camp['name']}", "signal": c["verdict"], "hidden": True,
            "status": "warn" if c["fatigued"] else {"Winner": "ok", "Underperformer": "bad", "Never ran": "bad"}.get(c["verdict"]),
            "metrics": [["ROAS", f"{c['roas']:.2f}x" if c["roas"] is not None else "–"], ["CTR", f"{p['ctr']:.2f}%" if p else "–"],
                        ["Frequency (last wk)", f"{p['last']['frequency']:.1f}" if p else "–"], ["Score", f"{c['score']}/10"]],
            "links": [{"id": f"campaign:{camp['name']}", "name": camp["name"]}, {"id": f"product:{c['product']}", "name": c["product"]}, {"id": f"archetype:{c['archetype']}", "name": c["archetype"]}],
            "sections": [{"title": "Visual", "kind": "text", "text": c["visual"]},
                         {"title": "What worked / didn't", "kind": "text", "text": f"Positives: {', '.join(c['pos']) or '–'}\nNegatives: {', '.join(c['neg']) or '–'}" + ("\nFatiguing: refresh this concept." if c["fatigued"] else "")},
                         {"title": "Client feedback", "kind": "quotes", "rows": fb_quotes({c["id"]})}]}
    # link creative rows to creative profiles
    for e in E.values():
        for sec in e["sections"]:
            if sec.get("cols", [None])[0] == "ID":
                for r in sec["rows"]:
                    r["link"] = f"creative:{r['cells'][0]}"
    for e in E.values():
        e["sections"] = [s for s in e["sections"] if s.get("rows") or s.get("text")]
    return E


_cache = None


def entities():
    global _cache
    if _cache is None:
        _cache = build()
    return _cache
