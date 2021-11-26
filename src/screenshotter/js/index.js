const puppeteer = require('puppeteer');
const parseArgs = require('minimist');

const args = parseArgs(process.argv);
const { url, path, selector, waitseconds, waitfor } = args;
const headers = JSON.parse(args.headers);
const viewportWidth = parseInt(args.vwidth, 10);
const viewportHeight = parseInt(args.vheight, 10);
const timeout = parseInt(args.timeout, 10);
const waitSelectors = JSON.parse(args.waitselectors);

(async () => {
  const browser = await puppeteer.launch({
    args: [
      '--no-sandbox',
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

    const rect = await page.evaluate(aSelector => {
      // dynamic add screamshot css class to permit css customization
      document.body.classList.add('screamshot');
      const element = document.querySelector(aSelector);
      const { x, y, width, height } = element.getBoundingClientRect();
      return { left: x, top: y, width, height, id: element.id };
    }, selector);

    await page.screenshot({
      path,
      clip: {
        x: rect.left,
        y: rect.top,
        width: rect.width,
        height: rect.height,
      },
    });
  } catch (e) {
    console.error(e);
  } finally {
    await page.close();
    await browser.close();
  }
})();
