"""Render intro/outro title cards (1920x1080 PNG) from HTML in the app's style: white, Geist, black + #2F5BFF."""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).parent
LOGO = (ROOT.parent / "static" / "assets" / "logo_primary.png").resolve().as_uri()
BASE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  html,body{margin:0;width:1920px;height:1080px;background:#fff;font-family:Geist,sans-serif;color:#0a0b0f;-webkit-font-smoothing:antialiased}
  .wrap{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 200px}
  .mark{display:flex;align-items:center;gap:14px;font-size:24px;font-weight:600;color:#373b45;margin-bottom:56px}
  .dot{width:14px;height:14px;border-radius:4px;background:#2f5bff}
  h1{font-size:132px;line-height:1;font-weight:600;letter-spacing:-.045em;margin:0}
  h1 span{color:#2f5bff}
  p{font-size:40px;line-height:1.35;color:#6b7080;margin:36px 0 0;max-width:1300px;letter-spacing:-.015em}
  .layers{display:flex;gap:14px;margin-top:64px;flex-wrap:wrap}
  .chip{display:flex;align-items:center;gap:10px;height:52px;padding:0 20px;border:1.5px solid #ebecef;border-radius:12px;font-size:24px;color:#373b45}
  .chip i{width:12px;height:12px;border-radius:3px}
  .foot{position:absolute;left:200px;right:200px;bottom:80px;display:flex;justify-content:space-between;font-size:22px;color:#9a9eab}
  .mono{font-family:'Geist Mono',monospace}
</style></head><body>"""
CHIPS = "".join(f'<span class="chip"><i style="background:{c}"></i>{n}</span>' for n, c in [
    ("Brand book", "#2f5bff"), ("Campaigns", "#7a3cf0"), ("Consumer voice", "#0d8a72"), ("Market", "#c25e00"), ("Client feedback", "#d0306b")])

INTRO = BASE + f"""<div class="wrap">
  <div class="mark"><span class="dot"></span>Zocket · Company Brain Hackathon</div>
  <h1>Marketing Brain</h1>
  <p>A 360° marketing memory on <b style="color:#0a0b0f;font-weight:600">HydraDB</b> that every creative agent reads from, shows its work, and learns from every rejection.</p>
  <div class="layers">{CHIPS}</div>
</div>
<div class="foot"><span>Demo brand Tidelight is fictional · all data is synthetic</span><span class="mono">built on HydraDB · Gemini</span></div></body></html>"""

OUTRO = BASE + f"""<div class="wrap">
  <div class="mark"><span class="dot"></span>Marketing Brain</div>
  <h1>Memory that <span>shows its work.</span></h1>
  <p>Brand book, 18 months of campaigns, consumer voice, market and client feedback, in one HydraDB memory with a full retrieval trace.</p>
  <div class="layers"><span class="chip mono">github.com/mukund0604/marketing-brain</span></div>
</div>
<div class="foot"><span>Built by the Zocket team</span><span class="mono">HydraDB · BYOG · memories with infer · Gemini</span></div></body></html>"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1920, "height": 1080})
        for name, html in (("intro", INTRO), ("outro", OUTRO)):
            await page.set_content(html)
            await page.wait_for_timeout(1200)  # fonts
            await page.screenshot(path=str(ROOT / f"{name}.png"))
        await b.close()
    print("cards rendered")


asyncio.run(main())
