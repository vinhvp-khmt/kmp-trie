#!/usr/bin/env python3
"""Vẽ biểu đồ từ kết quả benchmark.

Checklist của đề: "hình/bảng phải có chú thích" — mọi hình sinh ra đều có tiêu
đề, nhãn trục KÈM ĐƠN VỊ, chú giải, và một dòng caption ghi nguồn dữ liệu.

Cách chạy:
    python scripts/plot_results.py
    python scripts/plot_results.py --in results/benchmarks --out results/figures
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    print("Cần matplotlib: pip install matplotlib", file=sys.stderr)
    raise SystemExit(3)

IN = ROOT / "results" / "benchmarks"
OUT = ROOT / "results" / "figures"

plt.rcParams.update(
    {
        "figure.dpi": 130,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.figsize": (7.2, 4.4),
    }
)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(row: dict, key: str, default=None):
    v = row.get(key, "")
    if v in ("", None):
        return default
    try:
        return float(v)
    except ValueError:
        return default


def caption(fig, text: str) -> None:
    """Chú thích dưới hình — yêu cầu của đề."""
    fig.text(0.5, -0.06, text, ha="center", va="top", fontsize=7.5, color="#555",
             wrap=True)


# --------------------------------------------------------------------------- #
def fig1_time_vs_n(rows: list[dict], out: Path) -> None:
    """Thời gian theo n, thang log-log, tách theo loại văn bản."""
    kinds = sorted({r["text_kind"] for r in rows})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    for ax, (col_kmp, col_naive, title, ylab) in zip(
        axes,
        [
            ("kmp_median_ns", "naive_median_ns", "Thời gian chạy", "thời gian (ns)"),
            ("kmp_comparisons", "naive_comparisons", "Số phép so sánh ký tự",
             "số phép so sánh"),
        ],
    ):
        for kind in kinds:
            sub = sorted(
                (r for r in rows if r["text_kind"] == kind),
                key=lambda r: num(r, "n", 0),
            )
            ns = [num(r, "n") for r in sub]
            ax.plot(ns, [num(r, col_kmp) for r in sub], "o-", ms=3.5,
                    label=f"KMP · {kind}")
            yv = [(num(r, "n"), num(r, col_naive)) for r in sub
                  if num(r, col_naive) is not None]
            if yv:
                ax.plot([a for a, _ in yv], [b for _, b in yv], "s--", ms=3,
                        alpha=0.55, label=f"naive · {kind}")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("n = độ dài văn bản (ký tự)")
        ax.set_ylabel(ylab)
        ax.set_title(title)
        ax.legend(fontsize=6, ncol=2)

    fig.suptitle("E1 — KMP so với tìm kiếm ngây thơ khi n tăng (m = 64)",
                 fontsize=11)
    caption(fig, "Nguồn: results/benchmarks/e1_scaling_n.csv · trung vị của 7 lần "
                 "lặp · thang log-log · naive chỉ chạy tới n ≤ 300 000")
    fig.savefig(out / "fig1_time_vs_n.png")
    plt.close(fig)


def fig2_comparisons_per_n(rows: list[dict], out: Path) -> None:
    """Tỉ số so sánh / n — bằng chứng trực tiếp cho O(n+m)."""
    kinds = sorted({r["text_kind"] for r in rows})
    fig, ax = plt.subplots()

    for kind in kinds:
        sub = sorted(
            (r for r in rows if r["text_kind"] == kind),
            key=lambda r: num(r, "n", 0),
        )
        ax.plot([num(r, "n") for r in sub],
                [num(r, "kmp_cmp_per_n") for r in sub],
                "o-", ms=4, label=f"KMP · {kind}")
        yv = [(num(r, "n"), num(r, "naive_cmp_per_n")) for r in sub
              if num(r, "naive_cmp_per_n") is not None]
        if yv:
            ax.plot([a for a, _ in yv], [b for _, b in yv], "s--", ms=3,
                    alpha=0.5, label=f"naive · {kind}")

    ax.axhline(2.0, color="crimson", ls=":", lw=1.4,
               label="chặn lý thuyết của KMP = 2")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n = độ dài văn bản (ký tự)")
    ax.set_ylabel("số phép so sánh / n (không đơn vị)")
    ax.set_title("E1 — Số phép so sánh chuẩn hóa theo n (m = 64)")
    ax.legend(fontsize=6.5, ncol=2)
    caption(fig, "KMP: tỉ số PHẲNG và luôn dưới 2 ⇒ tuyến tính, khớp lập luận "
                 "khấu hao. naive: tỉ số TĂNG theo n trên văn bản đối kháng. "
                 "Nguồn: e1_scaling_n.csv")
    fig.savefig(out / "fig2_comparisons_per_n.png")
    plt.close(fig)


def fig3_effect_of_m(rows: list[dict], out: Path) -> None:
    """Ảnh hưởng của m: KMP không đổi, naive tăng."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, kind in zip(axes, ["uniform", "natural"]):
        sub = sorted(
            (r for r in rows if r["text_kind"] == kind),
            key=lambda r: num(r, "m", 0),
        )
        if not sub:
            ax.set_visible(False)
            continue
        ms = [num(r, "m") for r in sub]
        ax.plot(ms, [num(r, "kmp_cmp_per_n") for r in sub], "o-", ms=4,
                label="KMP")
        ax.plot(ms, [num(r, "naive_cmp_per_n") for r in sub], "s--", ms=4,
                label="naive")
        ax.axhline(2.0, color="crimson", ls=":", lw=1.3, label="chặn KMP = 2")
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xlabel("m = độ dài mẫu (ký tự)")
        ax.set_ylabel("số phép so sánh / n")
        ax.set_title(f"văn bản: {kind}")
        ax.legend(fontsize=7)
    fig.suptitle("E2 — Ảnh hưởng của độ dài mẫu m (n cố định)", fontsize=11)
    caption(fig, "KMP: đường PHẲNG ⇒ m không ảnh hưởng số so sánh trên văn bản. "
                 "naive: TĂNG theo m trên văn bản đối kháng a^n. "
                 "Nguồn: e2_scaling_m.csv")
    fig.savefig(out / "fig3_effect_of_m.png")
    plt.close(fig)


