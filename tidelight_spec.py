"""Tidelight: a FICTIONAL San Francisco clean-skincare brand used to demo the Marketing Brain.

Everything here is synthetic but written to the depth of a real brand book, media plan and
approval history. Shapes follow BrandOS (Neo4j guideline sections, ClickHouse ad tables,
middleware approvals). Competitors are fictional too.
"""

BRAND = {
    "name": "tidelight", "display_name": "Tidelight", "country_code": "us", "safe_brand": "tidelight",
    "url": "https://tidelight.example", "hq": "San Francisco, CA", "founded": 2021,
    "category": "clean skincare", "channels": ["DTC (Shopify)", "Amazon", "Target (in-store + online)"],
    "summary": ("Tidelight is a San Francisco clean-skincare brand built on cold-water ocean botanicals "
                "(sea fennel, bull kelp, Pacific sea buckthorn). Fragrance-free, dermatologist-tested formulas "
                "for sensitive, fog-and-wind-stressed skin. Priced at masstige ($18-$58)."),
}

GUIDELINES = {
    "summary": "Calm, clinical-meets-coastal. Products are the hero; skin is shown real and unretouched. Science-forward claims only when substantiated.",
    "last_updated": "2026-09-02",
    "positioning_statement": "Barrier-first skincare from the cold Pacific, for skin that's had enough.",
    "usp_claims": ["Fragrance-free across the entire line", "Dermatologist-tested on sensitive skin", "Cold-water ocean botanicals, sustainably wild-harvested off Mendocino", "Refillable aluminum packaging on 4 of 8 SKUs"],
    "proof_points": ["4.6★ average across 18,400 reviews", "National Eczema Association Seal of Acceptance on Kelp Ceramide Cream", "Allure Best of Beauty 2025 (Sea Fennel C Serum)"],
    "personas": [
        {"name": "Sensitive-Skin Skeptic", "age": "28-40", "who": "Has reacted to 'clean' brands with essential oils; reads INCI lists; Reddit r/SkincareAddiction lurker", "wants": "Proof it won't sting", "objection": "Clean = fragrance = irritation"},
        {"name": "Fog-Belt Professional", "age": "25-38", "who": "Bay Area / Seattle / Portland, cycles or walks to work, wind + cold + low sun", "wants": "Barrier repair and an SPF that doesn't pill under makeup", "objection": "Mineral SPF leaves a white cast"},
        {"name": "Minimalist Gifter", "age": "30-50", "who": "Buys sets at Target or DTC during Q4", "wants": "Beautiful, refillable, giftable", "objection": "Price vs drugstore"},
    ],
    "audience_segments": ["sensitive / rosacea-prone skin", "eczema-adjacent dry skin", "outdoor-active Pacific Northwest + Bay Area", "refill / low-waste shoppers"],
    "persona_objections": ["mineral SPF white cast on deeper skin tones", "vitamin C serum oxidizing", "price vs CeraVe-tier drugstore"],
}

