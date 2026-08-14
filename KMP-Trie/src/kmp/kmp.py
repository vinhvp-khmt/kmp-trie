"""Mô-đun A — So khớp mẫu tuyến tính bằng KMP (Knuth-Morris-Pratt).

===============================================================================
PHÁT BIỂU BÀI TOÁN
===============================================================================
Vào : văn bản T[0..n-1], mẫu P[0..m-1] trên bảng chữ cái Σ bất kỳ.
      KMP chỉ cần phép so sánh BẰNG giữa hai ký tự — không cần thứ tự, không
      cần |Σ| hữu hạn. Đây là khác biệt bản chất so với Trie.
Ra  : tập { i : T[i..i+m-1] = P }, tức MỌI vị trí xuất hiện, KỂ CẢ CHỒNG LẤN.
Ràng buộc: m ≥ 1 (m = 0 bị từ chối tường minh); nếu m > n thì kết quả rỗng.

===============================================================================
HÀM TIỀN TỐ π (LPS — Longest Proper Prefix which is also Suffix)
===============================================================================
Định nghĩa. Một chuỗi B là **biên** (border) của chuỗi S nếu B vừa là tiền tố
thật sự vừa là hậu tố thật sự của S (thật sự: B ≠ S, cho phép B rỗng).

    π[i] = độ dài biên DÀI NHẤT của P[0..i]

Ví dụ P = "ababaca":
    i        : 0  1  2  3  4  5  6
    P[i]     : a  b  a  b  a  c  a
    π[i]     : 0  0  1  2  3  0  1

    π[4] = 3 vì P[0..4] = "ababa" có biên dài nhất là "aba" (dài 3).

===============================================================================
TÍNH ĐÚNG
===============================================================================
Bổ đề 1 (tính đúng của BUILD_LPS). Bằng quy nạp theo i:
  - Cơ sở: π[0] = 0 vì P[0..0] chỉ có biên rỗng.
  - Bước quy nạp: giả sử π[0..i-1] đã đúng và length = π[i-1]. Mọi biên của
    P[0..i] có dạng (một biên B của P[0..i-1]) + P[i], với điều kiện ký tự
    tiếp sau B trong mẫu, tức P[|B|], bằng P[i]. Tập độ dài các biên của
    P[0..i-1] chính là dãy giảm dần
        π[i-1], π[π[i-1]-1], π[π[π[i-1]-1]-1], ...
    Vòng while duyệt đúng dãy này theo thứ tự GIẢM, nên biên hợp lệ đầu tiên
    tìm được là biên DÀI NHẤT. Nếu không có biên nào thỏa thì π[i] = 0.

Bổ đề 2 (KMP không bỏ sót vị trí). Bất biến của vòng lặp chính: trước khi xử
lý T[j], giá trị i thỏa 0 ≤ i < m và
        i = độ dài lớn nhất < m sao cho P[0..i-1] là hậu tố T[0..j-1]
Khi mismatch T[j] ≠ P[i], mọi lần khớp bắt đầu trong (j-i, j) đều bất khả thi
(nếu có, nó sẽ cho một biên của P[0..i-1] dài hơn π[i-1] — mâu thuẫn Bổ đề 1).
Vì vậy dịch i ← π[i-1] không làm mất nghiệm, và con trỏ văn bản j KHÔNG lùi.

Bổ đề 3 (bắt được chồng lấn). Khi i = m ta đã tìm thấy một lần khớp tại
j-m+1. Đặt i ← π[m-1] (KHÔNG phải i ← 0) chính là giữ lại đúng hậu tố dài
nhất của đoạn vừa khớp còn là tiền tố của P, nên lần khớp tiếp theo chồng lấn
lên lần này vẫn được phát hiện.
    Kiểm chứng: T = "aaaa", P = "aa" ⇒ π = [0,1]; kết quả [0,1,2].

===============================================================================
ĐỘ PHỨC TẠP (lập luận khấu hao)
===============================================================================
Thời gian O(n + m):
  - j chỉ tăng, không bao giờ giảm ⇒ ≤ n bước tiến.
  - Mỗi lần mismatch, i giảm THỰC SỰ (vì π[i-1] < i). Mỗi lần khớp, i tăng
    đúng 1. Tổng lượng tăng của i ≤ n, nên tổng lượng giảm cũng ≤ n.
  ⇒ tổng số phép so sánh ≤ 2n. Lập luận tương tự cho BUILD_LPS: ≤ 2m.
Bộ nhớ phụ O(m): chỉ mảng π. Không sao chép văn bản.

Chỉ rõ biến quyết định kích thước: n = |T| và m = |P|. |Σ| KHÔNG xuất hiện
trong độ phức tạp của KMP.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..common.metrics import OpCounter

__all__ = [
    "build_lps",
    "kmp_search",
    "kmp_search_iter",
    "kmp_count",
    "kmp_find_first",
    "KMPMatcher",
    "SearchResult",
]


# --------------------------------------------------------------------------- #
# Hàm tiền tố
# --------------------------------------------------------------------------- #
def build_lps(pattern: str, counter: OpCounter | None = None) -> list[int]:
    """Xây mảng LPS (hàm tiền tố π) của `pattern`.

    Đề yêu cầu tường minh: "Mô-đun KMP phải SINH RA LPS" — nên hàm này là một
    phần của giao diện công khai, không phải chi tiết ẩn bên trong.

    Args:
        pattern: mẫu P, độ dài m ≥ 0.
        counter: bộ đếm tùy chọn; ghi vào `lps_comparisons`.

    Returns:
        Danh sách π độ dài m; π[i] = độ dài biên dài nhất của P[0..i].

    Độ phức tạp: O(m) thời gian (khấu hao), O(m) bộ nhớ.

    >>> build_lps("ababaca")
    [0, 0, 1, 2, 3, 0, 1]
    >>> build_lps("aaaa")
    [0, 1, 2, 3]
    >>> build_lps("abcd")
    [0, 0, 0, 0]
    >>> build_lps("")
    []
    """
    m = len(pattern)
    lps = [0] * m
    if m == 0:
        return lps

    length = 0  # bất biến: length == lps[i-1] ở đầu mỗi vòng lặp
    for i in range(1, m):
        while True:
            if counter is not None:
                counter.lps_comparisons += 1
            if pattern[i] == pattern[length]:
                length += 1
                break
            if length == 0:
                break
            # Lùi theo dãy biên giảm dần — xem Bổ đề 1.
            length = lps[length - 1]
        lps[i] = length
    return lps


# --------------------------------------------------------------------------- #
# Tìm kiếm
# --------------------------------------------------------------------------- #
def kmp_search(
    text: str,
    pattern: str,
    counter: OpCounter | None = None,
    *,
    overlapping: bool = True,
    lps: list[int] | None = None,
) -> list[int]:
    """Tìm mọi vị trí xuất hiện của `pattern` trong `text`.

    Args:
        text: văn bản T.
        pattern: mẫu P; rỗng ⇒ ValueError (quy ước đã ghi trong README).
        counter: bộ đếm tùy chọn (`char_comparisons`, `lps_comparisons`).
        overlapping: True (mặc định) trả cả các lần xuất hiện chồng lấn;
            False chỉ trả các lần xuất hiện rời nhau (dùng cho so sánh với
            hành vi của `str.find` trong vòng lặp bước m).
        lps: mảng π đã tính trước — dùng khi truy vấn cùng một mẫu nhiều lần
            (xem `KMPMatcher`).

    Returns:
        Danh sách chỉ số bắt đầu 0-based, tăng dần.

    Raises:
        ValueError: nếu `pattern` rỗng.

    Độ phức tạp: O(n + m) thời gian, O(m) bộ nhớ phụ.

    >>> kmp_search("aaaa", "aa")
    [0, 1, 2]
    >>> kmp_search("aaaa", "aa", overlapping=False)
    [0, 2]
    >>> kmp_search("abc", "abcd")
    []
    >>> kmp_search("ababcabab", "abab")
    [0, 5]
    """
    if not pattern:
        raise ValueError(
            "Mẫu rỗng không hợp lệ: theo quy ước của hệ thống, mẫu rỗng khớp "
            "tại mọi vị trí nên không mang thông tin. Yêu cầu m ≥ 1."
        )

    n, m = len(text), len(pattern)
    if m > n:
        # Xử lý biên tường minh, không dựa vào vòng lặp tự rỗng.
        return []

    if lps is None:
        lps = build_lps(pattern, counter)

    result: list[int] = []
    # Bất biến: 0 ≤ i < m và i là độ dài lớn nhất < m sao cho tiền tố
    # P[0..i-1] là hậu tố của phần văn bản đã xử lý.
    i = 0

    for j in range(n):
        while True:
            if counter is not None:
                counter.char_comparisons += 1
            if text[j] == pattern[i]:
                i += 1
                break
            if i == 0:
                break
            i = lps[i - 1]  # Bổ đề 2: dịch mẫu, KHÔNG lùi j

        if i == m:
            result.append(j - m + 1)
            # Bổ đề 3: giữ hậu tố dài nhất còn là tiền tố ⇒ bắt được chồng lấn.
            i = lps[m - 1] if overlapping else 0

    return result


def kmp_search_iter(
    text: str,
    pattern: str,
    counter: OpCounter | None = None,
    *,
    overlapping: bool = True,
):
    """Phiên bản generator: sinh từng vị trí khớp.

    Dùng khi chỉ cần vài kết quả đầu trên văn bản rất lớn (bộ nhớ O(m) thay vì
    O(số lần khớp)), ví dụ trong demo hiển thị 100 match đầu tiên.
    """
    if not pattern:
        raise ValueError("Mẫu rỗng không hợp lệ; yêu cầu m ≥ 1.")
    n, m = len(text), len(pattern)
    if m > n:
        return
    lps = build_lps(pattern, counter)
    i = 0
    for j in range(n):
        while True:
            if counter is not None:
                counter.char_comparisons += 1
            if text[j] == pattern[i]:
                i += 1
                break
            if i == 0:
                break
            i = lps[i - 1]
        if i == m:
            yield j - m + 1
            i = lps[m - 1] if overlapping else 0


def kmp_count(text: str, pattern: str, counter: OpCounter | None = None) -> int:
    """Đếm số lần xuất hiện (kể cả chồng lấn) mà không lưu danh sách."""
    return sum(1 for _ in kmp_search_iter(text, pattern, counter))


def kmp_find_first(
    text: str, pattern: str, counter: OpCounter | None = None
) -> int:
    """Vị trí khớp đầu tiên, hoặc -1 nếu không có (giống hợp đồng của str.find)."""
    for pos in kmp_search_iter(text, pattern, counter):
        return pos
    return -1


# --------------------------------------------------------------------------- #
# Bọc lại để tái sử dụng π
# --------------------------------------------------------------------------- #
@dataclass
class SearchResult:
    """Kết quả tìm kiếm, khớp định dạng JSON đã khai báo trong README."""

    pattern: str
    positions: list[int] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.positions)

    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "positions": self.positions,
            "count": self.count,
        }


class KMPMatcher:
    """Mẫu đã tiền xử lý, dùng lại cho nhiều văn bản.

    Lý do tồn tại: trong hệ thống tìm kiếm tương tác, một mẫu thường được áp
    lên nhiều tài liệu. Tính π một lần rồi tái sử dụng biến chi phí từ
    O(k·(n+m)) thành O(m + k·n) cho k tài liệu.

    >>> mt = KMPMatcher("aba")
    >>> mt.lps
    [0, 0, 1]
    >>> mt.search("abababa")
    [0, 2, 4]
    >>> mt.search("xyz")
    []
    """

    __slots__ = ("pattern", "lps")

    def __init__(self, pattern: str) -> None:
        if not pattern:
            raise ValueError("Mẫu rỗng không hợp lệ; yêu cầu m ≥ 1.")
        self.pattern = pattern
        self.lps = build_lps(pattern)

    def __repr__(self) -> str:
        return f"KMPMatcher(pattern={self.pattern!r}, m={len(self.pattern)})"

    def search(
        self,
        text: str,
        counter: OpCounter | None = None,
        *,
        overlapping: bool = True,
    ) -> list[int]:
        return kmp_search(
            text,
            self.pattern,
            counter,
            overlapping=overlapping,
            lps=self.lps,
        )

    def result(self, text: str, counter: OpCounter | None = None) -> SearchResult:
        return SearchResult(self.pattern, self.search(text, counter))

    def borders(self) -> list[int]:
        """Dãy độ dài mọi biên của toàn mẫu, giảm dần.

        Ứng dụng: giải thích trực quan trong slide vì sao KMP lùi theo dãy này.

        >>> KMPMatcher("abaaba").borders()
        [3, 1, 0]
        >>> KMPMatcher("abcd").borders()
        [0]
        """
        out = []
        k = self.lps[-1]
        while k > 0:
            out.append(k)
            k = self.lps[k - 1]
        out.append(0)
        return out
