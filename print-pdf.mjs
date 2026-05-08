/**
 * Generate a PDF from a reveal.js presentation using Chrome's print-to-PDF.
 * Includes speaker notes on separate pages via showNotes=separate-page.
 *
 * Usage: node print-pdf.mjs <url> <output.pdf>
 */

import { launch } from '/Users/thieta/.npm/_npx/cb02d645f7861450/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js';

const [,, url, outputPath] = process.argv;
if (!url || !outputPath) {
  console.error('Usage: node print-pdf.mjs <url> <output.pdf>');
  process.exit(1);
}

// Append print-pdf and showNotes query params
const printUrl = new URL(url);
printUrl.searchParams.set('print-pdf', '');
printUrl.searchParams.set('showNotes', 'separate-page');

console.log(`Loading: ${printUrl}`);

const browser = await launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080 });

// Wait for reveal.js to fully initialize and render all slides in print mode
await page.goto(printUrl.toString(), { waitUntil: 'networkidle0', timeout: 60000 });

// Extra wait to ensure all images and fonts are loaded
await new Promise(r => setTimeout(r, 2000));

await page.pdf({
  path: outputPath,
  width: '1920px',
  height: '1080px',
  printBackground: true,
  margin: { top: 0, bottom: 0, left: 0, right: 0 },
});

await browser.close();
console.log(`Saved: ${outputPath}`);
