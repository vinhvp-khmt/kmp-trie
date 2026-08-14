#!/usr/bin/env python3
"""Sinh bộ dữ liệu nhiều quy mô cho thực nghiệm.

Đề yêu cầu: "Xây dựng bộ dữ liệu có nhiều quy mô, đo thời gian/bộ nhớ hoặc số
thao tác đặc trưng; không chỉ chụp một lần chạy."

MỌI phần ngẫu nhiên đều dùng SEED CỐ ĐỊNH ⇒ số liệu tái lập được (checklist).

Cách chạy:
    python scripts/gen_data.py                 # sinh toàn bộ
    python scripts/gen_data.py --quick         # bộ nhỏ, chạy nhanh để thử
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.common.alphabet import (  # noqa: E402
    ASCII_LOWER,
    BINARY,
    PRINTABLE_ASCII,
    Alphabet,
)

SEED = 20260728
DATA = ROOT / "data"

# Quy mô văn bản: 10^3 .. 10^7 (bậc 10 và nửa bậc)
TEXT_SIZES = [1_000, 3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000]
TEXT_SIZES_QUICK = [1_000, 10_000, 100_000]

DICT_SIZES = [1_000, 5_000, 20_000, 100_000, 500_000]
DICT_SIZES_QUICK = [1_000, 10_000]


def sha256_file(path: Path) -> str:
    """Mã băm nội dung để kiểm chứng dữ liệu tái sinh byte-for-byte."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# Sinh văn bản
# --------------------------------------------------------------------------- #
def random_text(rng: random.Random, alphabet: Alphabet, n: int) -> str:
    """Văn bản ngẫu nhiên đều trên Σ. Đặc tính: ít khớp một phần."""
    chars = alphabet.chars
    return "".join(rng.choice(chars) for _ in range(n))