SECTIONS = {
    "ColorPalette": {
        "primary_colors": [
            {"name": "Fog", "hex": "#E9ECEA", "pantone": "Cool Gray 1 C", "cmyk": "7/3/5/0", "usage": "Default background. 60% of any layout."},
            {"name": "Deep Tide", "hex": "#123B4A", "pantone": "7700 C", "cmyk": "92/62/45/35", "usage": "Headlines, logo, CTA buttons. 25% of layout."},
        ],
        "secondary_colors": [
            {"name": "Kelp", "hex": "#4F6B4A", "pantone": "7743 C", "usage": "Ingredient and sustainability stories only. Max 10%."},
            {"name": "Buckthorn", "hex": "#E8913A", "pantone": "715 C", "usage": "Vitamin C serum only (product-tier color). Max 10%; never as background."},
            {"name": "Driftwood", "hex": "#B9A68C", "usage": "Supporting neutral for props and textures."},
        ],
        "accessibility_pairs": ["Deep Tide on Fog = 10.4:1 (AAA)", "Fog on Deep Tide = 10.4:1 (AAA)", "Kelp on Fog = 5.6:1 (AA body)", "Buckthorn on Fog = 2.3:1, FAILS: never use Buckthorn for text"],
        "banned_combinations": ["Buckthorn text on any background", "Kelp + Buckthorn adjacent (reads 'autumn', off-brand)", "Pure white #FFFFFF backgrounds (use Fog)", "Pure black #000000 (use Deep Tide)", "Neon or saturated pink (owned by competitor Petal & Pine)"],
        "usage_guidelines": "60/25/15 rule: Fog / Deep Tide / one secondary. Max one secondary color per creative. Gradients only Fog→white-ish mist at 8% opacity for 'fog' atmosphere.",
    },
    "Typography": {
        "primary_typeface": {"family": "Söhne Breit", "fallback": "Inter Tight", "weights": ["Halbfett (600)"], "use": "Headlines, all lowercase", "tracking": "-1%"},
        "secondary_typefaces": [{"family": "Söhne", "fallback": "Inter", "weights": ["Buch (400)", "Kräftig (500)"], "use": "Body, claims, CTAs; sentence case"},
                                {"family": "Söhne Mono", "fallback": "JetBrains Mono", "weights": ["400"], "use": "Ingredient percentages and INCI callouts only, e.g. '2% sea fennel extract'"}],
        "type_scale": {"1:1 feed (1080px)": "headline 72-88px, sub 32px, legal 18px min", "4:5 feed (1080x1350)": "headline 80-96px, sub 34px, legal 18px min", "9:16 story/reels (1080x1920)": "headline 96-120px, sub 40px, legal 22px min, keep text inside safe zone", "Amazon A+ (970x600)": "headline 48px, body 18px"},
        "hierarchy_notes": "Max 2 type sizes + legal per creative. Headline max 7 words, lowercase. Line-height 1.05 headlines, 1.4 body.",
        "overlay_rules": "Text never over the product or over a face. Text sits on Fog or Deep Tide fields, never on busy photography. Ingredient % always in Söhne Mono.",
    },
    "LogoUsage": {
        "description": "Wordmark 'tidelight' (lowercase) with the tide-line mark (three stacked horizontal waves).",
        "variants": [{"name": "primary-deep-tide", "logo": "https://cdn.tidelight.example/logo/primary.svg", "use": "On Fog / light photography"},
                     {"name": "reversed-fog", "logo": "https://cdn.tidelight.example/logo/reversed.svg", "use": "On Deep Tide / dark photography"},
                     {"name": "mark-only", "logo": "https://cdn.tidelight.example/logo/mark.svg", "use": "Social avatars, packaging caps; never alone in paid ads"}],
        "clear_space_rule": "Clear space = height of the tide-line mark on all sides.",
        "minimum_size": "Wordmark min 140px wide on 1080px canvas (13%); min 0.75in print.",
        "placement_preference": "Bottom-left on feed (1:1, 4:5). Top-center on 9:16, below the 250px top safe zone.",
        "prohibited_uses": ["recolor outside Deep Tide / Fog", "drop shadows or glows", "placing on Buckthorn", "stretching", "mark-only in paid ads", "locking up with retailer logos without legal approval"],
    },
    "LayoutSystem": {
        "grid": "8px base grid. Outer margin 64px on 1080px canvases (6%).",
        "safe_zones": {"9:16": "Top 250px and bottom 340px reserved for platform UI (TikTok/Reels); no text or logo there", "4:5": "Keep critical content inside central 1080x1080 for grid crops", "1:1": "64px margin all sides"},
        "composition": ["Product occupies 35-50% of the frame on hero creatives", "One focal product per creative (kits excepted)", "Negative space on Fog >= 30%", "Ingredient callouts max 2, connected by 1px Deep Tide hairlines"],
        "cta": "Pill button, Deep Tide fill, Fog text, 'shop now' or 'find your routine' (lowercase). Never 'buy now'.",
    },
    "VisualIdentity": {
        "overall_style": "Calm clinical-coastal still life + unretouched real skin.",
        "photography_style": "Soft overcast daylight (the 'fog light'), 5600K, low contrast, matte surfaces: wet slate, limestone, frosted glass, kelp fronds.",
        "camera_angles": ["straight-on product at eye level", "45° top-down", "macro texture swatch"],
        "talent_rules": ["Real, unretouched skin: visible pores, texture, redness allowed and encouraged", "Every campaign set must include Fitzpatrick IV-VI skin tones", "No retouching of skin texture (brand pledge since 2023)", "Hands and partial faces preferred over full beauty shots"],
        "shot_composition_rules": ["Product label legible and front-facing", "Texture swatch next to product on serum/cream heroes", "No water droplets on product photography (reads 'wet, cheap'); mist/fog atmosphere instead"],
        "banned_visuals": ["before/after split images (Meta policy + FTC substantiation risk)", "lab coats / fake dermatologists", "flowers and essential-oil props (implies fragrance)", "beach-sunset cliches, surfers, tropical palms (we are cold Pacific, not Hawaii)", "retouched glass-skin"],
        "proprietary_elements": ["tide-line mark as a subtle 3-wave hairline motif", "Mendocino kelp frond prop", "frosted glass refill pod"],
    },
    "ToneOfVoice": {
        "brand_mantra": "skin that's had enough.",
        "personality_traits": ["calm", "precise", "dry wit", "never preachy"],
        "language_style": "Plain, specific, lowercase headlines. Talk like a cosmetic chemist friend, not a wellness influencer.",
        "messaging_principles": ["Lead with the barrier, not 'glow'", "Name the ingredient and the %", "One claim per creative", "Acknowledge sensitivity honestly"],
        "approved_copy_lines": ["skin that's had enough.", "fragrance-free. obviously.", "sea fennel, not snake oil.", "fog-proof your barrier."],
        "vocabulary_do": ["barrier", "calm", "fragrance-free", "dermatologist-tested", "refill"],
        "vocabulary_dont": ["glow-up", "toxin", "chemical-free", "detox", "miracle", "anti-aging (say 'visible signs of aging')", "clean beauty (say 'clean formulas')"],
        "banned_copy_behaviour": ["fear-mongering about 'toxins' or 'chemicals'", "disparaging named competitors", "urgency scarcity ('selling out!') unless true and approved"],
    },
    "ComplianceRules": {
        "mandatory_always": ["'#ad' or platform paid-partnership label on all creator content (FTC Endorsement Guides)", "SPF creatives: 'Broad Spectrum SPF 30' exact wording + 'reapply every 2 hours' in legal line (FDA OTC monograph)"],
        "banned_always": ["'cures', 'treats', 'heals' eczema/rosacea/acne (drug claims)", "'clinically proven' without study ID approved by legal", "'waterproof' / 'sweatproof' for SPF (FDA prohibited)", "'hypoallergenic' (not substantiated)", "'reef-safe' (FTC greenwashing risk; use 'formulated without oxybenzone and octinoxate')"],
        "documented_exceptions": ["'dermatologist-tested' approved (study TL-2024-03)", "'92% said skin felt calmer in 2 weeks' approved for Kelp Ceramide Cream only (consumer perception study TL-2025-07, n=112), must carry asterisk + footnote"],
        "rule_pack": [
            {"id": "no.drug_claim", "tier": "hard", "check": "banned_phrase", "title": "No drug claims", "value": ["cure", "treat", "heal", "eczema relief", "rosacea treatment"], "fix": "Use 'soothes the look of redness' / 'supports the skin barrier'."},
            {"id": "spf.exact_wording", "tier": "hard", "check": "required_text", "when": "product == Fog Shield SPF 30", "title": "SPF monograph wording", "value": "Broad Spectrum SPF 30", "fix": "Add exact wording + reapply line."},
            {"id": "no.waterproof", "tier": "hard", "check": "banned_phrase", "title": "No waterproof claims", "value": ["waterproof", "sweatproof"], "fix": "Use 'water resistant (40 minutes)' only."},
            {"id": "claims.study_id", "tier": "standard", "check": "judgment", "title": "Stat claims need a study", "rule": "Any percentage claim must map to an approved study ID", "fix": "Remove or use an approved claim."},
            {"id": "ftc.ad_label", "tier": "hard", "check": "required_text", "when": "creator content", "title": "Paid partnership label", "value": "#ad", "fix": "Add #ad in first line."},
            {"id": "style.lowercase_headline", "tier": "style", "check": "judgment", "title": "Lowercase headlines", "fix": "Lowercase the headline."},
        ],
    },
    "CreativeArchetypes": {"archetypes": ["Ingredient Macro", "Real Skin UGC", "Barrier Science Explainer", "Fog Belt Lifestyle", "Refill Ritual", "Gift Set Flatlay", "Reviewer Quote Card"]},
    "BrandAmbassador": {"has_ambassador": True, "ambassadors": [{"name": "Dr. Maya Okafor (fictional), board-certified dermatologist advisor", "verified_asset_links": ["https://cdn.tidelight.example/talent/okafor-01.jpg"], "usage": "Only in Barrier Science Explainer; must not imply she 'prescribes'; disclosure 'paid advisor' required"}]},
}

