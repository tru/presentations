#!/usr/bin/env bash
# Build PDF from a mkslides presentation with speaker notes on separate pages.
# Usage: ./build-pdf.sh <presentation-dir> <output-pdf>
# Example: ./build-pdf.sh eurollvm26/release-update eurollvm26/release-update/slides-with-notes.pdf
#
# The presentation-dir must be a subdirectory of a parent "suite" directory.
# mkslides is invoked on the parent so all presentations are built, and the
# correct sub-path is used when generating the PDF.

set -euo pipefail

SLIDES_DIR="${1:-eurollvm26/release-update}"
OUTPUT_PDF="${2:-slides-with-notes.pdf}"
PORT=18732

# Resolve absolute paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_PDF_ABS="$(cd "$(dirname "$OUTPUT_PDF")" 2>/dev/null && pwd || echo "$SCRIPT_DIR")/$(basename "$OUTPUT_PDF")"

# Determine the parent suite dir and the presentation sub-path
PARENT_DIR="$(dirname "$SLIDES_DIR")"
SLIDES_NAME="$(basename "$SLIDES_DIR")"

echo "Building slides suite: $PARENT_DIR"
.venv/bin/mkslides build "$PARENT_DIR"

# Kill any existing server on the port
kill "$(lsof -ti:${PORT})" 2>/dev/null || true

# Start a local HTTP server in the background
python3 -m http.server "$PORT" --directory site &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null" EXIT

sleep 1

URL="http://localhost:${PORT}/${SLIDES_NAME}/slides.html"
echo "Generating PDF with notes: $URL"
echo "Output: $OUTPUT_PDF_ABS"

node "$SCRIPT_DIR/print-pdf.mjs" "$URL" "$OUTPUT_PDF_ABS"

echo "Done: $OUTPUT_PDF_ABS"
