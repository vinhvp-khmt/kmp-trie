#!/usr/bin/env python3
"""Chạy thực nghiệm và xuất bảng kết quả CSV.

Đề yêu cầu:
  - "Đo thời gian/bộ nhớ hoặc số thao tác đặc trưng; KHÔNG chỉ chụp một lần chạy."
  - "Tệp kết quả thực nghiệm dạng bảng; có thông tin môi trường chạy."

Bốn thí nghiệm:
  E1. KMP vs naive vs str.find theo n  — kiểm chứng O(n+m) và lợi thế trên ca đối kháng
  E2. KMP theo m                       — kiểm chứng m không ảnh hưởng số so sánh của KMP
  E3. Trie vs duyệt tuyến tính theo N  — kiểm chứng chi phí độc lập với N
  E4. Trie: bộ nhớ, số nút, dict vs mảng, dừng sớm theo k

Cách chạy:
    python scripts/run_benchmark.py                    # đầy đủ
    python scripts/run_benchmark.py --quick            # nhanh
    python scripts/run_benchmark.py --repeat 9         # tăng số lần lặp
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.common.alphabet import ASCII_LOWER  # noqa: E402
from src.common.metrics import OpCounter, environment_info, measure  # noqa: E402
from src.kmp import AhoCorasick, KMPMatcher, build_lps, kmp_search  # noqa: E402
from src.trie import ArrayTrie, Trie  # noqa: E402
from tests.baseline import (  # noqa: E402
    builtin_search,
    linear_autocomplete_sorted,
    naive_search,
)

DATA = ROOT / "data"
OUT = ROOT / "results" / "benchmarks"

#: Ngân sách cho baseline naive: số phép so sánh tối đa cho phép trong MỘT lần
#: chạy. Naive là O(n·m) nên trên (n, m) lớn nó mất hàng phút — vượt ngân sách
#: thì ta BỎ QUA và ghi ô rỗng trong CSV, đồng thời ghi rõ lý do trong cột
#: `naive_skipped`. Đây là quyết định trung thực về phương pháp đo: không cắt
#: bớt số liệu của thuật toán chính, chỉ giới hạn baseline.
NAIVE_BUDGET = 8_000_000


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        print(f"  (bỏ qua {path.name}: không có dữ liệu)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"  → {path.relative_to(ROOT)} ({len(rows)} dòng)")


def _load(kind: str, n: int) -> str | None:
    for bucket in ("small", "medium", "large"):
        p = DATA / bucket / f"{kind}_{n}.txt"
        if p.exists():
            return p.read_text(encoding="utf-8")
    return None


# =========================================================================== #
# E1 — KMP vs baseline theo n
# =========================================================================== #
def exp1_scaling_in_n(sizes: list[int], repeat: int) -> list[dict]:
    """Cố định m, tăng n. Ba loại văn bản × ba thuật toán.

    Kỳ vọng:
      - KMP: char_comparisons / n ≈ hằng số ⇒ tuyến tính.
      - naive trên văn bản 'uniform': char_comparisons / n ≈ m ⇒ tích.
    """
    rows: list[dict] = []
    m = 64

    for kind in ("natural", "random_s26", "random_s2", "repetitive", "uniform"):
        for n in sizes:
            text = _load(kind, n)
            if text is None:
                continue

            # Mẫu đối kháng cho ca uniform/repetitive; mẫu cắt từ văn bản cho ca khác.
            if kind == "uniform":
                pattern = "a" * (m - 1) + "b"      # naive thất bại ở ký tự cuối
            elif kind == "repetitive":
                pattern = ("ab" * m)[:m]
            else:
                pattern = text[len(text) // 3 : len(text) // 3 + m]
            if len(pattern) < m:
                continue

            matcher = KMPMatcher(pattern)

            c_kmp = OpCounter()
            t_kmp = measure(lambda: matcher.search(text), repeat=repeat)
            t_preprocess = measure(lambda: KMPMatcher(pattern), repeat=repeat)
            matcher.search(text, c_kmp)

            c_naive = OpCounter()
            # naive là O(n·m): chỉ chạy khi nằm trong ngân sách.
            run_naive = len(text) * m <= NAIVE_BUDGET
            if run_naive:
                t_naive = measure(
                    lambda: naive_search(text, pattern), repeat=repeat
                )
                naive_search(text, pattern, c_naive)

            t_builtin = measure(lambda: builtin_search(text, pattern), repeat=repeat)

            n_matches = len(matcher.search(text))

            rows.append(
                {
                    "experiment": "E1_scaling_n",
                    "text_kind": kind,
                    "n": len(text),
                    "m": m,
                    "n_matches": n_matches,
                    "kmp_median_ns": round(t_kmp.median_ns),
                    "kmp_preprocess_median_ns": round(t_preprocess.median_ns),
                    "kmp_one_shot_median_ns": round(
                        t_preprocess.median_ns + t_kmp.median_ns
                    ),
                    "kmp_rel_spread": round(t_kmp.relative_spread, 4),
                    "kmp_comparisons": c_kmp.char_comparisons,
                    "kmp_cmp_per_n": round(c_kmp.char_comparisons / len(text), 4),
                    "naive_median_ns": round(t_naive.median_ns) if run_naive else "",
                    "naive_comparisons": c_naive.char_comparisons if run_naive else "",
                    "naive_cmp_per_n": (
                        round(c_naive.char_comparisons / len(text), 4)
                        if run_naive
                        else ""
                    ),
                    "speedup_cmp": (
                        round(c_naive.char_comparisons / c_kmp.char_comparisons, 2)
                        if run_naive and c_kmp.char_comparisons
                        else ""
                    ),
                    "builtin_median_ns": round(t_builtin.median_ns),
                    "naive_skipped": "" if run_naive else f"n·m > {NAIVE_BUDGET:,}",
                    "repeat": repeat,
                }
            )
    return rows


# =========================================================================== #
# E2 — ảnh hưởng của m
# =========================================================================== #
def exp2_scaling_in_m(n: int, repeat: int) -> list[dict]:
    """Cố định n, tăng m. Kỳ vọng: số so sánh của KMP KHÔNG tăng theo m,
    còn của naive tăng gần tuyến tính theo m trên văn bản đối kháng."""
    rows: list[dict] = []
    text_unif = _load("uniform", n)
    text_nat = _load("natural", n)
    if text_unif is None:
        return rows

    for m in (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024):
        if m >= n:
            break
        for kind, text, pattern in (
            ("uniform", text_unif, "a" * (m - 1) + "b" if m > 1 else "b"),
            (
                "natural",
                text_nat,
                (text_nat[100 : 100 + m] if text_nat else None),
            ),
        ):
            if text is None or pattern is None or len(pattern) < m:
                continue

            c_kmp, c_naive = OpCounter(), OpCounter()
            matcher = KMPMatcher(pattern)
            t_kmp = measure(lambda: matcher.search(text), repeat=repeat)
            matcher.search(text, c_kmp)

            # KMPMatcher tính π sẵn trong hàm khởi tạo (để tái sử dụng giữa các
            # truy vấn), nên counter của search() KHÔNG chứa chi phí xây π.
            # Đo riêng ở đây để kiểm chứng chặn ≤ 2m của BUILD_LPS.
            c_lps = OpCounter()
            build_lps(pattern, c_lps)
            t_lps = measure(lambda: build_lps(pattern), repeat=repeat)

            run_naive = len(text) * m <= NAIVE_BUDGET
            if run_naive:
                t_naive = measure(
                    lambda: naive_search(text, pattern), repeat=repeat
                )
                naive_search(text, pattern, c_naive)

            rows.append(
                {
                    "experiment": "E2_scaling_m",
                    "text_kind": kind,
                    "n": len(text),
                    "m": m,
                    "n_matches": len(matcher.search(text)),
                    "kmp_median_ns": round(t_kmp.median_ns),
                    "kmp_comparisons": c_kmp.char_comparisons,
                    "kmp_cmp_per_n": round(c_kmp.char_comparisons / len(text), 4),
                    "lps_comparisons": c_lps.lps_comparisons,
                    "lps_cmp_per_m": round(c_lps.lps_comparisons / m, 4),
                    "lps_build_median_ns": round(t_lps.median_ns),
                    "naive_median_ns": round(t_naive.median_ns) if run_naive else "",
                    "naive_comparisons": c_naive.char_comparisons if run_naive else "",
                    "naive_cmp_per_n": (
                        round(c_naive.char_comparisons / len(text), 4)
                        if run_naive else ""
                    ),
                    "speedup_cmp": (
                        round(c_naive.char_comparisons / c_kmp.char_comparisons, 2)
                        if run_naive and c_kmp.char_comparisons
                        else ""
                    ),
                    "naive_skipped": "" if run_naive else f"n·m > {NAIVE_BUDGET:,}",
                    "repeat": repeat,
                }
            )
    return rows


# =========================================================================== #
# E3 — Trie vs duyệt tuyến tính theo N
# =========================================================================== #
def exp3_trie_vs_linear(dict_sizes: list[int], repeat: int) -> list[dict]:
    """Kỳ vọng: chi phí truy vấn Trie KHÔNG phụ thuộc N, còn duyệt tuyến tính
    tỉ lệ N. Đây là lý do dùng Trie thay vì list trong hệ thống autocomplete."""
    rows: list[dict] = []
    k = 10

    for kind in ("synthetic", "uniform"):
        for n in dict_sizes:
            path = DATA / "dictionaries" / f"{kind}_{n}.txt"
            if not path.exists():
                continue
            words = [w.strip() for w in path.read_text(encoding="utf-8").splitlines() if w.strip()]
            if words != sorted(set(words)):
                raise ValueError(f"{path} phải được sắp tăng ngặt và loại trùng")

            trie = Trie(ASCII_LOWER)
            c_build = OpCounter()
            t_build = measure(
                lambda: Trie(ASCII_LOWER).insert_many(words), repeat=repeat
            )
            trie.insert_many(words, c_build)

            # Chọn tiền tố có kết quả (2 ký tự đầu của một từ giữa danh sách).
            probe = words[len(words) // 2][:2]

            c_q = OpCounter()
            t_trie = measure(lambda: trie.autocomplete(probe, k), repeat=repeat)
            trie.autocomplete(probe, k, c_q)

            t_linear = measure(
                lambda: linear_autocomplete_sorted(words, probe, k), repeat=repeat
            )

            # Exact search: chi phí phải độc lập N
            word_present = words[len(words) // 2]
            c_s = OpCounter()
            t_search = measure(lambda: trie.search(word_present), repeat=repeat)
            trie.search(word_present, c_s)

            st = trie.stats()
            mem = measure(
                lambda: Trie(ASCII_LOWER).insert_many(words),
                repeat=1,
                warmup=0,
                track_memory=True,
            )

            rows.append(
                {
                    "experiment": "E3_trie_vs_linear",
                    "dict_kind": kind,
                    "N": len(words),
                    "num_words_distinct": st["num_words"],
                    "num_nodes": st["num_nodes"],
                    "nodes_per_char": round(float(st["nodes_per_char"]), 4),
                    "max_depth": st["max_depth"],
                    "probe_prefix": probe,
                    "k": k,
                    "build_median_ns": round(t_build.median_ns),
                    "build_nodes_created": c_build.nodes_created,
                    "trie_query_median_ns": round(t_trie.median_ns),
                    "trie_query_nodes_visited": c_q.nodes_visited,
                    "linear_query_median_ns": round(t_linear.median_ns),
                    "query_speedup": (
                        round(t_linear.median_ns / t_trie.median_ns, 2)
                        if t_trie.median_ns
                        else ""
                    ),
                    "trie_search_median_ns": round(t_search.median_ns),
                    "trie_search_nodes_visited": c_s.nodes_visited,
                    "peak_mem_bytes": mem.peak_mem_bytes,
                    "bytes_per_word": (
                        round(mem.peak_mem_bytes / len(words), 1) if words else ""
                    ),
                    "repeat": repeat,
                }
            )
    return rows


# =========================================================================== #
# E4 — dừng sớm theo k, và trade-off dict vs mảng
# =========================================================================== #
def exp4_early_stop_and_storage(repeat: int) -> tuple[list[dict], list[dict]]:
    """Trả về (bảng dừng sớm, bảng trade-off lưu cạnh).

    Hai bảng có tập cột khác nhau nên được ghi ra HAI tệp CSV riêng — trộn
    chúng vào một tệp sẽ tạo bảng thưa, khó đọc và khó vẽ.
    """
    rows: list[dict] = []
    storage: list[dict] = []
    path = DATA / "dictionaries" / "synthetic_20000.txt"
    if not path.exists():
        path = next((DATA / "dictionaries").glob("synthetic_*.txt"), None)
    if path is None:
        return rows, storage

    words = [w.strip() for w in path.read_text(encoding="utf-8").splitlines() if w.strip()]
    trie = Trie(ASCII_LOWER)
    trie.insert_many(words)

    # --- dừng sớm theo k, trên tiền tố 1 ký tự (cây con rất lớn) --- #
    probe = words[len(words) // 2][:1]
    total_hits = sum(1 for w in words if w.startswith(probe))
    for k in (1, 5, 10, 20, 50, 100, 500, 1000, max(total_hits, 1)):
        c = OpCounter()
        t = measure(lambda: trie.autocomplete(probe, k), repeat=repeat)
        r = trie.autocomplete(probe, k, c)
        rows.append(
            {
                "experiment": "E4_early_stop",
                "N": len(words),
                "probe_prefix": probe,
                "subtree_hits": total_hits,
                "k": k,
                "returned": len(r.suggestions),
                "truncated": r.truncated,
                "nodes_visited": c.nodes_visited,
                "nodes_per_result": (
                    round(c.nodes_visited / len(r.suggestions), 2)
                    if r.suggestions
                    else ""
                ),
                "median_ns": round(t.median_ns),
                "repeat": repeat,
            }
        )

    # --- dict vs mảng: bộ nhớ --- #
    for size in (1_000, 5_000, 20_000):
        sub = words[:size]
        if len(sub) < size:
            continue
        d = Trie(ASCII_LOWER)
        d.insert_many(sub)
        a = ArrayTrie(ASCII_LOWER)
        for w in sub:
            a.insert(w)

        md = measure(
            lambda: (lambda t: [t.insert(w) for w in sub])(Trie(ASCII_LOWER)),
            repeat=1, warmup=0, track_memory=True,
        )
        ma = measure(
            lambda: (lambda t: [t.insert(w) for w in sub])(ArrayTrie(ASCII_LOWER)),
            repeat=1, warmup=0, track_memory=True,
        )

        storage.append(
            {
                "experiment": "E4_storage_tradeoff",
                "N": len(sub),
                "alphabet_size": len(ASCII_LOWER),
                "dict_nodes": d.num_nodes,
                "array_nodes": a.num_nodes,
                "array_slots": a.num_slots,
                "slots_per_node": len(ASCII_LOWER),
                "dict_peak_mem_bytes": md.peak_mem_bytes,
                "array_peak_mem_bytes": ma.peak_mem_bytes,
                "array_over_dict": (
                    round(ma.peak_mem_bytes / md.peak_mem_bytes, 2)
                    if md.peak_mem_bytes
                    else ""
                ),
            }
        )

    return rows, storage


# =========================================================================== #
# E5 — Aho-Corasick vs KMP lặp nhiều mẫu (phần mở rộng)
# =========================================================================== #
def exp5_multipattern(repeat: int) -> list[dict]:
    rows: list[dict] = []
    text = _load("natural", 100_000) or _load("natural", 10_000)
    if text is None:
        return rows

    words = sorted({w for w in text.split() if 3 <= len(w) <= 8})
    for num in (1, 2, 5, 10, 25, 50, 100):
        if num > len(words):
            break
        patterns = words[:: max(1, len(words) // num)][:num]
        if len(patterns) < num:
            continue

        ac = AhoCorasick(patterns)
        c_ac = OpCounter()
        t_ac = measure(lambda: ac.search(text), repeat=repeat)
        ac.search(text, c_ac)

        c_kmp = OpCounter()

        def run_kmp():
            for p in patterns:
                kmp_search(text, p)

        t_kmp = measure(run_kmp, repeat=repeat)
        for p in patterns:
            kmp_search(text, p, c_kmp)

        rows.append(
            {
                "experiment": "E5_multipattern",
                "n": len(text),
                "num_patterns": len(patterns),
                "total_pattern_len": sum(len(p) for p in patterns),
                "ac_nodes": ac.num_nodes,
                "ac_median_ns": round(t_ac.median_ns),
                "ac_comparisons": c_ac.char_comparisons,
                "kmp_repeated_median_ns": round(t_kmp.median_ns),
                "kmp_repeated_comparisons": c_kmp.char_comparisons,
                "cmp_ratio_kmp_over_ac": (
                    round(c_kmp.char_comparisons / c_ac.char_comparisons, 2)
                    if c_ac.char_comparisons
                    else ""
                ),
                "time_ratio_kmp_over_ac": (
                    round(t_kmp.median_ns / t_ac.median_ns, 2)
                    if t_ac.median_ns
                    else ""
                ),
                "num_matches": len(ac.search(text)),
                "repeat": repeat,
            }
        )
    return rows


# =========================================================================== #
def main() -> int:
    ap = argparse.ArgumentParser(description="Chạy thực nghiệm")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--repeat", type=int, default=5, help="số lần lặp mỗi phép đo (≥5)")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument(
        "--only",
        default="1,2,3,4,5",
        help="chỉ chạy các thí nghiệm này, ví dụ --only 3,4",
    )
    ap.add_argument("--n-for-m", type=int, default=0,
                    help="n dùng cho E2 (0 = tự chọn)")
    ap.add_argument("--dict-sizes", default="",
                    help="danh sách N cho E3, ví dụ 1000,5000,20000")
    args = ap.parse_args()
    if args.repeat < 5:
        ap.error("--repeat phải ≥ 5 để báo cáo trung vị ổn định")
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sizes = (
        [1_000, 10_000, 100_000]
        if args.quick
        else [1_000, 3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000]
    )
    dict_sizes = [1_000, 10_000] if args.quick else [1_000, 5_000, 20_000, 100_000, 500_000]
    if args.dict_sizes:
        dict_sizes = [int(s) for s in args.dict_sizes.split(",") if s.strip()]
    n_for_m = args.n_for_m or (10_000 if args.quick else 30_000)

    env = environment_info()
    env["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    env["repeat"] = str(args.repeat)
    env["quick_mode"] = str(args.quick)
    env["units"] = "thời gian: nanosecond (ns); bộ nhớ: byte; so sánh: số phép"
    (out / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Môi trường chạy:")
    for k, v in env.items():
        print(f"  {k}: {v}")
    print()

    if "1" in only:
        print("E1 — KMP vs baseline theo n")
        _write_csv(out / "e1_scaling_n.csv", exp1_scaling_in_n(sizes, args.repeat))

    if "2" in only:
        print("E2 — ảnh hưởng của m")
        _write_csv(out / "e2_scaling_m.csv", exp2_scaling_in_m(n_for_m, args.repeat))

    if "3" in only:
        print("E3 — Trie vs duyệt tuyến tính theo N")
        _write_csv(
            out / "e3_trie_vs_linear.csv",
            exp3_trie_vs_linear(dict_sizes, args.repeat),
        )

    if "4" in only:
        print("E4 — dừng sớm và trade-off lưu cạnh")
        early, storage = exp4_early_stop_and_storage(args.repeat)
        _write_csv(out / "e4_early_stop.csv", early)
        _write_csv(out / "e4_storage_tradeoff.csv", storage)

    if "5" in only:
        print("E5 — Aho-Corasick vs KMP lặp")
        _write_csv(out / "e5_multipattern.csv", exp5_multipattern(args.repeat))

    print(f"\n✓ Xong. Kết quả trong {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