PRODUCTS = [
    {"slug": "sea-fennel-c-serum", "name": "Sea Fennel Vitamin C Serum", "category": "serum", "price": 48, "size": "30 ml",
     "rtb": ["10% ethyl ascorbic acid (stable vitamin C)", "2% sea fennel extract", "fragrance-free"], "color_override": "Buckthorn accent allowed",
     "notes": "Allure Best of Beauty 2025. Known issue: early 2025 batches oxidized faster; reformulated with airless pump Mar 2026."},
    {"slug": "kelp-ceramide-cream", "name": "Kelp Ceramide Barrier Cream", "category": "moisturizer", "price": 42, "size": "50 ml refillable",
     "rtb": ["3 ceramides + bull kelp", "NEA Seal of Acceptance", "92% felt calmer in 2 weeks* (TL-2025-07)"], "notes": "Hero SKU, 38% of revenue."},
    {"slug": "fog-shield-spf30", "name": "Fog Shield Mineral SPF 30", "category": "sunscreen (OTC drug)", "price": 36, "size": "50 ml",
     "rtb": ["Broad Spectrum SPF 30", "18% non-nano zinc oxide", "tinted in 3 shades since Jun 2026"], "compliance_override": "FDA OTC monograph wording mandatory",
     "notes": "Top complaint: white cast on deeper skin (pre-Jun 2026 untinted). Tinted shades launched Jun 2026."},
    {"slug": "tide-pool-cleanser", "name": "Tide Pool Gel Cleanser", "category": "cleanser", "price": 24, "size": "150 ml", "rtb": ["pH 5.5", "low-foam", "fragrance-free"], "notes": "Pump breaks complaints Q1 2026; new pump shipped Apr 2026."},
    {"slug": "buckthorn-night-oil", "name": "Buckthorn Retinal Night Oil", "category": "treatment", "price": 58, "size": "30 ml", "rtb": ["0.05% retinal", "Pacific sea buckthorn oil"], "notes": "Not for use with SPF claims in same creative."},
    {"slug": "mist-toner", "name": "Cold Water Mist Toner", "category": "toner", "price": 28, "size": "100 ml refillable", "rtb": ["glycerin + sea fennel", "alcohol-free"]},
    {"slug": "barrier-lip-balm", "name": "Barrier Lip Balm", "category": "lip", "price": 18, "size": "10 g", "rtb": ["ceramides", "unflavored"]},
    {"slug": "fog-belt-routine-set", "name": "Fog Belt Routine Set", "category": "kit", "price": 98, "size": "cleanser + serum + cream minis", "rtb": ["$126 value"], "notes": "Q4 + Target exclusive packaging."},
]

