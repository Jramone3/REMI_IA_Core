import asyncio

async def _run_playwright(url: str, timeout_ms: int = 10000) -> dict:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            title = await page.title()
            body_text = " ".join((await page.inner_text("body")).split())[:1000]
            return {"url": url, "title": title, "excerpt": body_text}
        finally:
            await browser.close()

def browser_automation(url: str, timeout_ms: int = 10000) -> dict:
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "URL inválida."}
    return asyncio.run(_run_playwright(url, int(timeout_ms)))