def fig4_trie_vs_linear(rows: list[dict], out: Path) -> None:
    """Trie vs duyệt tuyến tính theo N."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    kinds = sorted({r["dict_kind"] for r in rows})

    for kind in kinds:
        sub = sorted((r for r in rows if r["dict_kind"] == kind),
                     key=lambda r: num(r, "N", 0))
        Ns = [num(r, "N") for r in sub]
        axes[0].plot(Ns, [num(r, "trie_query_median_ns") for r in sub],
                     "o-", ms=4, label=f"Trie · {kind}")
        axes[0].plot(Ns, [num(r, "linear_query_median_ns") for r in sub],
                     "s--", ms=4, alpha=0.6, label=f"duyệt tuyến tính · {kind}")
        axes[1].plot(Ns, [num(r, "num_nodes") for r in sub], "o-", ms=4,
                     label=f"số nút · {kind}")
        axes[1].plot(Ns, [num(r, "N") for r in sub], ":", lw=1, alpha=0.5,
                     label=f"N (tham chiếu) · {kind}" if kind == kinds[0] else None)

    axes[0].set_xscale("log"); axes[0].set_yscale("log")
    axes[0].set_xlabel("N = số từ trong từ điển")
    axes[0].set_ylabel("thời gian một truy vấn autocomplete (ns)")
    axes[0].set_title("Chi phí truy vấn (k = 10)")
    axes[0].legend(fontsize=6.5)

    axes[1].set_xscale("log"); axes[1].set_yscale("log")
    axes[1].set_xlabel("N = số từ trong từ điển")
    axes[1].set_ylabel("số nút Trie")
    axes[1].set_title("Bộ nhớ: số nút theo N")
    axes[1].legend(fontsize=6.5)

    fig.suptitle("E3 — Trie so với duyệt tuyến tính khi từ điển lớn dần",
                 fontsize=11)
    caption(fig, "Trie: thời gian gần như PHẲNG theo N (chi phí ~ O(|q|+k)). "
                 "Duyệt tuyến tính: TĂNG tuyến tính theo N. "
                 "'synthetic' = nhiều tiền tố chung; 'uniform' = ít tiền tố "
                 "chung. Nguồn: e3_trie_vs_linear.csv")
    fig.savefig(out / "fig4_trie_vs_linear.png")
    plt.close(fig)


def fig5_early_stop(rows: list[dict], out: Path) -> None:
    """Dừng sớm: số nút duyệt theo k."""
    sub = sorted(
        (r for r in rows if r["experiment"] == "E4_early_stop"),
        key=lambda r: num(r, "k", 0),
    )
    if not sub:
        return
    fig, ax = plt.subplots()
    ks = [num(r, "k") for r in sub]
    ax.plot(ks, [num(r, "nodes_visited") for r in sub], "o-", ms=4,
            label="số nút đã duyệt")
    ax.plot(ks, [num(r, "returned") for r in sub], "s--", ms=3.5, alpha=0.7,
            label="số kết quả trả về")
    hits = num(sub[0], "subtree_hits")
    if hits:
        ax.axhline(hits, color="crimson", ls=":", lw=1.3,
                   label=f"toàn bộ cây con = {int(hits)} từ")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("k = số gợi ý tối đa")
    ax.set_ylabel("số nút / số kết quả")
    ax.set_title("E4 — DFS dừng sớm: chi phí tỉ lệ k, không tỉ lệ cây con")
    ax.legend(fontsize=7.5)
    caption(fig, "Khi k nhỏ, autocomplete chỉ duyệt một phần rất nhỏ của cây "
                 "con dù cây con chứa hàng nghìn từ. Nguồn: "
                 "e4_early_stop.csv")
    fig.savefig(out / "fig5_early_stop.png")
    plt.close(fig)


def fig6_storage_tradeoff(rows: list[dict], out: Path) -> None:
    """dict vs mảng: ô cấp phát và bộ nhớ đỉnh."""
    sub = sorted(
        (r for r in rows if r["experiment"] == "E4_storage_tradeoff"),
        key=lambda r: num(r, "N", 0),
    )
    if not sub:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    Ns = [num(r, "N") for r in sub]
    w = 0.35
    x = range(len(Ns))

    axes[0].bar([i - w / 2 for i in x], [num(r, "dict_nodes") for r in sub],
                w, label="dict: số nút")
    axes[0].bar([i + w / 2 for i in x], [num(r, "array_slots") for r in sub],
                w, label="mảng: số ô cấp phát")
    axes[0].set_yscale("log")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels([f"{int(n):,}" for n in Ns])
    axes[0].set_xlabel("N = số từ")
    axes[0].set_ylabel("số nút / số ô (thang log)")
    axes[0].set_title("Số đơn vị lưu trữ")
    axes[0].legend(fontsize=7.5)

    axes[1].bar([i - w / 2 for i in x],
                [num(r, "dict_peak_mem_bytes", 0) / 1e6 for r in sub], w,
                label="dict")
    axes[1].bar([i + w / 2 for i in x],
                [num(r, "array_peak_mem_bytes", 0) / 1e6 for r in sub], w,
                label="mảng")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels([f"{int(n):,}" for n in Ns])
    axes[1].set_xlabel("N = số từ")
    axes[1].set_ylabel("bộ nhớ đỉnh khi xây (MB)")
    axes[1].set_title("Bộ nhớ đỉnh (tracemalloc)")
    axes[1].legend(fontsize=7.5)

    fig.suptitle("E4 — Trade-off lưu cạnh: hash map so với mảng |Σ| phần tử",
                 fontsize=11)
    caption(fig, "Cùng số nút, biến thể mảng cấp phát |Σ| = 26 ô mỗi nút, phần "
                 "lớn là None ⇒ tốn bộ nhớ hơn nhiều trên cây thưa. "
                 "Nguồn: e4_early_stop.csv")
    fig.savefig(out / "fig6_storage_tradeoff.png")
    plt.close(fig)


def fig7_multipattern(rows: list[dict], out: Path) -> None:
    """Aho-Corasick vs KMP lặp."""
    sub = sorted(rows, key=lambda r: num(r, "num_patterns", 0))
    if not sub:
        return
    fig, ax = plt.subplots()
    ks = [num(r, "num_patterns") for r in sub]
    ax.plot(ks, [num(r, "ac_comparisons") for r in sub], "o-", ms=4,
            label="Aho–Corasick (1 lượt duyệt)")
    ax.plot(ks, [num(r, "kmp_repeated_comparisons") for r in sub], "s--", ms=4,
            label="KMP lặp k lần")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("k = số mẫu tìm đồng thời")
    ax.set_ylabel("số phép so sánh ký tự")
    ax.set_title("E5 (mở rộng) — Aho–Corasick so với KMP lặp lại")
    ax.legend(fontsize=7.5)
    caption(fig, "KMP lặp: chi phí ~ k·n. Aho–Corasick: ~ n, gần như không đổi "
                 "theo k. Nguồn: e5_multipattern.csv")
    fig.savefig(out / "fig7_multipattern.png")
    plt.close(fig)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Vẽ biểu đồ từ CSV benchmark")
    ap.add_argument("--in", dest="in_", default=str(IN))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    src, out = Path(args.in_), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    env_path = src / "environment.json"
    if env_path.exists():
        env = json.loads(env_path.read_text(encoding="utf-8"))
        print("Môi trường của số liệu:")
        print(f"  {env.get('platform')} · Python {env.get('python_version')} · "
              f"repeat = {env.get('repeat')}")

    plots = [
        ("e1_scaling_n.csv", [fig1_time_vs_n, fig2_comparisons_per_n]),
        ("e2_scaling_m.csv", [fig3_effect_of_m]),
        ("e3_trie_vs_linear.csv", [fig4_trie_vs_linear]),
        ("e4_early_stop.csv", [fig5_early_stop]),
        ("e4_storage_tradeoff.csv", [fig6_storage_tradeoff]),
        ("e5_multipattern.csv", [fig7_multipattern]),
    ]

    made = 0
    for name, fns in plots:
        rows = read_csv(src / name)
        if not rows:
            print(f"  (thiếu {name}, bỏ qua)")
            continue
        for fn in fns:
            fn(rows, out)
            made += 1

    print(f"\n✓ Đã sinh {made} biểu đồ trong {out.relative_to(ROOT)}")
    for p in sorted(out.glob("*.png")):
        print(f"  {p.name}  ({p.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
