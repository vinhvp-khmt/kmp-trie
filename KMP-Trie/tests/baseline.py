"""Lời giải đối chiếu ĐỘC LẬP.

Đề bắt buộc: "Thiết kế kiểm thử có hệ thống và có ít nhất một phương pháp đối
chiếu độc lập" và trừ điểm nặng nếu "không có baseline".

Nguyên tắc khi viết baseline:
  - Cài đặt theo cách NGÂY THƠ nhất, dễ đọc, dễ tin là đúng. Không tối ưu.
  - KHÔNG dùng lại bất kỳ dòng nào của `src/` — nếu dùng chung code thì một lỗi
    logic sẽ xuất hiện ở cả hai phía và test sẽ pass sai.
  - Với KMP có hai baseline độc lập: naive tự viết, và `str.find` của Python
    (một hiện thực hoàn toàn khác, viết bằng C, dùng Crochemore-Perrin).
"""

from __future__ import annotations

from src.common.metrics import OpCounter

__all__ = [
    "naive_search",
    "builtin_search",
    "naive_build_lps",
    "linear_autocomplete",
    "linear_autocomplete_sorted",
    "linear_search_word",
    "linear_starts_with",
    "naive_multi_pattern_search",
]


# --------------------------------------------------------------------------- #
# Baseline cho mô-đun A (KMP)
# --------------------------------------------------------------------------- #
def naive_search(
    text: str,
    pattern: str,
    counter: OpCounter | None = None,
    *,
    overlapping: bool = True,
) -> list[int]:
    """Tìm kiếm ngây thơ O(n·m): thử mọi vị trí bắt đầu.

    Đây là baseline CHÍNH. Đơn giản tới mức có thể kiểm tra bằng mắt.

    >>> naive_search("aaaa", "aa")
    [0, 1, 2]
    >>> naive_search("abc", "d")
    []
    """
    n, m = len(text), len(pattern)
    if m == 0:
        raise ValueError("Mẫu rỗng không hợp lệ")
    result: list[int] = []
    i = 0
    while i <= n - m:
        matched = True
        for j in range(m):
            if counter is not None:
                counter.char_comparisons += 1
            if text[i + j] != pattern[j]:
                matched = False
                break
        if matched:
            result.append(i)
            i += 1 if overlapping else m
        else:
            i += 1
    return result


def builtin_search(text: str, pattern: str, *, overlapping: bool = True) -> list[int]:
    """Baseline THỨ HAI: dùng `str.find` của CPython trong vòng lặp.

    Hiện thực hoàn toàn khác (C, thuật toán Crochemore-Perrin), nên nếu KMP,
    naive và hàm này cùng cho một kết quả thì độ tin cậy rất cao.
    """
    if not pattern:
        raise ValueError("Mẫu rỗng không hợp lệ")
    result: list[int] = []
    step = 1 if overlapping else len(pattern)
    start = 0
    while True:
        pos = text.find(pattern, start)
        if pos == -1:
            break
        result.append(pos)
        start = pos + step
    return result


def naive_build_lps(pattern: str) -> list[int]:
    """Tính π theo ĐỊNH NGHĨA, O(m^3) — đối chiếu cho `build_lps`.

    Với mỗi i, thử mọi độ dài L từ i giảm về 1 và so tiền tố với hậu tố. Chậm,
    nhưng là bản dịch trực tiếp của định nghĩa "biên dài nhất" nên gần như
    không thể sai.

    >>> naive_build_lps("ababaca")
    [0, 0, 1, 2, 3, 0, 1]
    """
    m = len(pattern)
    lps = [0] * m
    for i in range(m):
        s = pattern[: i + 1]
        for length in range(i, 0, -1):  # biên thật sự ⇒ length ≤ i
            if s[:length] == s[len(s) - length :]:
                lps[i] = length
                break
    return lps


def naive_multi_pattern_search(
    text: str, patterns: list[str]
) -> list[tuple[int, int, str]]:
    """Baseline cho Aho-Corasick: chạy naive_search cho từng mẫu rồi gộp.

    Returns:
        Danh sách (start, pattern_index, pattern), sắp theo (end, index) để
        khớp thứ tự sinh của Aho-Corasick.
    """
    out: list[tuple[int, int, str]] = []
    for idx, p in enumerate(patterns):
        for pos in naive_search(text, p):
            out.append((pos, idx, p))
    out.sort(key=lambda t: (t[0] + len(t[2]), t[1]))
    return out


# --------------------------------------------------------------------------- #
# Baseline cho mô-đun B (Trie)
# --------------------------------------------------------------------------- #
def linear_autocomplete(
    words: list[str], prefix: str, k: int = 10
) -> tuple[list[str], bool]:
    """Baseline tổng quát cho danh sách chưa sắp.

    Chi phí O(N·|prefix| + H log H), trong đó H là số từ phân biệt khớp tiền
    tố. Phần sắp xếp là cần thiết để có cùng hợp đồng thứ tự với Trie.

    Phải trả về CÙNG THỨ TỰ với Trie (thứ tự từ điển) để so sánh được.

    Returns:
        (danh sách ≤ k gợi ý, có bị cắt bớt hay không)

    >>> linear_autocomplete(["tin", "tinh", "to"], "t", 2)
    (['tin', 'tinh'], True)
    """
    hits = sorted({w for w in words if w.startswith(prefix)})
    return hits[:k], len(hits) > k


def linear_autocomplete_sorted(
    words: list[str], prefix: str, k: int = 10
) -> tuple[list[str], bool]:
    """Baseline tuyến tính công bằng cho danh sách đã sắp và loại trùng.

    Hàm quét từ đầu danh sách, dùng `startswith` và dừng khi gặp kết quả thứ
    `k+1`. Vì đầu vào đã tăng ngặt, kết quả tự có thứ tự từ điển và không phải
    chịu thêm chi phí `set`/`sorted` như baseline tổng quát.

    Độ phức tạp tệ nhất O(N·|prefix|), bộ nhớ O(k).

    >>> linear_autocomplete_sorted(["tin", "tinh", "to"], "t", 2)
    (['tin', 'tinh'], True)
    """
    if k < 0:
        raise ValueError("k phải ≥ 0")
    out: list[str] = []
    for word in words:
        if word.startswith(prefix):
            if len(out) == k:
                return out, True
            out.append(word)
    return out, False


def linear_search_word(words: list[str], word: str) -> bool:
    """Exact search bằng duyệt tuyến tính."""
    return any(w == word for w in words)


def linear_starts_with(words: list[str], prefix: str) -> bool:
    """Prefix query bằng duyệt tuyến tính."""
    if prefix == "":
        return len(words) > 0
    return any(w.startswith(prefix) for w in words)
