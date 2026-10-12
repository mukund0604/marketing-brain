## Inspiration

At Zocket we build AI agents that make ads for brands. The question we hear on every sales call is: *"How do you keep the AI on-brand?"* Our own internal wiki has the honest answer. When an agent "keeps forgetting X", someone has to notice and hand-write a rule. Most brands never get those rules. Meanwhile the knowledge that actually matters is spread across silos: brand books in PDFs, ad performance in a warehouse, consumer reviews on Amazon and Reddit, and client feedback buried in approval threads.

We wanted a **marketing brain**: one memory that holds all of it, that every creative agent reads before it makes anything, and that learns from every rejection. Just as important, it should **show its work**, because nobody trusts a black box with their brand.

## What it does

Marketing Brain is a 360° memory for a brand, built on HydraDB, with an agent on top. Our demo brand is **Tidelight**, a fictional San Francisco clean-skincare company.

- **Five memory layers**, each its own HydraDB collection:
  - **Brand book:** color system (hex, Pantone, contrast pairs, banned combinations), type scale per placement, logo rules, layout grid and safe zones, photography and talent rules, voice, and an FDA/FTC compliance rule pack.
  - **Campaigns:** 18 months of campaigns, with every creative joined to its daily ad performance and fatigue signals.
  - **Consumer voice:** reviews and posts from Amazon, Target, Reddit, TikTok, Instagram and Trustpilot.
  - **Market:** competitors, share of voice and category trends.
  - **Client feedback memory:** approvals, send-backs and rejections from the brand, legal and performance leads.
- **An agentic chat.** Ask "how did our SPF campaigns do and what were people saying?" or "make a Meta 4:5 ad for the tinted SPF". The agent decides which layers to search, then answers or generates a creative, citing every source.
- **The Brain trace.** Every reply shows each HydraDB query, the collection and mode, latency, every result ranked by relevancy score, which results the agent **used vs ignored**, the graph paths HydraDB followed, and what HydraDB *inferred* from raw client comments.
- **With-brain vs control.** Generate the same brief with and without memory. The control writes "morning glow" next to a flower (both banned), invents the packaging and skips the FDA wording. The brain version uses the real logo and packshot, shows three skin tones, and includes the exact "Broad Spectrum SPF 30" legal line, all traced to sources.
- **It learns.** Tell it "legal just said X" and it writes a new HydraDB memory, waits until it's searchable, and the next generation retrieves it (tagged **NEW** in the trace) and applies it.
- **Promote to Skill.** It reads the feedback memory, spots corrections that keep coming back, and proposes durable brand skills you can activate with one click.
- **A Brain view** shows everything the brain holds: layers, record counts, sources by platform and sentiment, campaign ROAS against target, share of voice, and an interactive graph explorer.

## How we built it

- **HydraDB** is the memory layer: one database with five collections.
  - Knowledge goes in as **app sources** (`app_knowledge`): reviews and comments with their platform, campaigns and creatives with their performance.
  - Client feedback goes in as **memories with `infer=true`**, so HydraDB extracts the rule behind a raw comment.
  - We used **Bring Your Own Graph** (`graph_payload`) to load the brand's entities and relationships in the same schema as Zocket's production brand graph: `Brand → Guidelines → ColorPalette`, `Campaign → Ad → Creative → CreativeArchetype`, `Consumer → Product → ReviewTheme`. That's 632 relationships.
  - Search is hybrid; "thinking" mode returns graph context.
- **Data:**
  - 248 knowledge records plus 15 memories.
  - 8 campaigns, 23 creatives and roughly $900K of simulated spend across 1,029 daily rows, shaped like our ClickHouse ad tables.
  - 160 consumer posts across 7 platforms.
  - We wrote the brand book, campaigns and approvals by hand. Gemini wrote the consumer voice from a controlled theme spec. Performance comes from code with deliberate winner, loser and fatigue patterns. Everything is synthetic, and the brand and competitors are fictional.
- **Agent:** Gemini 2.5 Flash with function calling: five layer-specific search tools plus `generate_creative`, `remember_feedback`, `suggest_skills` and `promote_skill`. Agent steps and tool results stream to the UI over server-sent events.
- **Creative:** Gemini 3 Pro Image. Like Zocket's production image agent, we attach **verified brand assets** (the logo lockup and product packshots) as reference images instead of letting the model improvise.
- **App:** FastAPI plus a single-page UI (vanilla JS, vis-network for the graph).

## Challenges we ran into

- **Retrieval crowding.** In one combined collection, client feedback drowned out guidelines and performance data. Splitting memory into per-layer collections fixed relevance and made the trace far more readable.
- **Agent routing.** Asked "what are people saying about my campaigns?", the agent searched only client feedback; it read "people" as the client's approvers. Explicit layer routing and descriptive multi-search queries fixed it.
- **Honest comparisons.** At first the control leaked memory, because the agent's enriched brief already contained remembered insights. Now the control gets only the user's original words.
- **Realism.** "No people in hero ads" plus "show the pour" produced a bottle floating in mid-air. We added physical-realism rules, and a cropped hand doesn't count as "people". Logos and packaging were hallucinated until we attached verified assets.
- **Async indexing.** A new memory takes roughly 10–20 seconds to become searchable, and graph context only appears once HydraDB finishes building the graph. The trace shows those timings honestly instead of hiding them.
- **Stale citations.** Result IDs are per turn, so we strip and validate citations to stop the agent citing sources it never retrieved.

## Accomplishments that we're proud of

- A trace that makes retrieval auditable: you can see *why* the creative made each choice, down to the ranked memory and its score.
- A visible learning loop: feedback in, memory written, retrieved on the next generation, applied in the image.
- Brand-book depth that judges recognize from real brands: contrast ratios, safe zones, FDA sunscreen wording, FTC disclosure.
- Reusing our production graph schema inside HydraDB via BYOG, rather than inventing a toy one.

## What we learned

- For marketing, **memory has to be layered**. Brand rules, performance, consumer voice and client feedback are different kinds of truth, and the agent needs to know which one it's reading.
- **Showing retrieval builds trust** faster than a better answer does. People want to see what was used and what was ignored.
- **Free-text feedback is the most valuable and least captured data.** HydraDB's `infer` turns "kill it, we don't retouch skin" into a reusable rule.
- Verified assets matter as much as memory: an on-brand concept with a hallucinated logo is still off-brand.

## What's next for Marketing Brain

- Connect live sources: Meta/Google/TikTok ad accounts, review and social listening feeds, and approval tools, so the brain stays current.
- A pre-flight compliance check that scores every generated creative against the rule pack before it reaches a human.
- Feed the brain into Zocket's production agents (image, video, performance) so every agent reads from, and writes back to, the same memory.
- Multi-brand, multi-sub-brand tiers with inheritance (product > sub-brand > brand).
- Evaluation: measure approval rate and revision rounds with vs without the brain.