COMPETITORS = [
    {"id": "c-petal", "competitor_name": "petal & pine", "competing_front": "clean beauty with botanicals + essential oils; owns saturated pink; heavy influencer spend",
     "pricing": "$22-$64", "ad_activity": "~140 active Meta ads; 70% creator UGC; leans 'toxin-free' messaging (which we avoid)", "share_of_voice": 0.31},
    {"id": "c-derma", "competitor_name": "dermafact", "competing_front": "clinical, drugstore-adjacent, ceramides at $14-$22; strong on Amazon",
     "pricing": "$14-$22", "ad_activity": "~60 Google Shopping + Amazon Sponsored; minimal social creative", "share_of_voice": 0.27},
    {"id": "c-noma", "competitor_name": "noma skin", "competing_front": "Korean-inspired gel textures, glass-skin aesthetic, TikTok native",
     "pricing": "$19-$45", "ad_activity": "~90 TikTok Spark Ads; glass-skin retouched visuals", "share_of_voice": 0.18},
]
TIDELIGHT_SOV = 0.24  # share of category voice (social + reviews + search), last 90 days

AGENT_SKILLS = [
    {"name": "spf-claims-guard", "title": "SPF claims guard", "description": "Fires for any creative featuring Fog Shield SPF 30.",
     "skill": "# SPF claims guard\nTrigger: Fog Shield SPF 30 in the brief or product.\n- Exact phrase 'Broad Spectrum SPF 30' on image or legal line\n- Legal line: 'Reapply every 2 hours. See Drug Facts.'\n- Never 'waterproof', 'sweatproof', 'reef-safe'\n- Show tinted shades on at least 2 skin tones (white-cast objection)", "tags": ["creative_ai", "compliance"]},
    {"name": "creator-disclosure", "title": "Creator disclosure", "description": "Fires for any UGC / creator-led creative.",
     "skill": "# Creator disclosure\nTrigger: creator, UGC, influencer, Spark Ads.\n- '#ad' in first line of caption and paid-partnership label on\n- Creator must have used product 14+ days (script attestation)\n- No scripted medical claims", "tags": ["creative_ai", "compliance"]},
]

