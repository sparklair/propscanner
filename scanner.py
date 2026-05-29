import asyncio
import json
from pathlib import Path

import aiofiles
from playwright.async_api import async_playwright

from payloads import JSON_PAYLOADS, POLLUTION_KEY, POLLUTION_VALUE, QUERY_PAYLOADS
from utils import bad, build_url, finding_filename, good, info, same_origin, warn


class PrototypePollutionScanner:
    def __init__(
        self,
        targets,
        crawl=False,
        max_pages=10,
        concurrency=3,
        timeout=15000,
        findings_dir="findings",
    ):
        self.targets = targets
        self.crawl = crawl
        self.max_pages = max_pages
        self.timeout = timeout
        self.findings_dir = Path(findings_dir)
        self.findings_dir.mkdir(exist_ok=True)
        self.semaphore = asyncio.Semaphore(concurrency)
        self.seen_findings = set()

        with open("hooks.js", "r", encoding="utf-8") as f:
            self.hooks = f.read()

    async def save_finding(self, url, finding):
        key = (url, finding)

        if key in self.seen_findings:
            return

        self.seen_findings.add(key)
        path = self.findings_dir / finding_filename(url)

        async with aiofiles.open(path, "a", encoding="utf-8") as f:
            await f.write(finding + "\n")

    async def new_page(self, browser, url, gadget_findings):
        context = await browser.new_context(
            ignore_https_errors=True,
            java_script_enabled=True,
        )
        page = await context.new_page()
        await page.add_init_script(self.hooks)

        async def on_console(msg):
            text = msg.text

            if "[PP Gadget]" not in text:
                return

            finding = f"[GADGET] {url} :: {text}"
            gadget_findings.append(finding)
            good(finding)
            await self.save_finding(url, finding)

        page.on("console", lambda msg: asyncio.create_task(on_console(msg)))

        return context, page

    async def test_pollution(self, page):
        return await page.evaluate(
            """
            ({ key, value }) => {
                return Object.prototype[key] === value || Object.prototype[key] === Number(value);
            }
            """,
            {"key": POLLUTION_KEY, "value": POLLUTION_VALUE},
        )

    async def extract_links(self, browser, base_url):
        info(f"Crawling {base_url}")
        gadget_findings = []
        context, page = await self.new_page(browser, base_url, gadget_findings)

        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=self.timeout)
            await page.wait_for_load_state("networkidle", timeout=5000)
        except Exception as exc:
            warn(f"Crawl load issue on {base_url}: {exc}")

        try:
            links = await page.evaluate(
                """
                () => Array.from(document.querySelectorAll("a[href]"), a => a.href)
                """
            )
        except Exception as exc:
            bad(f"Could not extract links from {base_url}: {exc}")
            links = []
        finally:
            await context.close()

        internal_links = []
        seen = {base_url}

        for link in links:
            if link in seen or not same_origin(link, base_url):
                continue

            seen.add(link)
            internal_links.append(link)

            if len(internal_links) >= self.max_pages:
                break

        return internal_links

    async def scan_query_payload(self, browser, url, payload):
        target = build_url(url, payload)
        gadget_findings = []

        async with self.semaphore:
            info(f"Testing query payload: {target}")
            context, page = await self.new_page(browser, target, gadget_findings)

            try:
                await page.goto(target, wait_until="networkidle", timeout=self.timeout)
                polluted = await self.test_pollution(page)

                if polluted:
                    finding = f"[QUERY] Pollution detected: {target}"
                    good(finding)
                    await self.save_finding(url, finding)
                else:
                    info(f"No pollution: {target}")

            except Exception as exc:
                bad(f"Query test failed for {target}: {exc}")
            finally:
                await context.close()

    async def scan_json_payload(self, browser, url, payload):
        gadget_findings = []
        body = json.dumps(payload, separators=(",", ":"))

        async with self.semaphore:
            info(f"Testing JSON payload: {url}")
            context, page = await self.new_page(browser, url, gadget_findings)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                await page.evaluate(
                    """
                    async (body) => {
                        const response = await fetch(window.location.href, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                "Accept": "application/json, text/plain, */*"
                            },
                            credentials: "include",
                            body
                        });

                        try {
                            const contentType = response.headers.get("content-type") || "";
                            if (contentType.includes("application/json")) {
                                await response.json();
                            } else {
                                await response.text();
                            }
                        } catch (_) {}
                    }
                    """,
                    body,
                )
                polluted = await self.test_pollution(page)

                if polluted:
                    finding = f"[JSON] Pollution detected: {url} :: {body}"
                    good(finding)
                    await self.save_finding(url, finding)
                else:
                    info(f"No JSON pollution: {url}")

            except Exception as exc:
                bad(f"JSON test failed for {url}: {exc}")
            finally:
                await context.close()

    async def scan_url(self, browser, url):
        info(f"Scanning {url}")

        query_tasks = [
            self.scan_query_payload(browser, url, payload)
            for payload in QUERY_PAYLOADS
        ]
        json_tasks = [
            self.scan_json_payload(browser, url, payload)
            for payload in JSON_PAYLOADS
        ]

        await asyncio.gather(*query_tasks, *json_tasks)

    async def scan_target(self, browser, target):
        urls = [target]

        if self.crawl:
            urls.extend(await self.extract_links(browser, target))

        for url in urls:
            await self.scan_url(browser, url)

    async def run(self):
        if not self.targets:
            warn("No targets supplied. Use -u URL or -f targets.txt.")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                await asyncio.gather(
                    *(self.scan_target(browser, target) for target in self.targets)
                )
            finally:
                await browser.close()
