#!/usr/bin/env python3
"""Kiểm tra tính nhất quán của research artifact trước khi nộp."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "MANIFEST.json"
PPTX = ROOT / "slides" / "SLIDE-CHUYEN-DE-10.pptx"
SLIDES_PDF = ROOT / "slides" / "SLIDE-CHUYEN-DE-10.pdf"
NOTES_PDF = ROOT / "slides" / "SLIDE-CHUYEN-DE-10-SPEAKER-NOTES.pdf"
REPORT_PDF = ROOT / "report" / "BAO-CAO-CHUYEN-DE-10.pdf"


def fail(message: str) -> None:
    raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = [*manifest["texts"], *manifest["dictionaries"]]
    entries.append(manifest["patterns"])
    entries.extend(manifest["demo"])
    for entry in entries:
        path = ROOT / entry["file"]
        if not path.is_file():
            fail(f"Thiếu dữ liệu trong manifest: {entry['file']}")
        if sha256(path) != entry["sha256"]:
            fail(f"SHA-256 không khớp: {entry['file']}")
    return len(entries)


def verify_storage_csv() -> int:
    path = ROOT / "results" / "benchmarks" / "e4_storage_tradeoff.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        fail("E4 storage không có dữ liệu")
    for row in rows:
        expected = float(row["array_peak_mem_bytes"]) / float(row["dict_peak_mem_bytes"])
        recorded = float(row["array_over_dict"])
        if abs(expected - recorded) > 0.011:
            fail(f"Tỉ số E4 sai tại N={row['N']}")
    return len(rows)


def verify_pptx_notes() -> tuple[int, set[str]]:
    with ZipFile(PPTX) as archive:
        names = [
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        if len(names) != 18:
            fail(f"PPTX có {len(names)}/18 speaker notes")
        speakers: set[str] = set()
        for name in names:
            xml = archive.read(name).decode("utf-8")
            match = re.search(r"\[(HUỲNH PHÁT LỢI|VÕ PHÚ VINH|THANH TÚ)", xml)
            if not match:
                fail(f"Note không có tên người nói: {name}")
            speakers.add(match.group(1))
    expected = {"HUỲNH PHÁT LỢI", "VÕ PHÚ VINH", "THANH TÚ"}
    if speakers != expected:
        fail(f"Phân công người nói chưa đủ: {sorted(speakers)}")
    return len(names), speakers


def pdf_pages(path: Path) -> int | None:
    if shutil.which("pdfinfo") is None:
        return None
    output = subprocess.check_output(["pdfinfo", str(path)], text=True)
    match = re.search(r"^Pages:\s+(\d+)$", output, re.MULTILINE)
    return int(match.group(1)) if match else None


def verify_artifact_files() -> None:
    for path in (REPORT_PDF, PPTX, SLIDES_PDF, NOTES_PDF):
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"Thiếu artifact: {path.relative_to(ROOT)}")
    for path in (SLIDES_PDF, NOTES_PDF):
        pages = pdf_pages(path)
        if pages is not None and pages != 18:
            fail(f"{path.name} có {pages}/18 trang")
    if list((ROOT / "report").glob("*.docx")):
        fail("DOCX song song có thể mâu thuẫn với nguồn LaTeX")


def verify_no_stale_claims() -> None:
    paths = [
        ROOT / "README.md",
        ROOT / "report" / "latex" / "chapters" / "report_content.tex",
        ROOT / "report" / "latex" / "appendices" / "appendix_resources.tex",
        ROOT / "slides" / "build" / "deck.js",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    stale = {
        "275 test": "số test cũ",
        "235 test": "số unit test cũ",
        "1,29": "tỉ số bộ nhớ E4 cũ",
        "mã băm MD5": "thuật toán băm cũ",
    }
    for needle, meaning in stale.items():
        if needle in combined:
            fail(f"Còn {meaning}: {needle!r}")


def main() -> int:
    try:
        files = verify_manifest()
        e4_rows = verify_storage_csv()
        notes, speakers = verify_pptx_notes()
        verify_artifact_files()
        verify_no_stale_claims()
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: {files} checksum SHA-256 trong MANIFEST")
    print(f"PASS: {e4_rows} dòng E4 khớp tỉ số bộ nhớ")
    print(f"PASS: {notes} speaker notes, đủ {len(speakers)} thành viên")
    print("PASS: report/PPTX/PDF đầy đủ và không có claim cũ")

    metadata = (
        ROOT / "report" / "latex" / "config" / "metadata.tex"
    ).read_text(encoding="utf-8")
    if "BỔ SUNG TÊN GIẢNG VIÊN" in metadata:
        print("WARNING: cần điền tên giảng viên trong metadata.tex", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