ORG_MEMORY = [
    {"key": "aspect_ratio_default", "content": "Meta: 4:5 for feed, 9:16 for Reels/Stories. TikTok: 9:16 only. Amazon A+: 970x600.", "tags": ["format"]},
    {"key": "legal_reviewer", "content": "All claims go to Jordan Lee (legal) before launch; turnaround 48h.", "tags": ["process"]},
]

# ---------------------------------------------------------------- campaigns + creatives
# perf targets drive the synthetic daily data (code computes the actual numbers).
CAMPAIGNS = [
    {"id": "cmp_01", "name": "Barrier Season Launch", "objective": "conversions", "platforms": ["meta"], "flight": ["2025-04-07", "2025-05-18"], "budget_usd": 85000,
     "audience": "Broad US women 25-44 + sensitive-skin interest stack", "kpi": "ROAS 2.5", "product": "Kelp Ceramide Barrier Cream",
     "learning": "Real-skin UGC beat studio beauty 2.1x on ROAS. Texture macro was the best-performing static."},
    {"id": "cmp_02", "name": "Fog Shield SPF Summer", "objective": "conversions", "platforms": ["meta", "tiktok"], "flight": ["2025-06-02", "2025-08-10"], "budget_usd": 140000,
     "audience": "Outdoor-active, Bay Area / PNW geo overweight", "kpi": "ROAS 2.2", "product": "Fog Shield Mineral SPF 30",
     "learning": "Underdelivered vs the 2.2 target. Comments flooded with white-cast complaints from deeper skin tones; creative showed only light skin. Led to tinted reformulation."},
    {"id": "cmp_03", "name": "Sea Fennel C: Best of Beauty", "objective": "conversions", "platforms": ["meta", "google"], "flight": ["2025-10-01", "2025-11-09"], "budget_usd": 95000,
     "audience": "Lookalike 1-3% of purchasers + Allure readers", "kpi": "ROAS 2.8", "product": "Sea Fennel Vitamin C Serum",
     "learning": "Award badge lifted CTR 34%. Ingredient-% callouts in Söhne Mono outperformed lifestyle."},
    {"id": "cmp_04", "name": "Holiday Fog Belt Set", "objective": "conversions", "platforms": ["meta", "google"], "flight": ["2025-11-17", "2025-12-21"], "budget_usd": 160000,
     "audience": "Gifters 30-55, Target shoppers", "kpi": "ROAS 3.0", "product": "Fog Belt Routine Set",
     "learning": "Best ROAS of the year. Flatlay on Fog with refill pod beat festive red/gold variants, which legal and brand also rejected as off-palette."},
    {"id": "cmp_05", "name": "Skin That's Had Enough (brand)", "objective": "awareness", "platforms": ["tiktok", "meta"], "flight": ["2026-01-12", "2026-03-01"], "budget_usd": 120000,
     "audience": "Broad 22-40, sensitive skin + eczema interest", "kpi": "CPM < $9, thumbstop 30%", "product": "Kelp Ceramide Barrier Cream",
     "learning": "Unfiltered winter-redness UGC got 41% thumbstop. One creator video was pulled for saying 'cured my eczema' (drug claim)."},
    {"id": "cmp_06", "name": "Refill Ritual (Earth Month)", "objective": "conversions", "platforms": ["meta"], "flight": ["2026-04-01", "2026-04-30"], "budget_usd": 60000,
     "audience": "Low-waste interest, existing customers", "kpi": "ROAS 2.5 / refill attach 20%", "product": "Kelp Ceramide Barrier Cream",
     "learning": "Refill pod close-up drove 27% refill attach. 'Reef-safe' headline was killed by legal pre-launch."},
    {"id": "cmp_07", "name": "Tinted Fog Shield Relaunch", "objective": "conversions", "platforms": ["meta", "tiktok"], "flight": ["2026-06-08", "2026-08-16"], "budget_usd": 150000,
     "audience": "Broad + deeper skin tone creator partnerships", "kpi": "ROAS 2.4", "product": "Fog Shield Mineral SPF 30",
     "learning": "ROAS recovered above target after showing all 3 tints on Fitzpatrick IV-VI. Swatch-on-hand creative was the winner; fatigued after ~3 weeks."},
    {"id": "cmp_08", "name": "Back to Barrier (Q3 always-on)", "objective": "conversions", "platforms": ["meta", "google"], "flight": ["2026-08-24", "2026-10-04"], "budget_usd": 90000,
     "audience": "Retargeting + broad Advantage+", "kpi": "ROAS 2.6", "product": "Kelp Ceramide Barrier Cream",
     "learning": "Reviewer quote cards strong on retargeting. Barrier Science Explainer with Dr. Okafor is fatiguing (frequency 4.1)."},
]

