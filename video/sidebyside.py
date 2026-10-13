"""Full-screen side-by-side stills of control vs brain creatives from the captured run (1920x1080 PNG)."""
import asyncio
import base64
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).parent
GEN = ROOT.parent / "generated"
CSS = """<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap" rel="stylesheet">
<style>html,body{margin:0;width:1920px;height:1080px;background:#fff;font-family:Geist,sans-serif;color:#0a0b0f}
.t{position:absolute;top:56px;left:0;right:0;text-align:center;font-size:40px;font-weight:600;letter-spacing:-.03em}
.row{position:absolute;top:150px;left:0;right:0;display:flex;justify-content:center;gap:56px}
.c{display:flex;flex-direction:column;gap:14px;align-items:flex-start}
.l{display:flex;align-items:center;gap:10px;font-size:26px;font-weight:500;color:#6b7080}
.l.b{color:#2f5bff}.l i{width:12px;height:12px;border-radius:50%;background:#9a9eab}.l.b i{background:#2f5bff}
img{height:760px;border-radius:14px;border:1.5px solid #ebecef}.b+img{border:3px solid #2f5bff;box-shadow:0 0 0 6px #f0f4ff}
.n{font-size:22px;color:#6b7080;max-width:600px;line-height:1.4}</style>"""


def uri(name):
    return "data:image/png;base64," + base64.b64encode((GEN / name).read_bytes()).decode()


def html(title, ctrl, brain, cnote, bnote):
    return f"""<!doctype html><html><head><meta charset="utf-8">{CSS}</head><body><div class="t">{title}</div><div class="row">
<div class="c"><div class="l"><i></i>Control · no memory</div><img src="{uri(ctrl)}"><div class="n">{cnote}</div></div>
<div class="c"><div class="l b"><i></i>With Marketing Brain</div><img src="{uri(brain)}"><div class="n">{bnote}</div></div>
</div></body></html>"""


SHOTS = {
    "compare_sbs": ("Same request. One has memory.", "00abaee9a3.png", "55469918b4.png",
                    "Invented packaging and logo, no FDA wording.", "Verified logo + packshot, real skin tones, exact SPF legal line."),
    "learn_sbs": ("After legal: “never show the SPF on a beach or near water.”", "5fe8fd4782.png", "53b83ad97d.png",
                  "On a beach, which legal just banned.", "New rule retrieved from HydraDB memory and applied."),
}


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1920, "height": 1080})
        for name, args in SHOTS.items():
            await page.set_content(html(*args))
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(ROOT / f"{name}.png"))
        await b.close()
    print("rendered", list(SHOTS))


asyncio.run(main())
