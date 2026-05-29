# PropScanner

PropScanner is a small Playwright-based prototype pollution scanner for authorized bug bounty and security research workflows.

It opens targets in a real Chromium browser, injects lightweight runtime hooks, sends common query-string and JSON prototype pollution payloads, and stores confirmed signals in `findings/`.

> Use this tool only on assets where you have explicit permission to test.

## Features

- Query parameter payload testing:
  - `__proto__[pp_test]=1337`
  - `constructor[prototype][pp_test]=1337`
  - dot-notation variants
- JSON `POST` payload testing.
- Same-origin crawling mode.
- Isolated browser context per payload to reduce false positives from polluted state leaking between checks.
- Browser sink instrumentation for useful gadget signals:
  - `innerHTML`
  - `outerHTML`
  - `insertAdjacentHTML`
  - `setAttribute`
  - `document.write`
  - `eval`
  - `Function`
  - `setTimeout`
  - `setInterval`
  - `fetch`
- Per-target finding files in `findings/`.
- Simple CLI for single targets or target lists.

## Installation

```bash
git clone https://github.com/your-name/propscanner.git
cd propscanner

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## Usage

Scan one target:

```bash
python main.py -u https://example.com
```

Scan a list of targets:

```bash
python main.py -f targets.txt
```

Enable same-origin crawling:

```bash
python main.py -u https://example.com --crawl --max-pages 25
```

Tune concurrency and timeout:

```bash
python main.py -f targets.txt --crawl -c 5 --timeout 20000
```

`targets.txt` supports blank lines and comments:

```txt
# program scope
https://app.example.com
https://admin.example.com
```

## Output

Console output uses three signal types:

```txt
[*] Testing query payload: https://example.com/?__proto__[pp_test]=1337
[+] [QUERY] Pollution detected: https://example.com/?__proto__[pp_test]=1337
[+] [GADGET] https://example.com/ :: [PP Gadget][innerHTML] ...
```

Findings are saved under:

```txt
findings/
```

Each target gets a separate text file. A `[QUERY]` or `[JSON]` finding means the marker reached `Object.prototype`. A `[GADGET]` finding means the marker flowed into an instrumented browser sink and deserves manual review.

## CLI Options

```txt
-u, --url           Single target URL
-f, --file          File with target URLs
--crawl             Crawl same-origin links before scanning
--max-pages         Maximum crawled pages per target, default: 10
-c, --concurrency   Concurrent browser checks, default: 3
--timeout           Navigation timeout in milliseconds, default: 15000
```

## How It Works

PropScanner starts Chromium through Playwright, injects `hooks.js` before page scripts run, and then tests each payload in a fresh browser context.

For query payloads, it appends the payload to the URL and checks whether:

```js
Object.prototype.pp_test === '1337'
```

For JSON payloads, it loads the page and sends a same-page `POST` request with prototype pollution-shaped JSON bodies. The browser hooks also log possible gadget flows when the marker reaches dangerous DOM or code execution sinks.

## Extending Payloads

Add new payloads in `payloads.py`:

```python
QUERY_PAYLOADS = [
    "__proto__[pp_test]=1337",
]

JSON_PAYLOADS = [
    {"__proto__": {"pp_test": "1337"}},
]
```

Good next payload families to add:

- framework-specific keys
- sanitizer configuration keys
- client-side router state keys
- library-specific merge parser bypasses
- application-specific feature flags discovered during recon

## Bug Bounty Workflow

A practical workflow usually looks like this:

```txt
subdomain discovery -> HTTP probing -> crawling -> PropScanner -> manual gadget analysis -> proof of impact
```

Prototype pollution reports are strongest when you can show impact beyond pollution itself, such as DOM XSS, authorization bypass, sanitizer bypass, or control over a security-sensitive configuration value.

## Limitations

- This is a prototype scanner, not a complete exploitation framework.
- JSON checks depend on how the application handles same-page `POST` requests.
- A gadget log is a signal for manual investigation, not automatically a vulnerability.
- Headless browser behavior may differ from a real user session.
- Authenticated areas require you to add your own session handling or proxy workflow.

## Legal Notice

PropScanner is intended for authorized testing, bug bounty research, and defensive validation. Do not run it against systems where you do not have permission to test.