# creative: (campaign, id, platform, format, archetype, product, headline, visual, roas, ctr%, fatigue 0-1, score, positives, negatives)
CREATIVES = [
    ("cmp_01", "tl_101", "meta", "4:5 static", "Ingredient Macro", "Kelp Ceramide Barrier Cream", "skin that's had enough.", "Macro swatch of cream texture on wet slate beside the refillable jar, fog light", 3.4, 2.1, 0.1, 8.8, ["texture", "on-palette"], []),
    ("cmp_01", "tl_102", "meta", "9:16 video", "Real Skin UGC", "Kelp Ceramide Barrier Cream", "my barrier, 2 weeks in", "Creator with visible redness applies cream, unfiltered, natural light, #ad", 3.1, 1.9, 0.2, 8.5, ["real skin", "disclosure"], []),
    ("cmp_01", "tl_103", "meta", "4:5 static", "Fog Belt Lifestyle", "Kelp Ceramide Barrier Cream", "Glow Up Your Skin", "Retouched model with glass skin, studio white background", 1.3, 0.8, 0.0, 4.1, [], ["retouched", "'glow up' banned vocab", "pure white bg"]),
    ("cmp_02", "tl_201", "meta", "4:5 static", "Fog Belt Lifestyle", "Fog Shield Mineral SPF 30", "fog-proof your face", "Cyclist on the Golden Gate Bridge path in fog, light skin only, product in hand", 1.7, 1.2, 0.3, 6.2, ["local relevance"], ["only light skin", "white-cast concern"]),
    ("cmp_02", "tl_202", "tiktok", "9:16 video", "Real Skin UGC", "Fog Shield Mineral SPF 30", "the SPF that doesn't pill", "Creator rubs in untinted SPF, visible white cast on medium-deep skin", 1.2, 1.4, 0.0, 4.8, ["honest"], ["white cast visible", "comment backlash"]),
    ("cmp_02", "tl_203", "meta", "1:1 static", "Fog Belt Lifestyle", "Fog Shield Mineral SPF 30", "waterproof sun protection", "Surfer at a sunny beach with SPF bottle", 0.9, 0.7, 0.0, 2.9, [], ["'waterproof' FDA-prohibited", "beach/surf cliche banned"]),
    ("cmp_03", "tl_301", "meta", "4:5 static", "Ingredient Macro", "Sea Fennel Vitamin C Serum", "10% vitamin c. 0% fragrance.", "Serum dropper over frosted glass, Buckthorn accent, '10% ethyl ascorbic acid' in mono callout, Allure badge", 3.3, 2.4, 0.15, 9.0, ["award badge", "ingredient %"], []),
    ("cmp_03", "tl_302", "google", "responsive display", "Reviewer Quote Card", "Sea Fennel Vitamin C Serum", "\"finally a vitamin c that doesn't sting\"", "Quote card on Fog with 4.6 stars and serum bottle", 2.9, 1.1, 0.0, 8.1, ["social proof"], []),
    ("cmp_03", "tl_303", "meta", "4:5 static", "Fog Belt Lifestyle", "Sea Fennel Vitamin C Serum", "Brighten Your Glow!", "Model with orange sunset glow and flowers around the bottle", 1.4, 1.0, 0.0, 3.8, [], ["flowers imply fragrance", "sunset cliche", "uppercase + 'glow'"]),
    ("cmp_04", "tl_401", "meta", "4:5 static", "Gift Set Flatlay", "Fog Belt Routine Set", "the gift for skin that's had enough.", "Top-down flatlay of the set on Fog linen with kelp frond and refill pod", 4.1, 2.6, 0.05, 9.2, ["on-palette", "refill pod"], []),
    ("cmp_04", "tl_402", "meta", "4:5 static", "Gift Set Flatlay", "Fog Belt Routine Set", "Holiday Glow Sale - 30% OFF", "Set on red and gold glitter background with ornaments", 1.6, 1.8, 0.0, 3.5, ["clear offer"], ["off-palette red/gold", "discount-led", "'glow'"]),
    ("cmp_04", "tl_403", "google", "shopping", "Gift Set Flatlay", "Fog Belt Routine Set", "fog belt routine set, $98 ($126 value)", "Product feed image on Fog", 3.8, 1.5, 0.0, 7.9, ["value framing"], []),
    ("cmp_05", "tl_501", "tiktok", "9:16 video", "Real Skin UGC", "Kelp Ceramide Barrier Cream", "winter did this to my face", "Creator shows cracked, red winter cheeks, applies cream, day 1 vs day 14 talking (no split image), #ad", 2.6, 2.2, 0.25, 8.7, ["41% thumbstop", "real redness"], []),
    ("cmp_05", "tl_502", "tiktok", "9:16 video", "Real Skin UGC", "Kelp Ceramide Barrier Cream", "this cured my eczema", "Creator claims cream cured eczema", 2.2, 2.5, 0.0, 2.0, ["high engagement"], ["DRUG CLAIM, pulled after 4 days"]),
    ("cmp_05", "tl_503", "meta", "9:16 video", "Barrier Science Explainer", "Kelp Ceramide Barrier Cream", "what your barrier actually is", "Animated brick-and-mortar barrier diagram in Deep Tide/Fog", 1.9, 1.3, 0.1, 7.4, ["educational"], ["low CTR"]),
    ("cmp_06", "tl_601", "meta", "4:5 static", "Refill Ritual", "Kelp Ceramide Barrier Cream", "refill, don't rebuy.", "Hand twisting frosted glass refill pod into aluminum jar, macro, fog light", 3.0, 1.9, 0.1, 8.6, ["refill pod hero"], []),
    ("cmp_06", "tl_602", "meta", "4:5 static", "Refill Ritual", "Kelp Ceramide Barrier Cream", "reef-safe skincare", "Jar on beach rocks with ocean waves", 0.0, 0.0, 0.0, 3.0, [], ["'reef-safe' killed by legal pre-launch, never ran"]),
    ("cmp_07", "tl_701", "meta", "4:5 static", "Ingredient Macro", "Fog Shield Mineral SPF 30", "three tints. zero white cast.", "Three tint swatches on three hands (Fitzpatrick II, IV, VI), 'Broad Spectrum SPF 30' on image", 3.6, 2.3, 0.4, 9.1, ["inclusive swatches", "monograph wording"], []),
    ("cmp_07", "tl_702", "tiktok", "9:16 video", "Real Skin UGC", "Fog Shield Mineral SPF 30", "deep skin, no ghost face", "Creator with deep skin applies tinted SPF, blends fully, #ad", 3.2, 2.6, 0.35, 8.9, ["comment sentiment flipped positive"], []),
    ("cmp_07", "tl_703", "meta", "4:5 static", "Fog Belt Lifestyle", "Fog Shield Mineral SPF 30", "sun protection for the fog belt", "Runner at Lands End in fog, deep skin tone, product in hand, legal line present", 2.4, 1.5, 0.1, 7.8, ["local", "inclusive"], []),
    ("cmp_08", "tl_801", "meta", "4:5 static", "Reviewer Quote Card", "Kelp Ceramide Barrier Cream", "\"my rosacea-prone skin finally calmed down\"", "Quote card on Fog, 4.7 stars, jar, legal footnote", 3.3, 1.7, 0.1, 8.4, ["retargeting winner"], []),
    ("cmp_08", "tl_802", "meta", "9:16 video", "Barrier Science Explainer", "Kelp Ceramide Barrier Cream", "a dermatologist explains your barrier", "Dr. Okafor (paid advisor) explains ceramides with diagram, disclosure on screen", 2.7, 1.6, 0.45, 8.0, ["authority"], ["frequency 4.1, fatiguing"]),
    ("cmp_08", "tl_803", "google", "performance max", "Ingredient Macro", "Kelp Ceramide Barrier Cream", "3 ceramides. bull kelp. no fragrance.", "Macro texture + jar, Söhne Mono callouts", 2.9, 1.2, 0.0, 8.2, ["ingredient specificity"], []),
]

