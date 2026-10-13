"""Capture Devpost gallery screenshots from the live app (3:2, rendered at 2x, JPEG < 5 MB)."""
import asyncio
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "gallery"
OUT.mkdir(exist_ok=True)
URL = "http://localhost:8010/"


def save(png, name):
    im = Image.open(png).convert("RGB")
    im.save(OUT / f"{name}.jpg", quality=88, optimize=True)
    Path(png).unlink()
    print("saved", name, im.size)


async def shot(page, name):
    tmp = OUT / f"{name}.png"
    await page.screenshot(path=str(tmp))
    save(tmp, name)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1500, "height": 1000}, device_scale_factor=2)
        await page.goto(URL)
        await page.wait_for_function("() => document.querySelectorAll('.layer-link').length === 5", timeout=20000)
        await page.wait_for_timeout(1200)
        await shot(page, "01-ask")

        await page.locator(".starter").first.click()
        await page.wait_for_selector(".msg.bot .answer", timeout=180000)
        await page.wait_for_function("() => busy === false", timeout=180000)
        await page.wait_for_timeout(800)
        c = page.locator(".msg.bot .answer .cite.V").first
        if not await c.count():
            c = page.locator(".msg.bot .answer .cite").first
        await c.click()
        await page.wait_for_timeout(1500)
        await page.evaluate("document.querySelector('#thread').scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        await shot(page, "02-ask-answer-trace")

        await page.click('.nav button[data-tab="explore"]')
        await page.wait_for_timeout(3500)
        await page.evaluate("selectNode('HUB:CAMPAIGN')")
        await page.wait_for_timeout(1500)
        await page.evaluate("selectNode('CAMPAIGN:Fog Shield SPF Summer')")
        await page.wait_for_timeout(2500)
        await shot(page, "03-explore-graph")

        await page.click('.nav button[data-tab="brain"]')
        await page.wait_for_timeout(2000)
        await shot(page, "04-brain")
        await page.evaluate("document.querySelector('#bcamps').scrollIntoView({block: 'center'})")
        await page.wait_for_timeout(800)
        await shot(page, "05-brain-campaigns")

        await page.click('.nav button[data-tab="skills"]')
        await page.wait_for_timeout(1500)
        await shot(page, "06-skills")
        await b.close()

    for i, name in ((7, "compare_sbs"), (8, "learn_sbs")):
        src = ROOT / f"{name}.png"
        if src.exists():
            im = Image.open(src).convert("RGB")
            im.save(OUT / f"{i:02d}-{name.replace('_sbs', '')}-control-vs-brain.jpg", quality=90, optimize=True)
            print("saved", name)


asyncio.run(main())
