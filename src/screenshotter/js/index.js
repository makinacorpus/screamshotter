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

(async () => {
  try {
    if (externalPuppeteer) {
      browser = await puppeteer.connect({
        browserWSEndpoint: externalPuppeteer,
        ignoreHTTPSErrors: true,
      });
    } else {
      browser = await puppeteer.launch({
        headless: 'new',
        ignoreHTTPSErrors: true,
        args: [
          '--no-sandbox',
          '--no-zygote',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
        ],
      });
    }

    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(timeout);
    page.setDefaultTimeout(timeout);

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
      await page.waitForTimeout(waitseconds);
    }

    const rect = await page.evaluate((aSelector, cssClass) => {
      document.body.classList.add(cssClass);
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
  } finally {
    try {
      const pages = await browser?.pages?.();
      if (pages) {
        await Promise.all(
          pages.map(async p => {
            try {
              await p.close();
            } catch (e) {
              console.error('page.close() failed → ignore');
            }
          }),
        );
      }
    } catch (e) {
      console.error('browser.pages() failed → ignore');
    }

    try {
      if (browser) {
        await browser.close();
      }
    } catch (e) {
      console.error('browser.close() failed → force kill', e);

      try {
        if (browser?.process()) {
          browser.process().kill('SIGKILL');
        }
      } catch (_e) {
        console.error('browser.process().kill() failed → ignore', _e);
      }
    }
  }
})();
