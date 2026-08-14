"""MỞ RỘNG — Aho-Corasick: so khớp nhiều mẫu đồng thời.

Đây là phần "Mở rộng khuyến khích" của đề, và là mở rộng có giá trị học thuật
cao nhất cho chuyên đề 10, vì nó **nối hai mô-đun lại với nhau**:

    KMP                              Aho-Corasick
    ---------------------------      -----------------------------------------
    π trên MỘT mẫu (mảng)            failure link trên TRIE của NHIỀU mẫu
    π[i] = biên dài nhất của P[0..i] fail(u) = nút biểu diễn hậu tố thật sự
                                     dài nhất của str(u) còn là tiền tố của
                                     một mẫu nào đó
    lùi theo dãy biên khi mismatch   lùi theo dãy fail khi mismatch
    O(n + m)                         O(n + Σm_i + số lần khớp)

Nói cách khác: Aho-Corasick = Trie (mô-đun B) + ý tưởng hàm tiền tố (mô-đun A).
Khi từ điển chỉ có một mẫu, Trie suy biến thành một đường thẳng và failure link
trùng đúng với mảng π — có kiểm chứng trong tests/unit/test_aho_corasick.py.

TÍNH ĐÚNG
---------
Bất biến khi duyệt văn bản: sau khi đọc T[0..j], nút hiện tại `node` biểu diễn
hậu tố DÀI NHẤT của T[0..j] còn là tiền tố của một mẫu. Chứng minh bằng quy nạp
giống Bổ đề 2 của KMP, với dãy biên thay bằng dãy fail.

Mọi mẫu kết thúc tại vị trí j chính là các mẫu nằm trên chuỗi
    node, fail(node), fail(fail(node)), ...
Để tránh duyệt lại dãy fail mỗi bước, ta nén nó thành `output_link`: con trỏ
tới nút gần nhất trong dãy fail có is_end = True. Nhờ vậy tổng chi phí liệt kê
kết quả tỉ lệ SỐ LẦN KHỚP, không phải độ dài dãy fail.

ĐỘ PHỨC TẠP
-----------
Xây : O(Σ|P_i| · chi phí truy cập cạnh) — với dict là O(Σ|P_i|) khấu hao.
Tìm : O(n + số lần khớp).
Bộ nhớ: O(Σ|P_i|) nút.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from ..common.metrics import OpCounter

__all__ = ["AhoCorasick", "Match"]


@dataclass(frozen=True)
class Match:
    """Một lần khớp: mẫu thứ `pattern_index` kết thúc tại `end` (bao gồm)."""

    start: int
    end: int
    pattern_index: int
    pattern: str

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "pattern_index": self.pattern_index,
            "pattern": self.pattern,
        }


class _Node:
    __slots__ = ("children", "fail", "output_link", "pattern_index", "depth")

    def __init__(self, depth: int = 0) -> None:
        self.children: dict[str, _Node] = {}
        self.fail: _Node | None = None
        self.output_link: _Node | None = None
        self.pattern_index: int = -1  # -1 ⇒ không phải cuối mẫu nào
        self.depth: int = depth


class AhoCorasick:
    """So khớp đồng thời một tập mẫu.

    >>> ac = AhoCorasick(["he", "she", "his", "hers"])
    >>> [(m.start, m.pattern) for m in ac.search("ushers")]
    [(1, 'she'), (2, 'he'), (2, 'hers')]
    >>> ac.count_all("ushers")
    {'he': 1, 'she': 1, 'his': 0, 'hers': 1}
    """

    __slots__ = ("_root", "patterns", "_num_nodes")

    def __init__(self, patterns: list[str]) -> None:
        if not patterns:
            raise ValueError("Cần ít nhất một mẫu")
        for p in patterns:
            if not p:
                raise ValueError("Mẫu rỗng không hợp lệ")

        self.patterns = list(patterns)
        self._root = _Node(0)
        self._num_nodes = 1
        self._build_trie()
        self._build_failure_links()

    # ------------------------------------------------------------------ #
    # Xây dựng
    # ------------------------------------------------------------------ #
    def _build_trie(self) -> None:
        """Bước 1: xây Trie các mẫu (giống hệt mô-đun B)."""
        for idx, pattern in enumerate(self.patterns):
            node = self._root
            for ch in pattern:
                nxt = node.children.get(ch)
                if nxt is None:
                    nxt = _Node(node.depth + 1)
                    node.children[ch] = nxt
                    self._num_nodes += 1
                node = nxt
            # Nếu cùng một mẫu xuất hiện hai lần, giữ chỉ số đầu tiên.
            if node.pattern_index == -1:
                node.pattern_index = idx

    def _build_failure_links(self) -> None:
        """Bước 2: BFS theo tầng để xây fail và output_link.

        Vì fail(u) luôn có depth nhỏ hơn depth(u), BFS bảo đảm khi xử lý u thì
        fail của mọi nút nông hơn đã sẵn sàng — đây là điều kiện để công thức
        truy hồi dưới đây đúng.
        """
        root = self._root
        root.fail = root
        queue: deque[_Node] = deque()

        # Tầng 1: fail luôn là gốc.
        for child in root.children.values():
            child.fail = root
            queue.append(child)

        while queue:
            node = queue.popleft()
            for ch, child in node.children.items():
                # Truy hồi: đi theo dãy fail của node tới khi có cạnh ch.
                f = node.fail
                assert f is not None
                while f is not root and ch not in f.children:
                    f = f.fail
                    assert f is not None
                candidate = f.children.get(ch)
                child.fail = candidate if candidate is not None and candidate is not child else root

                # output_link: nút gần nhất trong dãy fail là cuối một mẫu.
                cf = child.fail
                child.output_link = (
                    cf if cf.pattern_index != -1 else cf.output_link
                )
                queue.append(child)

    # ------------------------------------------------------------------ #
    # Truy vấn
    # ------------------------------------------------------------------ #
    def search(
        self, text: str, counter: OpCounter | None = None
    ) -> list[Match]:
        """Trả về mọi lần khớp của mọi mẫu, sắp theo vị trí kết thúc.

        Độ phức tạp: O(n + số lần khớp).
        """
        matches: list[Match] = []
        node = self._root
        root = self._root

        for j, ch in enumerate(text):
            # Lùi theo dãy fail tới khi có cạnh ch (hoặc về gốc).
            while node is not root and ch not in node.children:
                if counter is not None:
                    counter.char_comparisons += 1
                node = node.fail  # type: ignore[assignment]
            if counter is not None:
                counter.char_comparisons += 1
            nxt = node.children.get(ch)
            node = nxt if nxt is not None else root
            if counter is not None:
                counter.nodes_visited += 1

            # Liệt kê mọi mẫu kết thúc tại j, qua output_link.
            out: _Node | None = node if node.pattern_index != -1 else node.output_link
            while out is not None:
                idx = out.pattern_index
                pat = self.patterns[idx]
                matches.append(Match(j - len(pat) + 1, j, idx, pat))
                out = out.output_link

        return matches

    def count_all(self, text: str) -> dict[str, int]:
        """Số lần xuất hiện của từng mẫu (mẫu không xuất hiện ⇒ 0)."""
        counts = {p: 0 for p in self.patterns}
        for m in self.search(text):
            counts[m.pattern] += 1
        return counts

    def failure_array(self) -> list[int]:
        """Trả về dãy depth(fail(u)) theo thứ tự BFS.

        Dùng cho kiểm chứng: khi chỉ có MỘT mẫu, dãy này phải trùng đúng với
        mảng LPS của mẫu đó.
        """
        out: list[int] = []
        queue: deque[_Node] = deque(
            self._root.children[c] for c in sorted(self._root.children)
        )
        while queue:
            node = queue.popleft()
            out.append(node.fail.depth if node.fail else 0)
            for c in sorted(node.children):
                queue.append(node.children[c])
        return out

    @property
    def num_nodes(self) -> int:
        return self._num_nodes

    def __repr__(self) -> str:
        return (
            f"AhoCorasick(num_patterns={len(self.patterns)}, "
            f"num_nodes={self._num_nodes})"
        )