def repetitive_text(n: int, period: str = "ab") -> str:
    """Văn bản tuần hoàn. Đặc tính: rất nhiều khớp một phần và chồng lấn."""
    return (period * (n // len(period) + 1))[:n]


def uniform_text(n: int, char: str = "a") -> str:
    """Văn bản một ký tự — ca xấu nhất cho baseline naive."""
    return char * n


def natural_like_text(rng: random.Random, n: int, words: list[str]) -> str:
    """Văn bản giống ngôn ngữ tự nhiên: ghép từ theo phân phối Zipf.

    Đặc tính: độ dài từ và tần suất lệch mạnh — giống dữ liệu thật (log, bài
    viết), nên phản ánh hiệu năng trong ứng dụng hơn là văn bản ngẫu nhiên đều.
    """
    # Trọng số Zipf: từ thứ i có trọng số ~ 1/i
    weights = [1.0 / (i + 1) for i in range(len(words))]
    out: list[str] = []
    total = 0
    while total < n:
        w = rng.choices(words, weights=weights, k=1)[0]
        out.append(w)
        total += len(w) + 1
    return " ".join(out)[:n]


# --------------------------------------------------------------------------- #
# Sinh từ điển
# --------------------------------------------------------------------------- #
SYLLABLE_ONSETS = [
    "b", "c", "ch", "d", "đ", "g", "gh", "h", "k", "kh", "l", "m", "n",
    "ng", "nh", "p", "ph", "qu", "r", "s", "t", "th", "tr", "v", "x",
]
SYLLABLE_NUCLEI = [
    "a", "ai", "an", "ang", "anh", "e", "en", "eo", "i", "ich", "in", "inh",
    "o", "oa", "oi", "ong", "u", "ua", "un", "ung", "uy", "y",
]


def synthetic_dictionary(
    rng: random.Random, size: int, alphabet: Alphabet, max_len: int = 12
) -> list[str]:
    """Từ điển giống ngôn ngữ tự nhiên: nhiều tiền tố chung, độ dài lệch.

    Cách sinh: ghép âm tiết thay vì random ký tự đều. Điều này quan trọng vì
    Trie chỉ có lợi khi từ điển CÓ tiền tố chung — từ điển random đều tạo cây
    gần như không chia sẻ nhánh, làm thực nghiệm không phản ánh ứng dụng thật.
    """
    words: set[str] = set()
    valid_onsets = [s for s in SYLLABLE_ONSETS if alphabet.accepts(s)]
    valid_nuclei = [s for s in SYLLABLE_NUCLEI if alphabet.accepts(s)]

    if not valid_onsets or not valid_nuclei:
        # Bảng chữ cái quá hẹp (ví dụ |Σ|=2): quay về ghép ký tự có tiền tố chung.
        chars = alphabet.chars
        stems = ["".join(rng.choice(chars) for _ in range(3)) for _ in range(64)]
        while len(words) < size:
            stem = rng.choice(stems)
            tail_len = rng.randint(1, max_len - 3)
            words.add(stem + "".join(rng.choice(chars) for _ in range(tail_len)))
        return sorted(words)

    while len(words) < size:
        n_syl = rng.choices([1, 2, 3], weights=[0.35, 0.5, 0.15], k=1)[0]
        w = "".join(
            rng.choice(valid_onsets) + rng.choice(valid_nuclei) for _ in range(n_syl)
        )
        if 1 <= len(w) <= max_len:
            words.add(w)
    return sorted(words)


def uniform_random_dictionary(
    rng: random.Random, size: int, alphabet: Alphabet, length: int = 8
) -> list[str]:
    """Từ điển random đều — đối chứng: ÍT tiền tố chung.

    Dùng để cho thấy lợi ích của Trie phụ thuộc đặc tính dữ liệu.
    """
    chars = alphabet.chars
    words: set[str] = set()
    while len(words) < size:
        words.add("".join(rng.choice(chars) for _ in range(length)))
    return sorted(words)


# --------------------------------------------------------------------------- #
# Mẫu truy vấn
# --------------------------------------------------------------------------- #
def make_patterns(rng: random.Random, text: str, alphabet: Alphabet) -> dict:
    """Sinh các mẫu cho từng nhóm ca kiểm thử, có cấy sẵn nghiệm."""
    lengths = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
    out: dict[str, list[str]] = {"present": [], "absent": [], "adversarial": []}

    for m in lengths:
        if m >= len(text):
            continue
        # Mẫu CÓ trong văn bản: cắt ra từ chính văn bản.
        start = rng.randint(0, len(text) - m)
        out["present"].append(text[start : start + m])

        # Mẫu KHÔNG có: dùng ký tự cuối bảng chữ cái nối nhau (khó trùng).
        rare = alphabet.chars[-1]
        out["absent"].append(rare * m)

        # Mẫu đối kháng: a^(m-1) + b — naive thất bại ở ký tự cuối.
        c0, c1 = alphabet.chars[0], alphabet.chars[1]
        out["adversarial"].append(c0 * (m - 1) + c1)

    return out


# --------------------------------------------------------------------------- #
# Chương trình chính
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Sinh dữ liệu thực nghiệm")
    ap.add_argument("--quick", action="store_true", help="bộ nhỏ để thử nhanh")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    text_sizes = TEXT_SIZES_QUICK if args.quick else TEXT_SIZES
    dict_sizes = DICT_SIZES_QUICK if args.quick else DICT_SIZES

    manifest: dict = {"seed": args.seed, "texts": [], "dictionaries": []}

    def bucket(n: int) -> str:
        return "small" if n <= 10_000 else "medium" if n <= 100_000 else "large"

    # ---------------- Văn bản ---------------- #
    print("Sinh văn bản...")
    base_words = synthetic_dictionary(random.Random(args.seed + 1), 3000, ASCII_LOWER)

    for n in text_sizes:
        specs = [
            (f"random_s26_{n}.txt", random_text(rng, ASCII_LOWER, n), "random đều, |Σ|=26"),
            (f"random_s2_{n}.txt", random_text(rng, BINARY, n), "random đều, |Σ|=2"),
            (f"repetitive_{n}.txt", repetitive_text(n, "ab"), "tuần hoàn 'ab'"),
            (f"uniform_{n}.txt", uniform_text(n), "một ký tự 'a' (ca xấu nhất naive)"),
            (
                f"natural_{n}.txt",
                natural_like_text(rng, n, base_words),
                "giống ngôn ngữ tự nhiên (Zipf)",
            ),
        ]
        for name, content, desc in specs:
            path = DATA / bucket(n) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            manifest["texts"].append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "n": len(content),
                    "kind": name.split("_")[0],
                    "description": desc,
                    "sha256": sha256_file(path),
                }
            )
        print(f"  n = {n:>9,}  ✓ 5 biến thể")

    # ---------------- Mẫu truy vấn ---------------- #
    print("Sinh mẫu truy vấn...")
    biggest = DATA / bucket(text_sizes[-1]) / f"natural_{text_sizes[-1]}.txt"
    patterns = make_patterns(rng, biggest.read_text(encoding="utf-8"), ASCII_LOWER)
    pat_path = DATA / "patterns.json"
    pat_path.write_text(
        json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest["patterns"] = {
        "file": str(pat_path.relative_to(ROOT)),
        "sha256": sha256_file(pat_path),
    }
    print(f"  ✓ {sum(len(v) for v in patterns.values())} mẫu")

    # ---------------- Từ điển ---------------- #
    print("Sinh từ điển...")
    for n in dict_sizes:
        for name, words, desc in [
            (
                f"synthetic_{n}.txt",
                synthetic_dictionary(rng, n, ASCII_LOWER),
                "âm tiết ghép, NHIỀU tiền tố chung (giống ngôn ngữ tự nhiên)",
            ),
            (
                f"uniform_{n}.txt",
                uniform_random_dictionary(rng, n, ASCII_LOWER),
                "random đều dài 8, ÍT tiền tố chung (đối chứng)",
            ),
        ]:
            path = DATA / "dictionaries" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(words) + "\n", encoding="utf-8")
            manifest["dictionaries"].append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "num_words": len(words),
                    "kind": name.split("_")[0],
                    "description": desc,
                    "sha256": sha256_file(path),
                }
            )
        print(f"  N = {n:>9,}  ✓ 2 biến thể")

    # ---------------- Bộ nhỏ để kiểm thử bằng mắt ---------------- #
    tiny = DATA / "small"
    tiny.mkdir(parents=True, exist_ok=True)
    demo_corpus_path = tiny / "demo_corpus.txt"
    demo_corpus_path.write_text(
        "thuat toan tim kiem chuoi kmp va cau truc trie\n"
        "kmp tim moi vi tri xuat hien cua mau trong van ban\n"
        "trie luu tu dien va ho tro autocomplete theo tien to\n"
        "aaaa aa aaa aaaa\n"
        "abab ababab abababab\n",
        encoding="utf-8",
    )
    demo_words_path = DATA / "dictionaries" / "demo_words.txt"
    demo_words_path.write_text(
        "\n".join(
            [
                "thuat", "thuat-toan", "tim", "tim-kiem", "tin", "tinh", "to",
                "toan", "trie", "truc", "tu", "tu-dien", "kmp", "kiem", "chuoi",
                "cau", "autocomplete", "auto", "an", "and", "ant", "banana",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest["demo"] = [
        {
            "file": str(demo_corpus_path.relative_to(ROOT)),
            "sha256": sha256_file(demo_corpus_path),
        },
        {
            "file": str(demo_words_path.relative_to(ROOT)),
            "sha256": sha256_file(demo_words_path),
        },
    ]

    (DATA / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✓ Xong. Manifest: {(DATA / 'MANIFEST.json').relative_to(ROOT)}")
    print(f"  {len(manifest['texts'])} tệp văn bản, "
          f"{len(manifest['dictionaries'])} từ điển, seed = {args.seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
