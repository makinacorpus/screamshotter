import os

from django.conf import settings
from playwright.sync_api import sync_playwright

from .exceptions import ScreenshotterException
from .settings import app_settings

CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-zygote",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-extensions",
    "--disable-features=AudioServiceOutOfProcess,IsolateSandboxedIframes",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--mute-audio",
    "--password-store=basic",
    "--use-mock-keychain",
]


def _reap_zombies():
    try:
        while True:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid <= 0:
                break
    except ChildProcessError, OSError:
        pass


def _dismiss_dialog(dialog):
    try:
        dialog.dismiss()
    except Exception:
        pass


def take_screenshot(
    url,
    width=1920,
    height=1080,
    waitfor="body",
    wait_selectors=(),
    selector="body",
    wait_seconds=1,
    timeout=settings.TIMEOUT,
    forward_headers=None,
    screamshotter_css_class="screamshot",
):
    if forward_headers is None:
        forward_headers = {}

    _reap_zombies()

    try:
        timeout_val = float(timeout)
    except TypeError, ValueError:
        timeout_val = 60.0
    timeout_ms = max(timeout_val * 1000.0, 1.0)

    external_browser = os.getenv("EXTERNAL_PLAYWRIGHT") or os.getenv(
        "EXTERNAL_PUPPETEER", ""
    )
    executable_path = (
        app_settings.CHROMIUM_BROWSER_FILEPATH
        or os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
        or None
    )

    with sync_playwright() as playwright:
        browser = None
        context = None
        page = None
        try:
            if external_browser:
                browser = playwright.chromium.connect_over_cdp(external_browser)
            else:
                launch_kwargs = {
                    "headless": True,
                    "args": CHROMIUM_ARGS,
                }
                if executable_path:
                    launch_kwargs["executable_path"] = executable_path
                browser = playwright.chromium.launch(**launch_kwargs)

            headers = {str(k): str(v) for k, v in forward_headers.items()}
            context = browser.new_context(
                viewport={"width": int(width), "height": int(height)},
                ignore_https_errors=True,
                extra_http_headers=headers,
            )
            page = context.new_page()
            page.set_default_navigation_timeout(timeout_ms)
            page.set_default_timeout(timeout_ms)
            page.on("dialog", _dismiss_dialog)

            page.goto(url, wait_until="networkidle")

            for sel in wait_selectors:
                page.wait_for_selector(sel, timeout=timeout_ms)

            if waitfor:
                page.wait_for_selector(waitfor, timeout=timeout_ms)

            if wait_seconds and wait_seconds > 0:
                page.wait_for_timeout(wait_seconds * 1000)

            rect = page.evaluate(
                """([aSelector, cssClass]) => {
                    if (cssClass) {
                        document.body.classList.add(cssClass);
                    }
                    const element = document.querySelector(aSelector);
                    if (!element) {
                        return { error: `Selector ${aSelector} not found` };
                    }
                    const { x, y, width, height } = element.getBoundingClientRect();
                    return { left: x, top: y, width, height };
                }""",
                [selector, screamshotter_css_class],
            )

            if rect.get("error"):
                body_html = page.evaluate("() => document.body.innerHTML")
                raise ScreenshotterException(f"{rect['error']}\n{body_html}")

            screenshot_bytes = page.screenshot(
                clip={
                    "x": rect["left"],
                    "y": rect["top"],
                    "width": rect["width"],
                    "height": rect["height"],
                }
            )
            if not screenshot_bytes:
                raise ScreenshotterException("Empty screenshot generated")

            return screenshot_bytes
        except ScreenshotterException:
            raise
        except Exception as exc:
            raise ScreenshotterException(str(exc)) from exc
        finally:
            for resource in (page, context, browser):
                if resource is not None:
                    try:
                        resource.close()
                    except Exception:
                        pass
            _reap_zombies()
