#!/usr/bin/env bash
# Generate a speaker notes PDF from notes.html.
# Usage: ./build-notes-pdf.sh <notes-html> <output-pdf>
# Example: ./build-notes-pdf.sh eurollvm26/release-update/notes.html eurollvm26/release-update/notes.pdf

set -euo pipefail

NOTES_HTML="${1:-eurollvm26/release-update/notes.html}"
OUTPUT_PDF="${2:-eurollvm26/release-update/notes.pdf}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

NOTES_HTML_ABS="$(cd "$(dirname "$NOTES_HTML")" && pwd)/$(basename "$NOTES_HTML")"
OUTPUT_PDF_ABS="$(cd "$(dirname "$OUTPUT_PDF")" 2>/dev/null && pwd || echo "$SCRIPT_DIR")/$(basename "$OUTPUT_PDF")"

echo "Generating notes PDF from: $NOTES_HTML_ABS"
echo "Output: $OUTPUT_PDF_ABS"

node --input-type=module <<EOF
import { launch } from '/Users/thieta/.npm/_npx/cb02d645f7861450/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js';

const browser = await launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();

await page.goto('file://${NOTES_HTML_ABS}', { waitUntil: 'networkidle0' });

await page.pdf({
  path: '${OUTPUT_PDF_ABS}',
  format: 'A4',
  landscape: true,
  printBackground: true,
  margin: { top: 0, bottom: 0, left: 0, right: 0 },
});

await browser.close();
console.log('Saved: ${OUTPUT_PDF_ABS}');
EOF
