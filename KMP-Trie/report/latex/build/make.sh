#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LATEX_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$(cd "$LATEX_DIR/.." && pwd)"
OUTPUT="$REPORT_DIR/BAO-CAO-CHUYEN-DE-10.pdf"

if ! command -v latexmk >/dev/null 2>&1; then
  echo "Không tìm thấy latexmk. Hãy cài TeX Live/MacTeX." >&2
  exit 1
fi
if ! command -v xelatex >/dev/null 2>&1; then
  echo "Không tìm thấy XeLaTeX. Template này bắt buộc dùng XeLaTeX." >&2
  exit 1
fi

cd "$LATEX_DIR"
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
cp main.pdf "$OUTPUT"
latexmk -C >/dev/null
if [[ -f main.bbl ]]; then
  cleanup_dir="$(mktemp -d "${TMPDIR:-/tmp}/kmp-trie-latex-cleanup.XXXXXX")"
  mv main.bbl "$cleanup_dir/main.bbl"
fi

pages="$(pdfinfo "$OUTPUT" 2>/dev/null | awk '/^Pages:/ {print $2}')"
echo "✓ PDF LaTeX: $OUTPUT (${pages:-?} trang)"
