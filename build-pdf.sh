#!/usr/bin/env bash
# Build PDF from a mkslides presentation with speaker notes on separate pages.
# Usage: ./build-pdf.sh <presentation-dir> <output-pdf>
# Examples:
#   ./build-pdf.sh eurollvm26/release-update eurollvm26/release-update/slides-with-notes.pdf
#   ./build-pdf.sh llvm-arch llvm-arch/slides.pdf
#
# For nested presentations (suite/name), mkslides is invoked on the parent suite
# and the sub-path is used when generating the PDF.
# For top-level presentations (no parent suite), mkslides is invoked directly on
# the presentation directory.

set -euo pipefail

SLIDES_DIR="${1:-eurollvm26/release-update}"
OUTPUT_PDF="${2:-slides-with-notes.pdf}"
NOTES_FLAG="${3:-}"
PORT=18732

# Resolve absolute paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_PDF_ABS="$(cd "$(dirname "$OUTPUT_PDF")" 2>/dev/null && pwd || echo "$SCRIPT_DIR")/$(basename "$OUTPUT_PDF")"

# Determine the parent suite dir and the presentation sub-path
PARENT_DIR="$(dirname "$SLIDES_DIR")"
SLIDES_NAME="$(basename "$SLIDES_DIR")"

if [ "$PARENT_DIR" = "." ]; then
  # Top-level presentation: build the directory directly, served at /index.html
  echo "Building top-level presentation: $SLIDES_DIR"
  .venv/bin/mkslides build "$SLIDES_DIR"
  SLIDES_URL_PATH="index.html"
else
  # Nested presentation inside a suite directory
  echo "Building slides suite: $PARENT_DIR"
  .venv/bin/mkslides build "$PARENT_DIR"
  SLIDES_URL_PATH="${SLIDES_NAME}/slides.html"
fi

# Kill any existing server on the port
kill "$(lsof -ti:${PORT})" 2>/dev/null || true

# Start a local HTTP server in the background
python3 -m http.server "$PORT" --directory site &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null" EXIT

sleep 1

URL="http://localhost:${PORT}/${SLIDES_URL_PATH}"
echo "Generating PDF: $URL"
echo "Output: $OUTPUT_PDF_ABS"

node "$SCRIPT_DIR/print-pdf.mjs" "$URL" "$OUTPUT_PDF_ABS" $NOTES_FLAG

echo "Done: $OUTPUT_PDF_ABS"
