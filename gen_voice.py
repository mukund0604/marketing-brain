"""Generate synthetic consumer voice (reviews, Reddit threads, TikTok/IG comments) for Tidelight
with Gemini, controlled by tidelight_spec.VOICE_THEMES / VOICE_PLATFORMS. Output: seed/tidelight/voice.json
"""
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

import tidelight_spec as S

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
TOTAL = 160
random.seed(11)

DATE_WINDOWS = {
    "white cast on deeper skin (untinted SPF)": ("2025-06-01", "2026-05-31"),
    "tinted SPF finally works on deep skin": ("2026-06-10", "2026-10-10"),
    "vitamin C serum oxidized / turned orange": ("2025-03-01", "2026-02-28"),
    "cleanser pump broke": ("2026-01-05", "2026-04-15"),
    "great gift set, Target exclusive": ("2025-11-15", "2026-01-10"),
}
STYLE = {
    "amazon": "Amazon review: star rating 1-5, short title, 2-6 sentences, sometimes 'Verified Purchase' tone, mentions price/value, typos ok.",
    "target": "Target.com review: rating 1-5, title, 1-4 sentences, mentions in-store/pickup sometimes.",
    "tidelight.com": "Brand-site review: rating 1-5, title, mentions skin type and age range.",
    "trustpilot": "Trustpilot review about the company: rating 1-5, title, about shipping/support/product.",
    "reddit": "Reddit post or comment in r/SkincareAddiction, r/30PlusSkinCare or r/Sensitiveskin: casual, detailed, may compare brands, may include INCI talk; give a post title for posts. No rating.",
    "tiktok": "TikTok comment under a Tidelight ad or creator video: 1-2 short sentences, slang, emoji ok. No rating.",
    "instagram": "Instagram comment under a Tidelight post: 1-2 sentences, emoji ok. No rating.",
}


def plan():
    jobs = []
    for theme, sentiment, share, products in S.VOICE_THEMES:
        n = max(3, round(share * TOTAL))
        plats = random.choices([p for p, _, _ in S.VOICE_PLATFORMS], weights=[w for _, _, w in S.VOICE_PLATFORMS], k=n)
        jobs.append((theme, sentiment, products, plats))
    return jobs


def gen(job):
    theme, sentiment, products, plats = job
    lo, hi = DATE_WINDOWS.get(theme, ("2025-03-01", "2026-10-10"))
    spec = "\n".join(f"{i + 1}. platform={p}: {STYLE[p]}" for i, p in enumerate(plats))
    prompt = f"""Write {len(plats)} realistic, varied consumer posts about the FICTIONAL US skincare brand Tidelight
(San Francisco, fragrance-free, ocean botanicals; products: {', '.join(p['name'] for p in S.PRODUCTS)}).
Competitors (fictional): petal & pine (fragranced 'clean' botanicals), dermafact (cheap clinical drugstore), noma skin (glass-skin K-beauty style).

Theme for ALL items: "{theme}" (overall sentiment: {sentiment}). Products to mention: {', '.join(products)}.
Dates between {lo} and {hi}. Make them sound like different real people: different skin types, tones, ages, cities,
writing styles and lengths. Some mention a second minor point. Do not use real people's names; usernames should be plausible handles.

Items:
{spec}

Return JSON list, same order, each:
{{"platform": "...", "kind": "review|thread|comment", "author": "handle", "date": "YYYY-MM-DD", "rating": 1-5 or null,
  "title": "string or null", "body": "text", "product": "one product name", "likes": int,
  "skin": "e.g. 'deep skin, combination, 34' or null", "sentiment": "positive|negative|mixed|neutral"}}"""
    for attempt in range(3):
        try:
            r = client.models.generate_content(model="gemini-2.5-flash", contents=prompt,
                                               config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.9))
            items = json.loads(r.text)
            break
        except (json.JSONDecodeError, ValueError):
            if attempt == 2:
                raise
    for it in items:
        it["theme"] = theme
    return items


if __name__ == "__main__":
    with ThreadPoolExecutor(8) as ex:
        batches = list(ex.map(gen, plan()))
    items = [it for b in batches for it in b]
    items.sort(key=lambda x: x.get("date") or "")
    for i, it in enumerate(items, 1):
        it["id"] = f"cv_{i:04d}"
        it["kind"] = {"reddit": "thread", "tiktok": "comment", "instagram": "comment"}.get(it["platform"], "review")
    out = ROOT / "seed" / "tidelight" / "voice.json"
    out.write_text(json.dumps(items, indent=1))
    from collections import Counter
    print(len(items), "items", Counter(i["platform"] for i in items), Counter(i["sentiment"] for i in items))
