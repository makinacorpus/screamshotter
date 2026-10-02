const Sentry = require('@sentry/node');
const puppeteer = require('puppeteer');
const parseArgs = require('minimist');
const prettify = require('html-prettify');

const args = parseArgs(process.argv);

const {
  version,
  sentrydsn,
  sentryenv,
  sentrytracerate,
  url,
  path,
  selector,
  waitseconds,
  waitfor,
} = args;

try {
  if (sentrydsn) {
    Sentry.init({
      dsn: sentrydsn,
      environment: sentryenv,
      release: version,
      tracesSampleRate: sentrytracerate,
    });
  }
} catch (e) {
  console.error('Sentry init failed', e);
}

const headers = JSON.parse(args.headers || '{}');
const viewportWidth = parseInt(args.vwidth, 10) || 1280;
const viewportHeight = parseInt(args.vheight, 10) || 800;
const timeout = parseInt(args.timeout, 10) || 30000;
const screamshotterCssClass = args.screamshottercssclass || '';
const waitSelectors = JSON.parse(args.waitselectors || '[]');
const externalPuppeteer = args.external_puppeteer || '';

let browser;

const closeBrowser = async () => {
  if (!browser) return;
  const proc = browser.process ? browser.process() : null;
  const pid = proc ? proc.pid : null;

  try {
    const pages = await Promise.race([
      browser.pages ? browser.pages() : [],
      new Promise(resolve => { setTimeout(() => resolve([]), 1500); }),
    ]);
    if (pages && pages.length > 0) {
      await Promise.race([
        Promise.all(
          pages.map(async p => {
            try {
              await p.close();
            } catch (_) {
              // ignore
            }
          }),
        ),
        new Promise(resolve => { setTimeout(resolve, 2000); }),
      ]);
    }
  } catch (_) {
    // ignore
  }

  let closed = false;
  try {
    await Promise.race([
      browser.close().then(() => { closed = true; }),
      new Promise(resolve => { setTimeout(resolve, 3000); }),
    ]);
  } catch (_) {
    // ignore
  }

  if (!closed && pid) {
    try {
      process.kill(-pid, 'SIGKILL');
    } catch (_) {
      try {
        proc.kill('SIGKILL');
      } catch (__) {
        // ignore
      }
    }
  }
};

let isShuttingDown = false;
const cleanExit = async (code = 1) => {
  if (isShuttingDown) return;
  isShuttingDown = true;
  await closeBrowser();
  process.exit(code);
};

process.on('SIGTERM', () => { cleanExit(143); });
process.on('SIGINT', () => { cleanExit(130); });
process.on('SIGHUP', () => { cleanExit(129); });
process.on('unhandledRejection', async err => {
  console.error('Unhandled rejection:', err);
  await cleanExit(1);
});

const overallTimeout = timeout + 10000;
const watchdog = setTimeout(async () => {
  console.error(`Execution watchdog timeout exceeded (${overallTimeout}ms). Force killing...`);
  await cleanExit(1);
}, overallTimeout);
watchdog.unref();

(async () => {
  try {
    if (externalPuppeteer) {
      browser = await puppeteer.connect({
        browserWSEndpoint: externalPuppeteer,
        acceptInsecureCerts: true,
        ignoreHTTPSErrors: true,
      });
    } else {
      browser = await puppeteer.launch({
        headless: true,
        pipe: true,
        acceptInsecureCerts: true,
        ignoreHTTPSErrors: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--no-zygote',
          '--no-first-run',
          '--no-default-browser-check',
          '--disable-background-networking',
          '--disable-background-timer-throttling',
          '--disable-backgrounding-occluded-windows',
          '--disable-breakpad',
          '--disable-client-side-phishing-detection',
          '--disable-component-update',
          '--disable-default-apps',
          '--disable-domain-reliability',
          '--disable-extensions',
          '--disable-features=AudioServiceOutOfProcess,IsolateSandboxedIframes',
          '--disable-hang-monitor',
          '--disable-ipc-flooding-protection',
          '--disable-popup-blocking',
          '--disable-prompt-on-repost',
          '--disable-renderer-backgrounding',
          '--disable-sync',
          '--force-color-profile=srgb',
          '--metrics-recording-only',
          '--mute-audio',
          '--password-store=basic',
          '--use-mock-keychain',
        ],
      });
    }

    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(timeout);
    page.setDefaultTimeout(timeout);

    page.on('dialog', async dialog => {
      try {
        await dialog.dismiss();
      } catch (_) {
        // ignore
      }
    });

    await page.setViewport({
      width: viewportWidth,
      height: viewportHeight,
    });

    await page.setExtraHTTPHeaders(headers);

    await page.goto(url, { waitUntil: 'networkidle2' });

    // wait multiple elements safely
    if (waitSelectors.length > 0) {
      await Promise.all(
        waitSelectors.map(sel => page.waitForSelector(sel, { timeout })),
      );
    }

    // optional single wait
    if (waitfor) {
      await page.waitForSelector(waitfor, { timeout });
    }

    // wait X seconds if needed (convert to ms explicitly)
    if (waitseconds && waitseconds > 0) {
      await new Promise(resolve => {
        setTimeout(resolve, waitseconds);
      });
    }

    const rect = await page.evaluate((aSelector, cssClass) => {
      if (cssClass) {
        document.body.classList.add(cssClass);
      }
      const element = document.querySelector(aSelector);
      if (!element) {
        return { error: `Selector ${aSelector} not found` };
      }

      const { x, y, width, height } = element.getBoundingClientRect();
      return { left: x, top: y, width, height };
    }, selector, screamshotterCssClass);

    if (rect.error) {
      const bodyHTML = await page.evaluate(() => document.body.innerHTML);
      throw new Error(`${rect.error}\n${prettify(bodyHTML)}`);
    }

    await page.screenshot({
      path,
      clip: {
        x: rect.left,
        y: rect.top,
        width: rect.width,
        height: rect.height,
      },
    });

    console.log('Screenshot OK');
  } catch (err) {
    console.error('Capture failed:', err);
    process.exitCode = 1;
  } finally {
    clearTimeout(watchdog);
    await closeBrowser();
  }
})();
