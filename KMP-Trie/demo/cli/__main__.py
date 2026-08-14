#!/usr/bin/env python3
"""Demo CLI tương tác — Interactive Text Search & Autocomplete System.

Hai mô-đun hoạt động cùng nhau nhưng vai trò tách bạch:
  - Trie  gợi ý từ khóa theo tiền tố đang gõ  (mô-đun B)
  - KMP   tìm mọi vị trí của từ khóa đã chọn  (mô-đun A)

Cách chạy:
    python -m demo.cli
    python -m demo.cli --text data/small/demo_corpus.txt \
                       --dict data/dictionaries/demo_words.txt
    python -m demo.cli --search "kmp" --json     # chế độ không tương tác

Trong phiên tương tác, gõ `:help` để xem danh sách lệnh.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.common.alphabet import get_alphabet  # noqa: E402
from src.common.metrics import OpCounter  # noqa: E402
from src.common.textio import load_dictionary, read_text, tokenize  # noqa: E402
from src.kmp import AhoCorasick, KMPMatcher, build_lps  # noqa: E402
from src.trie import Trie  # noqa: E402

DEFAULT_TEXT = ROOT / "data" / "small" / "demo_corpus.txt"
DEFAULT_DICT = ROOT / "data" / "dictionaries" / "demo_words.txt"

BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"
HL, OK, WARN = "\033[43;30m", "\033[32m", "\033[33m"


def _c(s: str, code: str, color: bool) -> str:
    return f"{code}{s}{RESET}" if color else s


# --------------------------------------------------------------------------- #
class SearchSystem:
    """Gắn kết hai mô-đun thành một hệ thống."""

    def __init__(self, text: str, words: list[str], alphabet_name: str) -> None:
        self.text = text
        self.alphabet = get_alphabet(alphabet_name)
        self.trie = Trie(self.alphabet)
        self.trie.insert_many(words)
        self._matchers: dict[str, KMPMatcher] = {}

    # --- mô-đun B --- #
    def suggest(self, prefix: str, k: int = 8):
        c = OpCounter()
        r = self.trie.autocomplete(prefix, k, c)
        return r, c

    # --- mô-đun A --- #
    def search(self, pattern: str):
        m = self._matchers.get(pattern)
        if m is None:
            m = KMPMatcher(pattern)
            self._matchers[pattern] = m  # tái sử dụng π giữa các truy vấn
        c = OpCounter()
        return m.search(self.text, c), m.lps, c

    def highlight(self, pattern: str, positions: list[int], color: bool,
                  context: int = 40, limit: int = 10) -> list[str]:
        """Trích đoạn văn bản quanh mỗi lần khớp, tô sáng phần khớp."""
        out = []
        m = len(pattern)
        for pos in positions[:limit]:
            lo = max(0, pos - context)
            hi = min(len(self.text), pos + m + context)
            before = self.text[lo:pos].replace("\n", "⏎")
            hit = self.text[pos : pos + m].replace("\n", "⏎")
            after = self.text[pos + m : hi].replace("\n", "⏎")
            prefix = "…" if lo > 0 else ""
            suffix = "…" if hi < len(self.text) else ""
            out.append(
                f"  {DIM if color else ''}[{pos:>7}]{RESET if color else ''} "
                f"{prefix}{before}{_c(hit, HL, color)}{after}{suffix}"
            )
        if len(positions) > limit:
            out.append(f"  {DIM if color else ''}… và {len(positions)-limit} "
                       f"lần khớp nữa{RESET if color else ''}")
        return out


# --------------------------------------------------------------------------- #
HELP = """
Lệnh:
  <chuỗi>          tìm mọi vị trí xuất hiện của chuỗi bằng KMP (mô-đun A)
  ?<tiền tố>       gợi ý từ có tiền tố đó bằng Trie (mô-đun B)
  :lps <mẫu>       in mảng LPS (hàm tiền tố π) của mẫu
  :multi w1 w2 ..  tìm nhiều mẫu cùng lúc bằng Aho-Corasick (mở rộng)
  :stats           thống kê Trie và văn bản
  :count <tiền tố> số từ trong từ điển có tiền tố đó (dùng prefix_count, O(|q|))
  :help            trợ giúp
  :quit            thoát
