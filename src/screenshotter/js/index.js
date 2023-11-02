const Sentry = require('@sentry/node');
const Integrations = require('@sentry/tracing');

const puppeteer = require('puppeteer');
const parseArgs = require('minimist');
const prettify = require('html-prettify');

const args = parseArgs(process.argv);

const { version, sentrydsn, sentryenv, sentrytracerate, url, path, selector, waitseconds, waitfor } = args;

try {
  if (sentrydsn !== '') {
    Sentry.init({
      dsn: sentrydsn,
      environment: sentryenv,
      release: version,
      integrations: [new Integrations.BrowserTracing()],
      tracesSampleRate: sentrytracerate,

    });
  }
} catch (e) {
  console.error(e);
}

const headers = JSON.parse(args.headers);
const viewportWidth = parseInt(args.vwidth, 10);
const viewportHeight = parseInt(args.vheight, 10);
const timeout = parseInt(args.timeout, 10);
const screamshotterCssClass = args.screamshottercssclass;
const waitSelectors = JSON.parse(args.waitselectors);

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--no-zygote',
      '--disable-setuid-sandbox',
      // https://github.com/GoogleChrome/puppeteer/blob/master/docs/troubleshooting.md#tips
      '--disable-dev-shm-usage',
    ],
  });

  const page = await browser.newPage();
  await page.setDefaultNavigationTimeout(timeout);
  await page.setDefaultTimeout(timeout);

  try {
    await page.setViewport({
      width: viewportWidth,
      height: viewportHeight,
    });

    await page.setExtraHTTPHeaders(headers);

    await page.goto(url, { waitUntil: 'networkidle0' });

    if (waitSelectors.length > 0) {
      waitSelectors.forEach(async wait => {
        await page.waitForSelector(wait);
      });
    }

    if (waitfor !== '' && waitfor !== null) {
      await page.waitForSelector(waitfor);
    }

    if (waitseconds !== 0) {
      await page.waitForTimeout(waitseconds);
    }

    const rect = await page.evaluate((aSelector, aCss) => {
      // dynamic add screamshotterCssClass css class to permit css customization
      console.error(aCss);
      document.body.classList.add(aCss);
      const element = document.querySelector(aSelector);
      if (element !== null) {
        const { x, y, width, height } = element.getBoundingClientRect();
        return { left: x, top: y, width, height, id: element.id };
      }
      const Exception = `The selector ${aSelector} was not found on this page`;
      return { exception: Exception };
    }, selector, screamshotterCssClass);

    if (typeof rect.left !== 'undefined') {
      await page.screenshot({
        path,
        clip: {
          x: rect.left,
          y: rect.top,
          width: rect.width,
          height: rect.height,
        },
      });
    } else {
      const bodyHTML = await page.evaluate(() => document.body.innerHTML);
      throw new Error(`${rect.exception}: ${prettify(bodyHTML)}`);
    }
  } catch (e) {
    console.error(e);
  } finally {
    await page.close();
    await browser.close();
    const pid = -browser.process().pid;
    try {
      // force killing chromium processes avoiding zombie processes
      process.kill(pid, 'SIGKILL');
    } catch (e) {
      // console.log('Kll browser processes');
    }
  }
})();