APPROVALS = [
    ("apr_01", "tl_103", "rejected", "Sam Rivera (Brand Director)", "We don't retouch skin. That's a public pledge. And 'glow up' is on the banned list. Kill it."),
    ("apr_02", "tl_201", "sent_back", "Sam Rivera (Brand Director)", "Every SPF creative needs deeper skin tones. We're getting destroyed in the comments about white cast."),
    ("apr_03", "tl_203", "rejected", "Jordan Lee (Legal)", "'Waterproof' is prohibited by the FDA monograph for sunscreen. Also no beach/surf imagery: we're cold Pacific, not Hawaii."),
    ("apr_04", "tl_303", "rejected", "Sam Rivera (Brand Director)", "Flowers make people think there's fragrance. We're fragrance-free; that's our whole thing. No sunset glow either."),
    ("apr_05", "tl_402", "rejected", "Sam Rivera (Brand Director)", "Red and gold is off-palette and the discount-led headline cheapens the set. Fog, refill pod, kelp. Always."),
    ("apr_06", "tl_502", "rejected", "Jordan Lee (Legal)", "'Cured my eczema' is a drug claim. Pull it today. All creator scripts need legal review going forward."),
    ("apr_07", "tl_602", "rejected", "Jordan Lee (Legal)", "'Reef-safe' is a greenwashing risk under FTC guidance. Use 'formulated without oxybenzone and octinoxate'."),
    ("apr_08", "tl_701", "approved", "Sam Rivera (Brand Director)", "This is the bar. Three tints on three real hands, monograph wording right on the image."),
    ("apr_09", "tl_301", "approved", "Priya Shah (Performance Lead)", "Ingredient % in mono is our best static pattern. Use it on every product hero."),
    ("apr_10", "tl_802", "sent_back", "Priya Shah (Performance Lead)", "Okafor explainer is at frequency 4+ and CPA is creeping. We need a fresh cut or new hook."),
    ("apr_11", "tl_101", "sent_back", "Sam Rivera (Brand Director)", "Logo is below 13% width on mobile. Wordmark minimum is 140px on a 1080 canvas, bottom-left."),
    ("apr_12", "tl_702", "approved", "Sam Rivera (Brand Director)", "Love this. Creator-led with deep skin is exactly the direction. Keep #ad in the first line."),
]
CREATIVE_FEEDBACK = [
    ("fbk_01", "tl_503", "dislike", "Priya Shah (Performance Lead)", "Diagrams alone don't convert. Pair science with real skin or a reviewer quote."),
    ("fbk_02", "tl_401", "like", "Sam Rivera (Brand Director)", "Flatlay on Fog with the refill pod is the most 'us' thing we've made."),
    ("fbk_03", "tl_102", "like", "Priya Shah (Performance Lead)", "Unfiltered texture = trust. Never smooth the skin."),
]