"""


def interactive(sys_: SearchSystem, color: bool) -> int:
    print(_c("Interactive Text Search & Autocomplete System", BOLD, color))
    print(f"{DIM if color else ''}Chuyên đề 10 — KMP và Trie"
          f"{RESET if color else ''}")
    print(f"Văn bản: {len(sys_.text):,} ký tự | Từ điển: {len(sys_.trie):,} từ, "
          f"{sys_.trie.num_nodes:,} nút | Σ = {sys_.alphabet.name} "
          f"(|Σ| = {len(sys_.alphabet)})")
    print(HELP)

    while True:
        try:
            line = input(_c("› ", BOLD, color)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue

        # ---------------- lệnh ---------------- #
        if line in (":quit", ":q", ":exit"):
            return 0
        if line in (":help", ":h", "?"):
            print(HELP)
            continue
        if line == ":stats":
            st = sys_.trie.stats()
            print(_c("  Trie:", BOLD, color))
            for k, v in st.items():
                print(f"    {k:<22} {v}")
            print(_c("  Văn bản:", BOLD, color))
            print(f"    {'độ dài n':<22} {len(sys_.text):,}")
            print(f"    {'số ký tự phân biệt':<22} {len(set(sys_.text))}")
            continue
        if line.startswith(":lps "):
            pat = line[5:].strip()
            if not pat:
                print(_c("  Cần một mẫu.", WARN, color))
                continue
            lps = build_lps(pat)
            print("    i  : " + " ".join(f"{i:>3}" for i in range(len(pat))))
            print("    P  : " + " ".join(f"{ch:>3}" for ch in pat))
            print("    π  : " + " ".join(f"{v:>3}" for v in lps))
            print(f"    dãy biên của toàn mẫu: {KMPMatcher(pat).borders()}")
            continue
        if line.startswith(":count "):
            pref = line[7:].strip()
            print(f"  {sys_.trie.count_with_prefix(pref):,} từ có tiền tố "
                  f"{pref!r} (tính bằng prefix_count, O(|q|))")
            continue
        if line.startswith(":multi "):
            pats = [p for p in line[7:].split() if p]
            if not pats:
                print(_c("  Cần ít nhất một mẫu.", WARN, color))
                continue
            ac = AhoCorasick(pats)
            counts = ac.count_all(sys_.text)
            print(f"  Aho-Corasick: {ac.num_nodes} nút, một lượt duyệt")
            for p, n in counts.items():
                mark = _c("✓", OK, color) if n else _c("·", DIM, color)
                print(f"    {mark} {p:<20} {n:>6} lần")
            continue

        # ---------------- gợi ý (mô-đun B) ---------------- #
        if line.startswith("?"):
            prefix = line[1:]
            r, c = sys_.suggest(prefix, 8)
            if not r.suggestions:
                print(_c(f"  Không có từ nào bắt đầu bằng {prefix!r}", WARN, color))
            else:
                for s in r.suggestions:
                    rest = s[len(prefix):]
                    print(f"  {prefix}{_c(rest, BOLD, color)}")
                if r.truncated:
                    total = sys_.trie.count_with_prefix(prefix)
                    print(f"  {DIM if color else ''}… (hiển thị 8 / {total} kết quả)"
                          f"{RESET if color else ''}")
            print(f"  {DIM if color else ''}[Trie: {c.nodes_visited} nút đã duyệt]"
                  f"{RESET if color else ''}")
            continue

        # ---------------- tìm kiếm (mô-đun A) ---------------- #
        try:
            positions, lps, c = sys_.search(line)
        except ValueError as e:
            print(_c(f"  {e}", WARN, color))
            continue

        if not positions:
            print(_c(f"  Không tìm thấy {line!r}", WARN, color))
        else:
            print(_c(f"  {len(positions)} lần khớp", OK, color))
            for ln in sys_.highlight(line, positions, color):
                print(ln)
        n = len(sys_.text)
        print(f"  {DIM if color else ''}[KMP: π = {lps} | "
              f"{c.char_comparisons} phép so sánh trên n = {n:,} "
              f"⇒ {c.char_comparisons / n:.3f}·n ≤ 2n]{RESET if color else ''}")


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Demo CLI — Interactive Text Search & Autocomplete System"
    )
    ap.add_argument("--text", default=str(DEFAULT_TEXT), help="tệp văn bản")
    ap.add_argument("--dict", dest="dict_", default=str(DEFAULT_DICT),
                    help="tệp từ điển (1 từ/dòng)")
    ap.add_argument("--alphabet", default="ascii_lower_digits",
                    help="tên bảng chữ cái Σ")
    ap.add_argument("--build-dict-from-text", action="store_true",
                    help="xây từ điển bằng cách tách token từ văn bản")
    ap.add_argument("--search", help="chế độ không tương tác: tìm mẫu này rồi thoát")
    ap.add_argument("--suggest", help="chế độ không tương tác: gợi ý cho tiền tố này")
    ap.add_argument("-k", type=int, default=10, help="số gợi ý tối đa")
    ap.add_argument("--json", action="store_true", help="xuất JSON")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    text_path, dict_path = Path(args.text), Path(args.dict_)
    if not text_path.exists():
        print(f"Không tìm thấy tệp văn bản: {text_path}", file=sys.stderr)
        print("Gợi ý: chạy `python scripts/gen_data.py --quick` trước.",
              file=sys.stderr)
        return 2

    alphabet = get_alphabet(args.alphabet)
    text = read_text(text_path)

    if args.build_dict_from_text:
        words = sorted(set(tokenize(text, alphabet)))
    else:
        if not dict_path.exists():
            print(f"Không tìm thấy từ điển: {dict_path}", file=sys.stderr)
            return 2
        # skip_invalid=True ở tầng demo: dữ liệu sinh tự động có thể lẫn ký tự
        # ngoài Σ; tầng Trie vẫn từ chối tường minh khi insert.
        words = load_dictionary(dict_path, alphabet=alphabet, skip_invalid=True)

    system = SearchSystem(text, words, args.alphabet)
    color = not args.no_color and sys.stdout.isatty()

    # ------------------ chế độ không tương tác ------------------ #
    if args.search or args.suggest:
        payload: dict = {}
        if args.suggest is not None:
            r, c = system.suggest(args.suggest, args.k)
            payload["autocomplete"] = r.to_dict()
            payload["autocomplete"]["nodes_visited"] = c.nodes_visited
        if args.search:
            positions, lps, c = system.search(args.search)
            payload["search"] = {
                "pattern": args.search,
                "positions": positions,
                "count": len(positions),
                "lps": lps,
                "char_comparisons": c.char_comparisons,
                "n": len(text),
                "comparisons_per_n": round(c.char_comparisons / len(text), 4),
            }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            if "autocomplete" in payload:
                a = payload["autocomplete"]
                print(f"Gợi ý cho {a['prefix']!r} "
                      f"({'bị cắt' if a['truncated'] else 'đầy đủ'}):")
                for s in a["suggestions"]:
                    print(f"  {s}")
            if "search" in payload:
                s = payload["search"]
                print(f"{s['count']} lần khớp {s['pattern']!r}: "
                      f"{s['positions'][:20]}"
                      f"{' …' if s['count'] > 20 else ''}")
                print(f"π = {s['lps']}")
                print(f"{s['char_comparisons']} phép so sánh "
                      f"= {s['comparisons_per_n']}·n")
                for ln in system.highlight(args.search, s["positions"], color):
                    print(ln)
        return 0

    return interactive(system, color)


if __name__ == "__main__":
    raise SystemExit(main())
