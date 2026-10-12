# Design system: Marketing Brain

Category canon, played straight: a light, Glean/Linear-grade knowledge workspace. Mode: Operate. Recorded from the built UI (`static/index.html`).

## Shell
- Left sidebar (248px, `--side`), from top to bottom: workspace switcher (Tidelight mark plus "Demo workspace · fictional brand"), nav (Ask, Brain, Skills; the active item is a raised white pill with an accent icon), memory layers with counts, and a footer with HydraDB connection status, database name and the synthetic-data disclaimer.
- 52px top bar: breadcrumb, plus contextual actions (New chat, Trace toggle).
- Ask view: centered conversation (max 780px) plus a 400px Trace inspector on the right. On phones it collapses to a top nav, with the trace hidden behind a toggle.

## Color (Restrained)
- Neutrals: canvas `#f7f8fa`, surface `#fff`, sunken `#f2f4f7`, lines `#e5e8ee` / `#d5dae2`, ink `#0f172a`, secondary `#334155`, muted `#64748b`.
- One accent, `#3e63dd`, used only for primary action, selection, focus and score bars.
- Five provenance hues, used only to mark which memory layer something came from (citations, layer badges, trace rows): Brand book B `#3e63dd`, Campaigns C `#7c3aed`, Consumer voice V `#0e8a7d`, Market M `#b45309`, Client feedback F `#c2255c`, each with a soft tint background.
- Semantic colors: ok `#18794e`, warn `#ad5700`, bad `#cd2b31`.

## Type
- Inter (cv11, ss01) for everything. Scale: 22–26 page and empty-state titles, 13.5–14.5 body, 11–12.5 meta.
- JetBrains Mono only for IDs, collections, queries and scores.
- Tabular numerals in all data.

## Components
- Buttons: 32px tall, 6px radius, bordered (default), accent (primary), ghost.
- Panels: 12px radius, 1px border, no shadow. A panel head holds a 13.5px title plus muted meta.
- Tables: muted 12px headers on `--side`, 1px row dividers, clickable rows highlight in accent-soft.
- Citation chips: mono 10.5px, colored by layer. Clicking one highlights and expands that result in the Trace.
- Trace cards: the layer badge plus tool name, then a key-value block (query, collection, search mode), then ranked results (rank, ID, title, scaled score bar with raw score). Used results show a bold title with a green rank; unused ones are at 50% opacity. Graph paths and HydraDB-inferred text sit in tinted sub-blocks.
- Agent work log: a collapsible summary ("Searched 4 layers · 4 queries · 40 results · 61s") that collapses once the answer lands.
- Icons: Lucide, 16px, 1.75 stroke.

## Motion
150–250ms state transitions only: work-log spinner, flash on a jump-to-trace, toast rise, skeleton shimmer. Reduced-motion is respected.