# consumer voice spec: Gemini writes the items from this, so themes and ratios stay controlled.
VOICE_THEMES = [
    ("doesn't sting sensitive skin", "positive", 0.20, ["Kelp Ceramide Barrier Cream", "Sea Fennel Vitamin C Serum"]),
    ("barrier repair / redness calmed", "positive", 0.16, ["Kelp Ceramide Barrier Cream"]),
    ("white cast on deeper skin (untinted SPF)", "negative", 0.10, ["Fog Shield Mineral SPF 30"]),
    ("tinted SPF finally works on deep skin", "positive", 0.07, ["Fog Shield Mineral SPF 30"]),
    ("vitamin C serum oxidized / turned orange", "negative", 0.07, ["Sea Fennel Vitamin C Serum"]),
    ("cleanser pump broke", "negative", 0.05, ["Tide Pool Gel Cleanser"]),
    ("price vs drugstore (dermafact)", "mixed", 0.08, ["Kelp Ceramide Barrier Cream", "Sea Fennel Vitamin C Serum"]),
    ("love the refill / aluminum packaging", "positive", 0.08, ["Kelp Ceramide Barrier Cream", "Cold Water Mist Toner"]),
    ("fragrance-free is why I switched from petal & pine", "positive", 0.07, ["Kelp Ceramide Barrier Cream", "Tide Pool Gel Cleanser"]),
    ("retinal night oil purging / irritation", "mixed", 0.05, ["Buckthorn Retinal Night Oil"]),
    ("great gift set, Target exclusive", "positive", 0.04, ["Fog Belt Routine Set"]),
    ("shipping / out of stock at Target", "negative", 0.03, ["Kelp Ceramide Barrier Cream", "Fog Belt Routine Set"]),
]
VOICE_PLATFORMS = [  # provider, kind, share
    ("amazon", "review", 0.28), ("target", "review", 0.14), ("tidelight.com", "review", 0.12), ("trustpilot", "review", 0.06),
    ("reddit", "thread", 0.14), ("tiktok", "comment", 0.14), ("instagram", "comment", 0.12),
]
