#!/usr/bin/env bash
# Dựng PowerPoint, PDF trình chiếu và PDF có lời thoại cho từng slide.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PPTX="$ROOT/slides/SLIDE-CHUYEN-DE-10.pptx"
PDF="$ROOT/slides/SLIDE-CHUYEN-DE-10.pdf"
NOTES_PDF="$ROOT/slides/SLIDE-CHUYEN-DE-10-SPEAKER-NOTES.pdf"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

SOFFICE="$(command -v soffice || true)"
if [ -z "$SOFFICE" ] && [ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
  SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
fi
if [ -z "$SOFFICE" ]; then
  echo "Không tìm thấy LibreOffice (soffice)." >&2
  exit 1
fi

node "$ROOT/slides/build/deck.js"
node "$ROOT/slides/build/finalize_pptx.js" "$PPTX"

NOTES_COUNT="$(
  unzip -Z1 "$PPTX" \
    | rg '^ppt/notesSlides/notesSlide[0-9]+\.xml$' \
    | wc -l \
    | tr -d ' '
)"
if [ "$NOTES_COUNT" -ne 18 ]; then
  echo "PPTX phải có speaker notes cho đủ 18 slide; hiện có $NOTES_COUNT." >&2
  exit 1
fi

mkdir -p "$TMP/slides" "$TMP/notes"
"$SOFFICE" --headless \
  --convert-to pdf \
  --outdir "$TMP/slides" \
  "$PPTX" >/dev/null 2>&1
"$SOFFICE" --headless \
  --convert-to 'pdf:impress_pdf_Export:{"ExportNotesPages":{"type":"boolean","value":"true"},"ExportOnlyNotesPages":{"type":"boolean","value":"true"}}' \
  --outdir "$TMP/notes" \
  "$PPTX" >/dev/null 2>&1

cp "$TMP/slides/SLIDE-CHUYEN-DE-10.pdf" "$PDF"
cp "$TMP/notes/SLIDE-CHUYEN-DE-10.pdf" "$NOTES_PDF"

echo "✓ PPTX: $PPTX"
echo "✓ PDF : $PDF  ($(pdfinfo "$PDF" | awk '/^Pages/{print $2}') slide)"
echo "✓ Notes: $NOTES_PDF  ($(pdfinfo "$NOTES_PDF" | awk '/^Pages/{print $2}') trang có lời thoại)"
