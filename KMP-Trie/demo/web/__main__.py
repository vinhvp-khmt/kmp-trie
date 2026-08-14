#!/usr/bin/env python3
"""Demo web — Interactive Text Search & Autocomplete System.

Chỉ dùng thư viện chuẩn (http.server) — không framework, để mã nguồn chạy lại
được theo README mà không cần cài thêm gì (yêu cầu của đề).

Cách chạy:
    python -m demo.web
    python -m demo.web --port 8080 --text data/medium/natural_100000.txt \
                       --dict data/dictionaries/synthetic_20000.txt

Rồi mở http://localhost:8000

API:
    GET /api/suggest?prefix=...&k=8   → Trie autocomplete (mô-đun B)
    GET /api/search?pattern=...       → KMP tìm mọi vị trí (mô-đun A)
    GET /api/multi?patterns=a,b,c     → Aho-Corasick (mở rộng)
    GET /api/stats                    → thống kê
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.common.alphabet import get_alphabet  # noqa: E402
from src.common.metrics import OpCounter  # noqa: E402
from src.common.textio import load_dictionary, read_text  # noqa: E402
from src.kmp import AhoCorasick, KMPMatcher  # noqa: E402
from src.trie import Trie  # noqa: E402

STATE: dict = {}
INDEX_HTML = Path(__file__).parent / "index.html"


# --------------------------------------------------------------------------- #
def api_suggest(prefix: str, k: int) -> dict:
    trie: Trie = STATE["trie"]
    c = OpCounter()
    r = trie.autocomplete(prefix, k, c)
    return {
        **r.to_dict(),
        "total_with_prefix": trie.count_with_prefix(prefix),
        "nodes_visited": c.nodes_visited,
        "module": "B — Trie",
        "complexity": f"O(|q|={len(prefix)} + số nút duyệt={c.nodes_visited})",
    }


def api_search(pattern: str, limit: int = 200) -> dict:
    if not pattern:
        return {"error": "Mẫu rỗng không hợp lệ (yêu cầu m ≥ 1)"}
    text: str = STATE["text"]
    cache: dict = STATE["matchers"]
    m = cache.get(pattern)
    if m is None:
        m = KMPMatcher(pattern)
        cache[pattern] = m
    c = OpCounter()
    positions = m.search(text, c)
    n = len(text)
    return {
        "pattern": pattern,
        "positions": positions[:limit],
        "count": len(positions),
        "truncated": len(positions) > limit,
        "lps": m.lps,
        "borders": m.borders(),
        "n": n,
        "m": len(pattern),
        "char_comparisons": c.char_comparisons,
        "comparisons_per_n": round(c.char_comparisons / n, 4) if n else 0,
        "bound_2n": 2 * n,
        "snippets": [_snippet(text, p, len(pattern)) for p in positions[:40]],
        "module": "A — KMP",
        "complexity": f"O(n+m) = O({n}+{len(pattern)})",
    }


def _snippet(text: str, pos: int, m: int, ctx: int = 45) -> dict:
    lo, hi = max(0, pos - ctx), min(len(text), pos + m + ctx)
    return {
        "pos": pos,
        "before": text[lo:pos],
        "hit": text[pos : pos + m],
        "after": text[pos + m : hi],
        "elided_left": lo > 0,
        "elided_right": hi < len(text),
    }


def api_multi(patterns: list[str]) -> dict:
    patterns = [p for p in patterns if p]
    if not patterns:
        return {"error": "Cần ít nhất một mẫu"}
    text: str = STATE["text"]
    ac = AhoCorasick(patterns)
    c = OpCounter()
    matches = ac.search(text, c)
    counts = ac.count_all(text)

    # So sánh với KMP lặp, để thấy lợi ích của một lượt duyệt.
    c_kmp = OpCounter()
    for p in patterns:
        KMPMatcher(p).search(text, c_kmp)

    return {
        "patterns": patterns,
        "counts": counts,
        "total_matches": len(matches),
        "num_nodes": ac.num_nodes,
        "ac_comparisons": c.char_comparisons,
        "kmp_repeated_comparisons": c_kmp.char_comparisons,
        "ratio": (
            round(c_kmp.char_comparisons / c.char_comparisons, 2)
            if c.char_comparisons
            else 0
        ),
        "first_matches": [m.to_dict() for m in matches[:50]],
        "module": "Mở rộng — Aho-Corasick",
    }


def api_stats() -> dict:
    trie: Trie = STATE["trie"]
    text: str = STATE["text"]
    return {
        "trie": trie.stats(),
        "text": {
            "n": len(text),
            "distinct_chars": len(set(text)),
            "source": STATE["text_name"],
        },
        "dictionary_source": STATE["dict_name"],
    }


# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):  # bớt ồn
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, code: int = 200) -> None:
        self._send(
            code,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        path = parsed.path

        try:
            if path in ("/", "/index.html"):
                self._send(
                    200, INDEX_HTML.read_bytes(), "text/html; charset=utf-8"
                )
            elif path == "/api/suggest":
                self._json(
                    api_suggest(
                        q.get("prefix", [""])[0], int(q.get("k", ["8"])[0])
                    )
                )
            elif path == "/api/search":
                self._json(api_search(q.get("pattern", [""])[0]))
            elif path == "/api/multi":
                raw = q.get("patterns", [""])[0]
                self._json(api_multi([p.strip() for p in raw.split(",")]))
            elif path == "/api/stats":
                self._json(api_stats())
            else:
                self._json({"error": "not found"}, 404)
        except Exception as exc:  # trả lỗi dạng JSON để UI hiển thị được
            self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Demo web")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument(
        "--text", default=str(ROOT / "data" / "small" / "demo_corpus.txt")
    )
    ap.add_argument(
        "--dict",
        dest="dict_",
        default=str(ROOT / "data" / "dictionaries" / "demo_words.txt"),
    )
    ap.add_argument("--alphabet", default="ascii_lower_digits")
    ap.add_argument("--self-test", action="store_true",
                    help="kiểm tra API rồi thoát (dùng trong CI)")
    args = ap.parse_args()

    text_path, dict_path = Path(args.text), Path(args.dict_)
    for p in (text_path, dict_path):
        if not p.exists():
            print(f"Không tìm thấy: {p}", file=sys.stderr)
            print("Gợi ý: chạy `python scripts/gen_data.py --quick` trước.",
                  file=sys.stderr)
            return 2

    alphabet = get_alphabet(args.alphabet)
    trie = Trie(alphabet)
    trie.insert_many(
        load_dictionary(dict_path, alphabet=alphabet, skip_invalid=True)
    )

    STATE.update(
        text=read_text(text_path),
        trie=trie,
        matchers={},
        text_name=str(text_path.relative_to(ROOT)),
        dict_name=str(dict_path.relative_to(ROOT)),
    )

    if args.self_test:
        assert api_suggest("t", 5)["suggestions"], "suggest rỗng"
        s = api_search("tim")
        assert s["count"] >= 1, "search không tìm thấy"
        assert s["char_comparisons"] <= s["bound_2n"], "vượt chặn 2n"
        m = api_multi(["tim", "kmp"])
        assert m["total_matches"] >= 1
        assert api_stats()["trie"]["num_nodes"] > 1
        print("✓ self-test API: suggest / search / multi / stats đều OK")
        return 0

    print(f"Văn bản : {STATE['text_name']} ({len(STATE['text']):,} ký tự)")
    print(f"Từ điển : {STATE['dict_name']} ({len(trie):,} từ, "
          f"{trie.num_nodes:,} nút)")
    print(f"Σ       : {alphabet.name} (|Σ| = {len(alphabet)})")
    print(f"\n→ Mở http://{args.host}:{args.port}  (Ctrl+C để dừng)")

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng.")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
