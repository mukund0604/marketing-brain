"""Drive the live Marketing Brain app through the demo script and record it.
Real HydraDB queries and real generations; logs beat + wait timestamps to capture/beats.json for the edit."""
import asyncio
import json
import time
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path(__file__).parent / "capture"
URL = "http://localhost:8010/"
beats, t0 = [], None


def mark(kind, name):
    beats.append({"t": round(time.time() - t0, 2), "kind": kind, "name": name})
    print(f"{beats[-1]['t']:7.1f}s {kind:5s} {name}", flush=True)


async def wait_idle(page, timeout=240):
    await page.wait_for_function("() => typeof busy !== 'undefined' && busy === false", timeout=timeout * 1000)


async def smooth_scroll(page, selector, total, steps=40, pause=60):
    for _ in range(steps):
        await page.evaluate(f"document.querySelector('{selector}').scrollBy(0, {total / steps})")
        await page.wait_for_timeout(pause)


async def type_and_send(page, text):
    box = page.locator("#input")
    await box.click()
    await box.type(text, delay=22)
    await page.wait_for_timeout(400)
    await page.keyboard.press("Enter")


async def main():
    global t0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1536, "height": 864}, device_scale_factor=1,
                                        record_video_dir=str(OUT), record_video_size={"width": 1920, "height": 1080})
        page = await ctx.new_page()
        t0 = time.time()
        await page.goto(URL)
        await page.wait_for_function("() => document.querySelectorAll('.layer-link').length === 5", timeout=20000)
        await page.wait_for_timeout(600)

        mark("beat", "problem")                      # Ask empty state
        await page.wait_for_timeout(5000)

        mark("beat", "brain")                        # what the brain holds
        await page.click('.nav button[data-tab="brain"]')
        await page.wait_for_timeout(2500)
        await smooth_scroll(page, "#view-brain", 1500, steps=60, pause=110)
        await page.wait_for_timeout(1500)
        await page.evaluate("document.querySelector('#view-brain').scrollTo({top: 0, behavior: 'smooth'})")

        mark("beat", "explore")                      # browse the graph
        await page.click('.nav button[data-tab="explore"]')
        await page.wait_for_timeout(3500)
        await page.evaluate("selectNode('HUB:CAMPAIGN')")
        await page.wait_for_timeout(2500)
        await page.evaluate("selectNode('CAMPAIGN:Fog Shield SPF Summer')")
        await page.wait_for_timeout(3500)
        await smooth_scroll(page, "#xprofile", 500, steps=25, pause=90)
        await page.wait_for_timeout(1200)
        await page.evaluate("selectNode('CREATIVE:creative tl_202')")
        await page.wait_for_timeout(3500)

        mark("beat", "ask")                          # ask and audit the answer
        await page.click('.nav button[data-tab="chat"]')
        await page.wait_for_timeout(1200)
        await page.locator(".starter").first.click()
        mark("wait", "ask-start")
        await page.wait_for_selector(".msg.bot .answer", timeout=180000)
        await wait_idle(page)
        mark("wait", "ask-end")
        await page.wait_for_timeout(2500)
        cites = page.locator(".msg.bot .answer .cite")
        for pref in ("C", "V"):
            c = page.locator(f".msg.bot .answer .cite.{pref}").first
            if await c.count():
                await c.click()
                await page.wait_for_timeout(2800)
        await smooth_scroll(page, "#trace", 400, steps=20, pause=90)
        await page.wait_for_timeout(1500)

        mark("beat", "compare")                      # with brain vs control
        await type_and_send(page, "Make a Meta 4:5 ad for the tinted Fog Shield SPF 30, and compare it with a no-memory version")
        mark("wait", "compare-start")
        await page.wait_for_function("() => document.querySelectorAll('.cr').length >= 2", timeout=300000)
        await wait_idle(page)
        mark("wait", "compare-end")
        await page.evaluate("document.querySelectorAll('.creative')[0].scrollIntoView({block: 'start', behavior: 'smooth'})")
        await page.wait_for_timeout(5000)
        await smooth_scroll(page, "#thread", 350, steps=20, pause=120)
        await page.wait_for_timeout(3000)

        mark("beat", "learn")                        # relay feedback, then regenerate
        await type_and_send(page, "Jordan from legal says: never show the SPF on a beach or near water. Remember that.")
        mark("wait", "remember-start")
        await page.wait_for_function("() => [...document.querySelectorAll('.msg.bot')].length >= 3", timeout=30000)
        await wait_idle(page, 120)
        mark("wait", "remember-end")
        await page.wait_for_timeout(3000)
        await type_and_send(page, "Regenerate that SPF ad applying the new legal feedback")
        mark("wait", "regen-start")
        await page.wait_for_function("() => [...document.querySelectorAll('.msg.bot')].length >= 4", timeout=30000)
        await wait_idle(page, 300)
        mark("wait", "regen-end")
        await page.wait_for_timeout(1500)
        await page.evaluate("(() => { const n = document.querySelector('#trace .newtag'); if (n) n.closest('.res').scrollIntoView({block: 'center', behavior: 'smooth'}); })()")
        await page.wait_for_timeout(3500)
        await page.evaluate("document.querySelectorAll('.creative')[1]?.scrollIntoView({block: 'start', behavior: 'smooth'})")
        await page.wait_for_timeout(5000)

        mark("beat", "end")
        await page.wait_for_timeout(2000)
        video = page.video
        await ctx.close()
        path = await video.path()
        await browser.close()
    final = OUT / "raw.webm"
    Path(path).rename(final)
    (OUT / "beats.json").write_text(json.dumps(beats, indent=1))
    print("saved", final)


asyncio.run(main())
