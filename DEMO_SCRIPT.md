# Demo video script (target 2:30)

**Before recording**
1. `python reset_demo.py`: clean memory, no leftover images.
2. Restart the server, open http://localhost:8010, browser at least 1440px wide, zoom 110%, bookmarks bar hidden.
3. Warm-up (off camera): run the SPF ad request once so you know its timing (~60s). Cut the wait in the edit.
4. Record with QuickTime (File → New Screen Recording) or Loom. Mic on and quiet room; voiceover can also be added afterwards.

---

### 0:00–0:15 · Problem (Ask page, empty state)
> "Every brand's marketing knowledge is scattered: brand books in PDFs, ad results in a warehouse, reviews on Amazon and Reddit, client feedback buried in approval threads. So AI creative tools forget everything and keep making the same mistakes."

### 0:15–0:40 · What the brain holds (click **Brain**)
Slowly scroll: stats strip → layers table → consumer voice by source → campaign history (point at the red "Missed" row) → graph explorer (click a campaign node).
> "Marketing Brain puts all of it into one memory on HydraDB: five layers. A brand book down to hex codes, safe zones and FDA rules. Eighteen months of campaigns joined with daily ad performance. What consumers say across seven platforms. The market. And the client's own feedback. The structure is our production brand-graph schema, loaded with HydraDB's Bring Your Own Graph."

### 0:40–1:15 · Ask, and audit the answer (click **Ask** → starter 1: "How did our SPF campaigns perform…")
While it streams, point at the work log ("Searching campaigns… searching consumer voice…").
When the answer lands, click a **C** citation, then a **V** citation, so the trace jumps to them.
> "The agent decides which layers to search. And here's what nobody else shows you: every HydraDB query, every result ranked by relevance, which ones it actually used, and the graph paths it followed. The summer SPF campaign missed its target because of white-cast complaints from deeper skin tones, and you can see exactly which reviews prove it."

### 1:15–1:55 · With brain vs without (starter 3: "Make a Meta 4:5 ad for the tinted Fog Shield SPF 30, and compare…")
Cut the generation wait. Show both cards side by side; zoom on the control's headline and props, then on the brain version's logo, swatches and legal line.
> "Same request, with and without memory. Without it: 'glow', which is banned, a flower prop that implies fragrance, made-up packaging, no FDA wording. With the brain: the real logo and packshot as verified assets, three skin tones because that's what won before, and the exact 'Broad Spectrum SPF 30' line legal requires. Every decision traces back to a memory."

### 1:55–2:20 · It learns (type in chat)
"Jordan from legal says: never show the SPF on a beach or near water. Remember that." → show "searchable in N s". Then "Regenerate that ad applying the new feedback" → point at the **NEW** tag on the retrieved memory in the trace.
> "When the client pushes back, the brain writes it to HydraDB memory. Seconds later it's retrieved on the next generation, and applied."

*(If time is tight, skip the regenerate and end on the NEW tag. Optional extra beat: Skills → "Suggest from feedback" → Promote.)*

### 2:20–2:30 · Close
> "Marketing Brain: a 360° memory on HydraDB that every creative agent reads from, shows its work, and learns from every rejection. Built by the Zocket team."

---
**Lines to avoid:** don't claim it runs on real client data, and don't say it's in production. Tidelight is fictional and the data is synthetic.
